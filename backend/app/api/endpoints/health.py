"""
Endpoint Pengecekan Kesehatan Server & Diagnostik Model TTS.
Melaporkan:
- Status server (ok/degraded)
- Ketersediaan model ONNX di disk
- Ketersediaan FFmpeg
- Daftar suara dan status model masing-masing
"""

import shutil
from datetime import datetime
from pathlib import Path

from app.config import settings
from fastapi import APIRouter

router = APIRouter()


def _check_model_status() -> dict:
    """Periksa ketersediaan model ONNX di storage/models/."""
    models_dir = settings.MODELS_DIR
    result = {
        "models_dir": str(models_dir),
        "models_dir_exists": models_dir.exists(),
        "onnx_files": [],
        "primary_model": None,
        "primary_model_exists": False,
        "primary_model_size_mb": 0.0,
    }

    if not models_dir.exists():
        return result

    # Temukan semua file .onnx
    onnx_files = list(models_dir.glob("*.onnx"))
    for sub in models_dir.iterdir():
        if sub.is_dir():
            onnx_files.extend(sub.glob("*.onnx"))

    result["onnx_files"] = [
        {
            "name": f.name,
            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
            "path": str(f.relative_to(models_dir)),
        }
        for f in onnx_files
    ]

    # Cek model utama id_ID-news_tts-medium
    primary = models_dir / "id_ID-news_tts-medium.onnx"
    if primary.exists():
        result["primary_model"] = primary.name
        result["primary_model_exists"] = True
        result["primary_model_size_mb"] = round(
            primary.stat().st_size / (1024 * 1024), 2
        )

    # Cek config JSON
    config_file = models_dir / "id_ID-news_tts-medium.onnx.json"
    result["config_json_exists"] = config_file.exists()

    return result


def _check_ffmpeg() -> dict:
    """Periksa ketersediaan FFmpeg."""
    ffmpeg_path = shutil.which("ffmpeg")
    available = ffmpeg_path is not None

    if not available:
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            available = True
        except Exception:
            pass

    return {
        "available": available,
        "path": ffmpeg_path,
    }


def _check_voice_catalog() -> list[dict]:
    """Daftar suara di katalog beserta status model masing-masing."""
    voice_catalog = [
        {"id": "id_ID-news_tts-medium", "name": "Ida", "gender": "female"},
        {"id": "piper_id_gadis_fast", "name": "Gadis", "gender": "female"},
        {"id": "piper_id_bima_narrator", "name": "Bima", "gender": "male"},
        {"id": "piper_id_siti_podcast", "name": "Siti", "gender": "female"},
        {"id": "piper_id_dimas_news", "name": "Dimas", "gender": "male"},
    ]

    for voice in voice_catalog:
        vid = voice["id"]
        dedicated = (
            (settings.MODELS_DIR / f"{vid}.onnx").exists()
            or (settings.MODELS_DIR / vid / f"{vid}.onnx").exists()
        )
        voice["has_dedicated_model"] = dedicated
        voice["uses_shared_model"] = not dedicated
        if not dedicated:
            # Check if shared fallback exists
            fallback_exists = any(settings.MODELS_DIR.glob("*id_ID*.onnx"))
            voice["shared_model_available"] = fallback_exists
            voice["dsp_profile_applied"] = True
        else:
            voice["shared_model_available"] = True
            voice["dsp_profile_applied"] = False

    return voice_catalog


@router.get("/health")
async def health_check():
    """Endpoint pengecekan kesehatan server, model, dan konfigurasi hardware."""
    model_status = _check_model_status()
    ffmpeg_status = _check_ffmpeg()
    voice_catalog = _check_voice_catalog()

    # Tentukan status keseluruhan
    has_any_model = len(model_status["onnx_files"]) > 0
    has_ffmpeg = ffmpeg_status["available"]

    if has_any_model and has_ffmpeg:
        overall_status = "ok"
    elif has_any_model or has_ffmpeg:
        overall_status = "degraded"
    else:
        overall_status = "critical"

    warnings = []
    if not has_any_model:
        warnings.append(
            "Tidak ada file .onnx di storage/models/. "
            "Download: https://huggingface.co/rhasspy/piper-voices/resolve/main/"
            "id/id_ID/news_tts/medium/id_ID-news_tts-medium.onnx"
        )
    if not has_ffmpeg:
        warnings.append(
            "FFmpeg tidak ditemukan. Install: pip install imageio-ffmpeg "
            "atau download dari https://ffmpeg.org/download.html"
        )
    if not model_status.get("config_json_exists"):
        warnings.append(
            "File config id_ID-news_tts-medium.onnx.json tidak ditemukan."
        )

    return {
        "status": overall_status,
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "hardware": {
            "mode": "cpu_only",
            "target": "Intel Iris / CPU",
            "max_threads": settings.MAX_THREADS,
            "cuda_enabled": False,
        },
        "model": model_status,
        "ffmpeg": ffmpeg_status,
        "voices": voice_catalog,
        "default_engine": settings.DEFAULT_ENGINE,
        "remote_available": bool(settings.REMOTE_ENGINE_URL),
        "ai_disclosure_enabled": settings.EMBED_AI_LABEL,
        "warnings": warnings,
        "timestamp": datetime.utcnow().isoformat(),
    }
