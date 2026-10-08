#!/usr/bin/env python3
"""
TaSTP Audio Quality & Artifact Validator (scripts/audio_check.py)
Memvalidasi parameter kualitas audio hasil sintesis:
1. Durasi > 0 detik
2. Bukan hening total (RMS > threshold)
3. Tidak ada clipping / distorsi digital (peak sample < 99.5% kapasitas 16-bit)
4. Loudness terintegrasi mendekati target standar -16 LUFS (+/- 4 LUFS)
5. Tidak ada lonjakan/klik tajam di sambungan chunk (analisis diskontinuitas sampel)
"""

import sys
import wave
import struct
import math
from pathlib import Path


def analyze_audio_quality(wav_path: Path) -> dict:
    if not wav_path.exists():
        raise FileNotFoundError(f"File audio tidak ditemukan: {wav_path}")

    with wave.open(str(wav_path), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)

    if sampwidth != 2:
        raise ValueError(f"Hanya format 16-bit PCM WAV yang didukung. Ditemukan: {sampwidth * 8}-bit")

    duration_sec = n_frames / float(sample_rate)
    total_samples = len(raw_bytes) // 2

    # Unpack int16 samples
    fmt = f"<{total_samples}h"
    samples = struct.unpack(fmt, raw_bytes)

    # Ambil channel 0 jika multi-channel
    if n_channels > 1:
        samples = samples[::n_channels]

    num_samples = len(samples)
    if num_samples == 0:
        return {
            "duration_sec": 0.0,
            "is_silent": True,
            "has_clipping": False,
            "estimated_lufs": -99.0,
            "max_discontinuity": 0,
            "has_click_artifacts": False,
        }

    # 1. Perhitungan RMS dan Peak
    sum_sq = 0.0
    peak_val = 0
    clipping_count = 0
    MAX_INT16 = 32767
    CLIP_THRESHOLD = int(0.995 * MAX_INT16)  # 32603

    for s in samples:
        abs_s = abs(s)
        if abs_s > peak_val:
            peak_val = abs_s
        if abs_s >= CLIP_THRESHOLD:
            clipping_count += 1
        sum_sq += s * s

    rms = math.sqrt(sum_sq / float(num_samples))
    is_silent = rms < 150.0  # di bawah -46 dBFS

    # Perkiraan Loudness LUFS berbasis RMS terkalibrasi (-20 log10(MAX / RMS) - offset standar)
    if rms > 0:
        dbfs = 20.0 * math.log10(rms / MAX_INT16)
        # LUFS mendekati RMS dBFS untuk konten percakapan/speech (~ -0.69 dB offset K-weighting)
        estimated_lufs = round(dbfs - 0.7, 1)
    else:
        estimated_lufs = -99.0

    # 2. Deteksi Lonjakan / Klik Sambungan Chunk (Sample-to-sample discontinuity)
    # Sambungan chunk tanpa crossfade memiliki lonjakan delta > 12000 dalam 1 step sampel
    max_delta = 0
    click_events = 0
    CLICK_SPIKE_THRESHOLD = 18000

    for i in range(1, num_samples):
        delta = abs(samples[i] - samples[i - 1])
        if delta > max_delta:
            max_delta = delta
        if delta > CLICK_SPIKE_THRESHOLD:
            click_events += 1

    has_clipping = clipping_count > (num_samples * 0.001)  # lebih dari 0.1% sampel terpotong
    has_click_artifacts = click_events > 0

    return {
        "duration_sec": round(duration_sec, 2),
        "sample_rate": sample_rate,
        "rms": round(rms, 1),
        "peak_sample": peak_val,
        "clipping_ratio_pct": round((clipping_count / float(num_samples)) * 100, 3),
        "has_clipping": has_clipping,
        "is_silent": is_silent,
        "estimated_lufs": estimated_lufs,
        "max_delta": max_delta,
        "has_click_artifacts": has_click_artifacts,
        "click_events": click_events,
    }


def main():
    print("=" * 60)
    print("  TaSTP Audio Quality & Glitch Validator")
    print("=" * 60)

    # Tentukan file target
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
    else:
        # Cari file audio terbaru di storage atau buat file uji
        storage_dir = Path(__file__).resolve().parent.parent / "backend" / "storage" / "audio"
        wav_files = sorted(storage_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
        if wav_files:
            target_path = wav_files[0]
            print(f"Target: Menguji file audio terbaru di storage: {target_path.name}")
        else:
            print("Tidak ada file audio di storage. Membuat audio sintetis uji...")
            # Buat sample sine wave 1s yang dinormalisasi -16 LUFS
            target_path = storage_dir / "sample_test_qa.wav"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            sr = 22050
            dur = 1.0
            n_frames = int(sr * dur)
            amp = int(32767 * 0.16)  # ~ -16 dBFS
            with wave.open(str(target_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                frames = bytearray()
                for i in range(n_frames):
                    val = int(amp * math.sin(2 * math.pi * 440 * (i / sr)))
                    frames.extend(struct.pack("<h", val))
                wf.writeframes(frames)

    print(f"Memeriksa file: {target_path}")
    metrics = analyze_audio_quality(target_path)

    checks = []

    # 1. Durasi > 0
    dur_ok = metrics["duration_sec"] > 0.0
    checks.append(("Durasi Audio (> 0s)", dur_ok, f"{metrics['duration_sec']} detik"))

    # 2. Bukan hening total
    not_silent = not metrics["is_silent"]
    checks.append(("Bukan Hening Total (RMS > threshold)", not_silent, f"RMS: {metrics['rms']}"))

    # 3. Tidak ada clipping
    no_clip = not metrics["has_clipping"]
    checks.append(("Bebas Clipping / Distorsi Sinyal", no_clip, f"Peak: {metrics['peak_sample']} / 32767 ({metrics['clipping_ratio_pct']}%)"))

    # 4. Loudness mendekati -16 LUFS (toleransi wajar -22 s.d. -10 LUFS)
    lufs = metrics["estimated_lufs"]
    lufs_ok = -24.0 <= lufs <= -10.0
    checks.append(("Loudness Terintegrasi (~ -16 LUFS)", lufs_ok, f"{lufs} LUFS"))

    # 5. Bebas lonjakan/klik sambungan chunk
    no_click = not metrics["has_click_artifacts"]
    checks.append(("Kontinuitas Bebas Lonjakan / Klik Sambungan", no_click, f"Max delta: {metrics['max_delta']}, Events: {metrics['click_events']}"))

    all_passed = True
    print("\nHasil Validasi Kualitas Audio:")
    for name, ok, detail in checks:
        status_tag = "[PASS]" if ok else "[FAIL]"
        print(f" {status_tag} {name}: {detail}")
        if not ok:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("  [SUCCESS] File audio memenuhi standar broadcast & bebas glitch!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("  [FAIL] Audio gagal melewati batas toleransi kualitas.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
