"""
F5-TTS Engine Adapter (Optional heavy GPU model)
"""

from pathlib import Path
from typing import Any

from app.engines.base import TTSEngine


class F5TTSEngine(TTSEngine):
    def __init__(self):
        super().__init__(name="f5tts")

    def is_available(self) -> bool:
        return False  # Tidak aktif secara default pada dev laptop CPU

    async def load_model(self, voice_id: str) -> None:
        pass

    async def unload_model(self, voice_id: str) -> None:
        pass

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        speed: float = 1.0,
        pitch: float = 0.0,
        extra_params: dict[str, Any] | None = None,
    ) -> float:
        raise NotImplementedError("F5-TTS hanya didukung melalui remote GPU.")

    def get_supported_voices(self) -> list[dict[str, Any]]:
        return []
