#!/usr/bin/env python3
"""
TaSTP Voice Metrics & Prosody Reporter (scripts/voice_report.py)
Mengukur metrik objektif audio sintesis lintas karakter suara & emosi:
- Durasi (detik)
- Mean F0 (Hz) & F0 Standard Deviation (indikator kerataan/monoton)
- RMS (Root Mean Square / Intensitas Energi)
"""

import asyncio
import os
import sys
import wave
import numpy as np
from pathlib import Path

# Daftarkan backend ke sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.audio.pipeline import run_synthesis_pipeline
from app.config import settings

TEST_SENTENCE = (
    "Selamat pagi Indonesia, selamat datang di studio narasi suara pintar generasi masa depan."
)

CATALOG_VOICES = [
    ("id_ID-news_tts-medium", "Ida (Resmi ONNX)"),
    ("piper_id_gadis_fast", "Gadis (Kreator)"),
    ("piper_id_bima_narrator", "Bima (Narator Pria)"),
    ("piper_id_siti_podcast", "Siti (Podcast)"),
    ("piper_id_dimas_news", "Dimas (Penyiar Pria)"),
]

EMOTIONS = [
    ("neutral", "Netral"),
    ("gembira", "Gembira"),
    ("sedih", "Sedih"),
    ("marah", "Marah"),
]


def extract_f0_and_metrics(wav_path: Path):
    """
    Ekstraksi durasi, RMS, mean F0, dan std dev F0 menggunakan autokorelasi berbasis frame.
    """
    with wave.open(str(wav_path), "rb") as wf:
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)

    if len(samples) == 0:
        return 0.0, 0.0, 0.0, 0.0

    duration = len(samples) / float(sr)
    rms = float(np.sqrt(np.mean(samples ** 2)))

    # Analisis Frame Pitch (F0)
    frame_len = int(sr * 0.030)  # 30 ms
    hop_len = int(sr * 0.010)    # 10 ms
    min_lag = int(sr / 450.0)    # maks 450 Hz
    max_lag = int(sr / 75.0)     # min 75 Hz

    f0_list = []

    for i in range(0, len(samples) - frame_len, hop_len):
        frame = samples[i : i + frame_len]
        # Skip frame hening
        if np.max(np.abs(frame)) < 400:
            continue

        # Windowing Hamming
        win = np.hamming(len(frame))
        frame_win = frame * win

        # Autokorelasi
        corr = np.correlate(frame_win, frame_win, mode="full")
        corr = corr[len(corr) // 2 :]

        if len(corr) < max_lag:
            continue

        # Cari puncak autokorelasi dalam rentang lag vokal manusia
        corr_slice = corr[min_lag:max_lag]
        if len(corr_slice) == 0:
            continue

        peak_idx = min_lag + np.argmax(corr_slice)
        r_max = corr[peak_idx]
        r_zero = corr[0] if corr[0] > 0 else 1.0

        # Deteksi voiced frame jika peak correlation > 0.35
        if (r_max / r_zero) > 0.35:
            f0 = sr / float(peak_idx)
            if 75.0 <= f0 <= 450.0:
                f0_list.append(f0)

    if f0_list:
        mean_f0 = float(np.mean(f0_list))
        std_f0 = float(np.std(f0_list))
    else:
        mean_f0 = 0.0
        std_f0 = 0.0

    return duration, rms, mean_f0, std_f0


async def generate_voice_report(output_dir: Path | None = None):
    scratch_dir = output_dir or (Path(__file__).resolve().parent.parent / "scratch" / "voice_reports")
    scratch_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 90)
    print("      TaSTP Studio — Audio Metrics & Voice Differentiation Report")
    print("=" * 90)
    print(f"Kalimat Uji: \"{TEST_SENTENCE}\"")
    print(f"Scratch Folder: {scratch_dir}\n")

    results = []

    for voice_id, voice_label in CATALOG_VOICES:
        for emo_id, emo_label in EMOTIONS:
            job_id = f"report_{voice_id[:12]}_{emo_id}"
            out_file = scratch_dir / f"{job_id}.wav"

            try:
                res = await run_synthesis_pipeline(
                    text=TEST_SENTENCE,
                    voice_id=voice_id,
                    emotion=emo_id,
                    job_id=job_id,
                )
                dur, rms, mean_f0, std_f0 = extract_f0_and_metrics(res.audio_path)
                results.append({
                    "voice_id": voice_id,
                    "voice_name": voice_label,
                    "emotion": emo_label,
                    "duration": dur,
                    "mean_f0": mean_f0,
                    "std_f0": std_f0,
                    "rms": rms,
                    "file": res.audio_path.name,
                })
                print(f"  [OK] {voice_label:<22} | {emo_label:<8} -> Dur: {dur:.2f}s | F0: {mean_f0:.1f} Hz (±{std_f0:.1f} Hz) | RMS: {rms:.1f}")
            except Exception as e:
                print(f"  [ERR] {voice_label} ({emo_label}): {e}")

    # Cetak Tabel Markdown Terformat
    print("\n" + "=" * 90)
    print("                      TABEL METRIK HASIL SINTESIS (AFTER)")
    print("=" * 90)
    print(f"| {'Karakter Suara':<24} | {'Emosi':<9} | {'Durasi (s)':<10} | {'Mean F0 (Hz)':<13} | {'Std F0 (Hz)':<11} | {'RMS':<8} |")
    print(f"|{'-'*26}|{'-'*11}|{'-'*12}|{'-'*15}|{'-'*13}|{'-'*10}|")

    for r in results:
        print(
            f"| {r['voice_name']:<24} | {r['emotion']:<9} | {r['duration']:<10.2f} | {r['mean_f0']:<13.1f} | {r['std_f0']:<11.1f} | {r['rms']:<8.1f} |"
        )
    print("=" * 90)
    print("Catatan Indikator:")
    print("- Mean F0: Membedakan rentang tinggi/rendah nada antar karakter (Pria ~120-145 Hz, Wanita ~180-225 Hz).")
    print("- Std F0: Mengukur variasi intonasi & melodi (nilai rendah = datar/monoton, nilai lebih tinggi = dinamis & ekspresif).")
    print("- Durasi: Mengukur efek tempo kecepatan emosi (gembira/marah lebih cepat, sedih lebih lambat).")
    print("=" * 90 + "\n")
    return results


if __name__ == "__main__":
    asyncio.run(generate_voice_report())
