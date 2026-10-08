"""
Studio Manager API Endpoints (Versi DEMO Tanpa Login / Role):
Mengelola Suara (Voices), Preset Gaya (Presets), Emosi Vokal (Emotions),
dan Kamus Pelafalan (Lexicon) secara dinamis tanpa mengubah kode.

CATATAN KEAMANAN & PRODUKSI:
# TODO [PRODUKSI]: Tambahkan JWT Authentication & RBAC (Role-Based Access Control: ADMIN/STUDIO_MANAGER).
# TODO [PRODUKSI]: Tambahkan proteksi CSRF dan rate limiting ketat pada endpoint upload model.
# TODO [PRODUKSI]: Tambahkan audit trail / log aktivitas siapa yang mengubah konfigurasi sistem.
# TODO [PRODUKSI]: Batasi ukuran file model dan kuota penyimpanan per tenant/organisasi.
# TODO [PRODUKSI]: Validasi sanitasi file biner ONNX dari injeksi tensor berbahaya.
"""

import json
import re
import shutil
import uuid
from datetime import datetime

from app.config import settings
from app.database import get_db
from app.engines.piper_engine import PiperEngine
from app.models.schema import (
    EmotionCreate,
    EmotionRecord,
    EmotionRecordDTO,
    EmotionUpdate,
    LexiconCreate,
    LexiconDTO,
    LexiconUpdate,
    StylePresetCreate,
    StylePresetDTO,
    StylePresetRecord,
    StylePresetUpdate,
    VoiceCreate,
    VoiceDTO,
    VoiceRecord,
    VoiceUpdate,
)
from app.text.lexicon import LexiconService
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/studio", tags=["Studio Manager"])

# Engine singleton untuk pengujian sintesis suara baru
_test_piper_engine = PiperEngine()


# ============================================================================
# 1. SUARA (VOICES)
# ============================================================================


@router.get("/voices", response_model=list[VoiceDTO])
async def list_studio_voices(db: AsyncSession = Depends(get_db)):
    """Mengambil semua daftar suara untuk Studio Manager (termasuk yang nonaktif)."""
    # TODO [PRODUKSI]: Verifikasi token autentikasi staf/admin studio
    stmt = select(VoiceRecord).order_by(VoiceRecord.created_at.desc())
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


