"""
Modul Endpoint Projects (Dialog Multi-Speaker):
- Mengelola proyek narasi & naskah panjang
- Membagi naskah menjadi blok-blok percakapan (dialogue blocks)
- Tiap blok memiliki Voice ID, Emosi, Speaker, Speed, dan Pitch independen
- Render gabungan: Sintesis tiap blok lalu disambung dengan equal-power crossfade
"""

import uuid
from datetime import datetime
from pathlib import Path

from app.audio.crossfade import merge_wav_files_with_crossfade
from app.audio.effects import apply_audio_effects_ffmpeg
from app.audio.pipeline import run_synthesis_pipeline
from app.audio.watermark import embed_ai_disclosure_metadata
from app.config import settings
from app.database import get_db
from app.models.schema import (
    Project,
    ProjectBlock,
    ProjectBlockCreate,
    ProjectBlockDTO,
    ProjectCreate,
    ProjectDTO,
)
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/projects", tags=["Projects"])

PROJECTS_AUDIO_DIR = settings.AUDIO_OUTPUT_DIR / "projects"
PROJECTS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@router.get("", response_model=list[ProjectDTO])
@router.get("/", response_model=list[ProjectDTO])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """Mengambil seluruh daftar proyek narasi pengguna."""
    stmt = select(Project).order_by(Project.updated_at.desc())
    res = await db.execute(stmt)
    projects = res.scalars().all()

    output = []
    for p in projects:
        # Ambil blok
        b_stmt = (
            select(ProjectBlock)
            .where(ProjectBlock.project_id == p.id)
            .order_by(ProjectBlock.sequence.asc())
        )
        b_res = await db.execute(b_stmt)
        blocks = b_res.scalars().all()
        output.append(
            ProjectDTO(
                id=p.id,
                title=p.title,
                description=p.description,
                total_duration_sec=p.total_duration_sec,
                final_audio_url=f"/api/projects/{p.id}/audio"
                if p.final_audio_path
                else None,
                created_at=p.created_at,
                blocks=[
                    ProjectBlockDTO(
                        id=b.id,
                        project_id=b.project_id,
                        sequence=b.sequence,
                        speaker_name=b.speaker_name,
                        voice_id=b.voice_id,
                        emotion=b.emotion,
                        text=b.text,
                        speed=b.speed,
                        pitch=b.pitch,
                        duration_sec=b.duration_sec,
                        audio_path=b.audio_path,
                    )
                    for b in blocks
                ],
            )
        )
    return output


@router.post("", response_model=ProjectDTO)
@router.post("/", response_model=ProjectDTO)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Membuat proyek baru."""
    proj_id = f"proj_{uuid.uuid4().hex[:10]}"
    now = datetime.utcnow()
    project = Project(
        id=proj_id,
        title=data.title,
        description=data.description,
        total_duration_sec=0.0,
        final_audio_path=None,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    await db.commit()

    return ProjectDTO(
        id=project.id,
        title=project.title,
        description=project.description,
        total_duration_sec=0.0,
        final_audio_url=None,
        created_at=project.created_at,
        blocks=[],
    )


@router.get("/{project_id}", response_model=ProjectDTO)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Mengambil detail proyek dan seluruh blok dialognya."""
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    b_stmt = (
        select(ProjectBlock)
        .where(ProjectBlock.project_id == project_id)
        .order_by(ProjectBlock.sequence.asc())
    )
    b_res = await db.execute(b_stmt)
    blocks = b_res.scalars().all()

    return ProjectDTO(
        id=project.id,
        title=project.title,
        description=project.description,
        total_duration_sec=project.total_duration_sec,
        final_audio_url=f"/api/projects/{project.id}/audio"
        if project.final_audio_path
        else None,
        created_at=project.created_at,
        blocks=[
            ProjectBlockDTO(
                id=b.id,
                project_id=b.project_id,
                sequence=b.sequence,
                speaker_name=b.speaker_name,
                voice_id=b.voice_id,
                emotion=b.emotion,
                text=b.text,
                speed=b.speed,
                pitch=b.pitch,
                duration_sec=b.duration_sec,
                audio_path=b.audio_path,
            )
            for b in blocks
        ],
    )


@router.post("/{project_id}/blocks", response_model=ProjectBlockDTO)
async def add_project_block(
    project_id: str, data: ProjectBlockCreate, db: AsyncSession = Depends(get_db)
):
    """Menambahkan baris/blok dialog baru ke dalam proyek."""
    p_stmt = select(Project).where(Project.id == project_id)
    p_res = await db.execute(p_stmt)
    if not p_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    # Hitung urutan terakhir
    b_stmt = (
        select(ProjectBlock)
        .where(ProjectBlock.project_id == project_id)
        .order_by(ProjectBlock.sequence.desc())
    )
    b_res = await db.execute(b_stmt)
    last_block = b_res.scalars().first()
    next_seq = (last_block.sequence + 1) if last_block else 1

    block_id = f"blk_{uuid.uuid4().hex[:10]}"
    new_block = ProjectBlock(
        id=block_id,
        project_id=project_id,
        sequence=next_seq,
        speaker_name=data.speaker_name,
        voice_id=data.voice_id,
        emotion=data.emotion,
        text=data.text,
        speed=data.speed,
        pitch=data.pitch,
        duration_sec=0.0,
        audio_path=None,
        created_at=datetime.utcnow(),
    )
    db.add(new_block)
    await db.commit()

    return ProjectBlockDTO(
        id=new_block.id,
        project_id=new_block.project_id,
        sequence=new_block.sequence,
        speaker_name=new_block.speaker_name,
        voice_id=new_block.voice_id,
        emotion=new_block.emotion,
        text=new_block.text,
        speed=new_block.speed,
        pitch=new_block.pitch,
        duration_sec=0.0,
        audio_path=None,
    )


