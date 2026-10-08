"""
Modul Sanitasi & Validasi Input Teks TaSTP:
- Proteksi batas karakter maksimal (default 5.000 karakter)
- Pembersihan byte null, karakter kontrol berbahaya, dan tag skrip
- Normalisasi spasi dan baris baru
"""

import re

from app.config import settings

# Pola regex untuk tag HTML / script
HTML_TAG_PATTERN = re.compile(r"<[^>]+>", re.IGNORECASE)
SCRIPT_PATTERN = re.compile(r"<script.*?>.*?</script>", re.DOTALL | re.IGNORECASE)

# Pola karakter kontrol yang tidak valid (kecuali \n, \r, \t)
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_text(text: str | None, max_chars: int = settings.MAX_TEXT_LENGTH) -> str:
    """
    Membersihkan teks input dari karakter tidak aman dan memastikan batas panjang.
    Raises ValueError jika naskah kosong atau melebihi batas karakter.
    """
    if text is None:
        raise ValueError("Naskah teks wajib diisi.")

    # 1. Hapus null byte dan karakter kontrol biner
    cleaned = CONTROL_CHAR_PATTERN.sub("", text)

    # 2. Hapus potensi injection tag HTML/Script
    cleaned = SCRIPT_PATTERN.sub("", cleaned)
    cleaned = HTML_TAG_PATTERN.sub("", cleaned)

    # 3. Normalisasi spasi berturut-turut
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    cleaned = cleaned.strip()

    if not cleaned:
        raise ValueError("Naskah teks tidak boleh kosong setelah sanitasi.")

    # 4. Validasi Batas Panjang Karakter
    if len(cleaned) > max_chars:
        raise ValueError(
            f"Panjang naskah ({len(cleaned)} karakter) melebihi batas maksimal yang diizinkan ({max_chars} karakter)."
        )

    return cleaned
