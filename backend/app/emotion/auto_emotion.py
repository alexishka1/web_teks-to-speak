"""
Modul Analisis Auto Emotion Berbasis Aturan dan Kata Kunci Leksikon Lokal
(100% Offline tanpa API eksternal, latensi < 1 milidetik).
"""

import re
from typing import Any

# Pola kata kunci bahasa Indonesia yang dipetakan ke ID emosi
KEYWORD_RULES: list[tuple[re.Pattern, str, float]] = [
    # 1. Hook Kreator / Penarik Perhatian
    (
        re.compile(
            r"\b(stop scroll|tahu nggak|tahukah anda|rahasia terbesar|ini dia|jangan skip)\b",
            re.IGNORECASE,
        ),
        "energetic_hook",
        0.95,
    ),
    # 2. Terkejut / Kaget
    (
        re.compile(
            r"(\!\?|\?\!|\bastaga\b|\bwah\b|\bkaget\b|\bternyata\b|\btidak disangka\b|\bmengejutkan\b)",
            re.IGNORECASE,
        ),
        "surprised",
        0.90,
    ),
    # 3. Bisikan / Rahasia
    (
        re.compile(
            r"\b(sshh|bisik|rahasia|diam-diam|jangan bilang|tersembunyi)\b",
            re.IGNORECASE,
        ),
        "whisper",
        0.88,
    ),
    # 4. Gembira / Antusias
    (
        re.compile(
            r"\b(selamat|hore|asyik|sukses|hebat|keren|bangga|luar biasa|mantap|semangat|juara|terima kasih)\b",
            re.IGNORECASE,
        ),
        "happy",
        0.85,
    ),
    # 5. Sedih / Haru
    (
        re.compile(
            r"\b(sedih|menyedihkan|kecewa|sayang sekali|duka|berduka|menangis|tangis|terharu|haru|sayangnya|kehilangan|pilu|tragis)\b",
            re.IGNORECASE,
        ),
        "sad",
        0.85,
    ),
    # 6. Marah / Tegas
    (
        re.compile(
            r"(\!{2,}|\bkesal\b|\bmarah\b|\bbenci\b|\bketerlaluan\b|\bkurang ajar\b|\bstop\b)",
            re.IGNORECASE,
        ),
        "angry",
        0.80,
    ),
    # 7. Takut / Khawatir
    (
        re.compile(
            r"\b(takut|khawatir|waspada|ancaman|bahaya|mengerikan|ngeri|panik)\b",
            re.IGNORECASE,
        ),
        "fearful",
        0.80,
    ),
    # 8. Berita / Formal
    (
        re.compile(
            r"\b(dilaporkan|menurut data|berdasarkan riset|pemerintah|resmi|kabar terkini|fakta membuktikan)\b",
            re.IGNORECASE,
        ),
        "news_anchor",
        0.75,
    ),
    # 9. Panggilan Telepon / Radio
    (
        re.compile(r"\b(halo\?|halo di sana|sambungan telepon)\b", re.IGNORECASE),
        "telephone",
        0.85,
    ),
    (
        re.compile(r"\b(roger|breker|ganti|standby|frekuensi)\b", re.IGNORECASE),
        "radio_announcer",
        0.85,
    ),
    # 10. Dramatis / Reflektif
    (
        re.compile(
            r"(\.{3,}|\bpada akhirnya\b|\bdan kini\b|\bsejarah mencatat\b)",
            re.IGNORECASE,
        ),
        "dramatic",
        0.70,
    ),
    # 11. Tenang / Damai
    (
        re.compile(
            r"\b(tenang|damai|hening|santai|perlahan|tarik napas)\b", re.IGNORECASE
        ),
        "calm",
        0.75,
    ),
]


def detect_sentence_emotion(sentence: str) -> dict[str, Any]:
    """
    Menganalisis kalimat tunggal dan mengembalikan emosi yang terdeteksi beserta keyakinan (confidence).
    """
    clean_text = sentence.strip()
    if not clean_text:
        return {"emotion_id": "neutral", "confidence": 1.0, "rule_matched": "empty"}

    for pattern, emotion_id, confidence in KEYWORD_RULES:
        if pattern.search(clean_text):
            return {
                "emotion_id": emotion_id,
                "confidence": confidence,
                "rule_matched": pattern.pattern,
            }

    # Aturan berbasis tanda baca
    if clean_text.endswith("!"):
        return {
            "emotion_id": "enthusiastic",
            "confidence": 0.65,
            "rule_matched": "exclamation",
        }
    if clean_text.endswith("?"):
        return {"emotion_id": "hopeful", "confidence": 0.60, "rule_matched": "question"}

    return {"emotion_id": "neutral", "confidence": 0.50, "rule_matched": "default"}


def analyze_script_emotions(sentences: list[str]) -> list[dict[str, Any]]:
    """
    Menganalisis daftar kalimat naskah secara berurutan.
    """
    results = []
    for idx, sentence in enumerate(sentences):
        detection = detect_sentence_emotion(sentence)
        results.append({"sentence_index": idx, "text": sentence, **detection})
    return results
