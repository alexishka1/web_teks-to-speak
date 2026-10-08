"""
Modul Pengaturan Jeda Otomatis (Automatic Pauses) untuk TTS TaSTP.
Mengatur durasi hening alami berdasarkan tanda baca:
- Koma (,): 200ms
- Titik dua / Titik koma (: ;): 250ms
- Titik (.): 450ms
- Tanda seru (!) / Tanda tanya (?): 500ms
- Elipsis (... / …): 600ms
- Paragraf (\n\n): 800ms
"""

import re
from typing import NamedTuple

PAUSE_DURATIONS_MS = {
    "comma": 200,
    "semicolon": 250,
    "colon": 250,
    "period": 450,
    "exclamation": 500,
    "question": 500,
    "ellipsis": 600,
    "paragraph": 800,
}


class PausedSegment(NamedTuple):
    text: str
    pause_after_ms: int


def get_pause_for_punctuation(punct: str) -> int:
    """Mengembalikan durasi hening (ms) untuk tanda baca tertentu."""
    if punct in ("...", "…"):
        return PAUSE_DURATIONS_MS["ellipsis"]
    if punct == ",":
        return PAUSE_DURATIONS_MS["comma"]
    if punct == ";":
        return PAUSE_DURATIONS_MS["semicolon"]
    if punct == ":":
        return PAUSE_DURATIONS_MS["colon"]
    if punct == ".":
        return PAUSE_DURATIONS_MS["period"]
    if punct == "!":
        return PAUSE_DURATIONS_MS["exclamation"]
    if punct == "?":
        return PAUSE_DURATIONS_MS["question"]
    return 0


def insert_ssml_breaks(text: str) -> str:
    """
    Menyisipkan tag SSML <break time="...ms"/> pada naskah
    untuk engine yang mendukung SSML (mis. Azure, Edge, atau Piper SSML).
    """
    if not text:
        return ""

    # Ganti jeda paragraf terlebih dahulu
    result = re.sub(
        r"\n\s*\n", f'<break time="{PAUSE_DURATIONS_MS["paragraph"]}ms"/>\n\n', text
    )

    # Elipsis
    result = re.sub(
        r"(\.\.\.|…)", rf'\1<break time="{PAUSE_DURATIONS_MS["ellipsis"]}ms"/>', result
    )

    # Titik dua dan titik koma
    result = re.sub(
        r"([;:])\s*", rf'\1 <break time="{PAUSE_DURATIONS_MS["colon"]}ms"/> ', result
    )

    # Koma
    result = re.sub(
        r"(,)\s*", rf'\1 <break time="{PAUSE_DURATIONS_MS["comma"]}ms"/> ', result
    )

    # Tanda tanya dan seru
    result = re.sub(
        r"([!?])\s*",
        rf'\1 <break time="{PAUSE_DURATIONS_MS["exclamation"]}ms"/> ',
        result,
    )

    # Titik (yang bukan elipsis atau angka desimal)
    result = re.sub(
        r"(?<!\.)(\.)(?!\.)\s*",
        rf'\1 <break time="{PAUSE_DURATIONS_MS["period"]}ms"/> ',
        result,
    )

    # Bersihkan spasi ganda dalam tag
    result = re.sub(r"\s+", " ", result).strip()
    return result


def split_into_paused_segments(text: str) -> list[PausedSegment]:
    """
    Memecah teks menjadi potongan segmen bicara beserta durasi jeda setelahnya.
    Sangat berguna untuk engine non-SSML (Piper ONNX) agar audio generator
    dapat menyisipkan buffer hening (silence PCM) dengan durasi presisi.
    """
    if not text or not text.strip():
        return []

    segments: list[PausedSegment] = []
    paragraphs = text.split("\n\n")

    for p_idx, para in enumerate(paragraphs):
        # Pecah kalimat berdasarkan tanda baca jeda
        pattern = r"([^,.;:!?…]+(?:[…\.]{3}|[,.;:!?…])?)"
        tokens = re.findall(pattern, para)

        for token in tokens:
            cleaned = token.strip()
            if not cleaned:
                continue

            pause_ms = 0
            # Cek tanda baca di akhir token
            if cleaned.endswith("...") or cleaned.endswith("…"):
                pause_ms = PAUSE_DURATIONS_MS["ellipsis"]
            elif cleaned.endswith(","):
                pause_ms = PAUSE_DURATIONS_MS["comma"]
            elif cleaned.endswith(";"):
                pause_ms = PAUSE_DURATIONS_MS["semicolon"]
            elif cleaned.endswith(":"):
                pause_ms = PAUSE_DURATIONS_MS["colon"]
            elif cleaned.endswith("."):
                pause_ms = PAUSE_DURATIONS_MS["period"]
            elif cleaned.endswith("!"):
                pause_ms = PAUSE_DURATIONS_MS["exclamation"]
            elif cleaned.endswith("?"):
                pause_ms = PAUSE_DURATIONS_MS["question"]

            segments.append(PausedSegment(text=cleaned, pause_after_ms=pause_ms))

        # Jika bukan paragraf terakhir, tambahkan jeda paragraf pada segmen terakhir
        if p_idx < len(paragraphs) - 1 and segments:
            last = segments[-1]
            segments[-1] = PausedSegment(
                text=last.text, pause_after_ms=PAUSE_DURATIONS_MS["paragraph"]
            )

    return segments
