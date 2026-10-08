"""
Voice registry to load and discover voices
"""

import json
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).parent / "catalog.json"


def get_registered_voices() -> list[dict[str, Any]]:
    if CATALOG_PATH.exists():
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