@router.post("/voices", response_model=VoiceDTO, status_code=status.HTTP_201_CREATED)
async def create_studio_voice(payload: VoiceCreate, db: AsyncSession = Depends(get_db)):
    """Menambahkan metadata suara baru secara manual."""
    # TODO [PRODUKSI]: Hanya role ADMIN/STUDIO_MANAGER yang boleh menambah suara
    voice_id = payload.id or f"voice_{uuid.uuid4().hex[:8]}"

    # Cek duplikasi ID
    existing = await db.execute(select(VoiceRecord).where(VoiceRecord.id == voice_id))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Suara dengan ID '{voice_id}' sudah terdaftar.",
        )

    record = VoiceRecord(
        id=voice_id,
        name=payload.name,
        gender=payload.gender,
        language=payload.language,
        category=payload.category,
        description=payload.description,
        engine=payload.engine,
        model_path=str(settings.MODELS_DIR / f"{voice_id}.onnx"),
        sample_rate=payload.sample_rate,
        is_cloned=payload.is_cloned,
        is_active=payload.is_active,
        created_at=datetime.utcnow(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return VoiceDTO(
        id=record.id,
        name=record.name,
        gender=record.gender,
        language=record.language,
        category=record.category,
        description=record.description or "",
        engine=record.engine,
        sample_rate=record.sample_rate,
        is_cloned=record.is_cloned,
        is_active=record.is_active,
        preview_url=record.preview_audio_url,
    )


@router.put("/voices/{voice_id}", response_model=VoiceDTO)
async def update_studio_voice(
    voice_id: str, payload: VoiceUpdate, db: AsyncSession = Depends(get_db)
):
    """Memperbarui metadata suara atau mengubah status aktif/nonaktif."""
    # TODO [PRODUKSI]: Cek authorization token
    stmt = select(VoiceRecord).where(VoiceRecord.id == voice_id)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suara dengan ID '{voice_id}' tidak ditemukan.",
        )

    if payload.name is not None:
        record.name = payload.name
    if payload.gender is not None:
        record.gender = payload.gender
    if payload.language is not None:
        record.language = payload.language
    if payload.category is not None:
        record.category = payload.category
    if payload.description is not None:
        record.description = payload.description
    if payload.is_active is not None:
        record.is_active = payload.is_active

    await db.commit()
    await db.refresh(record)

    return VoiceDTO(
        id=record.id,
        name=record.name,
        gender=record.gender,
        language=record.language,
        category=record.category,
        description=record.description or "",
        engine=record.engine,
        sample_rate=record.sample_rate,
        is_cloned=record.is_cloned,
        is_active=record.is_active,
        preview_url=record.preview_audio_url,
    )


@router.delete("/voices/{voice_id}", status_code=status.HTTP_200_OK)
async def delete_studio_voice(voice_id: str, db: AsyncSession = Depends(get_db)):
    """Menghapus rekaman suara dari Studio Manager."""
    # TODO [PRODUKSI]: Cek authorization token & jangan izinkan hapus suara sistem inti
    stmt = select(VoiceRecord).where(VoiceRecord.id == voice_id)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suara dengan ID '{voice_id}' tidak ditemukan.",
        )

    await db.delete(record)
    await db.commit()
    return {"message": f"Suara '{voice_id}' berhasil dihapus.", "id": voice_id}


