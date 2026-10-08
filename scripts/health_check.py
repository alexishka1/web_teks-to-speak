#!/usr/bin/env python3
"""
TaSTP System Health Check Script
Memeriksa status operasional komponen inti:
1. Endpoint /health (HTTP 200)
2. Piper Engine (ketersediaan voice & status inisialisasi)
3. FFmpeg binary (tersedia dan executable)
4. Storage direktori audio (izin tulis & baca)
5. Database SQLite (koneksi & query)
"""

import sys
import os
import urllib.request
import urllib.error
import subprocess
import asyncio
from pathlib import Path

# Injeksi backend path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def check_ffmpeg() -> tuple[bool, str]:
    from app.audio.watermark import get_ffmpeg_executable

    exe = get_ffmpeg_executable()
    if not exe:
        return False, "FFmpeg binary tidak ditemukan di PATH maupun imageio-ffmpeg."
    try:
        res = subprocess.run([exe, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if res.returncode == 0:
            first_line = res.stdout.splitlines()[0] if res.stdout else "ffmpeg ready"
            return True, f"FFmpeg tersedia ({first_line[:40]}...)"
        return False, f"FFmpeg error: returncode {res.returncode}"
    except Exception as e:
        return False, f"FFmpeg execution failed: {e}"


def check_storage() -> tuple[bool, str]:
    from app.config import settings

    target_dir = settings.AUDIO_OUTPUT_DIR
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        test_file = target_dir / ".health_test_write.tmp"
        test_file.write_text("ok", encoding="utf-8")
        content = test_file.read_text(encoding="utf-8")
        test_file.unlink(missing_ok=True)
        if content == "ok":
            return True, f"Direktori audio dapat ditulis & dibaca ({target_dir})"
        return False, "Isi file uji coba storage tidak cocok."
    except Exception as e:
        return False, f"Gagal menulis ke storage audio: {e}"


async def check_database() -> tuple[bool, str]:
    from app.database import engine
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            val = res.scalar()
            if val == 1:
                return True, "Database SQLite terhubung dan dapat di-query (SELECT 1)."
            return False, f"Hasil query tidak sesuai: {val}"
    except Exception as e:
        return False, f"Gagal terhubung ke database SQLite: {e}"


def check_piper_engine() -> tuple[bool, str]:
    from app.engines.piper_engine import piper_engine

    try:
        voices = piper_engine.get_supported_voices()
        if not voices:
            return False, "PiperEngine tidak memiliki daftar suara terdaftar."
        return True, f"PiperEngine siap lazy-load ({len(voices)} suara terdaftar)."
    except Exception as e:
        return False, f"Gagal memeriksa PiperEngine: {e}"


def check_api_health(host: str = "127.0.0.1", port: int = 8000) -> tuple[bool, str]:
    url = f"http://{host}:{port}/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TaSTP-HealthCheck"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8")
                return True, f"Endpoint /health merespon HTTP 200: {body.strip()}"
            return False, f"Endpoint /health mengembalikan status {resp.status}"
    except urllib.error.URLError as e:
        return False, f"Server backend belum aktif di {url} ({e.reason})"
    except Exception as e:
        return False, f"Gagal memanggil {url}: {e}"


async def main():
    print("=" * 60)
    print("  TaSTP System Health Check")
    print("=" * 60)

    results = []

    # 1. FFmpeg
    ok, msg = check_ffmpeg()
    results.append(("FFmpeg Binary", ok, msg))

    # 2. Storage
    ok, msg = check_storage()
    results.append(("Audio Storage", ok, msg))

    # 3. Database
    ok, msg = await check_database()
    results.append(("SQLite Database", ok, msg))

    # 4. Piper Engine
    ok, msg = check_piper_engine()
    results.append(("Piper Engine", ok, msg))

    # 5. /health endpoint
    ok, msg = check_api_health()
    results.append(("HTTP /health Endpoint", ok, msg))

    all_passed = True
    print("\nHasil Pemeriksaan Komponen:")
    for name, ok, msg in results:
        status_tag = "[PASS]" if ok else "[FAIL]"
        print(f" {status_tag} {name}: {msg}")
        if not ok:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("  [SUCCESS] Seluruh 5 komponen sistem dalam status SEHAT!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("  [WARNING/FAIL] Ditemukan komponen yang tidak sehat.")
        print("=" * 60)
        # Note: if API is down while testing locally, exit 1
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
