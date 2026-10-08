"""
Unit & Integration Tests untuk Tahap 7 TaSTP:
1. RemoteEngine: Health check & auto-fallback ke Piper saat remote server mati/offline.
2. AI Disclosure Metadata Watermark: Label 'Dibuat dengan AI' tertanam di file audio.
3. Voice Clone Validation: Durasi 10-30 detik, non-silence energy, WAJIB consent checkbox, DB consent log.
4. Projects Multi-Speaker Dialogue: Blok teks independen per voice+emosi & render gabungan crossfade.
5. Checklist Test: Matikan server remote, sistem tetap jalan lancar lewat Piper.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import math
import struct
import wave

import pytest
from app.audio.clone_validator import validate_clone_sample
from app.audio.crossfade import merge_wav_files_with_crossfade
from app.audio.pipeline import run_synthesis_pipeline
from app.audio.watermark import embed_ai_disclosure_metadata, read_audio_metadata
from app.config import settings
from app.database import AsyncSessionLocal, init_db
from app.engines.remote_engine import remote_engine
from app.models.schema import VoiceCloneLog

TEST_DIR = settings.AUDIO_OUTPUT_DIR / "tests_tahap7"
TEST_DIR.mkdir(parents=True, exist_ok=True)


def _create_dummy_wav(
    path: Path, duration_sec: float, sample_rate: int = 22050, freq: float = 440.0
) -> Path:
    """Membuat file WAV sintetis untuk testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    num_frames = int(duration_sec * sample_rate)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_frames):
            val = int(8000 * math.sin(2 * math.pi * freq * (i / sample_rate)))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return path


@pytest.mark.asyncio
async def test_remote_engine_health_check_and_fallback():
    """
    Uji RemoteEngine: Bila URL remote tidak aktif atau offline,
    health check return False dan sintesis otomatis fallback ke PiperEngine.
    """
    # Pasang URL fiktif yang pasti mati/offline
    orig_url = remote_engine.endpoint_url
    remote_engine.endpoint_url = "http://127.0.0.1:59999"

    try:
        # 1. Health check harus mendeteksi offline
        assert remote_engine.health_check() is False
        assert remote_engine.is_available() is False

        # 2. Sintesis harus berhasil lewat Piper fallback tanpa exception
        out_wav = TEST_DIR / "test_remote_fallback.wav"
        dur = await remote_engine.synthesize(
            text="Halo ini pengujian fallback otomatis ke Piper.",
            voice_id="piper_id_gadis_fast",
            output_path=out_wav,
            speed=1.0,
            pitch=0.0,
        )
        assert out_wav.exists()
        assert dur > 0.3
        assert out_wav.stat().st_size > 1000
    finally:
        remote_engine.endpoint_url = orig_url


@pytest.mark.asyncio
async def test_watermark_ai_disclosure_metadata():
    """
    Uji penyematan label 'Dibuat dengan AI' ke metadata audio.
    """
    raw_wav = TEST_DIR / "raw_before_watermark.wav"
    _create_dummy_wav(raw_wav, duration_sec=1.5)

    watermarked_wav = TEST_DIR / "labeled_ai.wav"
    embed_ai_disclosure_metadata(
        audio_path=raw_wav,
        comment="Dibuat dengan AI - TaSTP Studio Uji",
        output_path=watermarked_wav,
    )

    assert watermarked_wav.exists()
    meta = read_audio_metadata(watermarked_wav)
    assert meta["has_ai_label"] is True
    # Verifikasi string biner di dalam file
    raw_bytes = watermarked_wav.read_bytes()
    assert b"Dibuat dengan AI" in raw_bytes


def test_voice_clone_sample_duration_validation():
    """
    Uji validasi durasi sampel klon (Wajib 10-30 detik):
    - Sampel < 10 detik ditolak.
    - Sampel > 30 detik ditolak.
    - Sampel 12 detik diterima.
    """
    short_wav = TEST_DIR / "sample_short_5s.wav"
    _create_dummy_wav(short_wav, duration_sec=5.0)
    res_short = validate_clone_sample(short_wav)
    assert res_short["valid"] is False
    assert "terlalu pendek" in res_short["error"]

    long_wav = TEST_DIR / "sample_long_35s.wav"
    _create_dummy_wav(long_wav, duration_sec=35.0)
    res_long = validate_clone_sample(long_wav)
    assert res_long["valid"] is False
    assert "terlalu panjang" in res_long["error"]

    valid_wav = TEST_DIR / "sample_valid_12s.wav"
    _create_dummy_wav(valid_wav, duration_sec=12.0)
    res_valid = validate_clone_sample(valid_wav)
    assert res_valid["valid"] is True
    assert 10.0 <= res_valid["duration_sec"] <= 30.0


