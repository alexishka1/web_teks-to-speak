import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "TaSTP - Self-Hosted TTS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Host & Port
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'storage' / 'tastp.db'}"

    # Hardware & Performance Guardrails (Intel Iris / CPU only)
    USE_CUDA: bool = False
    MAX_THREADS: int = 4
    MAX_TEXT_LENGTH: int = 5000  # Maksimal karakter per permintaan
    LAZY_LOAD_MODELS: bool = True

    # Engine Settings
    DEFAULT_ENGINE: str = "piper"  # "piper" atau "remote"
    MODELS_DIR: Path = BASE_DIR / "storage" / "models"
    AUDIO_OUTPUT_DIR: Path = BASE_DIR / "storage" / "audio"

    # Remote GPU Engine (Colab / Kaggle / Cloud GPU)
    REMOTE_ENGINE_URL: str = os.getenv("REMOTE_ENGINE_URL", "")
    REMOTE_ENGINE_API_KEY: str = os.getenv("REMOTE_ENGINE_API_KEY", "")
    REMOTE_TIMEOUT_SECONDS: int = 15
    AUTO_FALLBACK_TO_PIPER: bool = True

    # Audio Watermark / AI Disclosure
    EMBED_AI_LABEL: bool = True
    AI_LABEL_TEXT: str = "Dibuat dengan AI - TaSTP Studio"

    # Piper Intonation & Fallback Guardrails
    DEFAULT_NOISE_SCALE: float = 0.85
    DEFAULT_NOISE_W_SCALE: float = 1.0
    DEBUG_ALLOW_FALLBACK_TONE: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Pastikan folder penyimpanan tersedia
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
