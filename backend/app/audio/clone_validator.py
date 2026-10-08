"""
Modul Validasi & Pemrosesan Sampel Suara Kloning (Voice Clone Validator):
- Memeriksa format file audio (WAV, MP3, M4A, OGG, WEBM, FLAC) & batas ukuran
- Memvalidasi durasi rekaman (Wajib 10 s.d. 30 detik, ideal 15-30 detik)
- Memeriksa tingkat energi/RMS (mencegah file audio hening / noise kosong)
- Konversi otomatis ke WAV mono 24 kHz via FFmpeg
- Trim hening awal & akhir (silenceremove)
- Normalisasi volume suara vokal (-16 LUFS)
- Deteksi clipping & analisis metrik kualitas audio
"""

import math
import shutil
import struct
import subprocess
import wave
from pathlib import Path
from typing import Any

from app.audio.effects import get_ffmpeg_executable

MIN_SAMPLE_DURATION = 10.0
MAX_SAMPLE_DURATION = 30.0
IDEAL_MIN_DURATION = 15.0
IDEAL_MAX_DURATION = 30.0
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac", ".aac"}


def get_audio_duration(file_path: Path) -> float:
    """Mendapatkan durasi audio dalam satuan detik."""
    # 1. Coba baca via standar library wave jika format WAV
    try:
        with wave.open(str(file_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                return float(frames) / float(rate)
    except Exception:
        pass

    # 2. Coba pakai ffprobe jika tersedia
    ffmpeg_exe = get_ffmpeg_executable()
    if ffmpeg_exe:
        candidate = Path(ffmpeg_exe).parent / "ffprobe.exe"
        ffprobe_exe: str | None = (
            str(candidate) if candidate.exists() else shutil.which("ffprobe")
        )
        if ffprobe_exe and Path(ffprobe_exe).exists():
            try:
                cmd = [
                    str(ffprobe_exe),
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(file_path),
                ]
                res = subprocess.run(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                if res.returncode == 0 and res.stdout.strip():
                    return float(res.stdout.strip())
            except Exception:
                pass

    return 0.0


def check_audio_energy_and_silence(file_path: Path) -> tuple[bool, float]:
    """
    Menghitung estimasi energi RMS dari file audio WAV.
    Mengembalikan (is_silent: bool, rms_value: float).
    """
    try:
        with wave.open(str(file_path), "rb") as wf:
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            framerate = wf.getframerate() or 24000

            if sampwidth != 2:  # bukan 16-bit
                return (False, 1000.0)

            # Baca sample bertahap (hingga 5 detik)
            raw_frames = wf.readframes(min(n_frames, framerate * 5))
            if not raw_frames:
                return (True, 0.0)

            sum_sq = 0.0
            unpacked = struct.unpack(f"<{len(raw_frames) // 2}h", raw_frames)
            for s in unpacked:
                sum_sq += s * s

            rms = math.sqrt(sum_sq / max(1, len(unpacked)))
            is_silent = rms < 150.0  # Sangat hening di bawah ambang batas vokal manusia
            return (is_silent, rms)
    except Exception:
        # Jika bukan wav mentah, coba analisis durasi
        dur = get_audio_duration(file_path)
        return (dur <= 0.1, 1000.0 if dur > 0.1 else 0.0)


def analyze_audio_quality(file_path: Path) -> dict[str, Any]:
    """
    Menganalisis indikator kualitas vokal:
    - Durasi & apakah masuk rentang ideal (15-30s)
    - Deteksi sinyal clipping / distorsi
    - Estimasi level volume (lemah, optimal, berlebihan)
    """
    duration = get_audio_duration(file_path)
    is_ideal = IDEAL_MIN_DURATION <= duration <= IDEAL_MAX_DURATION

    clipping_detected = False
    max_peak = 0
    rms_value = 0.0

    try:
        with wave.open(str(file_path), "rb") as wf:
            if wf.getsampwidth() == 2:
                n_frames = wf.getnframes()
                raw_frames = wf.readframes(
                    min(n_frames, (wf.getframerate() or 24000) * 10)
                )
                if raw_frames:
                    unpacked = struct.unpack(f"<{len(raw_frames) // 2}h", raw_frames)
                    max_peak = max(abs(s) for s in unpacked) if unpacked else 0
                    sum_sq = sum(s * s for s in unpacked)
                    rms_value = math.sqrt(sum_sq / max(1, len(unpacked)))
                    # 16-bit integer max is 32767. Clipping jika mendekati 32500
                    if max_peak >= 32500:
                        clipping_detected = True
    except Exception:
        pass

    if rms_value < 1200.0:
        volume_status = "rendah"
        quality_score = 70
    elif rms_value > 20000.0 or clipping_detected:
        volume_status = "terlalu_tinggi"
        quality_score = 65
    else:
        volume_status = "optimal"
        quality_score = 95 if is_ideal else 85

    return {
        "duration_sec": round(duration, 2),
        "is_ideal_duration": is_ideal,
        "clipping_detected": clipping_detected,
        "peak_amplitude": max_peak,
        "rms_energy": round(rms_value, 1),
        "volume_status": volume_status,
        "quality_score": quality_score,
    }


def convert_sample_to_standard_wav(src_path: Path, dest_wav: Path) -> bool:
    """
    Mengonversi file sampel audio ke format WAV mono 24 kHz (24000 Hz, 16-bit PCM),
    memangkas hening di awal/akhir rekaman (trim silence),
    serta menormalisasi volume (-16 LUFS).
    """
    ffmpeg_exe = get_ffmpeg_executable()
    if ffmpeg_exe:
        try:
            # Filter silenceremove bolak-balik untuk trim awal dan akhir, dilanjutkan loudnorm
            filter_str = (
                "silenceremove=start_periods=1:start_duration=0.08:start_threshold=-45dB:detection=peak,"
                "areverse,"
                "silenceremove=start_periods=1:start_duration=0.08:start_threshold=-45dB:detection=peak,"
                "areverse,"
                "loudnorm=I=-16:TP=-1.5:LRA=11"
            )
            cmd = [
                ffmpeg_exe,
                "-y",
                "-i",
                str(src_path),
                "-af",
                filter_str,
                "-ar",
                "24000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(dest_wav),
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if (
                res.returncode == 0
                and dest_wav.exists()
                and dest_wav.stat().st_size > 44
            ):
                return True
        except Exception:
            pass

        # Fallback jika kombinasi filter gagal (misal file audio sangat pendek)
        try:
            fallback_cmd = [
                ffmpeg_exe,
                "-y",
                "-i",
                str(src_path),
                "-ar",
                "24000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(dest_wav),
            ]
            res2 = subprocess.run(
                fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            if res2.returncode == 0 and dest_wav.exists():
                return True
        except Exception:
            pass

    # Salin biasa jika ffmpeg tidak ada
    shutil.copy(src_path, dest_wav)
    return dest_wav.exists()


def _is_pcm_wav(file_path: Path) -> bool:
    """True jika file adalah WAV PCM yang bisa dibaca modul standar `wave`."""
    try:
        with wave.open(str(file_path), "rb") as wf:
            return wf.getframerate() > 0
    except Exception:
        return False


def decode_to_temp_wav(src_path: Path) -> Path | None:
    """
    Decode audio apa pun (WebM/Opus dari browser, MP3, M4A, dll) ke WAV PCM mono 24 kHz.
    Rekaman MediaRecorder Chrome tidak punya metadata durasi, sehingga durasi
    harus dibaca dari audio hasil decode, bukan dari header container.
    """
    ffmpeg_exe = get_ffmpeg_executable()
    if not ffmpeg_exe:
        return None
    out_path = src_path.with_name(f"{src_path.stem}.decoded.wav")
    try:
        res = subprocess.run(
            [
                ffmpeg_exe, "-y", "-i", str(src_path),
                "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(out_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        if res.returncode == 0 and out_path.exists() and out_path.stat().st_size > 44:
            return out_path
    except Exception:
        pass
    out_path.unlink(missing_ok=True)
    return None


def validate_clone_sample(audio_path: Path) -> dict[str, Any]:
    """
    Memvalidasi seluruh kriteria sampel audio untuk voice clone:
    - Format & ekstensi file
    - Ukuran maksimum file (<= 25 MB)
    - Durasi: Wajib 10.0 s.d. 30.0 detik (ideal 15 - 30 detik)
    - Non-silent: Harus mengandung sinyal audio vokal yang jelas
    """
    if not audio_path.exists():
        return {
            "valid": False,
            "duration_sec": 0.0,
            "error": "File sampel audio tidak ditemukan di server.",
        }

    file_size = audio_path.stat().st_size
    if file_size > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        return {
            "valid": False,
            "duration_sec": 0.0,
            "error": f"Ukuran file audio ({file_size / (1024 * 1024):.1f} MB) melebihi batas maksimum {max_mb} MB.",
        }

    # Non-WAV (mis. rekaman browser WebM/Opus) -> decode ke WAV PCM dulu
    work_path = audio_path
    decoded_path: Path | None = None
    if not _is_pcm_wav(audio_path):
        decoded_path = decode_to_temp_wav(audio_path)
        if decoded_path is not None:
            work_path = decoded_path

    try:
        dur = get_audio_duration(work_path)
        if dur <= 0.0:
            return {
                "valid": False,
                "duration_sec": 0.0,
                "error": "Format file audio tidak valid atau durasi tidak dapat dibaca. Pastikan FFmpeg terpasang di server.",
            }

        if dur < MIN_SAMPLE_DURATION:
            return {
                "valid": False,
                "duration_sec": round(dur, 2),
                "error": f"Durasi sampel audio terlalu pendek ({dur:.1f} detik). Sampel suara kloning wajib minimal 10 detik agar pola vokal dikenali.",
            }

        if dur > MAX_SAMPLE_DURATION:
            return {
                "valid": False,
                "duration_sec": round(dur, 2),
                "error": f"Durasi sampel audio terlalu panjang ({dur:.1f} detik). Maksimal durasi sampel suara kloning adalah 30 detik.",
            }

        is_silent, rms = check_audio_energy_and_silence(work_path)
        if is_silent:
            return {
                "valid": False,
                "duration_sec": round(dur, 2),
                "error": "Sampel audio hening atau tidak terdeteksi suara vokal manusia.",
            }

        quality_info = analyze_audio_quality(work_path)

        return {
            "valid": True,
            "duration_sec": round(dur, 2),
            "rms": round(rms, 2),
            "quality": quality_info,
            "error": None,
        }
    finally:
        if decoded_path is not None:
            decoded_path.unlink(missing_ok=True)
