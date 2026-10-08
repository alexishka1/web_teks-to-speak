"""
Emotion mapping to prosody parameters (rate, pitch, volume)
"""

EMOTION_PRESETS: dict[str, dict[str, float]] = {
    "neutral": {"speed": 1.0, "pitch": 0.0},
    "cheerful": {"speed": 1.08, "pitch": 1.5},
    "serious": {"speed": 0.95, "pitch": -0.8},
    "calm": {"speed": 0.90, "pitch": -0.5},
    "excited": {"speed": 1.15, "pitch": 2.0},
}


def map_emotion(emotion_id: str) -> dict[str, float]:
    return EMOTION_PRESETS.get(emotion_id, EMOTION_PRESETS["neutral"])
