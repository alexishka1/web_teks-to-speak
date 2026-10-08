from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class TTSEngine(ABC):
    """
    Interface tunggal untuk semua engine TTS di TaSTP:
    - Piper (ONNX CPU-only untuk laptop Intel Iris)
    - RemoteEngine (Colab/Kaggle GPU)
    - F5-TTS (opsional)
    """

    def __init__(self, name: str):
        self.name = name
        self._is_loaded = False

    @abstractmethod
    def is_available(self) -> bool:
        """Mengecek apakah engine siap digunakan di lingkungan ini."""

    @abstractmethod
    async def load_model(self, voice_id: str) -> None:
        """Memuat model secara lazy-load ketika dibutuhkan saja."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        speed: float = 1.0,
        pitch: float = 0.0,
        extra_params: dict[str, Any] | None = None,
    ) -> float:
        """
        Melakukan sintesis suara dan menyimpan hasilnya ke file output_path.
        Mengembalikan durasi audio dalam detik.
        """

    @abstractmethod
    def get_supported_voices(self) -> list[dict[str, Any]]:
        """Daftar suara yang didukung oleh engine ini."""
