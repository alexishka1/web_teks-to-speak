"""
Prosody micro-intonation variations to prevent robotic speech
"""

import random


def apply_prosody_jitter(
    speed: float, pitch: float, jitter_pct: float = 3.0
) -> tuple[float, float]:
    """Variasi mikro acak ±3% agar suara terasa alami dan dinamis."""
    factor = 1.0 + random.uniform(-jitter_pct, jitter_pct) / 100.0
    return speed * factor, pitch * factor
