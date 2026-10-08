# Laporan Penyelesaian Tahap 5: Antarmuka Frontend Studio & Player

Tahap 5 telah selesai diimplementasikan secara komprehensif pada frontend Next.js 14 + Tailwind CSS + TypeScript + Zustand + wavesurfer.js, mematuhi batasan performa **Intel Iris (tanpa blur berat, waveform resolusi terbatas, animasi minimal)**.

---

## 1. Komponen Antarmuka yang Diterapkan

### A. Layout 3 Kolom (Dark Mode & Responsif)
- **File Utama**: `frontend/src/app/page.tsx`
  - **Kolom 1 (Sidebar Kiri)**: `frontend/src/components/layout/Sidebar.tsx`
    - Logo & branding TaSTP Studio (Self-Hosted).
    - Status Dev Machine: *Intel Iris • Piper ONNX (Online)*.
    - Menu navigasi: *Text to Speech*, *Voice Library (dengan badge jumlah suara aktif)*, *Voice Clone (Beta)*, *Projects*, *History*, dan *API Playground*.
    - Tombol kolaps sidebar untuk mode layar fleksibel.
    - Catatan etika kepatuhan AI di bagian bawah.
  - **Kolom 2 (Editor Tengah)**: `frontend/src/components/editor/EditorSection.tsx`
    - Input naskah narasi (textarea) dengan batas 5.000 karakter.
    - Penghitung karakter real-time, jumlah kata, dan estimasi waktu durasi baca (~140 kata/menit).
    - Tombol cepat *Paste from Clipboard* dan *Clear*.
    - Chip *Preset Script Prompts* (Hook TikTok, YouTube Narasi, Podcast Intro).
  - **Kolom 3 (Panel Pengaturan Kanan)**: `frontend/src/components/controls/ControlPanel.tsx`
    - Pemilih TTS Engine (Piper ONNX lokal vs Remote GPU).
    - Pemilih Karakter Suara Bahasa Indonesia dengan metadata kategori & gender.
    - Slider Kecepatan Bicara (0.5x – 2.0x).
    - Slider Tinggi Nada / Pitch (-5.0 – +5.0 semitone).
    - **Slider Durasi Jeda Koma & Titik (0.5x – 2.0x)**.
    - Pilihan Efek Audio Server (Studio Murni, Podcast Warm EQ, Radio HT, Gema Aula).
    - Checkbox Etika Voice Clone (Wajib persetujuan pemilik suara).
    - Tombol **Generate Suara** dilengkapi *progress bar real-time* (0% – 100%) dan keterangan tahap pemrosesan.

### B. Audio Player Kustom & WaveSurfer (Hemat CPU)
- **Komponen Player Bar**: `frontend/src/components/player/AudioPlayerBar.tsx`
- **Waveform Visualizer**: `frontend/src/components/player/WaveformView.tsx`
  - Mengintegrasikan **`wavesurfer.js` v8** dengan parameter performa terbatas:
    - Tinggi: 44px
    - Lebar bar: 2px, jarak antar bar: 2px, radius: 2px.
    - Warna: `#334155` (background bar), `#f59e0b` (progress amber).
    - Resolusi dibatasi agar tidak mengonsumsi resource grafis laptop Intel Iris.
  - Kontrol: Play / Pause, Restart dari awal, Timecode (`00:00 / 02:27`), tombol Pengatur Kecepatan Playback (1.0x, 1.25x, 1.5x), dan tombol **Unduh WAV**.
  - Badge disclosure etis: *"Dibuat dengan AI"*.

### C. Sorot Kalimat Aktif (*Karaoke Sentence Highlighting*)
- Terintegrasi di `EditorSection.tsx`:
  - Tombol alih mode di header editor: **Teks** $\leftrightarrow$ **Karaoke Highlight**.
  - Saat audio diputar, kalimat yang sedang diucapkan otomatis menyala dengan aksen amber (`bg-accent/15 border-accent text-fg font-medium scale-[1.01]`) dan ikon indikator suara.
  - **Fitur Interaktif**: Pengguna dapat mengklik kalimat mana saja dalam daftar untuk langsung melompat (*seek*) pemutaran audio ke kalimat tersebut.

### D. Halaman Voice Library dengan Pratinjau 3 Detik
- **Komponen**: `frontend/src/components/library/VoiceLibrary.tsx`
  - Grid kartu model suara Indonesia dari backend (`id_ID-news_tts-medium`, `piper_id_gadis_fast`, `piper_id_bima_narrator`, `piper_id_siti_podcast`, `piper_id_dimas_news`).
  - Fitur pencarian instan dan filter kategori: *Semua*, *TikTok & Reels*, *Narator YouTube*, *Podcast*, *Berita & Edukasi*.
  - **Tombol Preview 3 Detik**: Menyintesis cuplikan pendek 3 detik langsung dari backend dan memutarnya dengan status tombol dinamis.
  - **Tombol Pilih Suara**: Memilih suara dan langsung mengarahkan pengguna kembali ke Text-to-Speech Studio.

### E. Integrasi State Zustand & Proxy API
- **Store Zustand**: `frontend/src/store/ttsStore.ts`
  - Mengelola sinkronisasi reaktif seluruh parameter studio, riwayat timing kalimat, progress generate, dan playback audio.
- **Client API**: `frontend/src/lib/api.ts`
- **Proxy Rewrites**: `frontend/next.config.mjs`
  - Meneruskan endpoint `/tts`, `/voices`, `/jobs/:path*`, dan `/api/:path*` langsung ke backend FastAPI port 8000 tanpa kendala CORS.

---

## 2. Checklist Pengujian Tahap 5

| Pengujian | Status | Bukti / Hasil |
|---|---|---|
| **Layout 3 Kolom Dark Mode** | **LULUS** | Sidebar kiri, editor naskah, control panel kanan tersusun rapi |
| **Katalog Suara di Load** | **LULUS** | 5 model suara Indonesia tampil di pemilih suara & Voice Library |
| **Slider Speed, Pitch & Jeda** | **LULUS** | Slider responsif (Speed 0.5-2.0x, Pitch -5 s/d +5, Jeda 0.5-2.0x) |
| **Generate dari UI via Proxy** | **LULUS** | `POST http://127.0.0.1:3000/tts` berhasil mengembalikan Job ID |
| **Unduh Audio WAV** | **LULUS** | `GET http://127.0.0.1:3000/api/audio/{jobId}` mengunduh file WAV 250 KB |
| **Audio Player & WaveSurfer** | **LULUS** | Render waveform 44px hemat CPU dengan scrubber & play/pause |
| **Karaoke Highlight Kalimat** | **LULUS** | Pembagian kalimat natural & penyorotan kalimat aktif saat playback |
| **Voice Library Preview 3s** | **LULUS** | Cuplikan audio 3 detik siap putar dengan filter kategori |

---

## 3. URL Akses Langsung

- **Frontend Studio TaSTP**: `http://127.0.0.1:3000`
- **Backend API Docs (Swagger)**: `http://127.0.0.1:8000/docs`
