#!/usr/bin/env python3
"""
TaSTP Automated Quality Assurance Scanner (scripts/scan.py)
Cross-platform native runner (Windows / macOS / Linux)
Menjalankan seluruh tahapan QA berurutan dan berhenti dengan ringkasan PASS/FAIL.
"""

import sys
import os
import subprocess
from pathlib import Path

# Set UTF-8 encoding untuk console output Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
PYTHON_EXE = sys.executable

# Auto-inject portable runtime paths di Windows jika tersedia
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
if LOCALAPPDATA:
    node_dir = Path(LOCALAPPDATA) / "nodejs"
    if node_dir.exists():
        os.environ["PATH"] = f"{node_dir};{os.environ.get('PATH', '')}"

IS_WIN = sys.platform == "win32"
NPM_CMD = "npm.cmd" if IS_WIN else "npm"
NPX_CMD = "npx.cmd" if IS_WIN else "npx"


def run_command(name: str, cmd_list: list[str], cwd: Path = ROOT_DIR) -> bool:
    print(f"\n>>> Menjalankan: {name}...")
    print(f"Perintah: {' '.join(str(c) for c in cmd_list)} (cwd: {cwd.name})")

    try:
        res = subprocess.run(cmd_list, cwd=str(cwd), check=False)
        if res.returncode == 0:
            print(f"[PASS] {name} BERHASIL")
            return True
        else:
            print(f"[FAIL] {name} GAGAL (exit code: {res.returncode})")
            return False
    except Exception as e:
        print(f"[FAIL] {name} GAGAL mengeksekusi: {e}")
        return False


def main():
    print("=" * 66)
    print("  TaSTP - Automated Quality & Security Scanner Suite")
    print("=" * 66)

    steps = [
        # --- Backend Checks ---
        ("Backend Ruff Lint", [PYTHON_EXE, "-m", "ruff", "check", "backend"], ROOT_DIR),
        ("Backend Ruff Format Check", [PYTHON_EXE, "-m", "ruff", "format", "--check", "backend"], ROOT_DIR),
        ("Backend Mypy Type Check", [PYTHON_EXE, "-m", "mypy", "backend/app"], ROOT_DIR),
        ("Backend Bandit Security", [PYTHON_EXE, "-m", "bandit", "-r", "backend/app", "-ll"], ROOT_DIR),
        ("Backend Dependency Audit", [PYTHON_EXE, "-m", "pip_audit", "--local"], ROOT_DIR),
        ("Backend Pytest & Coverage", [PYTHON_EXE, "-m", "pytest", "backend/tests", "--cov=backend/app", "--cov-report=term-missing"], ROOT_DIR),

        # --- Frontend Checks ---
        ("Frontend Type Check (tsc)", [NPX_CMD, "tsc", "--noEmit"], FRONTEND_DIR),
        ("Frontend ESLint", [NPX_CMD, "eslint", "src"], FRONTEND_DIR),
        ("Frontend Production Build", [NPM_CMD, "run", "build"], FRONTEND_DIR),

        # --- Security & Integrity Checks ---
        ("Secret & .env Exposure Check", [PYTHON_EXE, "scripts/check_secrets.py"], ROOT_DIR),
        ("System Health Check", [PYTHON_EXE, "scripts/health_check.py"], ROOT_DIR),
        ("Audio Quality & Artifact Check", [PYTHON_EXE, "scripts/audio_check.py"], ROOT_DIR),
    ]

    results = []
    for name, cmd, cwd in steps:
        ok = run_command(name, cmd, cwd)
        results.append((name, ok))
        print("-" * 66)

    # Ringkasan PASS / FAIL
    print("\n" + "=" * 66)
    print("  RINGKASAN HASIL QA SCAN TASTP")
    print("=" * 66)

    failed_count = 0
    for name, ok in results:
        status = "[PASS]" if ok else "[FAIL]"
        print(f" {status:<8} {name}")
        if not ok:
            failed_count += 1

    print("=" * 66)
    if failed_count == 0:
        print(f"  [SUCCESS] Seluruh {len(results)} langkah QA scan SELESAI & LULUS 100%!")
        print("=" * 66)
        sys.exit(0)
    else:
        print(f"  [ERROR] Ditemukan {failed_count} dari {len(results)} langkah yang GAGAL.")
        print("=" * 66)
        sys.exit(1)


if __name__ == "__main__":
    main()
