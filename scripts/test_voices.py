"""
Quick test: synthesize the same text with all 5 voices to verify they sound different.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from pathlib import Path

async def test_voices():
    from app.audio.pipeline import run_synthesis_pipeline

    test_text = "Selamat pagi Indonesia. Hari ini cuaca sangat cerah dan indah sekali."
    
    voices = [
        "id_ID-news_tts-medium",      # Ida (base, no DSP)
        "piper_id_gadis_fast",         # Gadis (+2.3 semitones, treble)
        "piper_id_bima_narrator",      # Bima (-4.8 semitones, bass)
        "piper_id_siti_podcast",       # Siti (+0.7 semitone, warm)
        "piper_id_dimas_news",         # Dimas (-3.6 semitones, bariton)
    ]
    
    print("=== Voice Differentiation Test ===\n")
    
    for voice_id in voices:
        try:
            result = await run_synthesis_pipeline(
                text=test_text,
                voice_id=voice_id,
                speed=1.0,
                pitch=0.0,
                emotion="neutral",
                emotion_intensity=100.0,
            )
            size_kb = result.audio_path.stat().st_size / 1024
            print(f"[OK] {voice_id}")
            print(f"  Duration: {result.duration_sec:.2f}s | Size: {size_kb:.1f}KB")
            print(f"  Engine: {result.engine_used} | Path: {result.audio_path}")
            print()
        except Exception as e:
            print(f"[FAIL] {voice_id}: {e}\n")

    print("=== Test Complete ===")

asyncio.run(test_voices())