@router.delete("/{project_id}/blocks/{block_id}")
async def delete_project_block(
    project_id: str, block_id: str, db: AsyncSession = Depends(get_db)
):
    """Menghapus blok dialog dari proyek."""
    stmt = select(ProjectBlock).where(
        ProjectBlock.id == block_id, ProjectBlock.project_id == project_id
    )
    res = await db.execute(stmt)
    block = res.scalar_one_or_none()
    if not block:
        raise HTTPException(status_code=404, detail="Blok tidak ditemukan.")

    await db.delete(block)
    await db.commit()
    return {"message": "Blok dialog berhasil dihapus."}


@router.post("/{project_id}/render", response_model=ProjectDTO)
async def render_project_dialogue(project_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fitur Render Gabungan Dialog Multi-Speaker:
    1. Menyintesis tiap blok teks dengan Voice ID & Emosi masing-masing pembicara.
    2. Menyambung seluruh audio blok secara berurutan dengan equal-power crossfade (40ms).
    3. Menerapkan mastering audio & menyematkan metadata AI "Dibuat dengan AI".
    4. Mengembalikan ProjectDTO lengkap dengan URL audio final.
    """
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    b_stmt = (
        select(ProjectBlock)
        .where(ProjectBlock.project_id == project_id)
        .order_by(ProjectBlock.sequence.asc())
    )
    b_res = await db.execute(b_stmt)
    blocks = b_res.scalars().all()
    if not blocks:
        raise HTTPException(
            status_code=400, detail="Proyek belum memiliki blok dialog untuk dirender."
        )

    proj_dir = PROJECTS_AUDIO_DIR / project_id
    proj_dir.mkdir(parents=True, exist_ok=True)

    block_wavs: list[Path] = []

    # 1. Sintesis tiap blok dengan karakter & ekspresi masing-masing
    for b in blocks:
        block_wav = proj_dir / f"{b.id}.wav"
        pipeline_res = await run_synthesis_pipeline(
            text=b.text,
            voice_id=b.voice_id,
            speed=b.speed,
            pitch=b.pitch,
            emotion=b.emotion,
            audio_effect="none",
            job_id=f"blk_render_{b.id}",
        )
        # Salin hasil sintesis ke folder proyek
        shutil_src = pipeline_res.audio_path
        if shutil_src.exists() and shutil_src != block_wav:
            import shutil

            shutil.copy(shutil_src, block_wav)

        b.duration_sec = pipeline_res.duration_sec
        b.audio_path = str(block_wav)
        block_wavs.append(block_wav)

    # 2. Penggabungan Audio Multi-Speaker dengan Equal-Power Crossfade
    merged_raw_wav = proj_dir / "merged_raw.wav"
    merge_wav_files_with_crossfade(
        block_wavs, merged_raw_wav, crossfade_ms=40, sample_rate=22050
    )

    # 3. Mastering Audio Standar Siaran & Filter
    final_output_wav = PROJECTS_AUDIO_DIR / f"{project_id}_final.wav"
    apply_audio_effects_ffmpeg(
        input_wav=merged_raw_wav,
        output_wav=final_output_wav,
        effect="none",
        normalize_lufs=True,
        apply_deesser=True,
        sample_rate=22050,
    )

    # 4. Sematkan Label Etika AI di Metadata Audio
    if settings.EMBED_AI_LABEL:
        embed_ai_disclosure_metadata(
            final_output_wav,
            comment=f"Dibuat dengan AI - TaSTP Multi-Speaker Dialogue ({project.title})",
        )

    # Hitung durasi total final
    import wave

    with wave.open(str(final_output_wav), "rb") as wf:
        total_duration = wf.getnframes() / float(wf.getframerate())

    project.final_audio_path = str(final_output_wav)
    project.total_duration_sec = total_duration
    project.updated_at = datetime.utcnow()
    await db.commit()

    return ProjectDTO(
        id=project.id,
        title=project.title,
        description=project.description,
        total_duration_sec=project.total_duration_sec,
        final_audio_url=f"/api/projects/{project.id}/audio",
        created_at=project.created_at,
        blocks=[
            ProjectBlockDTO(
                id=b.id,
                project_id=b.project_id,
                sequence=b.sequence,
                speaker_name=b.speaker_name,
                voice_id=b.voice_id,
                emotion=b.emotion,
                text=b.text,
                speed=b.speed,
                pitch=b.pitch,
                duration_sec=b.duration_sec,
                audio_path=b.audio_path,
            )
            for b in blocks
        ],
    )


@router.get("/{project_id}/audio")
async def get_project_audio(project_id: str, db: AsyncSession = Depends(get_db)):
    """Mengambil audio final WAV hasil gabungan seluruh dialog proyek."""
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project or not project.final_audio_path:
        raise HTTPException(status_code=404, detail="Audio proyek belum dirender.")

    audio_file = Path(project.final_audio_path)
    if not audio_file.exists():
        raise HTTPException(status_code=404, detail="File audio fisik tidak ditemukan.")

    return FileResponse(
        audio_file,
        media_type="audio/wav",
        filename=f"tastp_project_{project_id}.wav",
        headers={
            "X-Generated-By": "TaSTP-MultiSpeaker",
            "X-AI-Disclosure": settings.AI_LABEL_TEXT,
        },
    )
