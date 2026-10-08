"""
Modul Endpoint History TaSTP:
- Mengambil daftar riwayat sintesis audio (mendukung pagination / list tervirtualisasi)
- Memungkinkan pemutaran ulang dan pengunduhan file WAV
- Menghapus entri riwayat dan membersihkan file audio terkait di disk
"""

from app.config import settings
from app.database import get_db
from app.models.schema import HistoryDTO, HistoryRecord
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=list[HistoryDTO])
@router.get("/", response_model=list[HistoryDTO])
async def list_history(
    limit: int = Query(default=50, ge=1, le=200, description="Jumlah item per halaman"),
    offset: int = Query(default=0, ge=0, description="Offset pagination"),
    db: AsyncSession = Depends(get_db),
):
    """
    Mengambil daftar rekaman riwayat narasi yang pernah digenerate.
    Diurutkan dari yang paling baru (terbaru ke terlama).
    """
    stmt = (
        select(HistoryRecord)
        .order_by(HistoryRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    records = res.scalars().all()
    return records


@router.delete("/{history_id}")
async def delete_history_item(history_id: str, db: AsyncSession = Depends(get_db)):
    """
    Menghapus rekaman riwayat audio dan file fisiknya dari penyimpanan.
    """
    stmt = select(HistoryRecord).where(HistoryRecord.id == history_id)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item riwayat tidak ditemukan.",
        )

    # Hapus file audio fisik jika ada
    audio_file = settings.AUDIO_OUTPUT_DIR / f"{record.job_id}.wav"
    if audio_file.exists():
        try:
            audio_file.unlink(missing_ok=True)
        except Exception:
            pass

    await db.delete(record)
    await db.commit()
    return {"message": "Riwayat dan file audio berhasil dihapus."}
