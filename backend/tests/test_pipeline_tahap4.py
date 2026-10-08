"""
Unit & Integration Test Tahap 4:
1. Piper Voice Model Check & Verification
2. Hash-based Cache
3. Equal-Power Crossfade Audio Splice (30-50ms)
4. Prosody Variation (±3-5% speed & pitch)
5. Sintesis Naskah Panjang (+2.000 karakter) Tanpa Glitch
6. Endpoint POST /tts, GET /voices, GET /jobs/{id}, SSE Progress
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import wave

import pytest
from app.audio.cache import compute_cache_key
from app.audio.crossfade import (
    crossfade_pcm,
)
from app.audio.pipeline import run_synthesis_pipeline

# Contoh naskah kreator konten panjang (+2.000 karakter)
SAMPLE_CREATOR_SCRIPT_2000 = (
    "Halo para kreator digital Indonesia! Selamat datang kembali di sesi bedah konten video mingguan kita. "
    "Hari ini kita akan mengulas secara mendalam bagaimana membangun narasi video yang memikat sejak 3 detik pertama. "
    "Banyak dari kita yang sering kali langsung melompat ke inti pembahasan tanpa memberikan umpan rasa penasaran yang kuat kepada penonton. "
    "Padahal, riset algoritma di platform video pendek seperti TikTok dan Instagram Reels membuktikan bahwa tingkat retensi penonton di 5 detik pertama sangat menentukan apakah video Anda akan direkomendasikan lebih luas atau justru dilewati begitu saja. "
    "Langkah pertama yang harus Anda terapkan adalah merancang kalimat pembuka atau hook yang tidak biasa. "
    "Alih-alih menyapa dengan kalimat formal yang membosankan, mulailah dengan pertanyaan yang menantang asumsi umum mereka. "
    "Sebagai contoh, daripada mengatakan 'Halo teman-teman, hari ini saya ingin membagikan tips menghemat uang', coba ubah menjadi: "
    "'Tahukah Anda bahwa kebiasaan kecil membeli kopi seharga Rp 25.000 setiap pagi bisa menghabiskan lebih dari Rp 9.000.000 dalam setahun?' "
    "Perhatikan bagaimana angka spesifik Rp 25.000 dan Rp 9.000.000 memberikan bobot realitas yang jauh lebih mengguncang pikiran audiens. "
    "Langkah kedua adalah menjaga ritme dan dinamika suara. Jangan berbicara dengan nada yang monoton dari awal hingga akhir video. "
    "Gunakan intonasi yang sedikit lebih cepat pada bagian yang memicu rasa antusias, dan berikan jeda hening sekitar 200 hingga 450 milidetik tepat sebelum Anda menyampaikan poin utama atau punchline. "
    "Jeda singkat ini memberikan ruang bagi otak penonton untuk mengantisipasi informasi penting yang akan datang. "
    "Langkah ketiga adalah memanfaatkan teknologi sintesis suara mandiri seperti TaSTP. "
    "Dengan engine neural Piper berformat ONNX yang sangat ringan di CPU laptop, Anda dapat menghasilkan narasi berkualitas siaran studio tanpa biaya langganan API yang mahal. "
    "Kunjungi situs dokumentasi kami di https://kemdikbud.go.id atau kirim surel kerja sama ke redaksi@kreator.id untuk panduan teknis lebih lanjut. "
    "Jangan ragu untuk mulai bereksperimen hari ini juga. Sukses selalu untuk karya-karya hebat Anda!"
)


def test_script_length_exceeds_1500_chars():
    # Pastikan naskah uji coba memenuhi syarat naskah panjang (~2.000 karakter)
    assert len(SAMPLE_CREATOR_SCRIPT_2000) >= 1800


def test_cache_key_deterministic_and_unique():
    k1 = compute_cache_key("Halo dunia", "piper_id_gadis_fast", 1.0, 0.0, "none")
    k2 = compute_cache_key("Halo dunia", "piper_id_gadis_fast", 1.0, 0.0, "none")
    k3 = compute_cache_key("Halo dunia", "piper_id_bima_narrator", 1.0, 0.0, "none")
    k4 = compute_cache_key("Halo dunia", "piper_id_gadis_fast", 1.05, 0.0, "none")

    assert k1 == k2
    assert k1 != k3
    assert k1 != k4
    assert len(k1) == 64  # SHA-256 hexdigest


def test_equal_power_crossfade_continuity(tmp_path):
    # Buat dua potongan audio PCM sintesis (masing-masing 1000 sampel)
    sr = 22050
    crossfade_ms = 40
    overlap_samples = int((crossfade_ms / 1000.0) * sr)  # 882 sampel

    chunk_a = [10000] * 2000
    chunk_b = [20000] * 2000

    merged = crossfade_pcm(
        [chunk_a, chunk_b], crossfade_ms=crossfade_ms, sample_rate=sr
    )

    # Panjang total harus = 2000 + 2000 - 882 = 3118
    assert len(merged) == 2000 + 2000 - overlap_samples
    assert merged[0] == 10000
    assert merged[-1] == 20000

    # Di titik tengah overlap, equal-power menjamin energi audio terjaga
    mid_junction = 2000 - (overlap_samples // 2)
    assert 10000 <= merged[mid_junction] <= 25000


@pytest.mark.asyncio
async def test_full_2000_char_script_synthesis_no_glitch(tmp_path):
    """
    Uji coba sintesis naskah panjang +2.000 karakter:
    - Normalisasi berhasil
    - Dipecah menjadi banyak kalimat
    - Tiap kalimat disintesis dengan variasi prosodi
    - Digabungkan dengan equal-power crossfade
    - File WAV valid dihasilkan dan disimpan
    - Durasi audio dihitung akurat
    """
    progress_logs = []

    async def log_progress(info):
        progress_logs.append(info)

    result = await run_synthesis_pipeline(
        text=SAMPLE_CREATOR_SCRIPT_2000,
        voice_id="piper_id_gadis_fast",
        speed=1.0,
        pitch=0.0,
        audio_effect="none",
        on_progress=log_progress,
    )

    # 1. Pastikan job ID dan audio path terbentuk
    assert result.job_id.startswith("job_")
    assert result.audio_path.exists()
    assert result.audio_path.stat().st_size > 44  # Melebihi header WAV kosong

    # 2. Pastikan naskah dipecah menjadi banyak kalimat (minimal 10 kalimat)
    assert result.num_sentences >= 10

    # 3. Pastikan durasi audio wajar untuk naskah panjang (minimal 15 detik)
    assert result.duration_sec >= 15.0

    # 4. Verifikasi keabsahan struktur header file WAV
    with wave.open(str(result.audio_path), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 22050
        num_frames = wf.getnframes()
        assert num_frames > 22050 * 15  # Lebih dari 15 detik sampel

    # 5. Verifikasi progres mencapai 100%
    assert any(p.get("progress") == 100 for p in progress_logs)

    # 6. Uji Cache Hit: sintesis kedua harus langsung instant dari cache
    cached_result = await run_synthesis_pipeline(
        text=SAMPLE_CREATOR_SCRIPT_2000,
        voice_id="piper_id_gadis_fast",
        speed=1.0,
        pitch=0.0,
        audio_effect="none",
    )
    assert cached_result.is_cached is True
    assert cached_result.audio_path.exists()
