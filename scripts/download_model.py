"""
Script untuk mendownload model Piper TTS dari HuggingFace.
Jalankan: python scripts/download_model.py
"""

import sys
from pathlib import Path
from urllib.request import urlretrieve

MODELS_DIR = Path(__file__).resolve().parent.parent / "backend" / "storage" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODELS = {
    "id_ID-news_tts-medium.onnx": (
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        "id/id_ID/news_tts/medium/id_ID-news_tts-medium.onnx"
    ),
    "id_ID-news_tts-medium.onnx.json": (
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        "id/id_ID/news_tts/medium/id_ID-news_tts-medium.onnx.json"
    ),
}


def download_progress(block_num: int, block_size: int, total_size: int):
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100, downloaded * 100 // total_size)
        mb_down = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write(f"\r  [{pct:3d}%] {mb_down:.1f} / {mb_total:.1f} MB")
        sys.stdout.flush()


def main():
    print("=== Download Model Piper TTS ===\n")

    for filename, url in MODELS.items():
        target = MODELS_DIR / filename
        if target.exists() and target.stat().st_size > 1000:
            size_mb = target.stat().st_size / (1024 * 1024)
            print(f"✓ {filename} sudah ada ({size_mb:.1f} MB), skip.")
            continue

        print(f"↓ Downloading {filename}...")
        try:
            urlretrieve(url, str(target), reporthook=download_progress)
            print(f"\n  ✓ Berhasil: {target}")
        except Exception as e:
            print(f"\n  ✗ Gagal: {e}")
            sys.exit(1)

    print("\n=== Semua model siap! ===")


if __name__ == "__main__":
    main()
