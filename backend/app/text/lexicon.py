"""
Modul Kamus Pelafalan Kustom (Lexicon) untuk TTS TaSTP.
Mendukung operasi CRUD berbasis SQLite serta penerapan aturan penggantian kata
ke dalam naskah secara akurat (dengan batas kata / regex).
"""

import re
import uuid
from datetime import datetime

from app.models.schema import LexiconCreate, LexiconEntry, LexiconUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Kamus bawaan untuk istilah kreator konten digital & teknologi
DEFAULT_LEXICON: dict[str, str] = {
    "YouTube": "yu-tyub",
    "TikTok": "tik-tok",
    "Podcast": "pod-kes",
    "Content Creator": "konten kreator",
    "Voiceover": "vois over",
    "Reels": "rils",
    "Subscribe": "subskraib",
    "Like": "laik",
    "Share": "syer",
    "FYP": "ef ye pe",
    "AI": "e ai",
}


class LexiconService:
    @staticmethod
    async def create_entry(data: LexiconCreate, session: AsyncSession) -> LexiconEntry:
        """Menambahkan entri kamus pelafalan baru ke database."""
        entry_id = f"lex_{uuid.uuid4().hex[:10]}"
        entry = LexiconEntry(
            id=entry_id,
            word=data.word.strip(),
            replacement=data.replacement.strip(),
            voice_id=data.voice_id,
            is_regex=data.is_regex,
            is_active=data.is_active,
            created_at=datetime.utcnow(),
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry

    @staticmethod
    async def get_all_entries(
        session: AsyncSession, voice_id: str | None = None, active_only: bool = False
    ) -> list[LexiconEntry]:
        """Mengambil seluruh entri kamus, dapat difilter berdasarkan voice_id dan status aktif."""
        query = select(LexiconEntry)
        if active_only:
            query = query.where(LexiconEntry.is_active == True)  # noqa: E712
        if voice_id:
            query = query.where(
                (LexiconEntry.voice_id == voice_id) | (LexiconEntry.voice_id.is_(None))
            )
        res = await session.execute(query)
        return list(res.scalars().all())

    @staticmethod
    async def get_entry_by_id(
        entry_id: str, session: AsyncSession
    ) -> LexiconEntry | None:
        """Mengambil entri berdasarkan ID."""
        stmt = select(LexiconEntry).where(LexiconEntry.id == entry_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_entry_by_word(
        word: str, session: AsyncSession
    ) -> LexiconEntry | None:
        """Mengambil entri berdasarkan kata."""
        stmt = select(LexiconEntry).where(LexiconEntry.word == word.strip())
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def update_entry(
        entry_id: str, data: LexiconUpdate, session: AsyncSession
    ) -> LexiconEntry | None:
        """Memperbarui aturan penggantian kata."""
        entry = await LexiconService.get_entry_by_id(entry_id, session)
        if not entry:
            return None

        if data.word is not None:
            entry.word = data.word.strip()
        if data.replacement is not None:
            entry.replacement = data.replacement.strip()
        if data.voice_id is not None:
            entry.voice_id = data.voice_id
        if data.is_regex is not None:
            entry.is_regex = data.is_regex
        if data.is_active is not None:
            entry.is_active = data.is_active

        await session.commit()
        await session.refresh(entry)
        return entry

    @staticmethod
    async def delete_entry(entry_id: str, session: AsyncSession) -> bool:
        """Menghapus entri kamus."""
        entry = await LexiconService.get_entry_by_id(entry_id, session)
        if not entry:
            return False

        await session.delete(entry)
        await session.commit()
        return True


def apply_lexicon_rules(
    text: str,
    custom_rules: dict[str, str] | None = None,
    db_entries: list[LexiconEntry] | None = None,
) -> str:
    """
    Menerapkan kamus pelafalan ke teks naskah.
    Mendahulukan entri dari database, kemudian custom_rules, dan terakhir DEFAULT_LEXICON.
    Menggunakan batas kata (\b) agar tidak mengubah substring di dalam kata lain.
    """
    if not text:
        return ""

    result = text

    # 1. Terapkan entri dari database (jika ada)
    if db_entries:
        for entry in db_entries:
            if hasattr(entry, "is_active") and not entry.is_active:
                continue
            if entry.is_regex:
                try:
                    result = re.sub(entry.word, entry.replacement, result)
                except re.error:
                    pass
            else:
                pattern = rf"\b{re.escape(entry.word)}\b"
                result = re.sub(pattern, entry.replacement, result, flags=re.IGNORECASE)

    # 2. Terapkan custom_rules kamus dict
    rules = {**DEFAULT_LEXICON, **(custom_rules or {})}
    for word, replacement in rules.items():
        pattern = rf"\b{re.escape(word)}\b"
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result
