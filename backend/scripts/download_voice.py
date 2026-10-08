"""
Skrip Pengunduh Model Suara Piper TTS Bahasa Indonesia.
Mengecek katalog resmi rhasspy/piper-voices di Hugging Face,
mengunduh file model ONNX dan JSON config ke storage/models/,
serta memverifikasi checksum MD5.
"""

import hashlib
import json
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "storage" / "models"
CATALOG_FILE = BASE_DIR / "app" / "voices" / "catalog.json"

PIPER_VOICES_JSON_URL = (
    "https://huggingface.co/rhasspy/piper-voices/raw/main/voices.json"
)
HF_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"


def compute_md5(file_path: Path) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_file(url: str, dest_path: Path, expected_md5: str = None) -> bool:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and expected_md5:
        if compute_md5(dest_path) == expected_md5:
            print(f"  [OK] File sudah ada dan valid: {dest_path.name}")
            return True

    print(f"  [UNDUH] Mengunduh {dest_path.name}...")
    try:

        def reporthook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, int(block_num * block_size * 100 / total_size))
                print(
                    f"\r  Progres: {percent}% ({block_num * block_size // 1024} KB)",
                    end="",
                )

        urllib.request.urlretrieve(url, str(dest_path), reporthook=reporthook)
        print()
        if expected_md5:
            actual_md5 = compute_md5(dest_path)
            if actual_md5 != expected_md5:
                print(f"  [PERINGATAN] MD5 tidak cocok: {actual_md5} vs {expected_md5}")
        return True
    except Exception as e:
        print(f"\n  [ERROR] Gagal mengunduh: {e}")
        return False


def check_and_download_indonesian_voices():
    print("=" * 60)
    print("TaSTP — Pengecekan & Pengunduhan Model Suara Piper Indonesia")
    print("=" * 60)
    print(f"Menghubungi katalog resmi Piper: {PIPER_VOICES_JSON_URL}")

    try:
        req = urllib.request.urlopen(PIPER_VOICES_JSON_URL, timeout=15)
        voices_catalog = json.loads(req.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] Gagal mengambil katalog suara dari Hugging Face: {e}")
        return False

    # Cari model dengan kode id_ID
    id_voices = {
        k: v
        for k, v in voices_catalog.items()
        if k.startswith("id_ID") or v.get("language", {}).get("code") == "id_ID"
    }

    if not id_voices:
        print("\n[PEMBERITAHUAN PENTING]")
        print(
            "Model resmi dengan kode bahasa 'id_ID' TIDAK DITEMUKAN di repo resmi Piper."
        )
        print("\nAlternatif yang disarankan untuk kreator:")
        print("1. Menggunakan model multilingual (mis. mms-tts / vits fine-tune).")
        print(
            "2. Mengimpor checkpoint model Piper kustom hasil fine-tuning bahasa Indonesia."
        )
        print("3. Menggunakan RemoteEngine GPU ke server Colab/Cloud.")
        return False

    print(
        f"\n[SUKSES] Ditemukan {len(id_voices)} model suara bahasa Indonesia di repo resmi:"
    )
    for v_key, v_info in id_voices.items():
        print(
            f" - {v_key} ({v_info.get('quality')} quality, {v_info.get('num_speakers', 1)} speaker)"
        )

    # Unduh model id_ID-news_tts-medium
    target_key = "id_ID-news_tts-medium"
    if target_key in id_voices:
        print(f"\nMempersiapkan pengunduhan: {target_key}")
        files = id_voices[target_key].get("files", {})
        onnx_rel = None
        json_rel = None
        for path_str in files.keys():
            if path_str.endswith(".onnx"):
                onnx_rel = path_str
            elif path_str.endswith(".onnx.json"):
                json_rel = path_str

        if onnx_rel and json_rel:
            onnx_url = f"{HF_BASE_URL}/{onnx_rel}"
            json_url = f"{HF_BASE_URL}/{json_rel}"

            onnx_file = MODELS_DIR / f"{target_key}.onnx"
            json_file = MODELS_DIR / f"{target_key}.onnx.json"

            expected_onnx_md5 = files[onnx_rel].get("md5_digest")
            expected_json_md5 = files[json_rel].get("md5_digest")

            download_file(onnx_url, onnx_file, expected_onnx_md5)
            download_file(json_url, json_file, expected_json_md5)

            print(f"\n[SELESAI] Model {target_key} berhasil disimpan di: {MODELS_DIR}")
            return True

    return False


if __name__ == "__main__":
    check_and_download_indonesian_voices()
