import io
import math
import struct
import sys
import uuid
import wave
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.api.endpoints.clone import (
    compare_voice_clone_ab,
    upload_voice_clone_sample,
)
from app.audio.clone_validator import (
    analyze_audio_quality,
    convert_sample_to_standard_wav,
)
from app.database import AsyncSessionLocal, init_db
from app.models.schema import VoiceCloneLog, VoiceCompareABRequest, VoiceRecord
from sqlalchemy import select

TEST_DIR = Path(__file__).resolve().parent / "test_data"
TEST_DIR.mkdir(parents=True, exist_ok=True)


def _create_synthetic_wav(
    file_path: Path,
    duration_sec: float = 15.0,
    sample_rate: int = 22050,
    amplitude: int = 8000,
    add_silence_padding: bool = True,
):
    """Membuat file WAV sintetis vokal dengan padding hening di awal/akhir."""
    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        # 0.5s hening di awal
        if add_silence_padding:
            silence_frames = int(sample_rate * 0.5)
            wf.writeframes(struct.pack(f"<{silence_frames}h", *([0] * silence_frames)))

        # Sinyal audio vokal sinusoidal
        tone_frames = int(
            sample_rate * max(1.0, duration_sec - (1.0 if add_silence_padding else 0.0))
        )
        for i in range(tone_frames):
            val = int(amplitude * math.sin(2 * math.pi * 320 * i / sample_rate))
            wf.writeframes(struct.pack("<h", val))

        # 0.5s hening di akhir
        if add_silence_padding:
            silence_frames = int(sample_rate * 0.5)
            wf.writeframes(struct.pack(f"<{silence_frames}h", *([0] * silence_frames)))


def test_standard_wav_conversion_24khz_and_trim():
    """Uji konversi standar: 24 kHz mono, 16-bit PCM, silence trim, dan loudnorm."""
    src_wav = TEST_DIR / f"test_raw_{uuid.uuid4().hex[:8]}.wav"
    dest_wav = TEST_DIR / f"test_24k_{uuid.uuid4().hex[:8]}.wav"

    _create_synthetic_wav(src_wav, duration_sec=16.0, sample_rate=22050)
    try:
        success = convert_sample_to_standard_wav(src_wav, dest_wav)
        assert success is True
        assert dest_wav.exists()

        with wave.open(str(dest_wav), "rb") as wf:
            assert wf.getframerate() == 24000
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            dur = wf.getnframes() / float(wf.getframerate())
            # Memastikan durasi tetap valid setelah trim
            assert 10.0 <= dur <= 17.0
    finally:
        src_wav.unlink(missing_ok=True)
        dest_wav.unlink(missing_ok=True)