@router.post(
    "/voices/upload", response_model=VoiceDTO, status_code=status.HTTP_201_CREATED
)
async def upload_custom_voice_model(
    model_file: UploadFile = File(..., description="File model biner Piper .onnx"),
    config_file: UploadFile = File(..., description="File konfigurasi JSON .json"),
    name: str = Form(..., min_length=2, max_length=100),
    gender: str = Form(default="female"),
    language: str = Form(default="id-ID"),
    category: str = Form(default="custom"),
    description: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    """
    Mengunggah model suara Piper (.onnx + .json), memvalidasi ekstensi dan file,
    lalu menjalankan uji sintesis satu kalimat secara otomatis.
    Jika sintesis gagal, file dihapus dan pesan error informatif ditampilkan.
    """
    # TODO [PRODUKSI]: Validasi kuota penyimpanan disk dan scan antivirus/clamav
    # 1. Validasi Ekstensi File
    model_filename = model_file.filename or ""
    config_filename = config_file.filename or ""

    if not model_filename.lower().endswith(".onnx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File model harus berekstensi .onnx (format ONNX Piper TTS).",
        )

    if not config_filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File konfigurasi harus berekstensi .json (Piper configuration JSON).",
        )

    # 2. Siapkan ID Suara Unik
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", name.lower().strip())
    voice_id = f"custom_{slug}_{uuid.uuid4().hex[:6]}"

    # Pastikan direktori tujuan tersedia
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    target_onnx = settings.MODELS_DIR / f"{voice_id}.onnx"
    target_json = settings.MODELS_DIR / f"{voice_id}.onnx.json"

    # 3. Simpan File Sementara
    try:
        with open(target_onnx, "wb") as f_onnx:
            shutil.copyfileobj(model_file.file, f_onnx)

        with open(target_json, "wb") as f_json:
            shutil.copyfileobj(config_file.file, f_json)
    except Exception as e:
        target_onnx.unlink(missing_ok=True)
        target_json.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menyimpan berkas model ke disk: {e}",
        )

    # 4. Validasi Isi File JSON
    try:
        with open(target_json, "r", encoding="utf-8") as f_json_read:
            cfg_data = json.load(f_json_read)
        if not isinstance(cfg_data, dict):
            raise ValueError("Konten JSON harus berupa objek dictionary.")
    except Exception as e:
        target_onnx.unlink(missing_ok=True)
        target_json.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File konfigurasi JSON tidak valid: {e}",
        )

    # 5. Uji Sintesis Satu Kalimat
    test_sentence = f"Halo, suara {name} berhasil dipasang di TaSTP."
    test_output_wav = settings.AUDIO_OUTPUT_DIR / f"test_{voice_id}.wav"
    settings.AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        duration = await _test_piper_engine.synthesize(
            text=test_sentence,
            output_path=test_output_wav,
            voice_id=voice_id,
            speed=1.0,
            pitch=0.0,
        )
        if (
            duration <= 0
            or not test_output_wav.exists()
            or test_output_wav.stat().st_size < 100
        ):
            raise RuntimeError("Hasil audio uji sintesis kosong atau durasi 0 detik.")
    except Exception as err:
        # Bersihkan file jika gagal uji sintesis
        target_onnx.unlink(missing_ok=True)
        target_json.unlink(missing_ok=True)
        test_output_wav.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Uji sintesis kalimat gagal: {err}. "
                "Pastikan model ONNX cocok dengan arsitektur Piper VITS dan file JSON sesuai format."
            ),
        )

    # 6. Simpan Metadata Suara ke Database
    preview_url = f"/api/audio/test_{voice_id}.wav"
    voice_rec = VoiceRecord(
        id=voice_id,
        name=name,
        gender=gender,
        language=language,
        category=category,
        description=description or f"Model kustom diunggah via Studio Manager ({name})",
        engine="piper",
        model_path=str(target_onnx),
        sample_rate=cfg_data.get("audio", {}).get("sample_rate", 22050),
        is_cloned=False,
        is_active=True,
        preview_audio_url=preview_url,
        created_at=datetime.utcnow(),
    )
    db.add(voice_rec)
    await db.commit()
    await db.refresh(voice_rec)

    return VoiceDTO(
        id=voice_rec.id,
        name=voice_rec.name,
        gender=voice_rec.gender,
        language=voice_rec.language,
        category=voice_rec.category,
        description=voice_rec.description or "",
        engine=voice_rec.engine,
        sample_rate=voice_rec.sample_rate,
        is_cloned=voice_rec.is_cloned,
        is_active=voice_rec.is_active,
        preview_url=voice_rec.preview_audio_url,
    )


# ============================================================================
# 2. PRESET GAYA (PRESETS)
# ============================================================================


