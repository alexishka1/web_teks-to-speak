import math
import struct
import wave
from pathlib import Path


def generate_placeholder_wav(
    output_path: Path, duration_sec: float = 2.0, sample_rate: int = 22050
):
    """
    Menghasilkan file WAV sederhana (nada intro 440Hz halus)
    tanpa dependensi eksternal, digunakan untuk pengujian dan placeholder.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(duration_sec * sample_rate)

    with wave.open(str(output_path), "wb") as wav:
        wav.setnchannels(1)  # mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)

        for i in range(num_samples):
            # Envelop fade in / fade out lembut
            envelope = min(i / (sample_rate * 0.1), 1.0) * min(
                (num_samples - i) / (sample_rate * 0.1), 1.0
            )
            value = int(
                8000 * envelope * math.sin(2.0 * math.pi * 440.0 * (i / sample_rate))
            )
            data = struct.pack("<h", max(-32768, min(32767, value)))
            wav.writeframesraw(data)
