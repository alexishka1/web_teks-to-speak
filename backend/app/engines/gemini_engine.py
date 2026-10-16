"""
Adapter Engine Google Gemini TTS (Studio Grade Speech Generation).
Model: gemini-3.8-flash-tts
Mendukung instruksi gaya bicara verbatim natural language (speech_metadata.style)
dan menghasilkan audio WAV studio 24 kHz yang distandarisasi ke format pipeline TaSTP.
"""

import asyncio
import base64
import subprocess
import wave
from pathlib import Path
from typing import Any

import httpx
from app.audio.effects import get_ffmpeg_executable
from app.config import settings
from app.emotion.gemini_styles import get_gemini_style_instruction
from app.engines.base import TTSEngine

GEMINI_VOICE_MAPPING: dict[str, dict[str, str]] = {
    "gemini_kore": {
        "voice_name": "Kore",
        "gender": "female",
        "description": "Suara wanita hangat, empati, dan natural untuk narasi & cerita",
    },
    "gemini_puck": {
        "voice_name": "Puck",
        "gender": "male",
        "description": "Suara pria muda, cerah, energik untuk konten kreator & casual",
    },
    "gemini_fenrir": {
        "voice_name": "Fenrir",
        "gender": "male",
        "description": "Suara pria berbobot dalam, tegas, dan berwibawa untuk berita & formal",
    },
    "gemini_aoede": {
        "voice_name": "Aoede",
        "gender": "female",
        "description": "Suara wanita melodik, jernih, dan artikulatif untuk podcast & edukasi",
    },
}


