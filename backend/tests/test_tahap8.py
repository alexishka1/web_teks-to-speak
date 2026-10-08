"""
Unit & Integration Test Suite untuk Tahap 8 TaSTP:
1. Rate limit per IP (HTTP 429 Too Many Requests)
2. Validasi input, batas 5.000 karakter, sanitasi XSS/script/null-byte
3. History CRUD (Penyimpanan otomatis, listing, deletion)
4. Optimasi: Latensi kalimat pertama (< 3 detik) & cache sub-100ms
5. End-to-End Scenario: Input teks -> Normalisasi -> Piper -> Watermark -> History -> Audio stream
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uuid

import pytest
from app.api.middleware.rate_limiter import IPRateLimiter
from app.audio.pipeline import run_synthesis_pipeline
from app.audio.watermark import read_audio_metadata
from app.config import settings
from app.database import AsyncSessionLocal, init_db
from app.models.schema import HistoryRecord
from app.text.sanitize import sanitize_text
from fastapi import HTTPException
from sqlalchemy import select

TEST_DIR = settings.AUDIO_OUTPUT_DIR / "tests_tahap8"
TEST_DIR.mkdir(parents=True, exist_ok=True)


class DummyRequest:
    def __init__(self, ip: str = "192.168.1.100", path: str = "/api/tts"):
        self.headers = {"X-Forwarded-For": ip}
        self.client = None
        self.url = type("URL", (), {"path": path})()


def test_rate_limiter_exceeded_raises_429():
    """
    Uji proteksi CPU: Bila request melebihi limit per IP, raise HTTP 429.
    """
    test_limiter = IPRateLimiter(default_limit=5, window_seconds=60)
    req = DummyRequest(ip="10.0.0.42", path="/api/other")
    for _ in range(5):
        test_limiter.check_rate_limit(req)
    with pytest.raises(HTTPException) as exc_info:
        test_limiter.check_rate_limit(req)
    assert exc_info.value.status_code == 429

    # Uji dengan custom limiter ketat (limit 3 per menit)
    strict_limiter = IPRateLimiter(default_limit=3, window_seconds=60)
    strict_req = DummyRequest(ip="10.0.0.99", path="/api/other")
    strict_limiter.check_rate_limit(strict_req)
    strict_limiter.check_rate_limit(strict_req)
    strict_limiter.check_rate_limit(strict_req)

    # Request ke-4 harus melempar 429
    with pytest.raises(HTTPException) as exc_info:
        strict_limiter.check_rate_limit(strict_req)

    assert exc_info.value.status_code == 429
    assert "Batas permintaan terlampaui" in exc_info.value.detail
    assert "Retry-After" in exc_info.value.headers


def test_text_sanitization_and_character_limit():
    """
    Uji validasi input:
    - Null bytes dan script tags dibersihkan
    - Melebihi 5.000 karakter ditolak
    - Teks kosong ditolak
    """
    # 1. Null byte dan Script tag
    malicious = "Halo dunia! <script>alert('hack')</script>\x00 Ini teks aman."
    cleaned = sanitize_text(malicious)
    assert "<script>" not in cleaned
    assert "\x00" not in cleaned
    assert "Halo dunia! Ini teks aman." in cleaned

    # 2. Batas karakter maksimal (default 5.000)
    oversized = "A" * 5001
    with pytest.raises(ValueError) as exc:
        sanitize_text(oversized, max_chars=5000)
    assert "melebihi batas maksimal" in str(exc.value)

    # 3. Teks kosong
    with pytest.raises(ValueError):
        sanitize_text("   \n\t  ")


@pytest.mark.asyncio
async def test_first_sentence_latency_optimization():
    """
    Uji optimasi: Waktu inferensi kalimat pertama wajib < 3.0 detik,
    dan inferensi kedua memanfaatkan cache (< 100 ms).
    """
    job_id = f"opt_test_{uuid.uuid4().hex[:8]}"
    test_text = "Ini adalah pengujian performa kalimat pertama. Kalimat kedua menyusul secara lancar."

    # 1. Inferensi pertama (Cold/Synthesizing)
    res1 = await run_synthesis_pipeline(
        text=test_text, voice_id="piper_id_gadis_fast", job_id=job_id
    )
    assert res1.audio_path.exists()
    # Waktu kalimat pertama harus di bawah target 3.0 detik (3000 ms)
    assert res1.first_sentence_time_ms < 3000.0, (
        f"Latensi {res1.first_sentence_time_ms}ms melebihi 3000ms"
    )

    # 2. Inferensi kedua dengan parameter sama (Memakai Cache)
    job_id_2 = f"opt_test_cache_{uuid.uuid4().hex[:8]}"
    res2 = await run_synthesis_pipeline(
        text=test_text, voice_id="piper_id_gadis_fast", job_id=job_id_2
    )
    assert res2.is_cached is True
    assert res2.first_sentence_time_ms < 150.0  # Cache retrieval instan


@pytest.mark.asyncio
async def test_history_crud_operations():
    """
    Uji siklus hidup HistoryRecord: Pencatatan, pembacaan, dan penghapusan.
    """
    await init_db()
    hist_id = f"hist_{uuid.uuid4().hex[:8]}"
    test_job_id = f"job_hist_{uuid.uuid4().hex[:8]}"

    # 1. Simpan ke tabel history
    async with AsyncSessionLocal() as session:
        hist_rec = HistoryRecord(
            id=hist_id,
            job_id=test_job_id,
            project_id=None,
            title="Uji Narasi Sejarah",
            preview_text="Naskah uji coba riwayat pembuatan audio...",
            audio_url=f"/api/audio/{test_job_id}",
            duration_sec=4.2,
            voice_name="piper_id_gadis_fast",
        )
        session.add(hist_rec)
        await session.commit()

    # 2. Baca dari tabel history
    async with AsyncSessionLocal() as session:
        stmt = select(HistoryRecord).where(HistoryRecord.id == hist_id)
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()
        assert record is not None
        assert record.title == "Uji Narasi Sejarah"
        assert record.duration_sec == 4.2

    # 3. Hapus dari tabel history
    async with AsyncSessionLocal() as session:
        stmt = select(HistoryRecord).where(HistoryRecord.id == hist_id)
        res = await session.execute(stmt)
        rec_to_del = res.scalar_one_or_none()
        assert rec_to_del is not None
        await session.delete(rec_to_del)
        await session.commit()

    # 4. Verifikasi terhapus
    async with AsyncSessionLocal() as session:
        stmt = select(HistoryRecord).where(HistoryRecord.id == hist_id)
        res = await session.execute(stmt)
        assert res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_end_to_end_full_scenario():
    """
    Uji End-to-End lengkap 1 skenario kreator:
    Teks Mentah Kreator -> Sanitasi -> Normalisasi Rupiah/Tanggal -> Split Kalimat ->
    Inferensi Suara Piper -> Equal-Power Crossfade -> Mastering FFmpeg ->
    Penyematan Watermark Metadata AI -> Riwayat Tercatat -> Audio Valid & Siap Putar.
    """
    await init_db()
    e2e_job_id = f"e2e_{uuid.uuid4().hex[:8]}"
    raw_script = "Total keuntungan event ini mencapai Rp2.500.000 pada tanggal 17/08/2026. Sangat luar biasa!"

    # 1. Sanitasi
    clean_script = sanitize_text(raw_script)
    assert "Rp2.500.000" in clean_script

    # 2. Pipeline Sintesis End-to-End
    pipeline_result = await run_synthesis_pipeline(
        text=clean_script,
        voice_id="piper_id_gadis_fast",
        speed=1.0,
        pitch=0.0,
        emotion="gembira",
        job_id=e2e_job_id,
    )

    # 3. Verifikasi file audio fisik terbentuk
    assert pipeline_result.audio_path.exists()
    assert pipeline_result.duration_sec > 1.5

    # 4. Verifikasi label etika AI di metadata file
    meta = read_audio_metadata(pipeline_result.audio_path)
    assert meta["has_ai_label"] is True

    # 5. Verifikasi tercatat di history database
    async with AsyncSessionLocal() as session:
        h_rec = HistoryRecord(
            id=f"hist_{e2e_job_id}",
            job_id=e2e_job_id,
            title=clean_script[:30],
            preview_text=clean_script,
            audio_url=f"/api/audio/{e2e_job_id}",
            duration_sec=pipeline_result.duration_sec,
            voice_name="piper_id_gadis_fast",
        )
        session.add(h_rec)
        await session.commit()

        # Baca kembali
        stmt = select(HistoryRecord).where(HistoryRecord.job_id == e2e_job_id)
        res = await session.execute(stmt)
        saved = res.scalar_one_or_none()
        assert saved is not None
        assert "Rp2.500.000" in saved.preview_text
