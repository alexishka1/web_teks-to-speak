"""
Modul Pemrosesan Efek Audio Akustik Server-Side (FFmpeg):
- Reverb (Gema Ruang / Hall)
- Radio (Transmisi Walkie-Talkie / AM Bandpass)
- Telepon (Filter Seluler Bandwidth Terbatas G.711)
- Bisikan / Whisper (EQ High-Shelf, Low-Cut, Gain Rendah)
- Normalisasi Loudness Standar Siaran (-16 LUFS + True-Peak Limiter -1.5 dBTP)
- De-esser Ringan (Meredam Sibilance 5-9 kHz)
"""

import shutil
import subprocess
from pathlib import Path


def get_ffmpeg_executable() -> str | None:
    """Mencari path binary FFmpeg (dari sistem PATH atau bundle imageio-ffmpeg)."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def apply_audio_effects_ffmpeg(
    input_wav: Path,
    output_wav: Path,
    effect: str = "none",
    normalize_lufs: bool = True,
    apply_deesser: bool = True,
    pitch_semitones: float = 0.0,
    voice_profile_eq: str | None = None,
    sample_rate: int = 22050,
) -> Path:
    """
    Menerapkan rantai filter audio FFmpeg ke file WAV:
    - Pitch shifting (modulasi nada karakter & kontrol nada pengguna)
    - Formant / Resonansi EQ (pria/wanita)
    - Efek akustik (reverb, radio, dsb)
    - Normalisasi -16 LUFS & De-esser
    """
    ffmpeg_exe = get_ffmpeg_executable()
    if not ffmpeg_exe or not input_wav.exists():
        # Jika FFmpeg tidak ditemukan, salin file apa adanya
        if input_wav != output_wav:
            shutil.copy(input_wav, output_wav)
        return output_wav

    filters: list[str] = []

    # 1. Pitch Shifting (Modulasi Nada Suara)
    if abs(pitch_semitones) >= 0.1:
        clamped_pitch = max(-8.0, min(8.0, pitch_semitones))
        pitch_ratio = 2.0 ** (clamped_pitch / 12.0)
        scaled_rate = int(round(sample_rate * pitch_ratio))
        tempo_comp = 1.0 / pitch_ratio

        # asetrate mengubah pitch & kecepatan; aresample menstabilkan clock audio;
        # atempo mengembalikan tempo ke kecepatan semula sehingga durasi natural tanpa merubah pitch baru.
        filters.append(f"asetrate={scaled_rate}")
        filters.append(f"aresample={sample_rate}")
        if 0.5 <= tempo_comp <= 2.0:
            filters.append(f"atempo={tempo_comp:.4f}")
        elif tempo_comp > 2.0:
            filters.append("atempo=2.0")
            filters.append(f"atempo={(tempo_comp / 2.0):.4f}")
        else:
            filters.append("atempo=0.5")
            filters.append(f"atempo={(tempo_comp / 0.5):.4f}")

    # 2. Karakter Resonansi / Profil Akustik EQ (Karakter Suara Pria vs Wanita)
    if voice_profile_eq and voice_profile_eq != "anull":
        filters.append(voice_profile_eq)

    # 3. De-esser Ringan (Meredam frekuensi desis tajam s/sh di 5-9 kHz)
    if apply_deesser:
        filters.append("equalizer=f=6500:t=q:w=1.5:g=-4.0")

    # 2. Efek Akustik Spesifik
    if effect == "reverb":
        # Ruang gema reflektif halus (aecho)
        filters.append("aecho=0.8:0.85:35|50:0.35|0.25")
    elif effect == "radio":
        # Bandpass walkie-talkie (400 Hz - 3400 Hz) + saturasi
        filters.append("highpass=f=400,lowpass=f=3400,volume=1.2")
    elif effect == "telephone":
        # Karakter audio percakapan telepon (300 Hz - 3200 Hz)
        filters.append("highpass=f=300,lowpass=f=3200,volume=1.35")
    elif effect == "whisper":
        # Bisikan rahasia (potong nada rendah < 800 Hz, angkat treble halus, gain rendah)
        filters.append("highpass=f=800,lowpass=f=5500,treble=g=3:f=3000,volume=0.75")
    elif effect == "podcast_eq":
        # Warm proximity EQ untuk siniar
        filters.append("bass=g=3.0:f=120,treble=g=1.5:f=8000,volume=1.05")

    # 3. Normalisasi Loudness Standar Siaran YouTube / Podcast (-16 LUFS)
    if normalize_lufs:
        filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

    # Susun filtergraph
    filter_chain = ",".join(filters) if filters else "anull"

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    temp_target = (
        output_wav if output_wav != input_wav else output_wav.with_suffix(".tmp.wav")
    )

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        str(input_wav),
        "-af",
        filter_chain,
        "-ar",
        str(sample_rate),
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(temp_target),
    ]

    try:
        subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25, check=True
        )
        if temp_target != output_wav:
            temp_target.replace(output_wav)
        return output_wav
    except Exception as e:
        print(
            f"[AudioEffects] Peringatan: Gagal memproses FFmpeg ({e}). Menggunakan audio asli."
        )
        if input_wav != output_wav:
            shutil.copy(input_wav, output_wav)
        return output_wav


def apply_audio_effect(audio_path: Path, effect_name: str) -> Path:
    """Helper kompatibilitas langsung untuk pipeline lama."""
    if effect_name == "none":
        return audio_path
    output_path = audio_path.with_name(f"{audio_path.stem}_{effect_name}.wav")
    return apply_audio_effects_ffmpeg(audio_path, output_path, effect=effect_name)
