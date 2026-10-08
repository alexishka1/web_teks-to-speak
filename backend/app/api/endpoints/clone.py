"""
Endpoint Voice Clone TaSTP:
- Upload sampel audio 10-30 detik (WAV, MP3, WEBM dari browser)
- Validasi durasi, energi vokal, format, ukuran, dan kualitas vokal
- Konversi otomatis ke WAV mono 24 kHz via FFmpeg, trim silence & loudnorm
- WAJIB checkbox persetujuan pemilik suara (Etika AI)
- Simpan rekaman log persetujuan (VoiceCloneLog) ke database
- Registrasi ke RemoteEngine jika server remote aktif (fallback ke Piper)
- Pengujian komparasi A/B (Klon vokal vs Baseline Piper)
"""

import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.audio.clone_validator import (
    convert_sample_to_standard_wav,
    validate_clone_sample,
)
from app.audio.pipeline import run_synthesis_pipeline
from app.audio.watermark import embed_ai_disclosure_metadata
from app.config import settings
from app.database import get_db
from app.engines.remote_engine import remote_engine
from app.models.schema import (
    SynthesisJob,
    VoiceCloneLog,
    VoiceCloneResponse,
    VoiceCompareABRequest,
    VoiceCompareABResponse,
    VoiceRecord,
)
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/voice-clone", tags=["Voice Clone"])

CLONES_DIR = settings.AUDIO_OUTPUT_DIR / "clones"
CLONES_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CONSENT_STATEMENT = (
    "Saya secara sadar menyatakan bahwa saya memiliki izin tertulis dan hak legal "
    "atas sampel suara ini untuk digunakan dalam sistem kecerdasan buatan TaSTP, "
    "serta bertanggung jawab penuh atas segala penggunaannya."
)