class GeminiTTSEngine(TTSEngine):
    """Implementasi TTSEngine untuk Google Gemini Flash TTS API."""

    def __init__(self):
        super().__init__(name="gemini")
        self.endpoint_base = "https://generativelanguage.googleapis.com/v1beta/models"

    def is_available(self) -> bool:
        """Engine siap jika fitur online diizinkan dan GEMINI_API_KEY terkonfigurasi."""
        return bool(settings.ONLINE_ENGINES_ENABLED and settings.GEMINI_API_KEY)

    async def load_model(self, voice_id: str) -> None:
        """API berbasis cloud tidak membutuhkan pemuatan model ke RAM lokal."""
        pass

    def get_supported_voices(self) -> list[dict[str, Any]]:
        """Daftar karakter suara Gemini yang terdaftar resmi di TaSTP."""
        voices = []
        for v_id, meta in GEMINI_VOICE_MAPPING.items():
            voices.append(
                {
                    "id": v_id,
                    "name": meta["voice_name"],
                    "gender": meta["gender"],
                    "engine": "gemini",
                    "description": meta["description"],
                    "backed_by": "dedicated_model",
                }
            )
        return voices

    def _resolve_voice_name(self, voice_id: str) -> str:
        """Menerjemahkan voice_id TaSTP ke nama prebuilt voice Gemini."""
        if voice_id in GEMINI_VOICE_MAPPING:
            return GEMINI_VOICE_MAPPING[voice_id]["voice_name"]

        # Jika suara adalah suara kloning pengguna (clone_...)
        if voice_id.startswith("clone_"):
            try:
                import sqlite3
                from app.config import BASE_DIR

                db_path = BASE_DIR / "storage" / "tastp.db"
                if db_path.exists():
                    conn = sqlite3.connect(str(db_path))
                    c = conn.cursor()
                    row = c.execute(
                        "SELECT gender, name FROM voice_records WHERE id=?", (voice_id,)
                    ).fetchone()
                    conn.close()
                    if row:
                        gender, name = (row[0] or "").lower(), (row[1] or "").lower()
                        is_male = gender in ("male", "pria") or any(
                            k in name for k in ["boy", "pria", "cowok", "man", "bima", "dimas", "laki"]
                        )
                        if not is_male and gender not in ("female", "wanita", "perempuan", "cewek", "gadis"):
                            try:
                                from app.audio.pipeline import get_clone_acoustic_profile
                                shift, _ = get_clone_acoustic_profile(voice_id)
                                if shift <= -2.0:
                                    is_male = True
                            except Exception:
                                pass
                        return "Puck" if is_male else "Kore"
            except Exception as e:
                print(f"[GeminiEngine] Error lookup voice clone: {e}")
            return "Puck" if any(k in voice_id.lower() for k in ["boy", "male", "pria"]) else "Kore"

        # Jika user memasukkan langsung nama prebuilt (misal 'Kore', 'Puck', 'Fenrir', 'Aoede')
        clean = voice_id.replace("gemini_", "").capitalize()
        return clean if clean in ("Kore", "Puck", "Fenrir", "Aoede", "Charon") else "Kore"

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
        Sintesis suara menggunakan Gemini 3.8 Flash TTS.
        Mengirim teks verbatim dan gaya emosi ke speech_metadata.style.
        """
        if not settings.ONLINE_ENGINES_ENABLED:
            raise RuntimeError(
                "Engine online (Gemini TTS) dinonaktifkan oleh kebijakan privasi. "
                "Aktifkan ONLINE_ENGINES_ENABLED=true di konfigurasi backend/.env untuk menggunakan engine ini."
            )

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY belum disetel. Tambahkan GEMINI_API_KEY di file backend/.env."
            )

        voice_name = self._resolve_voice_name(voice_id)
        params = extra_params or {}
        emotion_id = params.get("emotion", "neutral")
        intensity = float(params.get("intensity", 100.0))

        # Petunjuk gaya bicara akting
        style_instruction = get_gemini_style_instruction(emotion_id, intensity)

        # Modifikasi kecepatan jika diinginkan
        if speed > 1.25:
            style_instruction += ", delivered at a fast, rapid pace"
        elif speed < 0.8:
            style_instruction += ", delivered at a slow, deliberate pace"

        # URL request tanpa mencatat key ke log publik
        model_name = settings.GEMINI_MODEL or "gemini-3.8-flash-tts"
        url = f"{self.endpoint_base}/{model_name}:generateContent"

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": text,
                            "speech_metadata": {
                                "style": style_instruction,
                            },
                        }
                    ]
                }
            ],
            "generationConfig": {
                "response_modalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": voice_name,
                        }
                    }
                },
            },
        }

        # Lakukan request HTTP dengan retry & backoff untuk menangani 429 / transient failure
        max_retries = 3
        backoff_delay = 1.5
        last_error_msg = ""
        audio_b64: str | None = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(max_retries):
                try:
                    resp = await client.post(
                        url,
                        params={"key": api_key},
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            raise RuntimeError(
                                f"Gemini API tidak mengembalikan kandidat audio: {data.get('promptFeedback', {})}"
                            )
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            inline_data = part.get("inlineData", {})
                            if inline_data.get("data"):
                                audio_b64 = inline_data["data"]
                                break
                        if audio_b64:
                            break
                        raise RuntimeError("Kandidat Gemini tidak memuat data audio inline.")

                    elif resp.status_code in (429, 503):
                        last_error_msg = f"HTTP {resp.status_code}: Batas kuota (Rate Limit/Quota) Gemini tercapai."
                        await asyncio.sleep(backoff_delay * (attempt + 1))
                    elif resp.status_code == 400:
                        err_detail = resp.text[:200]
                        raise RuntimeError(f"Permintaan Gemini TTS tidak valid (400): {err_detail}")
                    elif resp.status_code == 403:
                        raise RuntimeError("Akses Gemini API ditolak (403). Pastikan GEMINI_API_KEY valid dan aktif.")
                    else:
                        last_error_msg = f"Gemini API error (HTTP {resp.status_code}): {resp.text[:200]}"
                        await asyncio.sleep(backoff_delay)
                except httpx.RequestError as exc:
                    last_error_msg = f"Koneksi jaringan ke Gemini API gagal: {exc}"
                    await asyncio.sleep(backoff_delay)

        if not audio_b64:
            raise RuntimeError(
                f"Sintesis Gemini TTS gagal setelah {max_retries} percobaan: {last_error_msg or 'Audio tidak diterima'}"
            )

        # Simpan audio mentah hasil decode
        raw_bytes = base64.b64decode(audio_b64)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        raw_temp = output_path.with_suffix(".gemini_raw.wav")
        raw_temp.write_bytes(raw_bytes)

        # Standarisasi output audio ke WAV mono 22050 Hz 16-bit agar kompatibel dengan crossfade & loudnorm
        ffmpeg_exe = get_ffmpeg_executable()
        if ffmpeg_exe:
            try:
                cmd = [
                    ffmpeg_exe,
                    "-y",
                    "-i",
                    str(raw_temp),
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
                    raw_temp.unlink(missing_ok=True)
                else:
                    # Fallback jika konversi gagal
                    raw_temp.rename(output_path)
            except Exception:
                raw_temp.rename(output_path)
        else:
            raw_temp.rename(output_path)

        # Hitung durasi file audio
        try:
            with wave.open(str(output_path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate() or 22050
                return frames / float(rate)
        except Exception:
            return 1.0


gemini_engine = GeminiTTSEngine()
