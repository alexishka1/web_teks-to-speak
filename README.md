# TaSTP — Platform Text-to-Speech Self-Hosted

**Website TTS Mandiri Bergaya ElevenLabs / Google AI Studio**  
*Fokus Niche: Kreator Konten & Video Narasi (YouTube, TikTok, Reels, Podcast) — 100% Tanpa API Pihak Ketiga.*

TaSTP dirancang khusus untuk berjalan optimal pada hardware laptop pengembang (**Intel Iris / CPU-Only, RAM 4–16 GB**) menggunakan engine **Piper ONNX (CPU)** dengan dukungan **Remote GPU Engine (Google Colab / Kaggle / Cloud GPU)** ber-mekanisme *auto-fallback*.

---

## 🚀 Fitur Utama Sistem (Tahap 1 s.d. Tahap 8)

| Fitur | Deskripsi |
|---|---|
| **Text to Speech Studio** | Editor naskah 3-kolom responsif, pemecah kalimat natural, variasi prosodi ±3%, equal-power crossfade 40ms, player WaveSurfer, karaoke highlight. |
| **Voice Library** | Katalog suara bahasa Indonesia berkarakter: Gadis (Kreator Ceria), Bima (Narator Hangat), Siti (Podcast), Dimas (Dokumenter), Ida (Berita Resmi). Preview 3 detik instan. |
| **22 Preset Emosi & Efek** | Emosi vokal (antusias, tegas, bisik, tenang, sedih, dll.), slider intensitas 0–100, Auto-Emotion lokal, filter FFmpeg: -16 LUFS, de-esser, reverb, radio, telepon, bisikan. |
| **Remote GPU & Colab** | `RemoteEngine` menghubungkan GPU jarak jauh via `colab_server.ipynb` + Cloudflared tunnel gratis. Otomatis fallback ke Piper lokal jika server GPU offline. |
| **Voice Clone Studio** | Kloning vokal dengan sampel 10–30 detik. Validasi durasi & RMS non-silence. **WAJIB checkbox persetujuan pemilik suara** dan log audit tercatat di SQLite. |
| **Projects (Dialog Multi-Speaker)** | Naskah dibagi blok dialog. Tiap blok memiliki Voice ID, emosi, dan kecepatan berbeda. *Render Dialog Gabungan* menghasilkan satu file audio berurutan mulus. |
| **Etika AI & Watermark Audio** | Setiap audio WAV disematkan label metadata *"Dibuat dengan AI - TaSTP Studio"* pada RIFF INFO chunk (`ICMT`, `INAM`) dan header HTTP. |
| **Halaman History** | Daftar riwayat tervirtualisasi (windowed), fitur putar ulang inline, unduh file WAV berlabel AI, dan hapus riwayat. |
| **API Playground (AI Studio Style)** | Form interactive API testing, response inspector (status, headers, body, audio player), dan tombol salin kode instan (**cURL**, **Python**, **JavaScript**). |
| **Guardrails & Keamanan** | Rate limiter per IP (30 req/menit), sanitasi XSS/script/null-byte, batas 5.000 karakter, latensi kalimat pertama < 3 detik, cache hash sub-100ms. |

---

## ⚡ Panduan Menjalankan Sistem

### Opsi 1: Menjalankan dengan Docker Compose (Rekomendasi dari Nol)

Docker Compose menjalankan backend (beserta FFmpeg dan Python) dan frontend Next.js secara terisolasi tanpa perlu menginstal dependensi di OS lokal:

```bash
# 1. Masuk ke folder proyek
cd d:/web_teks-to-speak

# 2. Salin template environment
cp .env.example .env

# 3. Jalankan seluruh container dari nol
docker compose up --build -d

# 4. Periksa log server
docker compose logs -f
```

