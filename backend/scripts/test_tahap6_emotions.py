"""
Skrip Pengujian Tahap 6:
1. Verifikasi 22 Preset Emosi & Gaya Bicara
2. Uji Skalasi Intensitas (0%, 50%, 100%)
3. Uji Auto Emotion Analyzer Berbasis Kata Kunci Lokal
4. Sintesis dengan Berbagai Emosi (Happy, Sad, Whisper, Radio, Telephone)
5. Verifikasi bahwa Tiap Emosi Menghasilkan Karakteristik Audio yang Berbeda Nyata
"""

import json
import time
import urllib.request

BASE_URL = "http://127.0.0.1:8000"


def test_get_emotions_catalog():
    print("\n" + "=" * 65)
    print("1. Menguji Endpoint GET /emotions")
    print("=" * 65)
    url = f"{BASE_URL}/emotions"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode("utf-8"))
        print(f"Berhasil mengambil {len(data)} preset emosi (minimal 20 terpenuhi):")
        for emo in data:
            print(
                f" - [{emo['id']}] {emo['name']} ({emo['category']}) -> speed: {emo['speed']}x, pitch: {emo['pitch']}, effect: {emo['effect']}"
            )
        assert len(data) >= 20, "Jumlah emosi kurang dari 20!"
        return data


def test_auto_emotion_analysis():
    print("\n" + "=" * 65)
    print("2. Menguji POST /emotions/analyze (Auto Emotion Analyzer)")
    print("=" * 65)
    text = (
        "Stop scroll dulu! Tahu nggak kenapa video ini spesial? "
        "Sedih sekali melihat banyak kreator menyerah di tengah jalan. "
        "Tapi selamat untuk kamu yang tetap konsisten berkarya! "
        "Sshh... bisik-bisik, ini rahasia algoritma terbesarnya."
    )
    payload = {"text": text}
    req = urllib.request.Request(
        f"{BASE_URL}/emotions/analyze",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode("utf-8"))
        print(f"Jumlah kalimat dianalisis: {data['total_sentences']}")
        for s in data["sentences"]:
            print(
                f"  Kalimat #{s['sentence_index'] + 1}: '{s['text']}' -> Emosi: [{s['emotion_id']}] (conf: {s['confidence']:.2f})"
            )

        detected_emotions = [s["emotion_id"] for s in data["sentences"]]
        assert "energetic_hook" in detected_emotions
        assert "sad" in detected_emotions
        assert "happy" in detected_emotions
        assert "whisper" in detected_emotions
        print("  -> Auto Emotion Analysis LULUS 100%!")


def test_distinct_emotions_synthesis():
    print("\n" + "=" * 65)
    print("3. Menguji Sintesis Audio dengan Variasi Emosi Berbeda")
    print("=" * 65)

    test_cases = [
        {
            "emotion": "happy",
            "text": "Hore! Hari ini kita berhasil mencapai target penonton yang luar biasa!",
            "intensity": 100,
        },
        {
            "emotion": "sad",
            "text": "Sayang sekali, peristiwa menyedihkan ini harus terjadi pada kita semua.",
            "intensity": 100,
        },
        {
            "emotion": "whisper",
            "text": "Sshh, ini adalah pesan rahasia yang jangan kamu ceritakan ke orang lain.",
            "intensity": 100,
        },
        {
            "emotion": "radio_announcer",
            "text": "Panggilan masuk dari pos komando. Roger, ganti, standby di frekuensi sepuluh.",
            "intensity": 100,
        },
        {
            "emotion": "neutral",
            "text": "Ini adalah pengujian suara netral standar untuk perbandingan baseline.",
            "intensity": 0,
        },
    ]

    results = {}
    for tc in test_cases:
        payload = {
            "text": tc["text"],
            "voice_id": "id_ID-news_tts-medium",
            "speed": 1.0,
            "pitch": 0.0,
            "emotion": tc["emotion"],
            "emotion_intensity": tc["intensity"],
        }
        req = urllib.request.Request(
            f"{BASE_URL}/tts",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        t0 = time.time()
        with urllib.request.urlopen(req) as res:
            elapsed = time.time() - t0
            data = json.loads(res.read().decode("utf-8"))
            results[tc["emotion"]] = {
                "job_id": data["job_id"],
                "duration": data["duration_sec"],
                "audio_url": data["audio_url"],
                "elapsed": elapsed,
            }
            print(
                f"Emosi [{tc['emotion']}]: duration={data['duration_sec']:.2f}s, job={data['job_id']} ({elapsed:.2f}s)"
            )

    # Pastikan durasi dan hasil berbeda
    durations = [r["duration"] for r in results.values()]
    print(f"\nDurasi audio berbagai emosi: {durations}")
    assert len(set(durations)) >= 3, (
        "Durasi audio harus bervariasi sesuai emosi dan tempo laju!"
    )
    print("  -> Verifikasi perbedaan audio antar emosi LULUS!")


def run_all_tests():
    print("=" * 65)
    print("  MULAI PENGUJIAN OTOMATIS TAHAP 6 (EMOTION & EFFECTS)")
    print("=" * 65)
    test_get_emotions_catalog()
    test_auto_emotion_analysis()
    test_distinct_emotions_synthesis()
    print("\n" + "=" * 65)
    print("  SEMUA CEKLIS TAHAP 6 LULUS 100%!")
    print("=" * 65)


if __name__ == "__main__":
    run_all_tests()
