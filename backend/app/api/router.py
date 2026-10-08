from app.api.endpoints.clone import router as clone_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.history import router as history_router
from app.api.endpoints.projects import router as projects_router
from app.api.endpoints.studio import router as studio_router
from app.api.endpoints.tts import router as tts_router
from app.api.endpoints.voices import router as voices_router
from fastapi import APIRouter

router = APIRouter(prefix="/api")

# Hubungkan router modular
router.include_router(health_router, tags=["Health"])
router.include_router(voices_router, tags=["Voices"])
router.include_router(tts_router, tags=["Synthesis"])
router.include_router(clone_router)
router.include_router(projects_router)
router.include_router(history_router)
router.include_router(studio_router)