Setelah container berjalan:
- **Studio Web (Frontend):** [http://localhost:3000](http://localhost:3000)
- **REST API (Backend):** [http://localhost:8000](http://localhost:8000)
- **Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

Untuk menghentikan container:
```bash
docker compose down
```

---

### Opsi 2: Menjalankan Tanpa Docker (Local Development Windows / Linux)

#### 1. Persyaratan Sistem
- **Python:** 3.10 atau 3.11
- **Node.js:** v18+ atau v20+
- **FFmpeg:** Terpasang di PATH atau via `imageio-ffmpeg`

#### 2. Menjalankan Backend (FastAPI)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate   # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 3. Menjalankan Frontend (Next.js)
```powershell
cd frontend
npm install
npm run dev
```
Buka browser di **http://127.0.0.1:3000**.

> **Tips Cepat Windows:** Double-click file [`start_dev.bat`](file:///d:/web_teks-to-speak/start_dev.bat) untuk menjalankan backend dan frontend sekaligus dalam satu klik.

---

## ☁️ Menjalankan Remote GPU Engine (Google Colab)

Bila Anda ingin menyintesis suara resolusi tinggi menggunakan GPU tanpa membebani laptop Intel Iris:

1. Buka file [`colab_server.ipynb`](file:///d:/web_teks-to-speak/colab_server.ipynb) di [Google Colab](https://colab.research.google.com).
2. Ubah runtime ke **T4 GPU** (*Runtime > Change runtime type > T4 GPU*).
3. Jalankan seluruh sel di notebook.
4. Salin URL publik Cloudflared yang muncul di sel terakhir, contoh:
   ```env
   REMOTE_ENGINE_URL=https://random-words.trycloudflare.com
   ```
5. Tempel URL tersebut ke file `.env` di laptop lokal Anda.
6. TaSTP akan otomatis merutekan permintaan ke Colab GPU, dan bila Colab terputus, sistem akan **otomatis fallback ke Piper lokal**.

---

## 🧪 Menjalankan Pengujian Otomatis

TaSTP dilengkapi rangkaian pengujian unit, integrasi, dan end-to-end yang menyeluruh:

### 1. Pytest Backend (55 Pengujian)
```powershell
pytest backend/tests -v
```
Semua modul diuji:
- Normalisasi angka, rupiah, tanggal, jam, singkatan Indonesia (`test_text.py`)
- Pemecahan klausa, lexicon database, dan jeda natural (`test_text.py`)
- Crossfade sambungan, sintesis naskah 2.000 karakter, hash cache (`test_pipeline_tahap4.py`)
- 22 Preset emosi, slider intensitas 0-100, efek FFmpeg (`test_emotions_tahap6.py`)
- Fallback RemoteEngine saat offline, watermark AI, validasi klon suara (`test_tahap7.py`)
- Rate limiting per IP (HTTP 429), sanitasi XSS/batas karakter, history CRUD, skenario E2E (`test_tahap8.py`)

### 2. Pengujian Frontend
```powershell
cd frontend
npm test
npm run build   # Verifikasi type-checking TypeScript & Next.js production build
```

---

## 📂 Struktur Monorepo

```
d:/web_teks-to-speak/
├─ docker-compose.yml              # Orkestrasi Docker (backend & frontend)
├─ start_dev.bat                   # Peluncur dev satu-klik Windows
├─ colab_server.ipynb              # Notebook Remote GPU Colab + Cloudflared
├─ .env.example                    # Template konfigurasi environment
├─ README.md                       # Dokumentasi utama platform
├─ docs/
│  ├─ PROJECT.md                   # Spesifikasi kebutuhan & guardrails
│  └─ ARCHITECTURE.md              # Blueprint arsitektur teknis sistem
├─ backend/
│  ├─ Dockerfile                   # Debian Slim + FFmpeg + Python
│  ├─ requirements.txt             # Dependensi FastAPI, Uvicorn, SQLite, Piper
│  ├─ storage/                     # Folder SQLite, model ONNX, dan audio
│  ├─ app/
│  │  ├─ main.py                   # Entrypoint FastAPI & middleware
│  │  ├─ config.py                 # Konfigurasi guardrail Intel Iris
│  │  ├─ database.py               # SQLite async engine
│  │  ├─ models/schema.py          # Definisi tabel DB & DTO Pydantic
│  │  ├─ engines/                  # PiperEngine, RemoteEngine (fallback)
│  │  ├─ text/                     # Normalisasi, splitter, lexicon, sanitasi
│  │  ├─ emotion/                  # 22 Preset emosi, Auto-Emotion
│  │  ├─ audio/                    # Crossfade, effects, watermark AI, clone validator
│  │  ├─ voices/                   # Registry metadata suara kreator
│  │  └─ api/                      # Endpoints: health, tts, voices, clone, projects, history
│  └─ tests/                       # Test suite pytest (55 tests)
└─ frontend/
   ├─ Dockerfile                   # Multi-stage production build Node
   ├─ package.json                 # Next.js 14, Tailwind, Zustand, wavesurfer.js
   ├─ next.config.mjs              # Proxy rewrite API ke backend
   └─ src/
      ├─ app/                      # Root layout & page
      ├─ components/
      │  ├─ layout/Sidebar.tsx     # Kolom 1: Navigasi & status hardware
      │  ├─ editor/                # Kolom 2: Naskah, toolbar, karaoke
      │  ├─ controls/              # Kolom 3: Engine, suara, emosi, efek
      │  ├─ player/                # Waveform player wavesurfer.js
      │  ├─ library/               # Voice Library (preview 3s)
      │  ├─ clone/                 # Voice Clone (consent wajib, durasi 10-30s)
      │  ├─ projects/              # Dialog Multi-Speaker & Render Gabungan
      │  ├─ history/               # Riwayat tervirtualisasi & download
      │  └─ playground/            # API Playground ala AI Studio
      ├─ store/ttsStore.ts         # Global state management Zustand
      └─ lib/api.ts                # REST API client
```

---

## ⚖️ Kepatuhan Etika AI
1. **Transparansi:** Seluruh audio yang diproduksi wajib menyertakan metadata label `"Dibuat dengan AI - TaSTP Studio"`.
2. **Kloning Suara Berizin:** Pembuatan klon vokal wajib menyertakan persetujuan tertulis pemilik suara asli melalui checkbox persetujuan yang dicatat ke database audit log.
3. **Privasi Data:** Seluruh data pemrosesan tersimpan secara lokal tanpa dikirimkan ke server komersial pihak ketiga.
