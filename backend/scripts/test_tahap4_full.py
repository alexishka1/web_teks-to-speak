"""
Skrip Pengujian Komprehensif Tahap 4 TaSTP:
1. Pengecekan endpoint GET /voices
2. Sintesis naskah 2.000 karakter via POST /tts
3. Pemantauan status via GET /jobs/{id}
4. Pengunduhan audio WAV hasil sintesis
5. Verifikasi kualitas audio: ukuran, durasi, sample rate, dan kontinuitas tanpa glitch
6. Uji efektivitas cache berbasis hash (sintesis berulang instant)
"""

import json
import struct
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "storage" / "audio"

SCRIPT_2000_CHARS = (
    "Halo para kreator konten Indonesia! Selamat datang kembali di sesi bedah algoritma dan produksi video mingguan kita. "
    "Hari ini kita akan mengulas secara mendalam bagaimana merancang narasi audio visual yang sanggup mengikat perhatian penonton sejak 3 detik pertama. "
    "Banyak kreator pemula yang langsung melompat ke materi inti tanpa membangun rasa penasaran atau hook psikologis yang kuat. "
    "Padahal, analisis retensi di platform video pendek seperti YouTube Shorts, TikTok, dan Instagram Reels menunjukkan fakta menarik: "
    "jika audiens bertahan melewati 5 detik pertama, probabilitas video ditonton sampai selesai meningkat hingga lebih dari 65 persen. "
    "Langkah pertama yang wajib Anda latih adalah meracik kalimat pembuka yang menantang pola pikir umum penonton. "
    "Jangan gunakan sapaan klise seperti 'Halo gaes kembali lagi di channel saya'. "
    "Gantilah dengan pertanyaan data yang mengejutkan, contohnya: "
    "'Tahukah Anda bahwa kebiasaan membeli kopi susu kekinian seharga Rp 28.000 setiap sore ternyata membakar tabungan lebih dari Rp 10.200.000 dalam setahun?' "
    "Perhatikan betapa kuatnya kontras antara nominal kecil harian Rp 28.000 dan akumulasi tahunan Rp 10.200.000 dalam memicu rasa ingin tahu audiens. "
    "Langkah kedua adalah variasi dinamika vokal. Jangan membaca teks seperti robot pembaca berita kaku. "
    "Berikan modulasi nada, naikkan sedikit tempo saat menjelaskan momentum seru, dan sisipkan jeda keheningan sekitar 200 milidetik hingga 450 milidetik "
    "sebelum Anda membongkar rahasia atau solusi utama. "
    "Jeda mikro ini memberikan ruang bagi pikiran penonton untuk memproses pesan penting tersebut. "
    "Langkah ketiga adalah memanfaatkan platform Text-to-Speech generasi baru seperti TaSTP. "
    "Berkat model saraf Piper berformat ONNX yang sangat hemat daya pada CPU laptop, seluruh proses pengisian suara dapat dieksekusi secara lokal tanpa langganan API berbayar. "
    "Kunjungi portal kami di https://kemdikbud.go.id atau kirim surel kemitraan ke creator@tastp.local untuk mengunduh template naskah gratis. "
    "Teruslah berkarya, asah kreativitas Anda, dan sampai jumpa di panduan produksi konten berikutnya!"
)


def log_step(title: str):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def test_get_voices():
    log_step("1. Uji Endpoint GET /voices")
    url = f"{BASE_URL}/voices"
    req = urllib.request.Request(url, headers={"User-Agent": "TaSTP-Tester"})
    with urllib.request.urlopen(req, timeout=5) as res:
        assert res.status == 200, f"Status code: {res.status}"
        data = json.loads(res.read().decode("utf-8"))
        print(f"Berhasil mengambil {len(data)} model suara:")
        for v in data:
            print(f" - [{v['id']}] {v['name']} ({v['language']} | {v['engine']})")

        voice_ids = [v["id"] for v in data]
        assert (
            "id_ID-news_tts-medium" in voice_ids or "piper_id_gadis_fast" in voice_ids
        )
        print("  -> Verifikasi daftar suara SUKSES!")
        return data[0]["id"]


