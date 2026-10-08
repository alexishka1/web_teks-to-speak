"""
Modul Cache Audio Berbasis Hash (SHA-256) untuk TTS TaSTP.
Menyimpan audio hasil sintesis berdasarkan kombinasi teks, voice_id, dan parameter,
sehingga permintaan teks identik dapat langsung dikembalikan tanpa komputasi ulang.
"""

import hashlib
import shutil
from pathlib import Path

from app.config import settings

CACHE_DIR = settings.AUDIO_OUTPUT_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def compute_cache_key(
    text: str,
    voice_id: str,
    speed: float = 1.0,
    pitch: float = 0.0,
    audio_effect: str = "none",
) -> str:
    """Menghitung hash SHA-256 unik untuk parameter sintesis."""
    raw_payload = (
        f"v3_{text.strip()}_{voice_id}_{speed:.3f}_{pitch:.3f}_{audio_effect}".encode()
    )
    return hashlib.sha256(raw_payload).hexdigest()


def get_cached_audio(cache_key: str) -> Path | None:
    """Mengambil file audio dari cache jika ada."""
    cached_file = CACHE_DIR / f"{cache_key}.wav"
    if cached_file.exists() and cached_file.stat().st_size > 44:
        return cached_file
    return None


def save_to_cache(cache_key: str, source_path: Path) -> Path:
    """Menyimpan file audio hasil ke direktori cache."""
    cached_file = CACHE_DIR / f"{cache_key}.wav"
    if source_path != cached_file:
        shutil.copy(source_path, cached_file)
    return cached_file