@router.get("/presets", response_model=list[StylePresetDTO])
async def list_studio_presets(db: AsyncSession = Depends(get_db)):
    """Mengambil seluruh preset gaya vokal (termasuk nonaktif)."""
    # TODO [PRODUKSI]: Cek token autentikasi
    stmt = select(StylePresetRecord).order_by(StylePresetRecord.created_at.desc())
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        StylePresetDTO(
            id=r.id,
            name=r.name,
            category=r.category,
            voice_id=r.voice_id,
            speed=r.speed,
            pitch=r.pitch,
            pause_scale=r.pause_scale,
            audio_effect=r.audio_effect,
            emotion=r.emotion,
            emotion_intensity=r.emotion_intensity,
            description=r.description or "",
            is_active=r.is_active,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.post(
    "/presets", response_model=StylePresetDTO, status_code=status.HTTP_201_CREATED
)
async def create_studio_preset(
    payload: StylePresetCreate, db: AsyncSession = Depends(get_db)
):
    """Menambahkan preset gaya vokal baru."""
    # TODO [PRODUKSI]: Validasi otorisasi pengguna
    preset_id = payload.id or f"preset_{uuid.uuid4().hex[:8]}"

    existing = await db.execute(
        select(StylePresetRecord).where(StylePresetRecord.id == preset_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preset dengan ID '{preset_id}' sudah ada.",
        )

    rec = StylePresetRecord(
        id=preset_id,
        name=payload.name,
        category=payload.category,
        voice_id=payload.voice_id,
        speed=payload.speed,
        pitch=payload.pitch,
        pause_scale=payload.pause_scale,
        audio_effect=payload.audio_effect,
        emotion=payload.emotion,
        emotion_intensity=payload.emotion_intensity,
        description=payload.description,
        is_active=payload.is_active,
        created_at=datetime.utcnow(),
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)

    return StylePresetDTO(
        id=rec.id,
        name=rec.name,
        category=rec.category,
        voice_id=rec.voice_id,
        speed=rec.speed,
        pitch=rec.pitch,
        pause_scale=rec.pause_scale,
        audio_effect=rec.audio_effect,
        emotion=rec.emotion,
        emotion_intensity=rec.emotion_intensity,
        description=rec.description or "",
        is_active=rec.is_active,
        created_at=rec.created_at,
    )


@router.put("/presets/{preset_id}", response_model=StylePresetDTO)
async def update_studio_preset(
    preset_id: str, payload: StylePresetUpdate, db: AsyncSession = Depends(get_db)
):
    """Memperbarui parameter atau status aktif preset gaya vokal."""
    # TODO [PRODUKSI]: Cek token autentikasi
    stmt = select(StylePresetRecord).where(StylePresetRecord.id == preset_id)
    res = await db.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset dengan ID '{preset_id}' tidak ditemukan.",
        )

    if payload.name is not None:
        rec.name = payload.name
    if payload.category is not None:
        rec.category = payload.category
    if payload.voice_id is not None:
        rec.voice_id = payload.voice_id
    if payload.speed is not None:
        rec.speed = payload.speed
    if payload.pitch is not None:
        rec.pitch = payload.pitch
    if payload.pause_scale is not None:
        rec.pause_scale = payload.pause_scale
    if payload.audio_effect is not None:
        rec.audio_effect = payload.audio_effect
    if payload.emotion is not None:
        rec.emotion = payload.emotion
    if payload.emotion_intensity is not None:
        rec.emotion_intensity = payload.emotion_intensity
    if payload.description is not None:
        rec.description = payload.description
    if payload.is_active is not None:
        rec.is_active = payload.is_active

    await db.commit()
    await db.refresh(rec)

    return StylePresetDTO(
        id=rec.id,
        name=rec.name,
        category=rec.category,
        voice_id=rec.voice_id,
        speed=rec.speed,
        pitch=rec.pitch,
        pause_scale=rec.pause_scale,
        audio_effect=rec.audio_effect,
        emotion=rec.emotion,
        emotion_intensity=rec.emotion_intensity,
        description=rec.description or "",
        is_active=rec.is_active,
        created_at=rec.created_at,
    )


@router.delete("/presets/{preset_id}", status_code=status.HTTP_200_OK)
async def delete_studio_preset(preset_id: str, db: AsyncSession = Depends(get_db)):
    """Menghapus preset gaya vokal."""
    # TODO [PRODUKSI]: Cek authorization token
    stmt = select(StylePresetRecord).where(StylePresetRecord.id == preset_id)
    res = await db.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset dengan ID '{preset_id}' tidak ditemukan.",
        )

    await db.delete(rec)
    await db.commit()
    return {"message": f"Preset '{preset_id}' berhasil dihapus.", "id": preset_id}


# ============================================================================
# 3. EMOSI VOKAL (EMOTIONS)
# ============================================================================