@router.post("/upload", response_model=VoiceCloneResponse)
async def upload_voice_clone_sample(
    file: UploadFile = File(...),
    voice_name: str = Form(..., min_length=2, max_length=100),
    speaker_name: str = Form(..., min_length=2, max_length=100),
    gender: str = Form("custom"),
    transcript: str | None = Form(None),
    consent_checkbox: bool = Form(...),
    consent_text: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Mengunggah sampel suara untuk kloning vokal:
    Wajib:
    1. consent_checkbox == True (Etika & Kepatuhan AI)
    2. Durasi audio 10 - 30 detik (ideal 15 - 30 detik)
    3. Mengandung suara vokal (tidak hening)
    """
    # 1. Validasi WAJIB Persetujuan Pemilik Suara
    if not consent_checkbox:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WAJIB mencentang persetujuan pemilik suara (consent checkbox). TaSTP menolak kloning suara tanpa izin eksplisit.",
        )

    # 2. Simpan file unggahan sementara
    clone_id = f"clone_{uuid.uuid4().hex[:10]}"
    safe_suffix = Path(file.filename or "sample.wav").suffix or ".wav"
    temp_path = CLONES_DIR / f"temp_{clone_id}{safe_suffix}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Gagal menyimpan file audio sementara: {e}"
        )

    # 3. Validasi Sampel Audio (10–30 detik, non-silence)
    val_res = validate_clone_sample(temp_path)
    if not val_res["valid"]:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=val_res["error"]
        )

    # 4. Standardisasi Sampel ke WAV mono 24 kHz, Trim Silence, Loudness Normalization
    final_clone_wav = CLONES_DIR / f"{clone_id}.wav"
    convert_sample_to_standard_wav(temp_path, final_clone_wav)
    temp_path.unlink(missing_ok=True)

    if settings.EMBED_AI_LABEL:
        embed_ai_disclosure_metadata(
            final_clone_wav, comment=f"Klon AI dari {speaker_name} - TaSTP"
        )

    duration = val_res["duration_sec"]
    quality_info: dict[str, Any] = val_res.get("quality", {})
    now = datetime.utcnow()
    agreed_statement = consent_text or DEFAULT_CONSENT_STATEMENT

    # 5. Catat Consent Log ke Database SQLite
    clone_log = VoiceCloneLog(
        id=clone_id,
        voice_name=voice_name,
        speaker_name=speaker_name,
        consent_checkbox=True,
        consent_text=agreed_statement,
        sample_path=str(final_clone_wav),
        sample_duration_sec=duration,
        created_at=now,
    )
    db.add(clone_log)

    # 6. Registrasi ke RemoteEngine jika server remote aktif (fallback ke Piper)
    active_engine = "piper"
    if remote_engine.is_available():
        registered = remote_engine.register_clone_sample(
            voice_id=clone_id,
            audio_path=final_clone_wav,
            transcript=transcript,
            speaker_name=speaker_name,
        )
        if registered:
            active_engine = "remote"

    # 7. Registrasi Suara ke Voice Records agar dapat digunakan di Studio & TTS
    voice_rec = VoiceRecord(
        id=clone_id,
        name=f"{voice_name} (Klon)",
        gender=gender,
        language="id-ID",
        category="cloned",
        description=f"Klon suara dari {speaker_name} ({duration}s, 24 kHz). Terverifikasi etika AI.",
        engine=active_engine,
        model_path=str(final_clone_wav),
        sample_rate=24000,
        is_cloned=True,
        is_active=True,
        preview_audio_url=f"/api/voice-clone/audio/{clone_id}.wav",
        created_at=now,
    )
    db.add(voice_rec)
    await db.commit()

    engine_msg = (
        "Server GPU Remote aktif"
        if active_engine == "remote"
        else "Menggunakan simulasi lokal Piper (fallback)"
    )

    return VoiceCloneResponse(
        id=clone_id,
        voice_name=voice_name,
        speaker_name=speaker_name,
        sample_duration_sec=duration,
        consent_recorded=True,
        created_at=now,
        quality=quality_info,
        engine=active_engine,
        audio_preview_url=f"/api/voice-clone/audio/{clone_id}.wav",
        message=f"Klon suara '{voice_name}' berhasil diproses ({engine_msg}). Consent log dicatat dengan ID: {clone_id}.",
    )


@router.post("/compare-ab", response_model=VoiceCompareABResponse)
async def compare_voice_clone_ab(
    req: VoiceCompareABRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Fitur Komparasi A/B:
    Membandingkan hasil sintesis vokal Kloning Suara Pengguna (A)
    melawan Suara Default Piper (B) menggunakan kalimat uji yang sama.
    """
    text = req.text.strip()
    if not text:
        text = "Halo, ini adalah pengujian perbandingan suara hasil kloning saya melawan suara default Piper."

    # Cari informasi suara A (Klon) di DB
    stmt_a = select(VoiceRecord).where(VoiceRecord.id == req.voice_id)
    res_a_rec = await db.execute(stmt_a)
    voice_a_rec = res_a_rec.scalar_one_or_none()
    voice_a_name = voice_a_rec.name if voice_a_rec else f"Klon ({req.voice_id})"

    # Cari informasi suara B (Baseline) di DB
    baseline_id = req.baseline_voice_id or "id_ID-news_tts-medium"
    stmt_b = select(VoiceRecord).where(VoiceRecord.id == baseline_id)
    res_b_rec = await db.execute(stmt_b)
    voice_b_rec = res_b_rec.scalar_one_or_none()
    voice_b_name = (
        voice_b_rec.name if voice_b_rec else "Ardi - Berita HD (Piper Default)"
    )

    # 1. Sintesis Sampel A (Klon)
    res_a = await run_synthesis_pipeline(
        text=text,
        voice_id=req.voice_id,
        speed=1.0,
        pitch=0.0,
        emotion="neutral",
    )

    # Simpan job A di DB agar bisa diakses lewat /api/audio/{job_id}
    job_a = SynthesisJob(
        id=res_a.job_id,
        text=text,
        voice_id=req.voice_id,
        engine_name=res_a.engine_used,
        speed=1.0,
        pitch=0.0,
        status="completed",
        audio_path=str(res_a.audio_path),
        duration_sec=res_a.duration_sec,
        is_cloned=True,
        has_consent=True,
        created_at=datetime.utcnow(),
    )
    db.add(job_a)

    # 2. Sintesis Sampel B (Piper Default)
    res_b = await run_synthesis_pipeline(
        text=text,
        voice_id=baseline_id,
        speed=1.0,
        pitch=0.0,
        emotion="neutral",
    )

    # Simpan job B di DB
    job_b = SynthesisJob(
        id=res_b.job_id,
        text=text,
        voice_id=baseline_id,
        engine_name=res_b.engine_used,
        speed=1.0,
        pitch=0.0,
        status="completed",
        audio_path=str(res_b.audio_path),
        duration_sec=res_b.duration_sec,
        is_cloned=False,
        has_consent=True,
        created_at=datetime.utcnow(),
    )
    db.add(job_b)
    await db.commit()

    return VoiceCompareABResponse(
        text=text,
        sample_a={
            "voice_id": req.voice_id,
            "name": voice_a_name,
            "audio_url": f"/api/audio/{res_a.job_id}",
            "duration": res_a.duration_sec,
            "engine_used": res_a.engine_used,
            "label": "Suara Kloning Anda",
        },
        sample_b={
            "voice_id": baseline_id,
            "name": voice_b_name,
            "audio_url": f"/api/audio/{res_b.job_id}",
            "duration": res_b.duration_sec,
            "engine_used": res_b.engine_used,
            "label": "Baseline Piper Default",
        },
    )


@router.get("/logs")
async def list_voice_clone_logs(db: AsyncSession = Depends(get_db)):
    """Mengambil riwayat log persetujuan kloning suara untuk audit kepatuhan."""
    stmt = select(VoiceCloneLog).order_by(VoiceCloneLog.created_at.desc())
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [
        {
            "id": log_item.id,
            "voice_name": log_item.voice_name,
            "speaker_name": log_item.speaker_name,
            "consent_checkbox": log_item.consent_checkbox,
            "consent_text": log_item.consent_text,
            "sample_duration_sec": log_item.sample_duration_sec,
            "created_at": log_item.created_at,
        }
        for log_item in logs
    ]


@router.get("/audio/{filename}")
async def get_clone_audio(filename: str):
    """Mengambil file sampel audio klon."""
    file_path = CLONES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sampel klon tidak ditemukan.")
    return FileResponse(
        file_path,
        media_type="audio/wav",
        headers={
            "X-Generated-By": "TaSTP-VoiceClone",
            "X-AI-Disclosure": settings.AI_LABEL_TEXT,
        },
    )
