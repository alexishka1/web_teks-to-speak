"""
Audio processor: merge chunks with equal-power crossfade
"""

from pathlib import Path


def merge_audio_chunks(
    chunk_paths: list[Path], output_path: Path, crossfade_ms: int = 40
) -> Path:
    """Menggabungkan potongan WAV dengan crossfade halus 40ms."""
    # Placeholder: tahap 2
    if chunk_paths:
        import shutil

        shutil.copy(chunk_paths[0], output_path)
    return output_path
