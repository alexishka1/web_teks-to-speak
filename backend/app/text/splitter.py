"""
Modul Pemecah Teks (Sentence Splitter & Chunker) untuk TTS TaSTP.
Memecah teks per paragraf dan kalimat secara natural tanpa memotong di tengah singkatan,
serta mengelompokkan kalimat ke dalam chunk (maks. 250 kata) untuk inferensi hemat CPU.
"""

import re

# Daftar singkatan umum yang tidak boleh dianggap sebagai akhir kalimat
PROTECTED_ABBREVIATIONS = [
    r"\bDr\.",
    r"\bProf\.",
    r"\bIr\.",
    r"\bDrs\.",
    r"\bH\.",
    r"\bHj\.",
    r"\bPT\.",
    r"\bCV\.",
    r"\bUD\.",
    r"\bJl\.",
    r"\bNo\.",
    r"\bKav\.",
    r"\bdll\.",
    r"\bdsb\.",
    r"\bdst\.",
    r"\bmis\.",
    r"\bmisal\.",
    r"\btsb\.",
    r"\ba\.n\.",
    r"\bd\.a\.",
    r"\bu\.p\.",
]


def protect_abbreviations(text: str) -> str:
    """Mengganti titik pada singkatan dengan placeholder agar tidak terpotong."""
    protected = text
    for i, pattern in enumerate(PROTECTED_ABBREVIATIONS):

        def repl(match):
            return match.group(0).replace(".", "___DOT___")

        protected = re.sub(pattern, repl, protected, flags=re.IGNORECASE)

    # Lindungi juga titik pada jam dan angka ribuan (mis. 10.00 atau 1.500)
    protected = re.sub(r"(\d+)\.(\d+)", r"\1___DOT___\2", protected)
    return protected


def unprotect_abbreviations(text: str) -> str:
    """Mengembalikan placeholder titik ke bentuk semula."""
    return text.replace("___DOT___", ".")


def split_into_sentences(text: str) -> list[str]:
    """
    Memecah teks menjadi daftar kalimat yang utuh.
    Mempertahankan tanda baca penutup dan kutipan ("...").
    """
    if not text or not text.strip():
        return []

    protected = protect_abbreviations(text.strip())

    # Pecah berdasarkan tanda akhir kalimat (. ! ?) dengan fixed-width lookbehind yang didukung Python re
    sentence_pattern = r'(?:(?<=[.!?])|(?<=[.!?]["\']))\s+'
    raw_sentences = re.split(sentence_pattern, protected)

    sentences = []
    for s in raw_sentences:
        cleaned = unprotect_abbreviations(s).strip()
        if cleaned:
            sentences.append(cleaned)

    return sentences


def split_into_paragraphs(text: str) -> list[str]:
    """Memecah teks berdasarkan batas paragraf ganda (\n\n)."""
    if not text or not text.strip():
        return []
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def split_long_sentence_on_clauses(sentence: str, max_words: int = 150) -> list[str]:
    """
    Memecah kalimat yang terlalu panjang berdasarkan batas klausa alami
    (tanda koma, titik koma, atau kata penghubung koordinatif).
    """
    words = sentence.split()
    if len(words) <= max_words:
        return [sentence]

    # Coba pecah berdasarkan titik koma atau koma terlebih dahulu
    parts = re.split(r"(?<=[;,])\s+", sentence)
    if len(parts) > 1:
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        for p in parts:
            p_len = len(p.split())
            if current_len + p_len > max_words and current:
                chunks.append(" ".join(current))
                current = [p]
                current_len = p_len
            else:
                current.append(p)
                current_len += p_len
        if current:
            chunks.append(" ".join(current))
        return chunks

    return [sentence]


def chunk_text(text: str, max_words: int = 250) -> list[str]:
    """
    Mengelompokkan naskah menjadi chunk optimal (maksimal max_words)
    tanpa memotong di tengah kalimat atau frasa penting.
    """
    if not text or not text.strip():
        return []

    paragraphs = split_into_paragraphs(text)
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_chunk_words = 0

    for para in paragraphs:
        sentences = split_into_sentences(para)
        for sent in sentences:
            sent_words = len(sent.split())

            # Jika satu kalimat melebihi batas, pecah berdasarkan klausa
            if sent_words > max_words:
                sub_sentences = split_long_sentence_on_clauses(
                    sent, max_words=max_words
                )
            else:
                sub_sentences = [sent]

            for s in sub_sentences:
                s_len = len(s.split())
                if current_chunk_words + s_len > max_words and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [s]
                    current_chunk_words = s_len
                else:
                    current_chunk.append(s)
                    current_chunk_words += s_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
