from datetime import datetime

from app.config import settings
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Endpoint pengecekan kesehatan server & konfigurasi hardware."""
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "hardware": {
            "mode": "cpu_only",
            "target": "Intel Iris / CPU",
            "max_threads": settings.MAX_THREADS,
            "cuda_enabled": False,
        },
        "default_engine": settings.DEFAULT_ENGINE,
        "remote_available": bool(settings.REMOTE_ENGINE_URL),
        "ai_disclosure_enabled": settings.EMBED_AI_LABEL,
        "timestamp": datetime.utcnow().isoformat(),
    }
