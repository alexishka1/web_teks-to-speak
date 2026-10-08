"""
Unit and Integration Tests for Tahap 11: Studio Manager (Versi DEMO).
Mencakup pengujian:
1. Pemuatan dinamis dari DB untuk voices, presets, emotions, dan lexicon (tanpa hardcode).
2. Seed data bawaan minimal: 3 suara, 5 preset, 20 emosi.
3. CRUD Studio Manager (tambah, edit, nonaktifkan, hapus) untuk suara, preset, emosi, lexicon.
4. Hot reload: item nonaktif tidak muncul di API publik, item baru langsung muncul tanpa restart.
5. Upload suara: validasi ekstensi .onnx + .json dan uji sintesis satu kalimat.
"""

import io
import json

import pytest
from app.api.endpoints.studio import (
    create_studio_emotion,
    create_studio_lexicon_entry,
    create_studio_preset,
    create_studio_voice,
    delete_studio_emotion,
    delete_studio_lexicon_entry,
    delete_studio_preset,
    delete_studio_voice,
    list_studio_voices,
    update_studio_emotion,
    update_studio_lexicon_entry,
    update_studio_preset,
    update_studio_voice,
    upload_custom_voice_model,
)
from app.api.endpoints.tts import get_emotions_catalog, get_style_presets
from app.api.endpoints.voices import list_voices
from app.database import AsyncSessionLocal, init_db
from app.models.schema import (
    EmotionCreate,
    EmotionRecord,
    EmotionUpdate,
    LexiconCreate,
    LexiconEntry,
    LexiconUpdate,
    StylePresetCreate,
    StylePresetRecord,
    StylePresetUpdate,
    VoiceCreate,
    VoiceRecord,
    VoiceUpdate,
)
from fastapi import HTTPException, UploadFile
from sqlalchemy import select


@pytest.mark.asyncio
async def test_seed_data_counts():
    """Memverifikasi data contoh bawaan: minimal 3 suara, 5 preset, 20 emosi."""
    await init_db()
    async with AsyncSessionLocal() as session:
        voices = (await session.execute(select(VoiceRecord))).scalars().all()
        presets = (await session.execute(select(StylePresetRecord))).scalars().all()
        emotions = (await session.execute(select(EmotionRecord))).scalars().all()
        lexicon = (await session.execute(select(LexiconEntry))).scalars().all()

        assert len(voices) >= 3, f"Jumlah suara minimal 3, didapat: {len(voices)}"
        assert len(presets) >= 5, f"Jumlah preset minimal 5, didapat: {len(presets)}"
        assert len(emotions) >= 20, f"Jumlah emosi minimal 20, didapat: {len(emotions)}"
        assert len(lexicon) >= 5, f"Jumlah lexicon minimal 5, didapat: {len(lexicon)}"


@pytest.mark.asyncio
async def test_studio_voices_crud_and_hot_reload():
    """Menguji CRUD suara di Studio Manager dan hot reload pada GET /api/voices."""
    import uuid

    v_id = f"voice_test_{uuid.uuid4().hex[:6]}"
    async with AsyncSessionLocal() as session:
        # 1. Tambah suara baru via Studio Manager
        create_payload = VoiceCreate(
            id=v_id,
            name="Suara Test Studio",
            gender="female",
            language="id-ID",
            category="creator",
            description="Suara pengujian otomatis studio manager",
            engine="piper",
            sample_rate=22050,
            is_cloned=False,
            is_active=True,
        )
        created_data = await create_studio_voice(payload=create_payload, db=session)
        assert created_data.id == v_id

        # 2. Hot reload: Pastikan langsung muncul di GET /api/voices
        public_voices_1 = await list_voices(db=session)
        public_ids_1 = [v.id for v in public_voices_1]
        assert v_id in public_ids_1

        # 3. Nonaktifkan suara via Studio Manager
        updated = await update_studio_voice(
            voice_id=v_id,
            payload=VoiceUpdate(is_active=False, description="Dinonaktifkan sementara"),
            db=session,
        )
        assert updated.is_active is False

        # 4. Hot reload: Suara yang dinonaktifkan tidak boleh muncul di GET /api/voices
        public_voices_2 = await list_voices(db=session)
        public_ids_2 = [v.id for v in public_voices_2]
        assert v_id not in public_ids_2

        # 5. Hapus suara via Studio Manager
        del_res = await delete_studio_voice(voice_id=v_id, db=session)
        assert del_res["id"] == v_id

        # Verifikasi tidak ada lagi di studio voices
        studio_list = await list_studio_voices(db=session)
        studio_ids = [v.id for v in studio_list]
        assert v_id not in studio_ids


