"""
Modul Etika & Watermarking Metadata Audio TaSTP:
Menyematkan label "Dibuat dengan AI - TaSTP Studio" pada metadata audio (RIFF INFO chunk / FFmpeg tags)
sesuai regulasi transparansi kecerdasan buatan.
"""

import shutil
import struct
import subprocess
from pathlib import Path
from typing import Any

from app.audio.effects import get_ffmpeg_executable

AI_DEFAULT_DISCLOSURE = "Dibuat dengan AI - TaSTP Studio"


def embed_ai_disclosure_metadata(
    audio_path: Path,
    comment: str = AI_DEFAULT_DISCLOSURE,
    output_path: Path | None = None,
) -> Path:
    """
    Sematkan metadata INFO/ICMT ke file WAV/MP3:
    - title: "Dibuat dengan AI"
    - comment: "Dibuat dengan AI - TaSTP Studio"
    - artist: "TaSTP AI Synthesizer"
    """
    if not audio_path.exists():
        return audio_path

    target = output_path or audio_path
    temp_target = target.parent / f"watermarked_{target.name}"

    ffmpeg_exe = get_ffmpeg_executable()
    success = False

    if ffmpeg_exe:
        try:
            cmd = [
                ffmpeg_exe,
                "-y",
                "-i",
                str(audio_path),
                "-metadata",
                "title=Dibuat dengan AI",
                "-metadata",
                f"comment={comment}",
                "-metadata",
                "artist=TaSTP AI Voice",
                "-metadata",
                "album=TaSTP Studio Generation",
                "-metadata",
                "encoded_by=TaSTP AI",
                "-c",
                "copy",
                str(temp_target),
            ]
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
            )
            if result.returncode == 0 and temp_target.exists():
                if target == audio_path:
                    shutil.move(str(temp_target), str(target))
                else:
                    if temp_target != target:
                        shutil.move(str(temp_target), str(target))
                success = True
        except Exception:
            success = False

    if not success:
        # Fallback injeksi RIFF INFO chunk langsung ke file WAV binary
        try:
            _inject_riff_info_chunk(audio_path, target, comment)
            success = True
        except Exception as e:
            print(f"[Watermark] Fallback injeksi RIFF gagal: {e}")
            if audio_path != target:
                shutil.copy(audio_path, target)

    return target


def _inject_riff_info_chunk(src_wav: Path, dest_wav: Path, comment: str) -> None:
    """
    Menyisipkan LIST INFO chunk RIFF WAV secara binary (standar RIFF WAV).
    INFO chunk berisi:
    - INAM (Title): Dibuat dengan AI
    - ICMT (Comment): comment string
    - ISFT (Software): TaSTP AI Voice
    """
    data = bytearray(src_wav.read_bytes())
    if len(data) < 12 or data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        # Bukan WAV standar, salin apa adanya
        if src_wav != dest_wav:
            shutil.copy(src_wav, dest_wav)
        return

    # Bangun subchunk INFO
    def make_subchunk(fourcc: bytes, text: str) -> bytes:
        raw_txt = text.encode("utf-8") + b"\x00"
        if len(raw_txt) % 2 != 0:
            raw_txt += b"\x00"
        return fourcc + struct.pack("<I", len(raw_txt)) + raw_txt

    subchunks = (
        make_subchunk(b"INAM", "Dibuat dengan AI")
        + make_subchunk(b"ICMT", comment)
        + make_subchunk(b"ISFT", "TaSTP Platform")
    )
    list_chunk = b"LIST" + struct.pack("<I", 4 + len(subchunks)) + b"INFO" + subchunks

    # Perbarui ukuran RIFF header (byte 4..8)
    riff_size = len(data) - 8 + len(list_chunk)
    data[4:8] = struct.pack("<I", riff_size)

    # Tambahkan INFO chunk di akhir
    data.extend(list_chunk)
    dest_wav.write_bytes(data)


def read_audio_metadata(audio_path: Path) -> dict[str, Any]:
    """
    Membaca metadata dari file audio untuk memverifikasi label AI.
    """
    metadata: dict[str, Any] = {
        "title": None,
        "comment": None,
        "artist": None,
        "has_ai_label": False,
    }
    if not audio_path.exists():
        return metadata

    # 1. Coba baca via FFprobe jika tersedia
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
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    str(audio_path),
                ]
                res = subprocess.run(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                if res.returncode == 0:
                    import json

                    info = json.loads(res.stdout)
                    tags = info.get("format", {}).get("tags", {})
                    for k, v in tags.items():
                        kl = k.lower()
                        if kl in metadata:
                            metadata[kl] = v
                        if (
                            "ai" in str(v).lower()
                            or "dibuat dengan ai" in str(v).lower()
                        ):
                            metadata["has_ai_label"] = True
            except Exception:
                pass

    # 2. Cek binary byte scan untuk RIFF ICMT / string "Dibuat dengan AI"
    try:
        raw_bytes = audio_path.read_bytes()
        if b"Dibuat dengan AI" in raw_bytes:
            metadata["has_ai_label"] = True
            if not metadata["title"]:
                metadata["title"] = "Dibuat dengan AI"
            if not metadata["comment"]:
                metadata["comment"] = AI_DEFAULT_DISCLOSURE
    except Exception:
        pass

    return metadata
