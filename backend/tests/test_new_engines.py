"""
Unit and integration tests for new TTS engines (Gemini Flash TTS, Edge TTS, and Pipeline Integration).
All network requests are mocked to guarantee offline hermetic execution.
"""

import base64
import os
import wave
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.audio.pipeline import run_synthesis_pipeline
from app.config import settings
from app.engines.edge_engine import EdgeTTSEngine
from app.engines.gemini_engine import GeminiTTSEngine


def _create_dummy_wav(path: Path, duration_sec: float = 1.0, sample_rate: int = 22050):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        num_samples = int(duration_sec * sample_rate)
        wf.writeframes(b"\x00\x00" * num_samples)


@pytest.mark.asyncio
async def test_gemini_engine_availability():
    engine = GeminiTTSEngine()
    with patch.object(settings, "ONLINE_ENGINES_ENABLED", False):
        assert engine.is_available() is False

    with patch.object(settings, "ONLINE_ENGINES_ENABLED", True):
        with patch.object(settings, "GEMINI_API_KEY", ""):
            assert engine.is_available() is False
        with patch.object(settings, "GEMINI_API_KEY", "dummy_key_123"):
            assert engine.is_available() is True


@pytest.mark.asyncio
async def test_gemini_engine_synthesize_success(tmp_path):
    engine = GeminiTTSEngine()
    output_wav = tmp_path / "gemini_test.wav"

    dummy_raw_wav = tmp_path / "raw.wav"
    _create_dummy_wav(dummy_raw_wav, duration_sec=1.5, sample_rate=24000)
    wav_bytes = dummy_raw_wav.read_bytes()
    b64_audio = base64.b64encode(wav_bytes).decode("utf-8")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "audio/x-wav",
                                "data": b64_audio,
                            }
                        }
                    ]
                }
            }
        ]
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch.object(settings, "ONLINE_ENGINES_ENABLED", True):
        with patch.object(settings, "GEMINI_API_KEY", "test_key_valid"):
            with patch("httpx.AsyncClient") as MockClientClass:
                MockClientClass.return_value.__aenter__.return_value = mock_client
                dur = await engine.synthesize(
                    text="Halo dunia",
                    voice_id="gemini_kore",
                    output_path=output_wav,
                    speed=1.0,
                    pitch=0.0,
                    extra_params={"emotion": "happy", "intensity": 90.0},
                )

                assert dur > 0.0
                assert output_wav.exists()
                # Pastikan text dikirim verbatim dan style instruction dikirim ke speech_metadata
                call_kwargs = mock_client.post.call_args[1]
                req_json = call_kwargs["json"]
                part = req_json["contents"][0]["parts"][0]
                assert part["text"] == "Halo dunia"
                assert any(
                    w in part["speech_metadata"]["style"].lower()
                    for w in ["joyful", "cheerful", "happiness"]
                )


@pytest.mark.asyncio
async def test_gemini_engine_quota_and_key_protection(tmp_path):
    engine = GeminiTTSEngine()
    output_wav = tmp_path / "gemini_fail.wav"

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "RESOURCE_EXHAUSTED"

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with patch.object(settings, "ONLINE_ENGINES_ENABLED", True):
        with patch.object(settings, "GEMINI_API_KEY", "secret_key_hidden"):
            with patch("httpx.AsyncClient") as MockClientClass:
                MockClientClass.return_value.__aenter__.return_value = mock_client
                with pytest.raises(RuntimeError) as exc_info:
                    await engine.synthesize(
                        text="Uji kuota",
                        voice_id="gemini_puck",
                        output_path=output_wav,
                    )
                # Kunci API tidak boleh bocor ke pesan error
                assert "secret_key_hidden" not in str(exc_info.value)
                assert "429" in str(exc_info.value) or "kuota" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_edge_engine_availability():
    engine = EdgeTTSEngine()
    with patch.object(settings, "ONLINE_ENGINES_ENABLED", False):
        assert engine.is_available() is False

    with patch.object(settings, "ONLINE_ENGINES_ENABLED", True):
        assert engine.is_available() is True


@pytest.mark.asyncio
async def test_edge_engine_synthesize_success(tmp_path):
    engine = EdgeTTSEngine()
    output_wav = tmp_path / "edge_test.wav"

    async def fake_save(dest_path):
        _create_dummy_wav(Path(dest_path), duration_sec=1.2, sample_rate=22050)

    mock_comm = MagicMock()
    mock_comm.save = AsyncMock(side_effect=fake_save)

    with patch.object(settings, "ONLINE_ENGINES_ENABLED", True):
        with patch("edge_tts.Communicate", return_value=mock_comm) as mock_comm_cls:
            dur = await engine.synthesize(
                text="Selamat pagi dari Edge",
                voice_id="edge_ardi",
                output_path=output_wav,
                speed=1.2,
                pitch=0.5,
            )

            assert dur > 0.0
            assert output_wav.exists()
            # Cek pemanggilan edge_tts dengan rate dan pitch
            mock_comm_cls.assert_called_once()
            call_kwargs = mock_comm_cls.call_args[1]
            assert call_kwargs["voice"] == "id-ID-ArdiNeural"
            assert "+20%" in call_kwargs["rate"]


@pytest.mark.asyncio
async def test_pipeline_engine_dispatch_and_fallback(tmp_path):
    """Pengujian pipeline menggunakan engine online dan fallback otomatis saat error."""
    # 1. Jalankan dengan edge_engine sukses
    dummy_wav = tmp_path / "pipe_edge.wav"
    _create_dummy_wav(dummy_wav, duration_sec=1.0)

    async def fake_edge_synth(*args, **kwargs):
        out_p = kwargs["output_path"]
        _create_dummy_wav(out_p, duration_sec=1.0)
        return 1.0

    with patch.object(settings, "ONLINE_ENGINES_ENABLED", True):
        with patch("app.engines.edge_engine.edge_engine.synthesize", side_effect=fake_edge_synth):
            res = await run_synthesis_pipeline(
                text="Kalimat uji coba edge.",
                voice_id="edge_ardi",
                engine_name="edge",
            )
            assert res.engine_used == "edge"
            assert res.duration_sec > 0.0

    # 2. Jalankan dengan engine gagal -> fallback otomatis ke Piper ONNX
    async def failing_synth(*args, **kwargs):
        raise RuntimeError("Network offline simulated")

    with patch.object(settings, "ONLINE_ENGINES_ENABLED", True):
        with patch("app.audio.pipeline.get_cached_audio", return_value=None):
            with patch("app.engines.gemini_engine.gemini_engine.synthesize", side_effect=failing_synth):
                res_fb = await run_synthesis_pipeline(
                    text="Kalimat uji coba fallback tanpa cache.",
                    voice_id="gemini_kore",
                    engine_name="gemini",
                )
                # Karena Piper ONNX tersedia, fallback sukses menghasilkan audio dengan engine_used piper
                assert res_fb.engine_used == "piper"
                assert res_fb.duration_sec > 0.0
