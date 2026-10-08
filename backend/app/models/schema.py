from datetime import datetime
from typing import Any

from app.database import Base
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

# ========================
# SQLAlchemy Models
# ========================


class SynthesisJob(Base):
    __tablename__ = "synthesis_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    voice_id: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_name: Mapped[str] = mapped_column(String(32), default="piper")
    speed: Mapped[float] = mapped_column(Float, default=1.0)
    pitch: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(
        String(20), default="queued"
    )  # queued, processing, completed, failed
    audio_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_cloned: Mapped[bool] = mapped_column(Boolean, default=False)
    has_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VoiceRecord(Base):
    __tablename__ = "voice_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str] = mapped_column(String(20), default="female")  # male, female
    language: Mapped[str] = mapped_column(String(20), default="id-ID")
    category: Mapped[str] = mapped_column(
        String(50), default="content_creator"
    )  # creator, narrator, podcast, news
    description: Mapped[str] = mapped_column(String(255), default="")
    engine: Mapped[str] = mapped_column(String(32), default="piper")
    model_path: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    config_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sample_rate: Mapped[int] = mapped_column(Integer, default=22050)
    is_cloned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    preview_audio_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class StylePresetRecord(Base):
    __tablename__ = "style_presets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general")
    voice_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    speed: Mapped[float] = mapped_column(Float, default=1.0)
    pitch: Mapped[float] = mapped_column(Float, default=0.0)
    pause_scale: Mapped[float] = mapped_column(Float, default=1.0)
    audio_effect: Mapped[str] = mapped_column(String(50), default="none")
    emotion: Mapped[str] = mapped_column(String(50), default="neutral")
    emotion_intensity: Mapped[float] = mapped_column(Float, default=100.0)
    description: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EmotionRecord(Base):
    __tablename__ = "emotion_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="dasar")
    speed: Mapped[float] = mapped_column(Float, default=1.0)
    pitch: Mapped[float] = mapped_column(Float, default=0.0)
    pause_scale: Mapped[float] = mapped_column(Float, default=1.0)
    effect: Mapped[str] = mapped_column(String(50), default="none")
    color: Mapped[str] = mapped_column(String(20), default="#94a3b8")
    description: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LexiconEntry(Base):
    __tablename__ = "lexicon"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    word: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    replacement: Mapped[str] = mapped_column(String(150), nullable=False)
    voice_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_regex: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VoiceCloneLog(Base):
    __tablename__ = "voice_clone_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    voice_name: Mapped[str] = mapped_column(String(100), nullable=False)
    speaker_name: Mapped[str] = mapped_column(String(100), nullable=False)
    consent_checkbox: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_text: Mapped[str] = mapped_column(Text, nullable=False)
    sample_path: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    final_audio_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProjectBlock(Base):
    __tablename__ = "project_blocks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    speaker_name: Mapped[str] = mapped_column(String(100), default="Narator")
    voice_id: Mapped[str] = mapped_column(String(64), default="id_ID-news_tts-medium")
    emotion: Mapped[str] = mapped_column(String(64), default="neutral")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    speed: Mapped[float] = mapped_column(Float, default=1.0)
    pitch: Mapped[float] = mapped_column(Float, default=0.0)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    audio_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ========================
# Pydantic Request/Response
# ========================


class VoiceDTO(BaseModel):
    id: str
    name: str
    gender: str
    language: str
    category: str
    description: str
    engine: str
    sample_rate: int
    is_cloned: bool = False
    is_active: bool = True
    preview_url: str | None = None


class VoiceCreate(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(default="female")
    language: str = Field(default="id-ID")
    category: str = Field(default="creator")
    description: str = Field(default="")
    engine: str = Field(default="piper")
    sample_rate: int = Field(default=22050)
    is_cloned: bool = False
    is_active: bool = True


class VoiceUpdate(BaseModel):
    name: str | None = None
    gender: str | None = None
    language: str | None = None
    category: str | None = None
    description: str | None = None
    is_active: bool | None = None


class StylePresetDTO(BaseModel):
    id: str
    name: str
    category: str
    voice_id: str | None = None
    speed: float = 1.0
    pitch: float = 0.0
    pause_scale: float = 1.0
    audio_effect: str = "none"
    emotion: str = "neutral"
    emotion_intensity: float = 100.0
    description: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StylePresetCreate(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(default="general")
    voice_id: str | None = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-10.0, le=10.0)
    pause_scale: float = Field(default=1.0, ge=0.5, le=2.0)
    audio_effect: str = Field(default="none")
    emotion: str = Field(default="neutral")
    emotion_intensity: float = Field(default=100.0, ge=0.0, le=100.0)
    description: str = Field(default="")
    is_active: bool = True


class StylePresetUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    voice_id: str | None = None
    speed: float | None = None
    pitch: float | None = None
    pause_scale: float | None = None
    audio_effect: str | None = None
    emotion: str | None = None
    emotion_intensity: float | None = None
    description: str | None = None
    is_active: bool | None = None


class EmotionRecordDTO(BaseModel):
    id: str
    name: str
    category: str
    speed: float
    pitch: float
    pause_scale: float
    effect: str = "none"
    color: str = "#94a3b8"
    description: str = ""
    is_active: bool = True
    created_at: datetime


class EmotionCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(default="dasar")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-10.0, le=10.0)
    pause_scale: float = Field(default=1.0, ge=0.5, le=2.0)
    effect: str = Field(default="none")
    color: str = Field(default="#94a3b8")
    description: str = Field(default="")
    is_active: bool = True


class EmotionUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    speed: float | None = None
    pitch: float | None = None
    pause_scale: float | None = None
    effect: str | None = None
    color: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SynthesizeRequest(BaseModel):
    text: str = Field(
        ..., min_length=1, max_length=5000, description="Naskah teks untuk disintesis"
    )
    voice_id: str = Field(..., description="ID suara yang dipilih")
    speed: float = Field(
        default=1.0, ge=0.5, le=2.0, description="Kecepatan bicara (0.5x - 2.0x)"
    )
    pitch: float = Field(
        default=0.0, ge=-10.0, le=10.0, description="Tinggi rendah nada"
    )
    audio_effect: str | None = Field(
        default="none",
        description="Efek audio server: none, podcast_eq, radio, hall, telephone, whisper, reverb",
    )
    emotion: str | None = Field(
        default="neutral", description="Emosi vokal (atau 'auto' untuk auto-detect)"
    )
    emotion_intensity: float | None = Field(
        default=100.0, ge=0.0, le=100.0, description="Intensitas emosi 0-100"
    )
    pause_scale: float | None = Field(
        default=1.0, ge=0.5, le=2.0, description="Durasi jeda koma & titik"
    )
    sentence_emotions: list[str] | None = Field(
        default=None, description="Daftar ID emosi per kalimat"
    )
    is_cloned_voice: bool = Field(default=False)
    voice_clone_consent: bool = Field(
        default=False, description="Wajib disetujui jika memakai klon suara"
    )
    engine: str | None = Field(
        default=None, description="Engine yang dipilih: piper atau remote"
    )


class SynthesizeResponse(BaseModel):
    job_id: str
    status: str
    audio_url: str | None = None
    duration_sec: float = 0.0
    engine_used: str
    first_sentence_time_ms: float | None = None
    created_at: datetime
    message: str | None = None


class JobStatusResponse(BaseModel):
    id: str
    status: str
    audio_url: str | None = None
    duration_sec: float
    error_message: str | None = None
    created_at: datetime


class LexiconDTO(BaseModel):
    id: str
    word: str
    replacement: str
    voice_id: str | None = None
    is_regex: bool = False
    is_active: bool = True
    created_at: datetime


class LexiconCreate(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)
    replacement: str = Field(..., min_length=1, max_length=150)
    voice_id: str | None = None
    is_regex: bool = False
    is_active: bool = True


class LexiconUpdate(BaseModel):
    word: str | None = None
    replacement: str | None = None
    voice_id: str | None = None
    is_regex: bool | None = None
    is_active: bool | None = None


class VoiceCloneResponse(BaseModel):
    id: str
    voice_name: str
    speaker_name: str
    sample_duration_sec: float
    consent_recorded: bool
    created_at: datetime
    message: str
    quality: dict[str, Any] | None = None
    engine: str = "piper"
    audio_preview_url: str | None = None


class VoiceCompareABRequest(BaseModel):
    voice_id: str
    baseline_voice_id: str = "id_ID-news_tts-medium"
    text: str = Field(
        default="Halo, ini adalah pengujian perbandingan suara hasil kloning saya melawan suara default Piper.",
        min_length=3,
        max_length=500,
    )


class VoiceCompareABResponse(BaseModel):
    text: str
    sample_a: dict[str, Any]
    sample_b: dict[str, Any]


class ProjectBlockDTO(BaseModel):
    id: str
    project_id: str
    sequence: int
    speaker_name: str
    voice_id: str
    emotion: str
    text: str
    speed: float
    pitch: float
    duration_sec: float
    audio_path: str | None = None


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str | None = None


class ProjectBlockCreate(BaseModel):
    speaker_name: str = Field(default="Narator", max_length=100)
    voice_id: str = Field(default="id_ID-news_tts-medium")
    emotion: str = Field(default="neutral")
    text: str = Field(..., min_length=1)
    speed: float = Field(default=1.0)
    pitch: float = Field(default=0.0)


class ProjectDTO(BaseModel):
    id: str
    title: str
    description: str | None = None
    total_duration_sec: float
    final_audio_url: str | None = None
    created_at: datetime
    blocks: list[ProjectBlockDTO] = []


class HistoryRecord(Base):
    __tablename__ = "history"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), nullable=False)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    preview_text: Mapped[str] = mapped_column(String(255), nullable=False)
    audio_url: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    voice_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class HistoryDTO(BaseModel):
    id: str
    job_id: str
    project_id: str | None = None
    title: str
    preview_text: str
    audio_url: str
    duration_sec: float
    voice_name: str
    created_at: datetime
