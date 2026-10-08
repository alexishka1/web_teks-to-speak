"""
Pipeline Pemrosesan Suara Lengkap TaSTP:
Teks -> Normalisasi -> Lexicon -> Split Kalimat -> Variasi Prosodi +-3-5%
-> Sintesis per Kalimat -> Equal-Power Crossfade 40ms -> Post-Processing -> Cache.
"""

import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.audio.cache import compute_cache_key, get_cached_audio, save_to_cache
from app.audio.crossfade import merge_wav_files_with_crossfade
from app.audio.effects import apply_audio_effects_ffmpeg
from app.audio.watermark import embed_ai_disclosure_metadata
from app.config import settings
from app.emotion.auto_emotion import detect_sentence_emotion
from app.emotion.presets import calculate_scaled_parameters
from app.engines.edge_engine import edge_engine
from app.engines.gemini_engine import gemini_engine
from app.engines.piper_engine import piper_engine
from app.engines.remote_engine import remote_engine
from app.text.lexicon import apply_lexicon_rules
from app.text.normalize import normalize_indonesian_text
from app.text.splitter import split_into_sentences


class PipelineResult:
    def __init__(
        self,
        job_id: str,
        audio_path: Path,
        duration_sec: float,
        num_sentences: int,
        is_cached: bool = False,
        sentence_details: list[dict[str, Any]] | None = None,
        engine_used: str = "piper",
        first_sentence_time_ms: float = 0.0,
    ):
        self.job_id = job_id
        self.audio_path = audio_path
        self.duration_sec = duration_sec
        self.num_sentences = num_sentences
        self.is_cached = is_cached
        self.sentence_details = sentence_details or []
        self.engine_used = engine_used
        self.first_sentence_time_ms = first_sentence_time_ms