@router.get("/emotions", response_model=list[EmotionRecordDTO])
async def list_studio_emotions(db: AsyncSession = Depends(get_db)):
    """Mengambil katalog semua emosi vokal (termasuk nonaktif)."""
    # TODO [PRODUKSI]: Cek token autentikasi
    stmt = select(EmotionRecord).order_by(EmotionRecord.category, EmotionRecord.name)
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        EmotionRecordDTO(
            id=r.id,
            name=r.name,
            category=r.category,
            speed=r.speed,
            pitch=r.pitch,
            pause_scale=r.pause_scale,
            effect=r.effect,
            color=r.color,
            description=r.description or "",
            is_active=r.is_active,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.post(
    "/emotions", response_model=EmotionRecordDTO, status_code=status.HTTP_201_CREATED
)
async def create_studio_emotion(
    payload: EmotionCreate, db: AsyncSession = Depends(get_db)
):
    """Menambahkan emosi vokal baru dan mendaftarkannya ke runtime prosodi."""
    # TODO [PRODUKSI]: Otorisasi staf studio
    clean_id = re.sub(r"[^a-zA-Z0-9_-]", "_", payload.id.lower().strip())
    existing = await db.execute(
        select(EmotionRecord).where(EmotionRecord.id == clean_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Emosi dengan ID '{clean_id}' sudah terdaftar.",
        )

    rec = EmotionRecord(
        id=clean_id,
        name=payload.name,
        category=payload.category,
        speed=payload.speed,
        pitch=payload.pitch,
        pause_scale=payload.pause_scale,
        effect=payload.effect,
        color=payload.color,
        description=payload.description,
        is_active=payload.is_active,
        created_at=datetime.utcnow(),
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)

    # Sinkronisasi ke runtime katalog emosi
    from app.emotion.presets import EmotionPreset, register_emotion_preset

    register_emotion_preset(
        EmotionPreset(
            id=rec.id,
            name=rec.name,
            category=rec.category,
            speed=rec.speed,
            pitch=rec.pitch,
            pause_scale=rec.pause_scale,
            effect=rec.effect,
            color=rec.color,
            description=rec.description or "",
            is_active=rec.is_active,
        )
    )

    return EmotionRecordDTO(
        id=rec.id,
        name=rec.name,
        category=rec.category,
        speed=rec.speed,
        pitch=rec.pitch,
        pause_scale=rec.pause_scale,
        effect=rec.effect,
        color=rec.color,
        description=rec.description or "",
        is_active=rec.is_active,
        created_at=rec.created_at,
    )


@router.put("/emotions/{emotion_id}", response_model=EmotionRecordDTO)
async def update_studio_emotion(
    emotion_id: str, payload: EmotionUpdate, db: AsyncSession = Depends(get_db)
):
    """Memperbarui parameter atau status aktif emosi vokal."""
    # TODO [PRODUKSI]: Cek token autentikasi
    stmt = select(EmotionRecord).where(EmotionRecord.id == emotion_id)
    res = await db.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emosi dengan ID '{emotion_id}' tidak ditemukan.",
        )

    if payload.name is not None:
        rec.name = payload.name
    if payload.category is not None:
        rec.category = payload.category
    if payload.speed is not None:
        rec.speed = payload.speed
    if payload.pitch is not None:
        rec.pitch = payload.pitch
    if payload.pause_scale is not None:
        rec.pause_scale = payload.pause_scale
    if payload.effect is not None:
        rec.effect = payload.effect
    if payload.color is not None:
        rec.color = payload.color
    if payload.description is not None:
        rec.description = payload.description
    if payload.is_active is not None:
        rec.is_active = payload.is_active

    await db.commit()
    await db.refresh(rec)

    # Sinkronisasi ke runtime katalog emosi
    from app.emotion.presets import EmotionPreset, register_emotion_preset

    register_emotion_preset(
        EmotionPreset(
            id=rec.id,
            name=rec.name,
            category=rec.category,
            speed=rec.speed,
            pitch=rec.pitch,
            pause_scale=rec.pause_scale,
            effect=rec.effect,
            color=rec.color,
            description=rec.description or "",
            is_active=rec.is_active,
        )
    )

    return EmotionRecordDTO(
        id=rec.id,
        name=rec.name,
        category=rec.category,
        speed=rec.speed,
        pitch=rec.pitch,
        pause_scale=rec.pause_scale,
        effect=rec.effect,
        color=rec.color,
        description=rec.description or "",
        is_active=rec.is_active,
        created_at=rec.created_at,
    )


@router.delete("/emotions/{emotion_id}", status_code=status.HTTP_200_OK)
async def delete_studio_emotion(emotion_id: str, db: AsyncSession = Depends(get_db)):
    """Menghapus emosi vokal (kecuali neutral standar)."""
    # TODO [PRODUKSI]: Cek authorization token
    if emotion_id == "neutral":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emosi 'neutral' adalah baseline sistem dan tidak boleh dihapus.",
        )

    stmt = select(EmotionRecord).where(EmotionRecord.id == emotion_id)
    res = await db.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emosi dengan ID '{emotion_id}' tidak ditemukan.",
        )

    await db.delete(rec)
    await db.commit()

    from app.emotion.presets import unregister_emotion_preset

    unregister_emotion_preset(emotion_id)

    return {"message": f"Emosi '{emotion_id}' berhasil dihapus.", "id": emotion_id}


