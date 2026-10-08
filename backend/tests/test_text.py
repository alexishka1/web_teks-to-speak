import sys
from pathlib import Path

# Pastikan folder backend masuk ke sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


import pytest
from app.database import Base
from app.models.schema import LexiconCreate, LexiconUpdate
from app.text.lexicon import (
    LexiconService,
    apply_lexicon_rules,
)
from app.text.normalize import (
    normalize_abbreviations,
    normalize_currency,
    normalize_dates,
    normalize_indonesian_text,
    normalize_ordinals,
    normalize_percent,
    normalize_phone_numbers,
    normalize_symbols,
    normalize_time,
    normalize_units,
    normalize_urls_and_emails,
    number_to_words,
)
from app.text.pauses import (
    get_pause_for_punctuation,
    insert_ssml_breaks,
    split_into_paused_segments,
)
from app.text.splitter import (
    chunk_text,
    split_into_paragraphs,
    split_into_sentences,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ==========================================
# 1. Test Normalisasi Angka (Number to Words)
# ==========================================


def test_number_to_words_single_and_teens():
    assert number_to_words(0) == "nol"
    assert number_to_words(1) == "satu"
    assert number_to_words(10) == "sepuluh"
    assert number_to_words(11) == "sebelas"
    assert number_to_words(15) == "lima belas"
    assert number_to_words(20) == "dua puluh"
    assert number_to_words(25) == "dua puluh lima"
    assert number_to_words(99) == "sembilan puluh sembilan"


def test_number_to_words_hundreds_thousands():
    assert number_to_words(100) == "seratus"
    assert number_to_words(105) == "seratus lima"
    assert number_to_words(112) == "seratus dua belas"
    assert number_to_words(1500) == "seribu lima ratus"
    assert number_to_words(2024) == "dua ribu dua puluh empat"
    assert number_to_words(25500) == "dua puluh lima ribu lima ratus"


def test_number_to_words_millions_to_trillions():
    assert number_to_words(1_000_000) == "satu juta"
    assert number_to_words(25_500_000) == "dua puluh lima juta lima ratus ribu"
    assert number_to_words(1_000_000_000) == "satu miliar"
    assert number_to_words(1_000_000_000_000) == "satu triliun"


def test_number_negative():
    assert number_to_words(-5) == "minus lima"
    assert number_to_words(-100) == "minus seratus"


def test_number_decimals():
    raw = "Suhu naik 2,5 derajat dan tingkat akurasi 99,9 persen serta 0,05 detik."
    norm = normalize_indonesian_text(raw)
    assert "dua koma lima" in norm
    assert "sembilan puluh sembilan koma sembilan" in norm
    assert "nol koma nol lima" in norm


# ==========================================
# 2. Test Mata Uang (Currency)
# ==========================================


def test_currency_rupiah_simple():
    text = "Harganya hanya Rp15.000 per porsi."
    assert (
        normalize_currency(text) == "Harganya hanya lima belas ribu rupiah per porsi."
    )


def test_currency_rupiah_space_and_dot():
    text = "Biaya langganan Rp 25.000 atau Rp. 50.000 per bulan."
    norm = normalize_currency(text)
    assert "dua puluh lima ribu rupiah" in norm
    assert "lima puluh ribu rupiah" in norm


def test_currency_rupiah_scale_millions_billions():
    text = "Investasi mencapai Rp 2,5 juta dan valuasi Rp 10 miliar."
    norm = normalize_currency(text)
    assert "dua koma lima juta rupiah" in norm
    assert "sepuluh miliar rupiah" in norm


def test_currency_rupiah_with_sen():
    text = "Saldo tersisa Rp 1.500.000,50 di rekening."
    norm = normalize_currency(text)
    assert "satu juta lima ratus ribu rupiah lima puluh sen" in norm


def test_currency_foreign():
    text = "Harga lisensi $50 atau USD 100 dan €10."
    norm = normalize_currency(text)
    assert "lima puluh dolar" in norm
    assert "seratus dolar" in norm
    assert "sepuluh euro" in norm


# ==========================================
# 3. Test Tanggal & Waktu (Dates & Time)
# ==========================================


def test_dates_slash_and_dash():
    text = "Proklamasi pada 17/08/1945 dan pemilu 14-02-2024."
    norm = normalize_dates(text)
    assert "tujuh belas Agustus seribu sembilan ratus empat puluh lima" in norm
    assert "empat belas Februari dua ribu dua puluh empat" in norm


def test_dates_formal_text():
    text = "Tanggal 17 Agustus 1945 adalah hari bersejarah."
    norm = normalize_dates(text)
    assert "tujuh belas Agustus seribu sembilan ratus empat puluh lima" in norm


def test_time_with_timezone():
    text = "Upacara dimulai pukul 10.00 WIB dan siaran 08:30 WITA."
    norm = normalize_time(text)
    assert "pukul sepuluh tepat Waktu Indonesia Barat" in norm
    assert "pukul delapan lewat tiga puluh menit Waktu Indonesia Tengah" in norm


def test_time_simple_minutes():
    text = "Jadwal kereta pukul 14.15 tiba tepat waktu."
    norm = normalize_time(text)
    assert "pukul empat belas lewat lima belas menit" in norm


# ==========================================
# 4. Test Persen & Satuan (Percent & Units)
# ==========================================


def test_percent_integer_and_decimal():
    text = "Diskon 50% dan inflasi 12,5% tahun ini."
    norm = normalize_percent(text)
    assert "lima puluh persen" in norm
    assert "dua belas koma lima persen" in norm


def test_units_speed_and_temperature():
    text = "Mobil melaju 45 km/jam dengan suhu udara 28°C."
    norm = normalize_units(text)
    assert "45 kilometer per jam" in norm
    assert "28 derajat Celcius" in norm


def test_units_weight_and_length():
    text = "Berat paket 10 kg dan panjang tali 5 m."
    norm = normalize_units(text)
    assert "10 kilogram" in norm
    assert "5 meter" in norm


# ==========================================
# 5. Test Singkatan, Simbol, Phone, & URL
# ==========================================


def test_phone_number_sequence():
    text = "Hubungi customer care di nomor 0812-3456-7890."
    norm = normalize_phone_numbers(text)
    assert (
        "nol delapan satu dua, tiga empat lima enam, tujuh delapan sembilan nol" in norm
    )


def test_ordinals_ke():
    text = "Peringkat ke-1 dan babak ke-21 perlombaan."
    norm = normalize_ordinals(text)
    assert "pertama" in norm
    assert "ke dua puluh satu" in norm


def test_common_abbreviations():
    text = "Kunjungan kerja ke PT Kereta Api dan kantor BUMN dll. bersama Dr. Sutomo."
    norm = normalize_abbreviations(text)
    assert "Perseroan Terbatas" in norm
    assert "B U M N" in norm
    assert "dan lain-lain" in norm
    assert "Dokter" in norm


def test_symbols():
    text = "Riset & pengembangan 5 + 5 = 10 untuk #kreator."
    norm = normalize_symbols(text)
    assert " dan " in norm
    assert " tambah " in norm
    assert " sama dengan " in norm
    assert "tagar kreator" in norm


def test_urls_and_emails():
    text = "Kunjungi https://kemdikbud.go.id atau kirim surel ke panitia@sejarah.id sekarang."
    norm = normalize_urls_and_emails(text)
    assert (
        "h t t p s titik dua garis miring garis miring kemdikbud dot go dot id" in norm
    )
    assert "panitia at sejarah dot id" in norm


# ==========================================
# 6. Test Splitter & Chunker
# ==========================================


def test_splitter_simple_sentences():
    text = "Halo semuanya. Selamat datang di video ini! Apakah kalian sudah siap?"
    sentences = split_into_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "Halo semuanya."
    assert sentences[1] == "Selamat datang di video ini!"
    assert sentences[2] == "Apakah kalian sudah siap?"


def test_splitter_abbreviation_protection_edge_case():
    text = "Dr. Budi mengunjungi PT. KAI pada pukul 10.00 WIB. Pertemuan tersebut selesai pukul 12.00 WIB."
    sentences = split_into_sentences(text)
    assert len(sentences) == 2
    assert "Dr. Budi" in sentences[0]
    assert "PT. KAI" in sentences[0]
    assert sentences[1] == "Pertemuan tersebut selesai pukul 12.00 WIB."


def test_splitter_quotes_integrity():
    text = 'Bung Karno berseru, "Jangan sekali-kali meninggalkan sejarah!" Rakyat pun bersorak gembira.'
    sentences = split_into_sentences(text)
    assert len(sentences) == 2
    assert '"Jangan sekali-kali meninggalkan sejarah!"' in sentences[0]


def test_splitter_paragraphs():
    text = "Paragraf pertama naskah.\n\nParagraf kedua naskah yang lebih panjang."
    paras = split_into_paragraphs(text)
    assert len(paras) == 2
    assert paras[0] == "Paragraf pertama naskah."
    assert paras[1] == "Paragraf kedua naskah yang lebih panjang."


def test_chunk_text_under_limit():
    text = "Kalimat pertama. Kalimat kedua. Kalimat ketiga."
    chunks = chunk_text(text, max_words=50)
    assert len(chunks) == 1
    assert "Kalimat pertama." in chunks[0]


def test_chunk_text_over_limit():
    # Buat naskah 30 kalimat yang panjang
    sentences = [
        f"Ini adalah kalimat penjelasan ke-{i} yang memuat berbagai wawasan baru."
        for i in range(1, 25)
    ]
    long_script = " ".join(sentences)
    chunks = chunk_text(long_script, max_words=60)
    assert len(chunks) > 1
    # Pastikan tiap chunk tidak melompati batas drastis
    for c in chunks:
        assert len(c.split()) <= 80


# ==========================================
# 7. Test Lexicon Dictionary & CRUD
# ==========================================


def test_lexicon_in_memory_default_rules():
    raw = "Jangan lupa tonton video terbaru di YouTube dan TikTok serta dengarkan Podcast ini."
    replaced = apply_lexicon_rules(raw)
    assert "yu-tyub" in replaced
    assert "tik-tok" in replaced
    assert "pod-kes" in replaced


def test_lexicon_custom_rules_override():
    raw = "Saya adalah seorang Content Creator."
    custom = {"Content Creator": "pembuat konten handal"}
    replaced = apply_lexicon_rules(raw, custom_rules=custom)
    assert "pembuat konten handal" in replaced


@pytest.mark.asyncio
async def test_lexicon_db_crud_operations():
    # Buat engine in-memory SQLite untuk pengujian CRUD
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        # 1. Create
        data = LexiconCreate(
            word="Antigravity", replacement="anti-gra-vi-ti", is_regex=False
        )
        entry = await LexiconService.create_entry(data, session)
        assert entry.id.startswith("lex_")
        assert entry.word == "Antigravity"
        assert entry.replacement == "anti-gra-vi-ti"

        # 2. Read
        fetched = await LexiconService.get_entry_by_word("Antigravity", session)
        assert fetched is not None
        assert fetched.id == entry.id

        # 3. Update
        update_data = LexiconUpdate(replacement="an-ti-gra-fi-ti")
        updated = await LexiconService.update_entry(entry.id, update_data, session)
        assert updated is not None
        assert updated.replacement == "an-ti-gra-fi-ti"

        # 4. Apply to text with DB entry
        applied = apply_lexicon_rules(
            "Teknologi Antigravity sangat canggih.", db_entries=[updated]
        )
        assert "an-ti-gra-fi-ti" in applied

        # 5. Delete
        deleted = await LexiconService.delete_entry(entry.id, session)
        assert deleted is True
        assert await LexiconService.get_entry_by_id(entry.id, session) is None


# ==========================================
# 8. Test Pauses (Jeda Otomatis)
# ==========================================


def test_pauses_durations_constant():
    assert get_pause_for_punctuation(",") == 200
    assert get_pause_for_punctuation(";") == 250
    assert get_pause_for_punctuation(":") == 250
    assert get_pause_for_punctuation(".") == 450
    assert get_pause_for_punctuation("!") == 500
    assert get_pause_for_punctuation("?") == 500
    assert get_pause_for_punctuation("...") == 600


def test_pauses_insert_ssml_breaks():
    text = "Halo teman-teman, selamat datang. Apa kabar?"
    ssml = insert_ssml_breaks(text)
    assert '<break time="200ms"/>' in ssml
    assert '<break time="450ms"/>' in ssml
    assert '<break time="500ms"/>' in ssml


def test_pauses_split_into_segments():
    text = "Halo sahabat,\nselamat datang kembali.\n\nEpisode ini sangat seru!"
    segments = split_into_paused_segments(text)
    assert len(segments) >= 3

    # Segmen dengan koma harus memiliki pause_after_ms = 200
    assert any(s.pause_after_ms == 200 for s in segments)
    # Segmen penutup paragraf harus memiliki pause_after_ms = 800
    assert any(s.pause_after_ms == 800 for s in segments)


# ==========================================
# 9. Test Kasus Integrasi Lengkap (Real World)
# ==========================================


def test_full_integrated_indonesian_creator_script():
    script = (
        "Pada tanggal 17 Agustus 1945 pukul 10.00 WIB, proklamasi kemerdekaan dibacakan. "
        "Total dana anggaran mencapai Rp 25.500.000 untuk 1.500 pejuang. "
        "PT Kereta Api memberi diskon tarif 50% di rute 45 km/jam dengan suhu 28°C. "
        "Kunjungi https://kemdikbud.go.id atau kontak panitia@sejarah.id sekarang!"
    )
    normalized = normalize_indonesian_text(script)

    assert "tujuh belas Agustus seribu sembilan ratus empat puluh lima" in normalized
    assert "pukul sepuluh tepat Waktu Indonesia Barat" in normalized
    assert "dua puluh lima juta lima ratus ribu rupiah" in normalized
    assert "seribu lima ratus" in normalized
    assert "Perseroan Terbatas Kereta Api" in normalized
    assert "lima puluh persen" in normalized
    assert "empat puluh lima kilometer per jam" in normalized
    assert "dua puluh delapan derajat Celcius" in normalized
    assert "kemdikbud dot go dot id" in normalized
    assert "panitia at sejarah dot id" in normalized

    # Uji splitter pada hasil yang dinormalisasi
    sentences = split_into_sentences(normalized)
    assert len(sentences) == 4