def test_analyze_audio_quality_indicators():
    """Uji indikator kualitas audio (durasi ideal 15-30s, RMS, clipping, status volume)."""
    ideal_wav = TEST_DIR / f"test_ideal_{uuid.uuid4().hex[:8]}.wav"
    _create_synthetic_wav(
        ideal_wav, duration_sec=20.0, sample_rate=24000, amplitude=6000
    )

    try:
        quality = analyze_audio_quality(ideal_wav)
        assert quality["is_ideal_duration"] is True
        assert quality["clipping_detected"] is False
        assert quality["volume_status"] in ("optimal", "rendah")
        assert quality["quality_score"] >= 70
    finally:
        ideal_wav.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_voice_clone_upload_full_flow():
    """
    Uji alur upload sampel suara klon lengkap:
    - File audio 18 detik + persetujuan etika (consent_checkbox=True)
    - Metadata lengkap (nama suara, nama pemilik, gender, transkrip)
    - Verifikasi database: VoiceCloneLog tercatat & VoiceRecord terdaftar di DB
    """
    await init_db()

    sample_wav = TEST_DIR / f"test_sample_{uuid.uuid4().hex[:8]}.wav"
    _create_synthetic_wav(sample_wav, duration_sec=18.0, sample_rate=22050)

    unique_voice_name = f"Suara Podcaster {uuid.uuid4().hex[:6]}"
    speaker_name = "Budi Hartono"
    transcript_text = "Apakah kamu siap menciptakan konten narasi masa depan bersama TaSTP? Luar biasa!"

    try:
        async with AsyncSessionLocal() as session:
            with open(sample_wav, "rb") as f:
                upload_file = UploadFile(
                    filename=sample_wav.name,
                    file=io.BytesIO(f.read()),
                )

            res = await upload_voice_clone_sample(
                file=upload_file,
                voice_name=unique_voice_name,
                speaker_name=speaker_name,
                gender="male",
                transcript=transcript_text,
                consent_checkbox=True,
                consent_text="Persetujuan resmi hak suara.",
                db=session,
            )

            assert res.consent_recorded is True
            assert res.voice_name == unique_voice_name
            assert 10.0 <= res.sample_duration_sec <= 30.0
            clone_id = res.id

            # Verifikasi VoiceCloneLog di DB
            stmt_log = select(VoiceCloneLog).where(VoiceCloneLog.id == clone_id)
            res_log = await session.execute(stmt_log)
            log_entry = res_log.scalar_one_or_none()
            assert log_entry is not None
            assert log_entry.consent_checkbox is True
            assert log_entry.speaker_name == speaker_name

            # Verifikasi VoiceRecord di DB
            stmt_v = select(VoiceRecord).where(VoiceRecord.id == clone_id)
            res_v = await session.execute(stmt_v)
            v_entry = res_v.scalar_one_or_none()
            assert v_entry is not None
            assert v_entry.is_cloned is True
            assert v_entry.sample_rate == 24000
            assert v_entry.category == "cloned"
            assert v_entry.is_active is True
    finally:
        sample_wav.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_voice_clone_without_consent_rejected():
    """Uji etika: menolak proses kloning vokal jika consent_checkbox bernilai False."""
    sample_wav = TEST_DIR / f"test_noconsent_{uuid.uuid4().hex[:8]}.wav"
    _create_synthetic_wav(sample_wav, duration_sec=15.0)

    try:
        async with AsyncSessionLocal() as session:
            with open(sample_wav, "rb") as f:
                upload_file = UploadFile(
                    filename=sample_wav.name,
                    file=io.BytesIO(f.read()),
                )

            with pytest.raises(HTTPException) as exc_info:
                await upload_voice_clone_sample(
                    file=upload_file,
                    voice_name="Suara Ilegal",
                    speaker_name="Tanpa Izin",
                    consent_checkbox=False,
                    db=session,
                )

            assert exc_info.value.status_code == 400
            assert "WAJIB mencentang persetujuan" in exc_info.value.detail
    finally:
        sample_wav.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_voice_clone_ab_compare_flow():
    """
    Uji fitur komparasi A/B:
    Membandingkan sintesis vokal suara klon (A) vs baseline Piper (B)
    dengan kalimat uji yang sama.
    """
    await init_db()

    # Siapkan suara klon uji
    clone_id = f"clone_{uuid.uuid4().hex[:10]}"
    dummy_wav = TEST_DIR / f"{clone_id}.wav"
    _create_synthetic_wav(dummy_wav, duration_sec=16.0, sample_rate=24000)

    try:
        async with AsyncSessionLocal() as session:
            v_rec = VoiceRecord(
                id=clone_id,
                name="Suara Klon Uji A/B",
                gender="female",
                language="id-ID",
                category="cloned",
                description="Sampel uji A/B",
                engine="piper",
                model_path=str(dummy_wav),
                sample_rate=24000,
                is_cloned=True,
                is_active=True,
            )
            session.add(v_rec)
            await session.commit()

            req = VoiceCompareABRequest(
                voice_id=clone_id,
                baseline_voice_id="id_ID-news_tts-medium",
                text="Selamat datang di studio sintesis suara modern TaSTP.",
            )
            data = await compare_voice_clone_ab(req=req, db=session)

            assert data.sample_a["voice_id"] == clone_id
            assert data.sample_a["duration"] > 0
            assert data.sample_a["audio_url"].startswith("/api/audio/")
            assert data.sample_b["duration"] > 0
            assert data.sample_b["audio_url"].startswith("/api/audio/")
    finally:
        dummy_wav.unlink(missing_ok=True)
