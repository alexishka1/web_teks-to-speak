from pathlib import Path
from app.database import get_db
from app.models.schema import VoiceDTO, VoiceRecord
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/voices", response_model=list[VoiceDTO])
async def list_voices(db: AsyncSession = Depends(get_db)):
    """Mengambil daftar suara aktif dari database (hanya suara hasil rekaman/kloning pengguna)."""
    stmt = select(VoiceRecord).where(VoiceRecord.is_active == True)  # noqa: E712
    res = await db.execute(stmt)
    records = res.scalars().all()

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
        )
        for r in records
    ]


@router.delete("/voices/{voice_id}", status_code=status.HTTP_200_OK)
async def delete_voice(voice_id: str, db: AsyncSession = Depends(get_db)):
    """Menghapus suara rekaman/kloning pengguna beserta berkas audionya dari sistem."""
    stmt = select(VoiceRecord).where(VoiceRecord.id == voice_id)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suara dengan ID '{voice_id}' tidak ditemukan.",
        )

    # Bersihkan file audio referensi / model jika ada
    if record.model_path:
        p = Path(record.model_path)
        if p.exists():
            p.unlink(missing_ok=True)
    if record.config_path:
        cp = Path(record.config_path)
        if cp.exists():
            cp.unlink(missing_ok=True)

    await db.delete(record)
    await db.commit()
    return {"message": f"Suara '{record.name}' berhasil dihapus.", "id": voice_id}