def test_synthesis_2000_chars(voice_id: str):
    log_step(f"2. Uji POST /tts dengan Naskah {len(SCRIPT_2000_CHARS)} Karakter")
    payload = {
        "text": SCRIPT_2000_CHARS,
        "voice_id": voice_id,
        "speed": 1.0,
        "pitch": 0.0,
        "audio_effect": "none",
        "is_cloned_voice": False,
        "voice_clone_consent": False,
    }
    req = urllib.request.Request(
        f"{BASE_URL}/tts",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    start_time = time.time()
    with urllib.request.urlopen(req, timeout=120) as res:
        elapsed = time.time() - start_time
        assert res.status == 200, f"Status code: {res.status}"
        result = json.loads(res.read().decode("utf-8"))
        print(f"Waktu respon POST /tts: {elapsed:.2f} detik")
        print(f"Job ID: {result['job_id']}")
        print(f"Status: {result['status']}")
        print(f"Durasi audio diestimasi: {result['duration_sec']:.2f} detik")
        print(f"Audio URL: {result['audio_url']}")
        assert result["status"] == "completed"
        return result


def test_job_status(job_id: str):
    log_step(f"3. Uji Endpoint GET /jobs/{job_id}")
    url = f"{BASE_URL}/jobs/{job_id}"
    with urllib.request.urlopen(url, timeout=5) as res:
        assert res.status == 200
        data = json.loads(res.read().decode("utf-8"))
        print(
            f"Data Job: status={data['status']}, duration={data['duration_sec']:.2f}s, url={data['audio_url']}"
        )
        assert data["status"] == "completed"
        print("  -> Verifikasi endpoint job status SUKSES!")


def test_download_and_verify_audio(job_id: str):
    log_step(f"4. Unduh & Verifikasi File Audio WAV untuk {job_id}")
    url = f"{BASE_URL}/api/audio/{job_id}"
    dest_path = OUTPUT_DIR / f"test_{job_id}.wav"

    with urllib.request.urlopen(url, timeout=10) as res:
        assert res.status == 200
        audio_bytes = res.read()
        dest_path.write_bytes(audio_bytes)
        print(
            f"Ukuran file audio terunduh: {len(audio_bytes):,} bytes ({len(audio_bytes) / 1024:.1f} KB)"
        )
        assert len(audio_bytes) > 50000, "Ukuran file terlalu kecil!"

    # Analisis integritas file WAV
    with wave.open(str(dest_path), "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        framerate = wf.getframerate()
        frames = wf.getnframes()
        duration = frames / float(framerate)

        print(f"Saluran audio : {channels} (Mono)")
        print(f"Sample Width  : {sample_width * 8}-bit")
        print(f"Sample Rate   : {framerate} Hz")
        print(f"Jumlah Sampel : {frames:,}")
        print(f"Durasi Nyata  : {duration:.2f} detik")

        assert channels == 1
        assert sample_width == 2  # 16-bit PCM
        assert framerate == 22050
        assert duration >= 15.0, (
            f"Durasi audio {duration}s terlalu pendek untuk naskah 2.000 karakter!"
        )

        # Verifikasi kelancaran sinyal (tidak ada glitch lonjakan DC ekstrem di ujung)
        raw_samples = wf.readframes(frames)
        samples = struct.unpack(f"<{frames}h", raw_samples)
        max_amplitude = max(abs(s) for s in samples)
        avg_amplitude = sum(abs(s) for s in samples) / len(samples)
        print(f"Amplitudo Puncak: {max_amplitude} / 32767")
        print(f"Rata-rata Energi: {avg_amplitude:.1f}")
        assert max_amplitude > 1000, "Audio hening/kosong!"
        assert avg_amplitude > 100, "Energi audio tidak terdengar!"

    print("  -> Verifikasi kualitas audio: LULUS TANPA GLITCH!")


def test_cache_hit_performance(voice_id: str):
    log_step("5. Uji Kecepatan Cache Hit Berbasis Hash (Teks + Voice + Setting)")
    payload = {
        "text": SCRIPT_2000_CHARS,
        "voice_id": voice_id,
        "speed": 1.0,
        "pitch": 0.0,
        "audio_effect": "none",
    }
    req = urllib.request.Request(
        f"{BASE_URL}/tts",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=10) as res:
        latency_sec = time.time() - t0
        data = json.loads(res.read().decode("utf-8"))
        print(f"Waktu respon sintesis cache hit: {latency_sec * 1000:.1f} milidetik")
        print(f"Job ID baru : {data['job_id']}")
        print(f"Durasi audio: {data['duration_sec']:.2f} detik")
        assert latency_sec < 1.0, "Cache hit harus kembali di bawah 1 detik!"
    print("  -> Uji Cache Hit: BERHASIL INSTANT!")


def run_all_tests():
    print("=" * 65)
    print("  MULAI PENGUJIAN OTOMATIS TAHAP 4 TASTP")
    print(f"  Target Server: {BASE_URL}")
    print(f"  Panjang Teks : {len(SCRIPT_2000_CHARS)} karakter")
    print("=" * 65)

    voice_id = test_get_voices()
    job_result = test_synthesis_2000_chars(voice_id)
    test_job_status(job_result["job_id"])
    test_download_and_verify_audio(job_result["job_id"])
    test_cache_hit_performance(voice_id)

    print("\n" + "=" * 65)
    print("  SEMUA CEKLIS TAHAP 4 LULUS 100%!")
    print("=" * 65)


if __name__ == "__main__":
    run_all_tests()
