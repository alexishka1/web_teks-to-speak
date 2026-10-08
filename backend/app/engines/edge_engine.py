"""
Adapter Engine Microsoft Edge TTS (Online Free Neural TTS).
Menggunakan pustaka edge-tts untuk mengakses suara neural Bahasa Indonesia resmi:
- id-ID-ArdiNeural (Pria)
- id-ID-GadisNeural (Wanita)
- jv-ID-DimasNeural (Pria, Jawa)
- jv-ID-SitiNeural (Wanita, Jawa)

Catatan Teknis & Lisensi:
- edge-tts adalah klien tidak resmi (reverse-engineered) dari layanan browser Microsoft Edge.
- Tidak membutuhkan API key dan tidak dikenakan biaya kuota.
- Memerlukan koneksi internet stabil (bukan 100% offline).
- Tidak memiliki Service Level Agreement (SLA) resmi.
"""

import subprocess
import wave
from pathlib import Path
from typing import Any

import edge_tts
from app.audio.effects import get_ffmpeg_executable
from app.config import settings
from app.engines.base import TTSEngine

EDGE_VOICE_MAPPING: dict[str, dict[str, str]] = {
    "edge_ardi": {
        "voice_id": "id-ID-ArdiNeural",
        "name": "Ardi",
        "gender": "male",
        "description": "Suara pria neural Indonesia berbobot formal dan tegas",
    },
    "edge_gadis": {
        "voice_id": "id-ID-GadisNeural",
        "name": "Gadis (Edge)",
        "gender": "female",
        "description": "Suara wanita neural Indonesia jernih, alami, dan artikulatif",
    },
    "edge_dimas": {
        "voice_id": "jv-ID-DimasNeural",
        "name": "Dimas (Jawa)",
        "gender": "male",
        "description": "Suara pria neural dengan aksen / dialek Jawa alami",
    },
    "edge_siti": {
        "voice_id": "jv-ID-SitiNeural",
        "name": "Siti (Jawa)",
        "gender": "female",
        "description": "Suara wanita neural dengan aksen / dialek Jawa ramah",
    },
}


class EdgeTTSEngine(TTSEngine):
    """Implementasi TTSEngine menggunakan edge-tts (Microsoft Edge Online TTS)."""

    def __init__(self):
        super().__init__(name="edge")

    def is_available(self) -> bool:
        """Edge TTS siap digunakan jika flag koneksi online diizinkan."""
        return bool(settings.ONLINE_ENGINES_ENABLED)

    async def load_model(self, voice_id: str) -> None:
        """Layanan online tidak memerlukan model onnx lokal di RAM."""
        pass

    def get_supported_voices(self) -> list[dict[str, Any]]:
        """Daftar karakter suara Edge TTS resmi di katalog TaSTP."""
        voices = []
        for v_id, meta in EDGE_VOICE_MAPPING.items():
            voices.append(
                {
                    "id": v_id,
                    "name": meta["name"],
                    "gender": meta["gender"],
                    "engine": "edge",
                    "description": meta["description"],
                    "backed_by": "dedicated_model",
                }
            )
        return voices

    def _resolve_voice_id(self, voice_id: str) -> str:
        """Menerjemahkan alias suara TaSTP ke nama model Neural Microsoft."""
        if voice_id in EDGE_VOICE_MAPPING:
            return EDGE_VOICE_MAPPING[voice_id]["voice_id"]
        # Jika user memasukkan langsung nama resmi seperti 'id-ID-ArdiNeural'
        if "Neural" in voice_id:
            return voice_id
        # Default fallback ke Ardi untuk pria atau Gadis untuk wanita
        v_low = voice_id.lower()
        if any(k in v_low for k in ["pria", "male", "bima", "dimas", "ardi"]):
            return "id-ID-ArdiNeural"
        return "id-ID-GadisNeural"

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
        Sintesis ucapan via Edge TTS dan konversi hasilnya ke WAV mono 22050 Hz PCM.
        """
        if not settings.ONLINE_ENGINES_ENABLED:
            raise RuntimeError(
                "Engine online (Edge TTS) dinonaktifkan oleh kebijakan privasi. "
                "Aktifkan ONLINE_ENGINES_ENABLED=true di konfigurasi backend/.env untuk menggunakan engine ini."
            )

        neural_voice = self._resolve_voice_id(voice_id)

        # Hitung modulasi kecepatan (rate) dalam format persen, misal '+10%' atau '-15%'
        rate_pct = int(round((speed - 1.0) * 100))
        rate_str = f"{rate_pct:+d}%"

        # Hitung modulasi pitch dalam format Hz, misal '+10Hz' atau '-10Hz'
        pitch_hz = int(round(pitch * 8))
        pitch_str = f"{pitch_hz:+d}Hz"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_mp3 = output_path.with_suffix(".edge_temp.mp3")

        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=neural_voice,
                rate=rate_str,
                pitch=pitch_str,
            )
            await communicate.save(str(temp_mp3))
        except Exception as e:
            raise RuntimeError(
                f"Koneksi ke layanan Microsoft Edge TTS gagal: {e}. "
                "Pastikan koneksi internet aktif atau gunakan Piper ONNX untuk mode offline."
            ) from e

        if not temp_mp3.exists() or temp_mp3.stat().st_size == 0:
            raise RuntimeError("Hasil audio dari Edge TTS kosong atau tidak berhasil dibuat.")

        # Konversi file MP3 ke format WAV mono 22050 Hz 16-bit via FFmpeg
        ffmpeg_exe = get_ffmpeg_executable()
        if ffmpeg_exe:
            try:
                cmd = [
                    ffmpeg_exe,
                    "-y",
                    "-i",
                    str(temp_mp3),
                    "-ar",
                    "22050",
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s16le",
                    str(output_path),
                ]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if proc.returncode == 0 and output_path.exists():
                    temp_mp3.unlink(missing_ok=True)
                else:
                    temp_mp3.rename(output_path)
            except Exception:
                temp_mp3.rename(output_path)
        else:
            temp_mp3.rename(output_path)

        # Hitung durasi WAV
        try:
            with wave.open(str(output_path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate() or 22050
                return frames / float(rate)
        except Exception:
            return 1.0


edge_engine = EdgeTTSEngine()
