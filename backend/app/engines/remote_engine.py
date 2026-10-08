"""
Remote GPU Engine Adapter (Colab / Kaggle / Cloud GPU)
Fitur:
- Panggil endpoint server GPU via URL di .env (REMOTE_ENGINE_URL)
- Health check liveness remote server
- Fallback otomatis ke PiperEngine jika server remote mati/timeout
"""

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from app.config import settings
from app.engines.base import TTSEngine
from app.engines.piper_engine import piper_engine


class RemoteEngine(TTSEngine):
    def __init__(self):
        super().__init__(name="remote")
        self.endpoint_url = (
            settings.REMOTE_ENGINE_URL.rstrip("/") if settings.REMOTE_ENGINE_URL else ""
        )
        self.timeout_sec = settings.REMOTE_TIMEOUT_SECONDS

    def is_available(self) -> bool:
        """Engine remote dianggap ada jika URL diisi dan responsif."""
        if not self.endpoint_url:
            return False
        return self.health_check()

    def health_check(self) -> bool:
        """Memeriksa apakah server remote GPU aktif."""
        if not self.endpoint_url:
            return False
        try:
            url = f"{self.endpoint_url}/health"
            req = urllib.request.Request(
                url, headers={"User-Agent": "TaSTP-RemoteEngine"}
            )
            if settings.REMOTE_ENGINE_API_KEY:
                req.add_header(
                    "Authorization", f"Bearer {settings.REMOTE_ENGINE_API_KEY}"
                )

            with urllib.request.urlopen(req, timeout=3) as resp:  # nosec B310
                return resp.status == 200
        except Exception:
            return False

    async def load_model(self, voice_id: str) -> None:
        """Tidak perlu memuat bobot model di RAM laptop lokal."""

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
        """
        Kirim permintaan sintesis ke server GPU remote.
        Bila gagal atau server offline, beralih otomatis ke PiperEngine.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.endpoint_url or not self.health_check():
            print(
                f"[RemoteEngine] Server GPU ({self.endpoint_url or 'URL belum diset'}) offline. Auto-fallback ke PiperEngine."
            )
            return await piper_engine.synthesize(
                text=text,
                voice_id=voice_id,
                output_path=output_path,
                speed=speed,
                pitch=pitch,
                extra_params=extra_params,
            )

        try:
            payload = {
                "text": text,
                "voice_id": voice_id,
                "speed": speed,
                "pitch": pitch,
                **(extra_params or {}),
            }
            url = f"{self.endpoint_url}/tts"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            if settings.REMOTE_ENGINE_API_KEY:
                req.add_header(
                    "Authorization", f"Bearer {settings.REMOTE_ENGINE_API_KEY}"
                )

            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:  # nosec B310
                content_type = resp.headers.get("Content-Type", "")
                if "audio" in content_type or "octet-stream" in content_type:
                    output_path.write_bytes(resp.read())
                else:
                    # JSON response dengan audio_url atau base64
                    body = json.loads(resp.read().decode("utf-8"))
                    if "audio_url" in body:
                        # Unduh dari remote audio url
                        remote_audio_url = body["audio_url"]
                        if not remote_audio_url.startswith("http"):
                            remote_audio_url = f"{self.endpoint_url}{remote_audio_url}"
                        urllib.request.urlretrieve(remote_audio_url, str(output_path))  # nosec B310
                    else:
                        raise ValueError("Format respon audio remote tidak dikenali.")

            # Hitung durasi file audio
            import wave

            with wave.open(str(output_path), "rb") as wf:
                return wf.getnframes() / float(wf.getframerate())

        except Exception as e:
            print(
                f"[RemoteEngine] Gagal memanggil Remote GPU: {e}. Melakukan fallback otomatis ke PiperEngine."
            )
            return await piper_engine.synthesize(
                text=text,
                voice_id=voice_id,
                output_path=output_path,
                speed=speed,
                pitch=pitch,
                extra_params=extra_params,
            )

    def get_supported_voices(self) -> list[dict[str, Any]]:
        """Mengambil katalog suara dari remote jika online, fallback ke Piper."""
        if self.endpoint_url and self.health_check():
            try:
                url = f"{self.endpoint_url}/voices"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=3) as resp:  # nosec B310
                    return json.loads(resp.read().decode("utf-8"))
            except Exception:
                pass
        return piper_engine.get_supported_voices()

    def register_clone_sample(
        self,
        voice_id: str,
        audio_path: Path,
        transcript: str | None = None,
        speaker_name: str = "",
    ) -> bool:
        """
        Kirim sampel audio referensi ke Remote GPU server untuk ekstraksi embedding vokal.
        Jika server remote offline, mengembalikan False (akan menggunakan fallback Piper).
        """
        if not self.endpoint_url or not self.health_check():
            return False
        try:
            import uuid

            boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
            data = bytearray()
            # File data
            data.extend(f"--{boundary}\r\n".encode())
            data.extend(
                f'Content-Disposition: form-data; name="file"; filename="{audio_path.name}"\r\n'.encode()
            )
            data.extend(b"Content-Type: audio/wav\r\n\r\n")
            data.extend(audio_path.read_bytes())
            data.extend(b"\r\n")
            # voice_id
            data.extend(f"--{boundary}\r\n".encode())
            data.extend(
                f'Content-Disposition: form-data; name="voice_id"\r\n\r\n{voice_id}\r\n'.encode()
            )
            # speaker_name
            data.extend(f"--{boundary}\r\n".encode())
            data.extend(
                f'Content-Disposition: form-data; name="speaker_name"\r\n\r\n{speaker_name}\r\n'.encode()
            )
            # transcript
            if transcript:
                data.extend(f"--{boundary}\r\n".encode())
                data.extend(
                    f'Content-Disposition: form-data; name="transcript"\r\n\r\n{transcript}\r\n'.encode()
                )
            data.extend(f"--{boundary}--\r\n".encode())

            req = urllib.request.Request(
                f"{self.endpoint_url}/clone",
                data=bytes(data),
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            )
            if settings.REMOTE_ENGINE_API_KEY:
                req.add_header(
                    "Authorization", f"Bearer {settings.REMOTE_ENGINE_API_KEY}"
                )

            with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
                return resp.status in (200, 201)
        except Exception as e:
            print(f"[RemoteEngine] Gagal mengirim sampel klon ke server remote: {e}")
            return False


remote_engine = RemoteEngine()
