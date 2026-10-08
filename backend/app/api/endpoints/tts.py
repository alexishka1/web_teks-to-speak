import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any

from app.api.middleware.rate_limiter import limiter
from app.audio.pipeline import run_synthesis_pipeline
from app.config import settings
from app.database import AsyncSessionLocal, get_db
from app.models.schema import (
    HistoryRecord,
    JobStatusResponse,
    SynthesisJob,
    SynthesizeRequest,
    SynthesizeResponse,
)
from app.text.sanitize import sanitize_text
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# In-memory progress tracking untuk Server-Sent Events (SSE)
JOB_PROGRESS: dict[str, dict[str, Any]] = {}


@router.post("/tts", response_model=SynthesizeResponse)
@router.post("/synthesize", response_model=SynthesizeResponse)
async def create_tts_job(
    req: SynthesizeRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint sintesis suara utama.
    Menerima naskah dan parameter, memulai pipeline sintesis,
    dan menyediakan pelacakan status / SSE.
    Dilindungi proteksi Rate Limit per IP dan Sanitasi Naskah.
    """
    # 1. Cek Rate Limit per IP Klien
    limiter.check_rate_limit(request)

    # 2. Sanitasi & Validasi Panjang Karakter Naskah
    try:
        clean_text = sanitize_text(req.text)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    if req.is_cloned_voice and not req.voice_clone_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Persetujuan pemilik suara (consent checkbox) wajib dicentang untuk model klon suara.",
        )

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow()

    chosen_engine = req.engine or settings.DEFAULT_ENGINE

    # Catat job di DB
    job = SynthesisJob(
        id=job_id,
        text=clean_text,
        voice_id=req.voice_id,
        engine_name=chosen_engine,
        speed=req.speed,
        pitch=req.pitch,
        status="processing",
        audio_path=None,
        duration_sec=0.0,
        is_cloned=req.is_cloned_voice,
        has_consent=req.voice_clone_consent,
        created_at=now,
    )
    db.add(job)
    await db.commit()

    JOB_PROGRESS[job_id] = {
        "status": "processing",
        "progress": 5,
        "step": "started",
        "message": "Memulai proses sintesis...",
    }

    # Jalankan pipeline
    async def _progress_callback(info: dict[str, Any]):
        if job_id in JOB_PROGRESS:
            JOB_PROGRESS[job_id].update(info)

    pipeline_result_holder = {}

    async def _execute_synthesis():
        try:
            result = await run_synthesis_pipeline(
                text=clean_text,
                voice_id=req.voice_id,
                speed=req.speed,
                pitch=req.pitch,
                pause_scale=req.pause_scale or 1.0,
                audio_effect=req.audio_effect or "none",
                emotion=req.emotion or "neutral",
                emotion_intensity=req.emotion_intensity
                if req.emotion_intensity is not None
                else 100.0,
                sentence_emotions=req.sentence_emotions,
                engine_name=chosen_engine,
                job_id=job_id,
                on_progress=_progress_callback,
            )
            pipeline_result_holder["engine_used"] = result.engine_used
            pipeline_result_holder["first_sentence_time_ms"] = (
                result.first_sentence_time_ms
            )

            # Update status di DB & Catat ke Riwayat (HistoryRecord)
            async with AsyncSessionLocal() as session:
                stmt = select(SynthesisJob).where(SynthesisJob.id == job_id)
                res = await session.execute(stmt)
                db_job = res.scalar_one_or_none()
                if db_job:
                    db_job.status = "completed"
                    db_job.engine_name = result.engine_used
                    db_job.audio_path = str(result.audio_path)
                    db_job.duration_sec = result.duration_sec

                # Buat entri History
                hist_id = f"hist_{uuid.uuid4().hex[:10]}"
                preview_snippet = (
                    (clean_text[:140] + "...") if len(clean_text) > 140 else clean_text
                )
                hist_record = HistoryRecord(
                    id=hist_id,
                    job_id=job_id,
                    project_id=None,
                    title=clean_text[:40],
                    preview_text=preview_snippet,
                    audio_url=f"/api/audio/{job_id}",
                    duration_sec=result.duration_sec,
                    voice_name=req.voice_id,
                    created_at=now,
                )
                session.add(hist_record)
                await session.commit()

            JOB_PROGRESS[job_id] = {
                "status": "completed",
                "progress": 100,
                "step": "done",
                "audio_url": f"/api/audio/{job_id}",
                "duration_sec": result.duration_sec,
                "is_cached": result.is_cached,
                "engine_used": result.engine_used,
                "first_sentence_time_ms": result.first_sentence_time_ms,
            }
        except Exception as e:
            async with AsyncSessionLocal() as session:
                stmt = select(SynthesisJob).where(SynthesisJob.id == job_id)
                res = await session.execute(stmt)
                db_job = res.scalar_one_or_none()
                if db_job:
                    db_job.status = "failed"
                    db_job.error_message = str(e)
                    await session.commit()

            JOB_PROGRESS[job_id] = {
                "status": "failed",
                "progress": 100,
                "error": str(e),
            }

    # Untuk kecepatan respon langsung pada permintaan pendek atau via async
    await _execute_synthesis()

    final_info = JOB_PROGRESS.get(job_id, {})
    return SynthesizeResponse(
        job_id=job_id,
        status=final_info.get("status", "completed"),
        audio_url=f"/api/audio/{job_id}",
        duration_sec=final_info.get("duration_sec", 0.0),
        engine_used=pipeline_result_holder.get("engine_used", chosen_engine),
        first_sentence_time_ms=pipeline_result_holder.get(
            "first_sentence_time_ms", 0.0
        ),
        created_at=now,
        message="Sintesis berhasil diselesaikan.",
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Mendapatkan status job sintesis."""
    stmt = select(SynthesisJob).where(SynthesisJob.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job tidak ditemukan."
        )

    return JobStatusResponse(
        id=job.id,
        status=job.status,
        audio_url=f"/api/audio/{job.id}" if job.status == "completed" else None,
        duration_sec=job.duration_sec,
        error_message=job.error_message,
        created_at=job.created_at,
    )


@router.get("/jobs/{job_id}/progress")
async def stream_job_progress(job_id: str):
    """
    Server-Sent Events (SSE) streaming untuk memantau progres sintesis real-time.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        last_progress = -1
        while True:
            info = JOB_PROGRESS.get(job_id)
            if not info:
                yield f"data: {json.dumps({'status': 'not_found'})}\n\n"
                break

            current_progress = info.get("progress", 0)
            if current_progress != last_progress:
                payload = json.dumps({"job_id": job_id, **info})
                yield f"data: {payload}\n\n"
                last_progress = current_progress

            if info.get("status") in ("completed", "failed"):
                break

            await asyncio.sleep(0.15)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/audio/{job_id}")
async def get_audio_file(job_id: str, db: AsyncSession = Depends(get_db)):
    """Mengambil file audio WAV hasil sintesis."""
    headers = {
        "X-Generated-By": "TaSTP-AI",
        "X-AI-Disclosure": settings.AI_LABEL_TEXT,
    }

    # 1. Cek langsung di AUDIO_OUTPUT_DIR
    sample_file = settings.AUDIO_OUTPUT_DIR / f"{job_id}.wav"
    if sample_file.exists():
        return FileResponse(
            sample_file,
            media_type="audio/wav",
            filename=f"tastp_{job_id}.wav",
            headers=headers,
        )

    # 2. Cek apakah job_id sudah mengandung ekstensi .wav
    alt_file = settings.AUDIO_OUTPUT_DIR / job_id
    if alt_file.exists():
        return FileResponse(
            alt_file,
            media_type="audio/wav",
            filename=f"tastp_{job_id}.wav",
            headers=headers,
        )

    # 3. Cek di tabel database jika disimpan di cache path
    stmt = select(SynthesisJob).where(SynthesisJob.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if job and job.audio_path:
        db_file = Path(job.audio_path)
        if db_file.exists():
            return FileResponse(
                db_file,
                media_type="audio/wav",
                filename=f"tastp_{job_id}.wav",
                headers=headers,
            )

    raise HTTPException(status_code=404, detail="File audio tidak ditemukan.")


@router.get("/presets")
async def get_style_presets(db: AsyncSession = Depends(get_db)):
    """Mengambil daftar style presets aktif dari database."""
    from app.models.schema import StylePresetRecord

    stmt = select(StylePresetRecord).where(StylePresetRecord.is_active == True)  # noqa: E712
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "category": r.category,
            "voice_id": r.voice_id,
            "speed": r.speed,
            "pitch": r.pitch,
            "pause_scale": r.pause_scale,
            "audio_effect": r.audio_effect,
            "emotion": r.emotion,
            "emotion_intensity": r.emotion_intensity,
            "description": r.description,
            "is_active": r.is_active,
        }
        for r in records
    ]


@router.get("/emotions")
async def get_emotions_catalog(db: AsyncSession = Depends(get_db)):
    """Mengambil katalog lengkap emosi aktif dari database beserta parameter prosodi dan warnanya."""
    from app.emotion.presets import list_all_emotion_presets, sync_emotions_from_db
    from app.models.schema import EmotionRecord

    stmt = select(EmotionRecord).where(EmotionRecord.is_active == True)  # noqa: E712
    res = await db.execute(stmt)
    records = res.scalars().all()
    if records:
        sync_emotions_from_db(records)
        return [
            {
                "id": r.id,
                "name": r.name,
                "category": r.category,
                "speed": r.speed,
                "pitch": r.pitch,
                "pause_scale": r.pause_scale,
                "effect": r.effect,
                "color": r.color,
                "description": r.description,
                "is_active": r.is_active,
            }
            for r in records
        ]

    return list_all_emotion_presets(active_only=True)


@router.post("/emotions/analyze")
async def analyze_script_emotions_endpoint(payload: dict[str, Any]):
    """Menganalisis teks naskah dan mengembalikan emosi yang terdeteksi secara lokal per kalimat."""
    from app.emotion.auto_emotion import analyze_script_emotions
    from app.text.normalize import normalize_indonesian_text
    from app.text.splitter import split_into_sentences

    raw_text = payload.get("text", "")
    norm_text = normalize_indonesian_text(raw_text)
    sentences = split_into_sentences(norm_text)
    if not sentences:
        sentences = [raw_text] if raw_text.strip() else []

    results = analyze_script_emotions(sentences)
    return {"total_sentences": len(results), "sentences": results}