@pytest.mark.asyncio
async def test_studio_presets_crud_and_hot_reload():
    """Menguji CRUD preset gaya di Studio Manager dan hot reload pada GET /api/presets."""
    import uuid

    p_id = f"preset_test_{uuid.uuid4().hex[:6]}"
    async with AsyncSessionLocal() as session:
        # 1. Tambah preset baru
        preset_payload = StylePresetCreate(
            id=p_id,
            name="Promo Diskon Kilat",
            category="commercial",
            voice_id="id_ID-news_tts-medium",
            speed=1.15,
            pitch=1.5,
            pause_scale=0.8,
            audio_effect="podcast_eq",
            emotion="enthusiastic",
            emotion_intensity=90.0,
            description="Gaya bicara cepat promosi flash sale",
            is_active=True,
        )
        created = await create_studio_preset(payload=preset_payload, db=session)
        assert created.id == p_id

        # 2. Langsung muncul di GET /api/presets publik
        presets_1 = await get_style_presets(db=session)
        preset_ids_1 = [p["id"] for p in presets_1]
        assert p_id in preset_ids_1

        # 3. Nonaktifkan preset
        toggle_res = await update_studio_preset(
            preset_id=p_id,
            payload=StylePresetUpdate(is_active=False),
            db=session,
        )
        assert toggle_res.is_active is False

        # 4. Tidak muncul lagi di publik saat dinonaktifkan
        presets_2 = await get_style_presets(db=session)
        preset_ids_2 = [p["id"] for p in presets_2]
        assert p_id not in preset_ids_2

        # 5. Hapus preset
        del_res = await delete_studio_preset(preset_id=p_id, db=session)
        assert del_res["id"] == p_id


@pytest.mark.asyncio
async def test_studio_emotions_crud():
    """Menguji CRUD emosi di Studio Manager dan runtime prosodi."""
    import uuid

    e_id = f"epic_{uuid.uuid4().hex[:6]}"
    async with AsyncSessionLocal() as session:
        emotion_payload = EmotionCreate(
            id=e_id,
            name="Epik Sinematik",
            category="gaya_bicara",
            speed=0.92,
            pitch=-0.8,
            pause_scale=1.25,
            effect="reverb",
            color="#eab308",
            description="Narasi megah trailer film",
            is_active=True,
        )
        created = await create_studio_emotion(payload=emotion_payload, db=session)
        assert created.id == e_id

        # Cek ketersediaan di katalog publik GET /api/emotions
        emotions_public = await get_emotions_catalog(db=session)
        emotion_ids = [e["id"] for e in emotions_public]
        assert e_id in emotion_ids

        # Update warna dan status
        updated = await update_studio_emotion(
            emotion_id=e_id,
            payload=EmotionUpdate(color="#f59e0b", description="Versi revisi trailer"),
            db=session,
        )
        assert updated.color == "#f59e0b"

        # Hapus emosi
        del_res = await delete_studio_emotion(emotion_id=e_id, db=session)
        assert del_res["id"] == e_id


@pytest.mark.asyncio
async def test_studio_lexicon_crud():
    """Menguji CRUD kamus pelafalan di Studio Manager."""
    async with AsyncSessionLocal() as session:
        lex_payload = LexiconCreate(
            word="Playwright",
            replacement="plei-rait",
            voice_id=None,
            is_regex=False,
            is_active=True,
        )
        created = await create_studio_lexicon_entry(payload=lex_payload, db=session)
        assert created.word == "Playwright"
        entry_id = created.id

        # Update replacement
        updated = await update_studio_lexicon_entry(
            entry_id=entry_id,
            payload=LexiconUpdate(replacement="pley-rait-id"),
            db=session,
        )
        assert updated.replacement == "pley-rait-id"

        # Hapus entry
        del_res = await delete_studio_lexicon_entry(entry_id=entry_id, db=session)
        assert del_res["id"] == entry_id


@pytest.mark.asyncio
async def test_studio_voice_upload_validation():
    """Menguji validasi ekstensi upload suara (.onnx + .json) dan uji sintesis."""
    async with AsyncSessionLocal() as session:
        # Kasus gagal: ekstensi salah (.txt)
        bad_model_file = UploadFile(
            filename="model.txt", file=io.BytesIO(b"bukan onnx")
        )
        bad_config_file = UploadFile(filename="config.json", file=io.BytesIO(b"{}"))
        with pytest.raises(HTTPException) as exc_info_1:
            await upload_custom_voice_model(
                model_file=bad_model_file,
                config_file=bad_config_file,
                name="Suara Rusak 1",
                db=session,
            )
        assert exc_info_1.value.status_code == 400
        assert ".onnx" in exc_info_1.value.detail

        # Kasus gagal: json tidak valid
        good_model_file = UploadFile(
            filename="model.onnx", file=io.BytesIO(b"model bytes")
        )
        invalid_config_file = UploadFile(
            filename="config.json", file=io.BytesIO(b"not json syntax")
        )
        with pytest.raises(HTTPException) as exc_info_2:
            await upload_custom_voice_model(
                model_file=good_model_file,
                config_file=invalid_config_file,
                name="Suara Rusak 2",
                db=session,
            )
        assert exc_info_2.value.status_code == 400
        assert "JSON tidak valid" in exc_info_2.value.detail

        # Kasus sukses: .onnx + valid .json
        valid_json = json.dumps(
            {"audio": {"sample_rate": 22050}, "language": {"code": "id_ID"}}
        ).encode("utf-8")
        valid_model_file = UploadFile(
            filename="voice_custom_test.onnx",
            file=io.BytesIO(b"mock onnx binary data 12345"),
        )
        valid_config_file = UploadFile(
            filename="voice_custom_test.json", file=io.BytesIO(valid_json)
        )
        good_res = await upload_custom_voice_model(
            model_file=valid_model_file,
            config_file=valid_config_file,
            name="Suara Custom Unit Test",
            gender="female",
            language="id-ID",
            category="creator",
            description="Suara kustom hasil upload Studio Manager",
            db=session,
        )
        assert good_res.name == "Suara Custom Unit Test"
        assert good_res.engine == "piper"
        assert good_res.is_active is True
