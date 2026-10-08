"""
Unit & Integration Test Suite Tahap 6 (Emotion & Effects):
- 22 Emotion presets validation
- Intensity slider (0-100) prosody scaling
- Local rule-based auto-emotion text analysis
- FFmpeg audio effects (-16 LUFS, de-esser, reverb, radio, telephone, whisper)
- Multi-emotion synthesis distinct audio output
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from app.audio.effects import apply_audio_effects_ffmpeg
from app.audio.pipeline import run_synthesis_pipeline
from app.emotion.auto_emotion import analyze_script_emotions, detect_sentence_emotion
from app.emotion.presets import (
    EMOTION_CATALOG,
    calculate_scaled_parameters,
    get_emotion_preset,
    list_all_emotion_presets,
)


def test_at_least_20_emotion_presets_available():
    assert len(EMOTION_CATALOG) >= 20
    presets = list_all_emotion_presets()
    assert len(presets) >= 20

    # Pastikan kategori lengkap
    categories = {p["category"] for p in presets}
    assert "dasar" in categories
    assert "nuansa" in categories
    assert "gaya" in categories
    assert "karakter" in categories


def test_emotion_intensity_scaling_0_to_100():
    # Intensitas 0% harus kembali ke parameter baseline netral
    p0 = calculate_scaled_parameters(
        "happy", intensity=0.0, base_speed=1.0, base_pitch=0.0
    )
    assert p0["speed"] == 1.0
    assert p0["pitch"] == 0.0

    # Intensitas 50% harus setengah dari preset
    p50 = calculate_scaled_parameters(
        "happy", intensity=50.0, base_speed=1.0, base_pitch=0.0
    )
    preset_happy = get_emotion_preset("happy")
    expected_pitch = preset_happy.pitch * 0.5
    assert abs(p50["pitch"] - expected_pitch) < 0.1
    assert p50["speed"] > 1.0 and p50["speed"] < preset_happy.speed

    # Intensitas 100% harus sama persis dengan preset
    p100 = calculate_scaled_parameters(
        "happy", intensity=100.0, base_speed=1.0, base_pitch=0.0
    )
    assert p100["pitch"] == preset_happy.pitch
    assert abs(p100["speed"] - preset_happy.speed) < 0.01


def test_auto_emotion_text_analysis():
    # Hook kreator
    r1 = detect_sentence_emotion("Stop scroll dulu ya kawan!")
    assert r1["emotion_id"] == "energetic_hook"

    # Haru / sedih
    r2 = detect_sentence_emotion("Kabar duka yang sangat menyedihkan telah tiba.")
    assert r2["emotion_id"] == "sad"

    # Bisikan
    r3 = detect_sentence_emotion("Sshh... ini rahasia kita berdua saja.")
    assert r3["emotion_id"] == "whisper"

    # Gembira
    r4 = detect_sentence_emotion(
        "Selamat atas pencapaian luar biasa yang sangat membanggakan!"
    )
    assert r4["emotion_id"] == "happy"

    # Batch script analysis
    batch_res = analyze_script_emotions(
        [
            "Halo sahabat setia.",
            "Tahu nggak rahasia algoritma video pendek?",
            "Ternyata sangat mengejutkan!",
        ]
    )
    assert len(batch_res) == 3


def test_ffmpeg_effects_processing(tmp_path):
    # Buat file audio dummy mono 22050Hz PCM 16-bit
    import math
    import struct
    import wave

    src_wav = tmp_path / "test_input.wav"
    sr = 22050
    with wave.open(str(src_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        samples = [int(10000 * math.sin(2 * math.pi * 440 * i / sr)) for i in range(sr)]
        wf.writeframes(struct.pack(f"<{sr}h", *samples))

    # Terapkan efek reverb dan radio
    out_reverb = tmp_path / "test_reverb.wav"
    apply_audio_effects_ffmpeg(
        src_wav, out_reverb, effect="reverb", normalize_lufs=True, apply_deesser=True
    )
    assert out_reverb.exists()
    assert out_reverb.stat().st_size > 44

    out_radio = tmp_path / "test_radio.wav"
    apply_audio_effects_ffmpeg(
        src_wav, out_radio, effect="radio", normalize_lufs=True, apply_deesser=True
    )
    assert out_radio.exists()
    assert out_radio.stat().st_size > 44


@pytest.mark.asyncio
async def test_distinct_emotions_produce_different_audio():
    res_happy = await run_synthesis_pipeline(
        text="Hari ini adalah hari yang paling membahagiakan dalam hidup saya!",
        voice_id="id_ID-news_tts-medium",
        emotion="happy",
        emotion_intensity=100.0,
    )

    res_sad = await run_synthesis_pipeline(
        text="Hari ini adalah hari yang paling menyedihkan dalam hidup saya.",
        voice_id="id_ID-news_tts-medium",
        emotion="sad",
        emotion_intensity=100.0,
    )

    # Durasi dan timing emosi happy (tempo cepat) dan sad (tempo lambat) harus terbukti berbeda
    assert res_happy.duration_sec != res_sad.duration_sec
    assert res_happy.audio_path.exists()
    assert res_sad.audio_path.exists()
