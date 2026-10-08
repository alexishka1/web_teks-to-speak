"""
Modul Normalisasi Teks Bahasa Indonesia untuk TTS TaSTP.
Mengonversi angka, tanggal, jam, mata uang, persen, singkatan, simbol, URL, dan email
menjadi kata-kata terucap alami sesuai kaidah tata bahasa Indonesia.
"""

import re

SATUAN = [
    "",
    "satu",
    "dua",
    "tiga",
    "empat",
    "lima",
    "enam",
    "tujuh",
    "delapan",
    "sembilan",
]
BULAN_ID = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def number_to_words(n: int) -> str:
    """Mengonversi integer (positif/negatif) ke kata bahasa Indonesia."""
    if n == 0:
        return "nol"
    if n < 0:
        return f"minus {number_to_words(abs(n))}"

    if n < 10:
        return SATUAN[n]
    if n == 10:
        return "sepuluh"
    if n == 11:
        return "sebelas"
    if n < 20:
        return f"{SATUAN[n - 10]} belas"
    if n < 100:
        puluh = SATUAN[n // 10] + " puluh"
        sisa = n % 10
        return puluh if sisa == 0 else f"{puluh} {SATUAN[sisa]}"
    if n < 200:
        ratus = "seratus"
        sisa = n - 100
        return ratus if sisa == 0 else f"{ratus} {number_to_words(sisa)}"
    if n < 1000:
        ratus = SATUAN[n // 100] + " ratus"
        sisa = n % 100
        return ratus if sisa == 0 else f"{ratus} {number_to_words(sisa)}"
    if n < 2000:
        ribu = "seribu"
        sisa = n - 1000
        return ribu if sisa == 0 else f"{ribu} {number_to_words(sisa)}"
    if n < 1_000_000:
        ribu = f"{number_to_words(n // 1000)} ribu"
        sisa = n % 1000
        return ribu if sisa == 0 else f"{ribu} {number_to_words(sisa)}"
    if n < 1_000_000_000:
        juta = f"{number_to_words(n // 1_000_000)} juta"
        sisa = n % 1_000_000
        return juta if sisa == 0 else f"{juta} {number_to_words(sisa)}"
    if n < 1_000_000_000_000:
        miliar = f"{number_to_words(n // 1_000_000_000)} miliar"
        sisa = n % 1_000_000_000
        return miliar if sisa == 0 else f"{miliar} {number_to_words(sisa)}"

    triliun = f"{number_to_words(n // 1_000_000_000_000)} triliun"
    sisa = n % 1_000_000_000_000
    return triliun if sisa == 0 else f"{triliun} {number_to_words(sisa)}"


def decimal_digits_to_words(digits: str) -> str:
    """Mengonversi digit di belakang koma menjadi ucapan per digit."""
    digit_map = {
        "0": "nol",
        "1": "satu",
        "2": "dua",
        "3": "tiga",
        "4": "empat",
        "5": "lima",
        "6": "enam",
        "7": "tujuh",
        "8": "delapan",
        "9": "sembilan",
    }
    return " ".join(digit_map.get(d, d) for d in digits)


def normalize_currency(text: str) -> str:
    """
    Normalisasi Rupiah dan mata uang asing:
    Rp 15.000 / Rp15.000 -> lima belas ribu rupiah
    Rp 2,5 juta -> dua koma lima juta rupiah
    Rp 1.500.000,50 -> satu juta lima ratus ribu rupiah lima puluh sen
    $50 -> lima puluh dolar
    """

    # 1. Format: Rp 2,5 juta / Rp 10 miliar / Rp 1 triliun
    def _replace_rp_scale(match):
        val = match.group(1).replace(".", "").replace(",", ".")
        scale = match.group(2)
        try:
            val_f = float(val)
            if val_f.is_integer():
                num_str = number_to_words(int(val_f))
            else:
                parts = str(val).split(".")
                num_str = f"{number_to_words(int(parts[0]))} koma {decimal_digits_to_words(parts[1])}"
            return f"{num_str} {scale} rupiah"
        except ValueError:
            return match.group(0)

    text = re.sub(
        r"(?:Rp\.?|RP\.?)\s*(\d+(?:[.,]\d+)?)\s*(juta|miliar|triliun)",
        _replace_rp_scale,
        text,
        flags=re.IGNORECASE,
    )

    # 2. Format: Rp 15.000,50 (dengan sen)
    def _replace_rp_sen(match):
        main_val = match.group(1).replace(".", "")
        sen_val = match.group(2)
        try:
            main_int = int(main_val)
            sen_int = int(sen_val)
            main_words = number_to_words(main_int)
            if sen_int > 0:
                return f"{main_words} rupiah {number_to_words(sen_int)} sen"
            return f"{main_words} rupiah"
        except ValueError:
            return match.group(0)

    text = re.sub(
        r"(?:Rp\.?|RP\.?)\s*(\d{1,3}(?:\.\d{3})+),(\d{1,2})\b", _replace_rp_sen, text
    )

    # 3. Format: Rp 15.000 / Rp15.000 / Rp 500
    def _replace_rp_standard(match):
        val_str = match.group(1).replace(".", "")
        try:
            val_int = int(val_str)
            return f"{number_to_words(val_int)} rupiah"
        except ValueError:
            return match.group(0)

    text = re.sub(
        r"(?:Rp\.?|RP\.?)\s*(\d{1,3}(?:\.\d{3})+|\d+)\b", _replace_rp_standard, text
    )

    # 4. Dollar & Euro: $50 / USD 50 / €100
    def _replace_dollar(match):
        num_str = match.group(1).replace(".", "").replace(",", ".")
        try:
            num = int(float(num_str))
            return f"{number_to_words(num)} dolar"
        except ValueError:
            return match.group(0)

    text = re.sub(r"\$\s*(\d+(?:[.,]\d+)?)\b", _replace_dollar, text)
    text = re.sub(
        r"\bUSD\s*(\d+(?:[.,]\d+)?)\b", _replace_dollar, text, flags=re.IGNORECASE
    )

    def _replace_euro(match):
        num_str = match.group(1).replace(".", "").replace(",", ".")
        try:
            num = int(float(num_str))
            return f"{number_to_words(num)} euro"
        except ValueError:
            return match.group(0)

    text = re.sub(r"€\s*(\d+(?:[.,]\d+)?)\b", _replace_euro, text)

    return text


def normalize_dates(text: str) -> str:
    """
    Normalisasi format tanggal:
    17/08/1945 atau 17-08-1945 -> tujuh belas Agustus seribu sembilan ratus empat puluh lima
    17 Agustus 1945 -> tujuh belas Agustus seribu sembilan ratus empat puluh lima
    """

    # 1. Format: DD/MM/YYYY atau DD-MM-YYYY
    def _replace_date_slash(match):
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        if 1 <= day <= 31 and 1 <= month <= 12 and year > 0:
            month_name = BULAN_ID.get(month, "")
            return f"{number_to_words(day)} {month_name} {number_to_words(year)}"
        return match.group(0)

    text = re.sub(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", _replace_date_slash, text)

    # 2. Format: DD NamaBulan YYYY (mis. 17 Agustus 1945)
    def _replace_date_text(match):
        day = int(match.group(1))
        month_name = match.group(2)
        year = int(match.group(3))
        return f"{number_to_words(day)} {month_name} {number_to_words(year)}"

    months_pattern = "|".join(
        [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember",
        ]
    )
    text = re.sub(
        rf"\b(\d{{1,2}})\s+({months_pattern})\s+(\d{{4}})\b",
        _replace_date_text,
        text,
        flags=re.IGNORECASE,
    )

    return text


def normalize_time(text: str) -> str:
    """
    Normalisasi waktu/jam:
    10.00 WIB -> pukul sepuluh tepat Waktu Indonesia Barat
    08:30 WITA -> pukul delapan lewat tiga puluh menit Waktu Indonesia Tengah
    14.15 -> pukul empat belas lewat lima belas menit
    """
    tz_map = {
        "WIB": "Waktu Indonesia Barat",
        "WITA": "Waktu Indonesia Tengah",
        "WIT": "Waktu Indonesia Timur",
    }

    def _replace_time(match):
        hour = int(match.group(1))
        minute = int(match.group(2))
        tz = match.group(3)

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return match.group(0)

        hour_word = number_to_words(hour)
        if minute == 0:
            res = f"pukul {hour_word} tepat"
        else:
            res = f"pukul {hour_word} lewat {number_to_words(minute)} menit"

        if tz and tz.upper() in tz_map:
            res = f"{res} {tz_map[tz.upper()]}"
        return res

    text = re.sub(
        r"\b(?:pukul\s+)?(\d{1,2})[.:](\d{2})(?:\s*(WIB|WITA|WIT))?\b",
        _replace_time,
        text,
        flags=re.IGNORECASE,
    )
    return text


def normalize_percent(text: str) -> str:
    """
    Normalisasi persen:
    50% -> lima puluh persen
    12,5% -> dua belas koma lima persen
    """

    def _replace_percent(match):
        raw = match.group(1).replace(".", "").replace(",", ".")
        try:
            val = float(raw)
            if val.is_integer():
                return f"{number_to_words(int(val))} persen"
            parts = str(val).split(".")
            return f"{number_to_words(int(parts[0]))} koma {decimal_digits_to_words(parts[1])} persen"
        except ValueError:
            return match.group(0)

    return re.sub(r"(\d+(?:[.,]\d+)?)\s*%", _replace_percent, text)


def normalize_units(text: str) -> str:
    """
    Normalisasi satuan kecepatan, suhu, berat, panjang:
    45 km/jam -> empat puluh lima kilometer per jam
    28°C -> dua puluh delapan derajat Celcius
    10 kg -> sepuluh kilogram
    """
    unit_map = {
        r"km/jam": "kilometer per jam",
        r"km/h": "kilometer per jam",
        r"km": "kilometer",
        r"m/s": "meter per detik",
        r"kg": "kilogram",
        r"gr": "gram",
        r"cm": "sentimeter",
        r"mm": "milimeter",
        r"m": "meter",
    }

    # Suhu °C atau °
    text = re.sub(
        r"(\d+(?:[.,]\d+)?)\s*°\s*C\b", r"\1 derajat Celcius", text, flags=re.IGNORECASE
    )
    text = re.sub(r"(\d+(?:[.,]\d+)?)\s*°\b", r"\1 derajat", text)

    for pattern, replacement in unit_map.items():
        text = re.sub(
            rf"\b(\d+(?:[.,]\d+)?)\s*{pattern}\b",
            rf"\1 {replacement}",
            text,
            flags=re.IGNORECASE,
        )

    return text


def normalize_phone_numbers(text: str) -> str:
    """
    Normalisasi nomor telepon berantai:
    0812-3456-7890 -> nol delapan satu dua, tiga empat lima enam, tujuh delapan sembilan nol
    """

    def _replace_phone(match):
        full = match.group(0)
        chunks = full.split("-")
        words_chunks = []
        for c in chunks:
            words_chunks.append(decimal_digits_to_words(c))
        return ", ".join(words_chunks)

    return re.sub(r"\b08\d{2}-\d{3,4}-\d{3,5}\b", _replace_phone, text)


def normalize_ordinals(text: str) -> str:
    """
    Normalisasi angka bertingkat:
    ke-1 -> kesatu, ke-2 -> kedua, ke-21 -> kedua puluh satu, ke-100 -> keseratus
    """

    def _replace_ordinal(match):
        raw_num = match.group(1).replace(".", "")
        try:
            num = int(raw_num)
            if num == 1:
                return "pertama"
            words = number_to_words(num)
            if words.startswith("se"):
                return f"ke{words}"
            return f"ke {words}"
        except ValueError:
            return match.group(0)

    return re.sub(
        r"\bke-(\d+(?:\.\d+)?)\b", _replace_ordinal, text, flags=re.IGNORECASE
    )


def normalize_decimals_and_numbers(text: str) -> str:
    """
    Normalisasi desimal dan sisa angka kardinal di teks:
    2,5 -> dua koma lima
    1.500 -> seribu lima ratus
    25 -> dua puluh lima
    """

    # Desimal (koma)
    def _replace_decimal(match):
        whole = match.group(1).replace(".", "")
        fraction = match.group(2)
        try:
            whole_words = number_to_words(int(whole))
            frac_words = decimal_digits_to_words(fraction)
            return f"{whole_words} koma {frac_words}"
        except ValueError:
            return match.group(0)

    text = re.sub(r"\b(\d{1,3}(?:\.\d{3})*|\d+),(\d+)\b", _replace_decimal, text)

    # Angka ribuan bertitik: 1.500 / 25.500.000
    def _replace_thousand(match):
        raw = match.group(0).replace(".", "")
        try:
            return number_to_words(int(raw))
        except ValueError:
            return match.group(0)

    text = re.sub(r"\b\d{1,3}(?:\.\d{3})+\b", _replace_thousand, text)

    # Angka biasa: 1, 25, 500
    def _replace_plain_num(match):
        try:
            return number_to_words(int(match.group(0)))
        except ValueError:
            return match.group(0)

    text = re.sub(r"\b\d+\b", _replace_plain_num, text)

    return text


def normalize_abbreviations(text: str) -> str:
    """
    Normalisasi singkatan dan akronim umum Indonesia.
    """
    abbrevs: list[tuple[str, str]] = [
        (r"\bPT\.?\b", "Perseroan Terbatas"),
        (r"\bBUMN\b", "B U M N"),
        (r"\bdll\.?", "dan lain-lain"),
        (r"\bdsb\.?", "dan sebagainya"),
        (r"\bdst\.?", "dan seterusnya"),
        (r"\bmis\.\s*", "misalnya "),
        (r"\bmisal\.\s*", "misalnya "),
        (r"\btsb\.\s*", "tersebut "),
        (r"\bd/a\b", "dengan alamat"),
        (r"\ba/n\b", "atas nama"),
        (r"\bu/\b", "untuk"),
        (r"\bs/d\b", "sampai dengan"),
        (r"\bdgn\b", "dengan"),
        (r"\byg\b", "yang"),
        (r"\btlp\.?", "telepon"),
        (r"\bDr\.\s*", "Dokter "),
        (r"\bProf\.\s*", "Profesor "),
        (r"\bIr\.\s*", "Insinyur "),
    ]

    for pattern, replacement in abbrevs:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


def normalize_urls_and_emails(text: str) -> str:
    """
    Normalisasi URL dan Email:
    https://kemdikbud.go.id -> h t t p s titik dua garis miring garis miring kemdikbud dot go dot id
    panitia@sejarah.id -> panitia at sejarah dot id
    """

    # Email
    def _replace_email(match):
        user = match.group(1)
        domain = match.group(2)
        domain_spoken = domain.replace(".", " dot ")
        return f"{user} at {domain_spoken}"

    text = re.sub(
        r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b", _replace_email, text
    )

    # URL
    def _replace_url(match):
        url = match.group(0)
        # Sederhanakan pembacaan URL untuk TTS natural
        url = url.replace("https://", "h t t p s titik dua garis miring garis miring ")
        url = url.replace("http://", "h t t p titik dua garis miring garis miring ")
        url = url.replace("www.", "w w w dot ")
        url = url.replace(".", " dot ")
        url = url.replace("/", " garis miring ")
        url = url.replace("-", " strip ")
        url = re.sub(r"\s+", " ", url)
        return url.strip()

    text = re.sub(r"https?://[^\s]+", _replace_url, text)

    return text


def normalize_symbols(text: str) -> str:
    """
    Normalisasi simbol matematika dan tipografi:
    & -> dan, @ -> at, + -> tambah, = -> sama dengan, # -> tagar
    """
    symbol_map = [
        (r"\s*&\s*", " dan "),
        (r"\s*\+\s*", " tambah "),
        (r"\s*=\s*", " sama dengan "),
        (r"#([A-Za-z0-9]+)", r"tagar \1"),
        (r"#", "nomor "),
    ]

    for pattern, replacement in symbol_map:
        text = re.sub(pattern, replacement, text)

    return text


def normalize_indonesian_text(raw_text: str) -> str:
    """
    Fungsi utama normalisasi pipeline teks Indonesia untuk TTS.
    Menjalankan transformasi berurutan agar tidak terjadi tabrakan regex.
    """
    if not raw_text or not raw_text.strip():
        return ""

    text = raw_text

    # 1. URL & Email (sebelum simbol & titik diubah)
    text = normalize_urls_and_emails(text)

    # 2. Tanggal & Waktu
    text = normalize_dates(text)
    text = normalize_time(text)

    # 3. Mata uang (Rupiah, Dollar, Euro)
    text = normalize_currency(text)

    # 4. Nomor telepon / deret nomor
    text = normalize_phone_numbers(text)

    # 5. Persen & Satuan ukuran
    text = normalize_percent(text)
    text = normalize_units(text)

    # 6. Ordinal (ke-1, ke-21)
    text = normalize_ordinals(text)

    # 7. Sisa angka & desimal
    text = normalize_decimals_and_numbers(text)

    # 8. Singkatan bahasa Indonesia
    text = normalize_abbreviations(text)

    # 9. Simbol & Karakter khusus
    text = normalize_symbols(text)

    # 10. Bersihkan spasi ganda
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
