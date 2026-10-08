from app.config import settings
from app.database import get_db
from app.models.schema import VoiceDTO, VoiceRecord
from app.voices.registry import get_registered_voices
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/voices", response_model=list[VoiceDTO])
async def list_voices(db: AsyncSession = Depends(get_db)):
    """Mengambil daftar suara kreator yang aktif dari database (bawaan + upload + kloning)."""
    stmt = select(VoiceRecord).where(VoiceRecord.is_active == True)  # noqa: E712
    res = await db.execute(stmt)
    records = res.scalars().all()

    if not records:
        # Fallback cadangan bila DB belum di-seed
        return get_registered_voices()

    return [
        VoiceDTO(
            id=r.id,
            name=r.name,
            gender=r.gender,
            language=r.language,
            category=r.category,
            description=r.description or "",
            engine=r.engine,
            sample_rate=r.sample_rate,
            is_cloned=r.is_cloned,
            is_active=r.is_active,
            preview_url=r.preview_audio_url,
            backed_by=(
                "dedicated_model"
                if (
                    r.id == "id_ID-news_tts-medium"
                    or (settings.MODELS_DIR / f"{r.id}.onnx").exists()
                    or (settings.MODELS_DIR / r.id / f"{r.id}.onnx").exists()
                )
                else "profile_of_shared_model"
            ),
        )
        for r in records
    ]
