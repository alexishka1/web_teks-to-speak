# PROJECT: [TaSTP] - Platform Text-to-Speech Self-Hosted

## 1. Tujuan
Website TTS bergaya ElevenLabs / Google AI Studio, TANPA API provider pihak ketiga. Semua suara dihasilkan model open-source di server sendiri. Suara harus senatural mungkin (tidak terdengar robotik).

## 2. Identitas & Tema
- **Nama Proyek:** TaSTP (Text-to-Speech Platform)
- **Tema / Niche:** Kreator Konten & Video (YouTube, TikTok, Reels, Podcast, Voiceover)
- **Bahasa UI:** Indonesia
- **Mode Tampilan:** Dark mode default

## 3. Batasan Hardware (WAJIB DIPATUHI)
- **Mesin Dev:** Laptop Intel Iris (tanpa CUDA GPU), RAM 4/8/16 GB.
- **Engine Default:** Piper (ONNX, CPU only). Jangan muat model PyTorch berat saat startup. Wajib *lazy-load* model ketika dibutuhkan saja.
- **Model GPU Berat:** Dijalankan secara jarak jauh (Colab / Kaggle / GPU sewaan) lewat `RemoteEngine` dengan mekanisme *fallback* otomatis ke Piper jika server GPU offline/timeout.
- **Frontend Ringan:** Tanpa blur/glassmorphism berat, list tervirtualisasi, resolusi waveform dibatasi, efek audio diproses dan dirender di server.

## 4. Stack Teknologi
- **Frontend:** Next.js + TypeScript + Tailwind CSS + wavesurfer.js + zustand
- **Backend:** Python FastAPI, ffmpeg, pydub
- **Database:** SQLite (dev) + Antrean job sederhana
- **Deployment:** Docker Compose untuk menjalankan frontend & backend secara terisolasi.

## 5. Layout Antarmuka (3 Kolom)
- **Kolom 1 (Sidebar):** Text to Speech, Voice Library, Voice Clone, Projects, History, API Playground.
- **Kolom 2 (Editor Tengah):** Naskah narasi, counter kata/karakter, toolbar paste/clear, quick prompt kreator.
- **Kolom 3 (Panel Kanan):** Pemilih engine, pemilih suara, slider kecepatan/nada, efek audio server, tombol Generate.

## 6. Arsitektur Backend
- `engines/`: piper, remote, f5tts (opsional), satu interface tunggal `TTSEngine`
- `text/`: normalisasi teks Indonesia, splitter/chunking, lexicon/kamus pelafalan
- `emotion/`: pemetaan ekspresi & prosodi vokal
- `audio/`: pemrosesan ffmpeg, loudness normalization, audio watermarking
- `voices/`: registry metadata suara dan konfigurasi model
- `queue/`: antrean job eksekusi sintesis
- `api/`: REST API FastAPI

## 7. Etika & Kepatuhan AI
- Fitur Voice Clone wajib menyertakan checkbox persetujuan pemilik suara asli.
- Seluruh audio yang dihasilkan wajib diberi label/watermark visual & metadata audio "Dibuat dengan AI".
- Menerapkan validasi input ketat dan proteksi rate limiting.