# ============================================================================
# 4. KAMUS PELAFALAN (LEXICON)
# ============================================================================


@router.get("/lexicon", response_model=list[LexiconDTO])
async def list_studio_lexicon(
    voice_id: str | None = None, db: AsyncSession = Depends(get_db)
):
    """Mengambil seluruh entri kamus pelafalan (aktif & nonaktif)."""
    # TODO [PRODUKSI]: Cek token autentikasi
    records = await LexiconService.get_all_entries(
        db, voice_id=voice_id, active_only=False
    )
    return [
        LexiconDTO(
            id=r.id,
            word=r.word,
            replacement=r.replacement,
            voice_id=r.voice_id,
            is_regex=r.is_regex,
            is_active=r.is_active,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.post("/lexicon", response_model=LexiconDTO, status_code=status.HTTP_201_CREATED)
async def create_studio_lexicon_entry(
    payload: LexiconCreate, db: AsyncSession = Depends(get_db)
):
    """Menambahkan kata baru ke kamus pelafalan."""
    # TODO [PRODUKSI]: Otorisasi staf studio
    entry = await LexiconService.create_entry(payload, db)
    return LexiconDTO(
        id=entry.id,
        word=entry.word,
        replacement=entry.replacement,
        voice_id=entry.voice_id,
        is_regex=entry.is_regex,
        is_active=entry.is_active,
        created_at=entry.created_at,
    )


@router.put("/lexicon/{entry_id}", response_model=LexiconDTO)
async def update_studio_lexicon_entry(
    entry_id: str, payload: LexiconUpdate, db: AsyncSession = Depends(get_db)
):
    """Memperbarui aturan kata atau status aktif di kamus pelafalan."""
    # TODO [PRODUKSI]: Cek token autentikasi
    entry = await LexiconService.update_entry(entry_id, payload, db)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entri kamus dengan ID '{entry_id}' tidak ditemukan.",
        )

    return LexiconDTO(
        id=entry.id,
        word=entry.word,
        replacement=entry.replacement,
        voice_id=entry.voice_id,
        is_regex=entry.is_regex,
        is_active=entry.is_active,
        created_at=entry.created_at,
    )


@router.delete("/lexicon/{entry_id}", status_code=status.HTTP_200_OK)
async def delete_studio_lexicon_entry(
    entry_id: str, db: AsyncSession = Depends(get_db)
):
    """Menghapus entri kata dari kamus pelafalan."""
    # TODO [PRODUKSI]: Cek token autentikasi
    success = await LexiconService.delete_entry(entry_id, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entri kamus dengan ID '{entry_id}' tidak ditemukan.",
        )

    return {"message": f"Entri kamus '{entry_id}' berhasil dihapus.", "id": entry_id}