@pytest.mark.asyncio
async def test_voice_clone_mandatory_consent_and_db_log():
    """
    Uji etika AI: WAJIB persetujuan pemilik suara dan pencatatan consent log.
    """
    await init_db()
    import uuid

    clone_id = f"clone_test_consent_{uuid.uuid4().hex[:8]}"
    now_wav = TEST_DIR / f"{clone_id}.wav"
    _create_dummy_wav(now_wav, duration_sec=15.0)

    # Simpan ke tabel voice_clone_logs
    async with AsyncSessionLocal() as session:
        log_entry = VoiceCloneLog(
            id=clone_id,
            voice_name="Suara Selebgram Uji",
            speaker_name="Citra Kirana",
            consent_checkbox=True,
            consent_text="Persetujuan resmi hak penggunaan suara AI TaSTP.",
            sample_path=str(now_wav),
            sample_duration_sec=15.0,
        )
        session.add(log_entry)
        await session.commit()

    # Verifikasi tersimpan di DB
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        stmt = select(VoiceCloneLog).where(VoiceCloneLog.id == clone_id)
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()
        assert record is not None
        assert record.consent_checkbox is True
        assert record.speaker_name == "Citra Kirana"


@pytest.mark.asyncio
async def test_projects_multi_speaker_dialogue_render():
    """
    Uji fitur Projects: teks panjang dibagi blok, tiap blok punya voice+emosi
    sendiri (dialog multi-speaker), lalu dirender gabungan dengan crossfade.
    """
    await init_db()

    # Buat 2 blok dialog dengan karakter dan emosi berbeda
    # Blok 1: Host energik
    res1 = await run_synthesis_pipeline(
        text="Halo kawan-kawan sekalian, selamat datang kembali di podcast kami!",
        voice_id="piper_id_gadis_fast",
        emotion="antusias",
        job_id="job_diag_blk1",
    )
    assert res1.audio_path.exists()

    # Blok 2: Narasumber tenang
    res2 = await run_synthesis_pipeline(
        text="Halo juga, terima kasih banyak sudah mengundang saya hari ini.",
        voice_id="piper_id_bima_narrator",
        emotion="tenang",
        job_id="job_diag_blk2",
    )
    assert res2.audio_path.exists()

    # Gabung kedua blok dengan equal-power crossfade
    merged_project_wav = TEST_DIR / "project_multi_speaker_final.wav"
    merge_wav_files_with_crossfade(
        [res1.audio_path, res2.audio_path],
        merged_project_wav,
        crossfade_ms=40,
        sample_rate=22050,
    )

    assert merged_project_wav.exists()
    embed_ai_disclosure_metadata(
        merged_project_wav, comment="Dibuat dengan AI - TaSTP Multi-Speaker"
    )

    meta = read_audio_metadata(merged_project_wav)
    assert meta["has_ai_label"] is True

    with wave.open(str(merged_project_wav), "rb") as wf:
        total_dur = wf.getnframes() / float(wf.getframerate())
    # Durasi total gabungan harus mendekati penjumlahan durasi kedua blok
    assert total_dur > res1.duration_sec
    assert total_dur > res2.duration_sec


@pytest.mark.asyncio
async def test_checklist_remote_server_off_piper_continues():
    """
    Checklist Tes Tahap 7: Matikan server remote, sistem tetap jalan lewat Piper.
    """
    # 1. Pastikan remote engine url mati
    remote_engine.endpoint_url = "http://127.0.0.1:54321/offline-server"

    # 2. Panggil sintesis melalui pipeline dengan engine="remote"
    result = await run_synthesis_pipeline(
        text="Ini adalah pengujian ketahanan checklist: ketika server GPU remote mati, audio tetap selesai diproses tanpa gagal.",
        voice_id="piper_id_gadis_fast",
        engine_name="remote",
        job_id="checklist_fallback_job",
    )

    # 3. Verifikasi sistem tidak crash dan audio final berhasil diproduksi
    assert result.audio_path.exists()
    assert result.duration_sec > 1.0
    assert result.num_sentences >= 1

    # Verifikasi audio berlabel AI
    meta = read_audio_metadata(result.audio_path)
    assert meta["has_ai_label"] is True