async def run_synthesis_pipeline(
    text: str,
    voice_id: str = "piper_id_gadis_fast",
    speed: float = 1.0,
    pitch: float = 0.0,
    pause_scale: float = 1.0,
    audio_effect: str = "none",
    emotion: str = "neutral",
    emotion_intensity: float = 100.0,
    sentence_emotions: list[str] | None = None,
    engine_name: str | None = None,
    job_id: str | None = None,
    on_progress: Callable[[dict[str, Any]], Any] | None = None,
) -> PipelineResult:
    """
    Menjalankan seluruh alur sintesis narasi secara end-to-end:
    Normalisasi -> Lexicon -> Split Kalimat -> Analisis Emosi -> Sintesis Per Kalimat -> Crossfade -> FFmpeg Post-Processing.
    """
    if not job_id:
        job_id = f"job_{uuid.uuid4().hex[:12]}"

    # 1. Pengecekan Cache Berbasis Hash (Teks + Voice + Speed + Pitch + Efek + Emosi + Intensitas + Engine)
    import time

    pipeline_start_t = time.time()
    if engine_name:
        active_engine = engine_name
    elif voice_id.startswith("gemini"):
        active_engine = "gemini"
    elif voice_id.startswith("edge"):
        active_engine = "edge"
    elif voice_id.startswith("remote"):
        active_engine = "remote"
    else:
        active_engine = settings.DEFAULT_ENGINE

    actual_engine_used = active_engine
    cache_meta = f"{active_engine}_{emotion}_{emotion_intensity}_{pause_scale}_{sentence_emotions or ''}"
    cache_key = compute_cache_key(
        text, voice_id, speed, pitch, f"{audio_effect}_{cache_meta}"
    )
    cached_path = get_cached_audio(cache_key)

    if cached_path:
        if on_progress:
            await on_progress(
                {
                    "step": "cached",
                    "progress": 100,
                    "message": "Audio diambil dari cache.",
                }
            )
        import shutil

        output_wav = settings.AUDIO_OUTPUT_DIR / f"{job_id}.wav"
        if not output_wav.exists():
            shutil.copy(cached_path, output_wav)

        import wave

        with wave.open(str(cached_path), "rb") as wf:
            dur = wf.getnframes() / float(wf.getframerate())
        num_sents = max(1, len(split_into_sentences(text)))
        cache_latency = round((time.time() - pipeline_start_t) * 1000, 1)
        return PipelineResult(
            job_id=job_id,
            audio_path=output_wav,
            duration_sec=dur,
            num_sentences=num_sents,
            is_cached=True,
            engine_used=active_engine,
            first_sentence_time_ms=cache_latency,
        )

    # 2. Normalisasi Teks Bahasa Indonesia
    if on_progress:
        await on_progress(
            {"step": "normalizing", "progress": 10, "message": "Menormalkan teks..."}
        )
    normalized_text = normalize_indonesian_text(text)

    # 3. Terapkan Kamus Pelafalan (Lexicon)
    spoken_text = apply_lexicon_rules(normalized_text)

    # 4. Pemecahan Kalimat Natural
    if on_progress:
        await on_progress(
            {"step": "splitting", "progress": 20, "message": "Memecah kalimat..."}
        )
    sentences = split_into_sentences(spoken_text)
    if not sentences:
        sentences = [spoken_text]

    temp_dir = settings.AUDIO_OUTPUT_DIR / "temp" / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    sentence_wavs: list[Path] = []
    sentence_details: list[dict[str, Any]] = []
    total_sentences = len(sentences)
    first_sentence_time_ms = 0.0

    # 5. Sintesis per Kalimat dengan Pemetaan Emosi & Prosodi
    for idx, sentence in enumerate(sentences):
        # Tentukan emosi per kalimat
        if (
            sentence_emotions
            and idx < len(sentence_emotions)
            and sentence_emotions[idx]
        ):
            sent_emo_id = sentence_emotions[idx]
        elif emotion == "auto":
            auto_res = detect_sentence_emotion(sentence)
            sent_emo_id = auto_res["emotion_id"]
        else:
            sent_emo_id = emotion

        # Hitung parameter terkalibrasi intensitas (0-100)
        emo_params = calculate_scaled_parameters(
            emotion_id=sent_emo_id,
            intensity=emotion_intensity,
            base_speed=speed,
            base_pitch=pitch,
            base_pause=pause_scale,
        )

        # Kecepatan & pitch stabil konsisten per emosi (tanpa jitter acak yang membuat suara goyang)
        sent_speed = emo_params["speed"]
        sent_pitch = emo_params["pitch"]

        # Pemetaan emosi ke dinamika prosodi & intonasi (noise_scale & noise_w_scale)
        emo_id_lower = sent_emo_id.lower()
        if any(k in emo_id_lower for k in ["gembira", "happy", "semangat", "antusias"]):
            sent_noise_scale = 0.88
            sent_noise_w_scale = 1.15
        elif any(k in emo_id_lower for k in ["sedih", "sad", "somber"]):
            sent_noise_scale = 0.65
            sent_noise_w_scale = 0.75
        elif any(k in emo_id_lower for k in ["marah", "angry"]):
            sent_noise_scale = 0.95
            sent_noise_w_scale = 1.10
        elif any(k in emo_id_lower for k in ["tenang", "calm", "bisik", "whisper"]):
            sent_noise_scale = 0.70
            sent_noise_w_scale = 0.85
        else:
            sent_noise_scale = settings.DEFAULT_NOISE_SCALE
            sent_noise_w_scale = settings.DEFAULT_NOISE_W_SCALE

        sent_wav = temp_dir / f"sent_{idx:04d}.wav"

        async def _run_engine_synth(engine_to_use: str, target_voice: str):
            if engine_to_use == "gemini":
                return await gemini_engine.synthesize(
                    text=sentence,
                    voice_id=target_voice,
                    output_path=sent_wav,
                    speed=sent_speed,
                    pitch=sent_pitch,
                    extra_params={
                        "emotion": sent_emo_id,
                        "intensity": emotion_intensity,
                    },
                )
            elif engine_to_use == "edge":
                return await edge_engine.synthesize(
                    text=sentence,
                    voice_id=target_voice,
                    output_path=sent_wav,
                    speed=sent_speed,
                    pitch=sent_pitch,
                    extra_params={
                        "emotion": sent_emo_id,
                        "intensity": emotion_intensity,
                    },
                )
            elif engine_to_use == "remote":
                return await remote_engine.synthesize(
                    text=sentence,
                    voice_id=target_voice,
                    output_path=sent_wav,
                    speed=sent_speed,
                    pitch=sent_pitch,
                    extra_params={
                        "emotion": sent_emo_id,
                        "intensity": emotion_intensity,
                        "noise_scale": sent_noise_scale,
                        "noise_w_scale": sent_noise_w_scale,
                    },
                )
            else:
                return await piper_engine.synthesize(
                    text=sentence,
                    voice_id=target_voice,
                    output_path=sent_wav,
                    speed=sent_speed,
                    pitch=sent_pitch,
                    extra_params={
                        "noise_scale": sent_noise_scale,
                        "noise_w_scale": sent_noise_w_scale,
                    },
                )

        try:
            await _run_engine_synth(active_engine, voice_id)
        except Exception as primary_err:
            if active_engine != "piper" and piper_engine.is_available():
                print(
                    f"[Pipeline] Engine '{active_engine}' gagal ({primary_err}). "
                    f"Melakukan fallback otomatis ke Piper ONNX..."
                )
                actual_engine_used = "piper"
                await _run_engine_synth("piper", "id_ID-news_tts-medium")
            else:
                raise RuntimeError(
                    f"Sintesis suara gagal pada engine '{active_engine}': {primary_err}. "
                    "Fallback lokal Piper tidak tersedia atau dinonaktifkan."
                ) from primary_err

        # Terapkan modulasi pitch emosi per kalimat jika menggunakan Piper lokal
        if actual_engine_used == "piper" and abs(sent_pitch) >= 0.2:
            clamped_sent_pitch = max(-2.5, min(2.5, sent_pitch))
            apply_audio_effects_ffmpeg(
                input_wav=sent_wav,
                output_wav=sent_wav,
                pitch_semitones=clamped_sent_pitch,
                normalize_lufs=False,
                apply_deesser=False,
                sample_rate=22050,
            )

        sentence_wavs.append(sent_wav)
        if idx == 0:
            first_sentence_time_ms = round((time.time() - pipeline_start_t) * 1000, 1)

        sentence_details.append(
            {
                "index": idx,
                "text": sentence,
                "emotion": sent_emo_id,
                "speed": sent_speed,
                "pitch": sent_pitch,
                "color": emo_params["color"],
            }
        )

        if on_progress:
            current_pct = int(20 + ((idx + 1) / total_sentences) * 60)
            await on_progress(
                {
                    "step": "synthesizing",
                    "sentence_index": idx + 1,
                    "total_sentences": total_sentences,
                    "progress": current_pct,
                    "message": f"Menyintesis kalimat {idx + 1} ({emo_params['emotion_name']})...",
                }
            )

    # 6. Penggabungan Audio dengan Equal-Power Crossfade (30–50ms)
    if on_progress:
        await on_progress(
            {
                "step": "crossfading",
                "progress": 85,
                "message": "Menggabungkan sambungan audio...",
            }
        )

    raw_output_wav = temp_dir / f"merged_{job_id}.wav"
    # Gabungkan pause_scale umum dengan pause_scale dari emosi
    effective_pause_scale = pause_scale * emo_params.get("pause_scale", 1.0)
    natural_pause_ms = int(260 * max(0.2, min(3.0, effective_pause_scale)))
    merge_wav_files_with_crossfade(
        sentence_wavs,
        raw_output_wav,
        crossfade_ms=20,
        pause_ms=natural_pause_ms,
        sample_rate=22050,
    )

    # 7. Post-Processing FFmpeg (-16 LUFS, De-esser, Efek Akustik & Diferensiasi Karakter Vokal)
    if on_progress:
        await on_progress(
            {
                "step": "post_processing",
                "progress": 92,
                "message": "Menerapkan mastering audio & diferensiasi vokal...",
            }
        )

    # Deteksi apakah model adalah model mandiri nyata (Dedicated Model)
    # Suara dari engine online (Gemini, Edge) dan model ONNX mandiri tidak dimanipulasi dengan FFmpeg pitch/EQ profile hack.
    is_dedicated_real_voice = (
        actual_engine_used in ("gemini", "edge")
        or (settings.MODELS_DIR / f"{voice_id}.onnx").exists()
        or (settings.MODELS_DIR / voice_id / f"{voice_id}.onnx").exists()
    )

    profile_pitch = 0.0
    profile_eq = None

    # Profil akustik hanya diaplikasikan untuk suara legacy Piper yang berbagi satu model fisik:
    if not is_dedicated_real_voice and actual_engine_used == "piper":
        v_lower = voice_id.lower()
        if "bima" in v_lower:
            # Bima (Pria Narator): Nada berat berwibawa (-4.8 semitones) + resonansi dada
            profile_pitch = -4.8
            profile_eq = "bass=g=4.5:f=160,equalizer=f=3200:t=q:w=1.2:g=-2.5"
        elif "dimas" in v_lower:
            # Dimas (Pria Penyiar Berita): Nada bariton tegas (-3.6 semitones) + artikulasi jernih
            profile_pitch = -3.6
            profile_eq = "bass=g=3.0:f=200,equalizer=f=2500:t=q:w=1.5:g=1.2"
        elif "gadis" in v_lower:
            # Gadis (Wanita Kreator): Nada lebih tinggi & ceria (+2.3 semitones) + treble renyah
            profile_pitch = 2.3
            profile_eq = "treble=g=2.5:f=3500,equalizer=f=2800:t=q:w=1.0:g=1.8"
        elif "siti" in v_lower:
            # Siti (Wanita Teman Cerita / Podcast): Nada hangat ramah (+0.7 semitone)
            profile_pitch = 0.7
            profile_eq = "bass=g=2.0:f=180,treble=g=1.0:f=6000"
        elif any(k in v_lower for k in ["male", "pria", "budi", "podcast"]):
            # Profil pria generik untuk kloning suara pria tanpa model mandiri
            profile_pitch = -4.2
            profile_eq = "bass=g=3.5:f=170,equalizer=f=3000:t=q:w=1.2:g=-2.0"
        elif "id_id-news_tts" in v_lower or "ida" in v_lower:
            # Ida: Model bawaan resmi tanpa modulasi
            profile_pitch = 0.0
            profile_eq = None

    # Total nada = profil karakter bawaan + setelan slider pengguna (-5 s/d +5)
    total_pitch = profile_pitch + pitch

    # Efek akustik: gunakan pilihan pengguna jika disetel; jika "none", gunakan efek dari emosi jika ada
    effective_effect = (
        audio_effect
        if audio_effect and audio_effect != "none"
        else emo_params.get("effect", "none")
    )

    final_output_wav = settings.AUDIO_OUTPUT_DIR / f"{job_id}.wav"
    apply_audio_effects_ffmpeg(
        input_wav=raw_output_wav,
        output_wav=final_output_wav,
        effect=effective_effect,
        normalize_lufs=True,
        apply_deesser=True,
        pitch_semitones=total_pitch,
        voice_profile_eq=profile_eq,
        sample_rate=22050,
    )

    # 7.5 Sematkan label etika AI di metadata audio ("Dibuat dengan AI")
    if settings.EMBED_AI_LABEL:
        embed_ai_disclosure_metadata(final_output_wav, comment=settings.AI_LABEL_TEXT)

    # 8. Simpan Hasil ke Cache
    save_to_cache(cache_key, final_output_wav)

    # 9. Bersihkan File Temporer
    for sw in sentence_wavs:
        try:
            sw.unlink(missing_ok=True)
        except Exception:
            pass
    try:
        raw_output_wav.unlink(missing_ok=True)
        temp_dir.rmdir()
    except Exception:
        pass

    # Hitung durasi total audio master
    import wave

    with wave.open(str(final_output_wav), "rb") as wf:
        total_duration = wf.getnframes() / float(wf.getframerate())

    if on_progress:
        await on_progress(
            {
                "step": "completed",
                "progress": 100,
                "message": "Audio narasi selesai disintesis.",
            }
        )

    return PipelineResult(
        job_id=job_id,
        audio_path=final_output_wav,
        duration_sec=total_duration,
        num_sentences=total_sentences,
        is_cached=False,
        sentence_details=sentence_details,
        engine_used=actual_engine_used,
        first_sentence_time_ms=first_sentence_time_ms,
    )
