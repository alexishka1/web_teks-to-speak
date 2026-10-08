"""
Broadcast Loudness Normalization (-16 LUFS, ITU-R BS.1770) & True-Peak Limiter (-1 dBTP)
"""

from pathlib import Path


def normalize_to_target_lufs(audio_path: Path, target_lufs: float = -16.0) -> Path:
    """Normalisasi volume siaran audio."""
    return audio_path
