"""
Modul Crossfade Equal-Power Audio PCM untuk Menghubungkan Sambungan Kalimat.
Menerapkan kurva cos/sin 30-50ms di setiap batas potongan audio
untuk menghilangkan letupan (clicks/pops) dan celah keheningan.
"""

import math
import struct
import wave
from pathlib import Path


def read_wav_pcm16(wav_path: Path) -> tuple[list[int], int, int]:
    """Membaca data sampel 16-bit PCM dari file WAV."""
    with wave.open(str(wav_path), "rb") as wf:
        num_channels = wf.getnchannels()
        sample_rate = wf.getframerate()
        num_frames = wf.getnframes()
        raw_bytes = wf.readframes(num_frames)

    fmt = f"<{num_frames * num_channels}h"
    samples = list(struct.unpack(fmt, raw_bytes))

    # Jika stereo, ambil kanal pertama (mono)
    if num_channels > 1:
        samples = samples[::num_channels]

    return samples, sample_rate, 1


def write_wav_pcm16(output_path: Path, samples: list[int], sample_rate: int = 22050):
    """Menulis daftar sampel 16-bit PCM ke file WAV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    raw_bytes = struct.pack(
        f"<{len(samples)}h", *[max(-32768, min(32767, s)) for s in samples]
    )

    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw_bytes)


def crossfade_pcm(
    chunks_samples: list[list[int]],
    crossfade_ms: int = 20,
    pause_ms: int = 250,
    sample_rate: int = 22050,
) -> list[int]:
    """
    Menggabungkan potongan kalimat audio PCM dengan:
    1. Micro fade-out halus (15-20ms) di ujung kalimat untuk mencegah letupan (clicks/pops).
    2. Jeda hening bernafas natural antar kalimat (pause_ms, default 250ms).
    3. Micro fade-in halus (15-20ms) di awal kalimat berikutnya.
    """
    if not chunks_samples:
        return []
    if len(chunks_samples) == 1:
        return chunks_samples[0]

    fade_samples = max(1, int((crossfade_ms / 1000.0) * sample_rate))
    pause_samples = [0] * max(0, int((pause_ms / 1000.0) * sample_rate))

    result: list[int] = []

    for idx, chunk in enumerate(chunks_samples):
        if not chunk:
            continue
        c = list(chunk)
        # Fade in pada awal kalimat jika bukan kalimat pertama
        if idx > 0 and len(c) > fade_samples:
            for j in range(fade_samples):
                w = math.sin((j / float(fade_samples)) * (math.pi / 2.0))
                c[j] = int(c[j] * w)

        # Fade out pada akhir kalimat jika bukan kalimat terakhir
        if idx < len(chunks_samples) - 1 and len(c) > fade_samples:
            for j in range(fade_samples):
                w = math.cos((j / float(fade_samples)) * (math.pi / 2.0))
                c[-fade_samples + j] = int(c[-fade_samples + j] * w)

        result.extend(c)
        if idx < len(chunks_samples) - 1 and pause_samples:
            result.extend(pause_samples)

    return result


def merge_wav_files_with_crossfade(
    wav_files: list[Path],
    output_path: Path,
    crossfade_ms: int = 20,
    pause_ms: int = 250,
    sample_rate: int = 22050,
) -> Path:
    """Menggabungkan file WAV berurutan dengan jeda hening natural dan fade halus."""
    if not wav_files:
        raise ValueError("Daftar file WAV kosong")

    if len(wav_files) == 1:
        import shutil

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(wav_files[0], output_path)
        return output_path

    pcm_chunks = []
    sr = sample_rate

    for wf_path in wav_files:
        samples, file_sr, _ = read_wav_pcm16(wf_path)
        sr = file_sr
        pcm_chunks.append(samples)

    merged_samples = crossfade_pcm(
        pcm_chunks, crossfade_ms=crossfade_ms, pause_ms=pause_ms, sample_rate=sr
    )
    write_wav_pcm16(output_path, merged_samples, sample_rate=sr)
    return output_path
