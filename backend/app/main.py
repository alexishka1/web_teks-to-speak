from contextlib import asynccontextmanager

from app.api.router import router
from app.config import settings
from app.database import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Inisialisasi tabel SQLite
    await init_db()
    print(f"[{settings.APP_NAME}] Backend siap pada {settings.HOST}:{settings.PORT}")
    yield
    # Shutdown
    print(f"[{settings.APP_NAME}] Backend berhenti.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Platform Text-to-Speech Self-Hosted untuk Kreator Konten, didesain ringan untuk CPU/Intel Iris.",
    lifespan=lifespan,
)

# CORS Middleware agar Frontend Next.js (port 3000) bisa terhubung
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Mount endpoints juga di root path (/tts, /voices, /jobs/{id}) sesuai spesifikasi
from app.api.endpoints.clone import router as root_clone_router
from app.api.endpoints.health import router as root_health_router
from app.api.endpoints.history import router as root_history_router
from app.api.endpoints.projects import router as root_projects_router
from app.api.endpoints.tts import router as root_tts_router
from app.api.endpoints.voices import router as root_voices_router

app.include_router(root_tts_router)
app.include_router(root_voices_router)
app.include_router(root_health_router)
app.include_router(root_clone_router)
app.include_router(root_projects_router)
app.include_router(root_history_router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/health",
        "voices_url": "/api/voices",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
