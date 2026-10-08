#!/usr/bin/env python3
"""
TaSTP Secret & Environment Exposure Scanner (scripts/check_secrets.py)
Memeriksa:
1. File .env tidak terdaftar / terekspos tanpa perlindungan .gitignore
2. Tidak ada API key, token rahasia, atau credentials di source code
"""

import sys
import os
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Pola regex deteksi rahasia/credentials
SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{20,})['\"]", "API/Secret Key Literal"),
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{25,}", "Hardcoded Bearer Token"),
    (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "Private Key Header"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
]

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".next",
    ".pytest_cache",
    ".mypy_cache",
    "__pycache__",
    "storage",
    "backend/storage",
    ".system_generated",
    "dist",
    "build",
}

EXCLUDE_FILES = {
    ".env.example",
    "package-lock.json",
}


def check_env_files() -> list[str]:
    issues = []
    # Cek apakah ada file .env aktif di root
    root_env = ROOT_DIR / ".env"
    gitignore_path = ROOT_DIR / ".gitignore"

    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        if ".env" not in gitignore_content:
            issues.append("Peringatan: Aturan '.env' tidak tercantum dalam .gitignore!")
    else:
        issues.append("Error: File .gitignore tidak ditemukan di root repositori!")

    return issues


def scan_source_files() -> list[str]:
    issues = []
    text_extensions = {".py", ".ts", ".tsx", ".js", ".mjs", ".json", ".yml", ".yaml", ".md", ".sh"}

    for root, dirs, files in os.walk(ROOT_DIR):
        # Filter direktori yang dikecualikan
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not any(p in os.path.join(root, d) for p in [".next", "node_modules", ".git"])]

        for file in files:
            if file in EXCLUDE_FILES:
                continue
            file_path = Path(root) / file
            if file_path.suffix not in text_extensions:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern, desc in SECRET_PATTERNS:
                matches = re.finditer(pattern, content)
                for match in matches:
                    snippet = match.group(0)[:40]
                    # Abaikan placeholder dummy seperti 'your_api_key_here'
                    if "your_" in snippet.lower() or "dummy" in snippet.lower() or "test_" in snippet.lower():
                        continue
                    rel_path = file_path.relative_to(ROOT_DIR)
                    issues.append(f"Potensi {desc} pada {rel_path}: {snippet}...")

    return issues


def main():
    print("=" * 60)
    print("  TaSTP Security & Secret Leak Scanner")
    print("=" * 60)

    env_issues = check_env_files()
    secret_issues = scan_source_files()

    all_issues = env_issues + secret_issues

    if not all_issues:
        print(" [PASS] File .env aman terlindungi dalam .gitignore.")
        print(" [PASS] Tidak ditemukan hardcoded API key / secrets di kode sumber.")
        print("=" * 60)
        print("  [SUCCESS] Pemeriksaan rahasia dan kredensial BERSIH 100%!")
        print("=" * 60)
        sys.exit(0)
    else:
        print(" [FAIL] Ditemukan potensi kebocoran kredensial:")
        for iss in all_issues:
            print(f"  - {iss}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
