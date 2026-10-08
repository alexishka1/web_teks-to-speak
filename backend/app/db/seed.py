"""
Modul Seeder & Migrasi Data Awal TaSTP:
Memigrasikan data hardcode voices, presets, emotions, dan lexicon ke dalam database SQLite.
Memastikan semua item tersimpan dinamis di DB dan dapat dikelola via Studio Manager.
"""

import uuid
from datetime import datetime, timezone

from app.emotion.presets import EMOTION_CATALOG
from app.models.schema import (
    EmotionRecord,
    LexiconEntry,
    StylePresetRecord,
    VoiceRecord,
)
from app.text.lexicon import DEFAULT_LEXICON
from app.voices.registry import get_registered_voices
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_PRESETS = [
    {
        "id": "preset_podcast_warm",
        "name": "Podcast Hangat & Intim",
        "category": "podcast",
        "voice_id": "piper_id_siti_podcast",
        "speed": 1.0,
        "pitch": -0.5,
        "pause_scale": 1.1,
        "audio_effect": "podcast_eq",
        "emotion": "calm",
        "emotion_intensity": 90.0,
        "description": "Vokal hangat & intim dengan sedikit bass boost, pas untuk obrolan podcast.",
    },
    {
        "id": "preset_tiktok_viral",
        "name": "TikTok / Reels Cepat & Viral",
        "category": "creator",
        "voice_id": "piper_id_gadis_fast",
        "speed": 1.22,
        "pitch": 1.2,
        "pause_scale": 0.8,
        "audio_effect": "none",
        "emotion": "energetic_hook",
        "emotion_intensity": 100.0,
        "description": "Tempo cepat, nada riang, dan jeda sangat ringkas untuk video pendek FYP.",
    },
    {
        "id": "preset_news_formal",
        "name": "Berita Resmi & Wawasan",
        "category": "news",
        "voice_id": "id_ID-news_tts-medium",
        "speed": 1.05,
        "pitch": 0.0,
        "pause_scale": 1.0,
        "audio_effect": "none",
        "emotion": "news_anchor",
        "emotion_intensity": 85.0,
        "description": "Artikulasi formal, stabil, dan jernih untuk berita harian atau video edukasi.",
    },
    {
        "id": "preset_radio_commercial",
        "name": "Radio Komersial Siang",
        "category": "radio",
        "voice_id": "piper_id_dimas_news",
        "speed": 1.12,
        "pitch": 0.5,
        "pause_scale": 0.9,
        "audio_effect": "radio",
        "emotion": "enthusiastic",
        "emotion_intensity": 95.0,
        "description": "Gaya siaran radio komersial dengan efek bandwidth bandpass cerah.",
    },
    {
        "id": "preset_storytelling_night",
        "name": "Dongeng & Audio Book Malam",
        "category": "story",
        "voice_id": "piper_id_bima_narrator",
        "speed": 0.92,
        "pitch": -1.0,
        "pause_scale": 1.3,
        "audio_effect": "hall",
        "emotion": "storytelling",
        "emotion_intensity": 85.0,
        "description": "Tempo tenang berwibawa dengan reverb halus untuk dongeng pengantar tidur.",
    },
]


async def migrate_and_seed_database(session: AsyncSession) -> None:
    """Memeriksa dan mengisi data awal jika tabel database masih kosong."""
    now = datetime.now(timezone.utc)

    # 1. Pastikan kolom is_active ada jika database lama belum memilikinya
    try:
        await session.execute(
            text("ALTER TABLE voice_records ADD COLUMN is_active BOOLEAN DEFAULT 1")
        )
        await session.commit()
    except Exception:
        await session.rollback()

    try:
        await session.execute(
            text("ALTER TABLE lexicon ADD COLUMN is_active BOOLEAN DEFAULT 1")
        )
        await session.commit()
    except Exception:
        await session.rollback()

    # 2. Migrasi Suara (Voices)
    v_res = await session.execute(select(VoiceRecord))
    existing_voices = v_res.scalars().all()
    if not existing_voices:
        catalog_voices = get_registered_voices()
        for v in catalog_voices:
            v_rec = VoiceRecord(
                id=v["id"],
                name=v["name"],
                gender=v.get("gender", "female"),
                language=v.get("language", "id-ID"),
                category=v.get("category", "creator"),
                description=v.get("description", ""),
                engine=v.get("engine", "piper"),
                model_path=f"storage/models/{v['id']}.onnx",
                config_path=f"storage/models/{v['id']}.json",
                sample_rate=v.get("sample_rate", 22050),
                is_cloned=v.get("is_cloned", False),
                is_active=True,
                created_at=now,
            )
            session.add(v_rec)
        await session.commit()

    # 3. Migrasi Preset Suara (Style Presets)
    p_res = await session.execute(select(StylePresetRecord))
    existing_presets = p_res.scalars().all()
    if not existing_presets:
        for p in DEFAULT_PRESETS:
            p_rec = StylePresetRecord(
                id=p["id"],
                name=p["name"],
                category=p["category"],
                voice_id=p["voice_id"],
                speed=p["speed"],
                pitch=p["pitch"],
                pause_scale=p["pause_scale"],
                audio_effect=p["audio_effect"],
                emotion=p["emotion"],
                emotion_intensity=p["emotion_intensity"],
                description=p["description"],
                is_active=True,
                created_at=now,
            )
            session.add(p_rec)
        await session.commit()

    # 4. Migrasi Emosi (Emotion Records)
    e_res = await session.execute(select(EmotionRecord))
    existing_emotions = e_res.scalars().all()
    if not existing_emotions:
        for emo_id, emo in EMOTION_CATALOG.items():
            e_rec = EmotionRecord(
                id=emo.id,
                name=emo.name,
                category=emo.category,
                speed=emo.speed,
                pitch=emo.pitch,
                pause_scale=emo.pause_scale,
                effect=emo.effect,
                color=emo.color,
                description=emo.description,
                is_active=True,
                created_at=now,
            )
            session.add(e_rec)
        await session.commit()

    # 5. Migrasi Kamus Pelafalan (Lexicon)
    l_res = await session.execute(select(LexiconEntry))
    existing_lexicon = l_res.scalars().all()
    if not existing_lexicon:
        for word, replacement in DEFAULT_LEXICON.items():
            l_rec = LexiconEntry(
                id=f"lex_{uuid.uuid4().hex[:10]}",
                word=word,
                replacement=replacement,
                voice_id=None,
                is_regex=False,
                is_active=True,
                created_at=now,
            )
            session.add(l_rec)
        await session.commit()
