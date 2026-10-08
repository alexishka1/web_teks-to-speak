"""
Text normalization, splitter, lexicon, and pauses package
"""

from app.text.lexicon import DEFAULT_LEXICON, LexiconService, apply_lexicon_rules
from app.text.normalize import normalize_indonesian_text, number_to_words
from app.text.pauses import (
    PAUSE_DURATIONS_MS,
    get_pause_for_punctuation,
    insert_ssml_breaks,
    split_into_paused_segments,
)
from app.text.splitter import chunk_text, split_into_paragraphs, split_into_sentences

__all__ = [
    "DEFAULT_LEXICON",
    "PAUSE_DURATIONS_MS",
    "LexiconService",
    "apply_lexicon_rules",
    "chunk_text",
    "get_pause_for_punctuation",
    "insert_ssml_breaks",
    "normalize_indonesian_text",
    "number_to_words",
    "split_into_paragraphs",
    "split_into_paused_segments",
    "split_into_sentences",
]
