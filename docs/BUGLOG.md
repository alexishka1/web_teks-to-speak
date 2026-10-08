# Catatan Temuan & Resolusi Bug (BUGLOG) - TaSTP

Dokumen ini mencatat setiap kendala teknis dan bug yang ditemukan selama siklus pengembangan platform TaSTP, lengkap dengan akar penyebab, perbaikan yang diterapkan, dan tes pencegahan regresi.

---

## Format Template Standar Log Bug

Setiap entri bug wajib mengikuti struktur berikut:
- **ID:** Kode unik (e.g., `BUG-001`)
- **Tanggal:** Tanggal penemuan (YYYY-MM-DD)
- **Gejala:** Deskripsi error atau perilaku tidak normal
- **Langkah Reproduksi:** Urutan tindakan untuk memicu bug
- **Akar Masalah:** Analisis penyebab dasar di tingkat kode atau arsitektur
- **Perbaikan:** Kode atau konfigurasi yang diubah
- **Tes Pencegah:** Uji otomatis yang ditambahkan/dijalankan agar bug tidak terulang

---

## Daftar Riwayat Bug

### BUG-001
- **ID:** BUG-001
- **Tanggal:** 2026-10-07
- **Gejala:** `sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: voice_clone_logs.id` saat test suite dijalankan untuk kedua kalinya.
- **Langkah Reproduksi:** Jalankan `pytest backend/tests/test_tahap7.py` dua kali berturut-turut pada database SQLite persisten.
- **Akar Masalah:** File `test_tahap7.py` menggunakan ID statis `"clone_test_consent_001"` untuk menyimpan data ke database SQLite (`tastp.db`), sehingga pada eksekusi kedua ID tersebut bertabrakan dengan data lama.
- **Perbaikan:** Mengubah instansiasi ID menggunakan UUID acak:
  ```python
  clone_id = f"clone_test_consent_{uuid.uuid4().hex[:8]}"
  ```
- **Tes Pencegah:** `test_voice_clone_mandatory_consent_and_db_log` di `backend/tests/test_tahap7.py` berjalan bersih dan idempoten pada eksekusi berulang.

---

### BUG-002
- **ID:** BUG-002
- **Tanggal:** 2026-10-07
- **Gejala:** Server FastAPI melempar `RuntimeError: Form data requires "python-multipart" to be installed` saat endpoint `POST /api/voice-clone/upload` dimuat.
- **Langkah Reproduksi:** Kirim request `multipart/form-data` ke `/api/voice-clone/upload` pada instalasi FastAPI murni tanpa paket form.
- **Akar Masalah:** Pustaka FastAPI memerlukan dependensi opsional `python-multipart` untuk memproses parameter `File(...)` dan `Form(...)`.
- **Perbaikan:** Memasang `python-multipart` dan menyematkannya secara resmi pada [`backend/requirements.txt`](../backend/requirements.txt).
- **Tes Pencegah:** Verifikasi endpoint upload via automated tests dan startup server FastAPI.

---

### BUG-003
- **ID:** BUG-003
- **Tanggal:** 2026-10-07
- **Gejala:** Perintah `npm run build` berhenti dengan pesan error `ESLint must be installed in order to run during builds`.
- **Langkah Reproduksi:** Jalankan `next build` ketika file `.eslintrc.json` ada tetapi paket `eslint` belum terdaftar di `devDependencies`.
- **Akar Masalah:** Next.js mendeteksi konfigurasi ESLint lokal dan memicu pengecekan sebelum dependensi tersedia di lingkungan CI/dev.
- **Perbaikan:** Memasang `eslint@8.57.0` dan `eslint-config-next@14.2.35` secara resmi pada `devDependencies` frontend serta mengonfigurasi `.eslintrc.json` standar.
- **Tes Pencegah:** Langkah `npx eslint src` dan `npm run build` dijalankan di setiap scan otomatis.

---

### BUG-004
- **ID:** BUG-004
- **Tanggal:** 2026-10-07
- **Gejala:** `ModuleNotFoundError: No module named 'app'` saat memanggil `pytest backend/tests/test_tahap7.py`.
- **Langkah Reproduksi:** Jalankan pytest langsung dari root folder tanpa mengekspor environment variable `PYTHONPATH=backend`.
- **Akar Masalah:** Direktori `backend/` tidak otomatis terdaftar di `sys.path` Python saat pytest dipanggil tanpa argumen modul.
- **Perbaikan:**
  1. Menambahkan resolusi path otomatis di header file tes:
     ```python
     backend_dir = Path(__file__).resolve().parent.parent
     if str(backend_dir) not in sys.path:
         sys.path.insert(0, str(backend_dir))
     ```
  2. Mendaftarkan `pythonpath = ["backend"]` di [`pyproject.toml`](../pyproject.toml).
- **Tes Pencegah:** Eksekusi `pytest backend/tests` langsung dari root berjalan sukses di semua OS.

---

### BUG-005
- **ID:** BUG-005
- **Tanggal:** 2026-10-07
- **Gejala:** Skrip runner melempar `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'` di terminal Windows.
- **Langkah Reproduksi:** Jalankan runner Python di terminal Windows PowerShell atau CMD dengan default code page cp1252.
- **Akar Masalah:** Default console codepage Windows tidak mendukung karakter multi-byte emoji Unicode secara native tanpa konfigurasi encoding stdout eksplisit.
- **Perbaikan:**
  1. Menyetel `sys.stdout.reconfigure(encoding="utf-8")` saat inisialisasi runner.
  2. Mengganti simbol emoji dengan label teks ASCII standar `[PASS]`, `[FAIL]`, dan `[SUCCESS]`.
- **Tes Pencegah:** Eksekusi `scripts/scan.py` di terminal Windows murni tanpa exception encoding.

---

### BUG-006
- **ID:** BUG-006
- **Tanggal:** 2026-10-07
- **Gejala:** `FileNotFoundError: [WinError 2] The system cannot find the file specified: 'npm.cmd'` saat subproses Python memanggil NPM.
- **Langkah Reproduksi:** Jalankan subprocess `npm.cmd` dari Python runner pada lingkungan di mana Node.js berada di `%LOCALAPPDATA%\nodejs` yang belum terdaftar di PATH global.
- **Akar Masalah:** Subproses anak yang di-spawn oleh Python tidak mewarisi path kustom yang hanya diatur sementara di sesi terminal induk.
- **Perbaikan:** Menambahkan auto-discovery direktori Node.js dan menginjeksikannya langsung ke `os.environ["PATH"]` sebelum mengeksekusi subproses.
- **Tes Pencegah:** `scripts/scan.py` dapat menjalankan `npx.cmd` dan `npm.cmd` tanpa konfigurasi manual user.

---

### BUG-007
- **ID:** BUG-007
- **Tanggal:** 2026-10-07
- **Gejala:** Pengujian Playwright E2E gagal pada assertion `expect(downloadHref).toMatch(/\.wav$/i)`.
- **Langkah Reproduksi:** Jalankan `npx playwright test` pada flow TTS di mana link download memiliki format streaming API `/api/audio/{job_id}`.
- **Akar Masalah:** Endpoint audio backend melayani audio melalui rute API `/api/audio/{job_id}`, sedangkan nama file WAV (`tastp-output.wav`) ditentukan oleh atribut HTML `download`. Memeriksa ekstensi hanya pada `href` menyebabkan false-negative.
- **Perbaikan:**
  1. Mengubah pattern matcher `downloadHref` agar menerima URL format `/api/audio/`.
  2. Menambahkan verifikasi eksplisit atribut `download` yang harus berakhiran `.wav`.
  3. Memverifikasi `download.suggestedFilename()` pada event download aktual.
- **Tes Pencegah:** Test suite Playwright `frontend/e2e/tts-flow.spec.ts` lulus 100% pada pengetesan browser Chromium.

---

### BUG-008
- **ID:** BUG-008
- **Tanggal:** 2026-10-07
- **Gejala:** `pydantic_core._pydantic_core.ValidationError: 1 validation error for StylePresetDTO created_at Field required` saat payload pembuatan preset dikirim ke API.
- **Langkah Reproduksi:** Kirim permintaan `POST /api/studio/presets` dengan atribut data preset tanpa menyertakan `created_at`.
- **Akar Masalah:** Skema Pydantic `StylePresetDTO` mendeklarasikan atribut `created_at: str` tanpa nilai default / factory, sehingga validasi gagal saat client mengirim payload baru.
- **Perbaikan:** Menambahkan `default_factory=lambda: datetime.utcnow().isoformat()` pada field `created_at` di [`backend/app/models/schema.py`](../backend/app/models/schema.py).
- **Tes Pencegah:** Endpoint `POST /api/studio/presets` diverifikasi dalam test suite `backend/tests/test_tahap11.py`.

---

### BUG-009
- **ID:** BUG-009
- **Tanggal:** 2026-10-07
- **Gejala:** `sqlite3.IntegrityError: NOT NULL constraint failed: voices.model_path` saat menambahkan metadata suara via API studio.
- **Langkah Reproduksi:** Eksekusi `POST /api/studio/voices` dengan metadata suara tanpa mengisi path file lokal.
- **Akar Masalah:** Kolom `model_path` pada model SQLModel `VoiceRecord` bertipe `str` wajib tanpa penanda `nullable=True` atau `default=None`.
- **Perbaikan:** Mengubah tipe menjadi `model_path: str | None = Field(default=None)` di [`backend/app/models/schema.py`](../backend/app/models/schema.py).
- **Tes Pencegah:** Eksekusi `test_voices_crud_and_hot_reload` di `backend/tests/test_tahap11.py` berhasil menyimpan dan memperbarui data suara.

---

### BUG-010
- **ID:** BUG-010
- **Tanggal:** 2026-10-07
- **Gejala:** `Incompatible types in assignment (expression has type "dict_values[str, EmotionPreset]", variable has type "list[EmotionPreset]")` dilaporkan oleh Mypy.
- **Langkah Reproduksi:** Jalankan `mypy backend` setelah menambahkan fungsi helper sinkronisasi `sync_emotions_from_db`.
- **Akar Masalah:** Objek `dict_values` di-assign langsung ke anotasi `list[EmotionPreset]` tanpa pemanggilan konstruktor `list()`.
- **Perbaikan:** Membungkus kembalian dengan `list(EMOTION_CATALOG.values())` dan memperjelas anotasi tipe di [`backend/app/emotion/presets.py`](../backend/app/emotion/presets.py).
- **Tes Pencegah:** Pengecekan statis Mypy (`mypy backend`) lolos tanpa error type (47 source files).

---

### BUG-011
- **ID:** BUG-011
- **Tanggal:** 2026-10-07
- **Gejala:** `strict mode violation: getByText('Suara Tes Studio') resolved to 3 elements` pada pengetesan Playwright E2E Studio Manager.
- **Langkah Reproduksi:** Jalankan `npx playwright test frontend/e2e/studio-manager.spec.ts` setelah submit form upload suara.
- **Akar Masalah:** String nama suara muncul di toast notifikasi, header kartu, dan meta detail kartu secara serempak sehingga selector teks umum ambigu.
- **Perbaikan:** Mengganti locator menjadi berbasis role semantik eksplisit: `page.getByRole("heading", { name: testVoiceName })`.
- **Tes Pencegah:** Test suite Playwright `frontend/e2e/studio-manager.spec.ts` berjalan deterministik dan stabil.

---

### BUG-012
- **ID:** BUG-012
- **Tanggal:** 2026-10-07
- **Gejala:** `NameError: name 'Any' is not defined` pada `backend/app/models/schema.py` saat memuat skema `VoiceCloneResponse`.
- **Langkah Reproduksi:** Jalankan `pytest backend/tests/test_voice_clone_advanced.py` setelah menambahkan field `quality: dict[str, Any] | None`.
- **Akar Masalah:** Anotasi tipe `Any` digunakan pada deklarasi skema Pydantic tanpa diimpor dari modul `typing`.
- **Perbaikan:** Menambahkan `from typing import Any` pada baris atas [`backend/app/models/schema.py`](../backend/app/models/schema.py).
- **Tes Pencegah:** Test suite `pytest backend/tests/test_voice_clone_advanced.py` memuat skema dan mengeksekusi tes dengan sukses.

---

### BUG-013
- **ID:** BUG-013
- **Tanggal:** 2026-10-07
- **Gejala:** Permintaan `POST /api/voice-clone/compare-ab` menghasilkan `404 Not Found` pada pengetesan browser E2E Playwright.
- **Langkah Reproduksi:** Panggil endpoint komparasi A/B saat server uvicorn latar belakang masih menjalankan kode lama sebelum endpoint didaftarkan.
- **Akar Masalah:** Instance uvicorn latar belakang tidak menggunakan auto-reload dinamis, sehingga pembaruan pada router `clone.py` belum dimuat ke proses yang aktif.
- **Perbaikan:** Me-restart proses uvicorn secara terkoordinasi dan memverifikasi endpoint via health check sebelum pengetesan.
- **Tes Pencegah:** Test suite Playwright `frontend/e2e/voice-clone.spec.ts` berhasil mengeksekusi komparasi A/B dengan status 200 OK.

---

### BUG-014
- **ID:** BUG-014
- **Tanggal:** 2026-10-07
- **Gejala:** Assertion Playwright `expect(page.locator("#voice-selector")).toBeVisible()` gagal akibat elemen ID tidak ditemukan di DOM.
- **Langkah Reproduksi:** Jalankan tes E2E untuk memverifikasi kemunculan suara klon di tab Text to Speech.
- **Akar Masalah:** UI panel kontrol menggunakan daftar button interaktif dalam kontainer fleksibel, bukan elemen native `<select id="voice-selector">`.
- **Perbaikan:** Menyematkan atribut ID eksplisit `#voice-selection-list` pada kontainer daftar suara di [`frontend/src/components/controls/ControlPanel.tsx`](../frontend/src/components/controls/ControlPanel.tsx).
- **Tes Pencegah:** Playwright E2E assertion memverifikasi `#voice-selection-list` secara andal.

---

### BUG-015
- **ID:** BUG-015
- **Tanggal:** 2026-10-07
- **Gejala:** `I001 Import block is un-sorted or un-formatted` dilaporkan oleh Ruff pada [`backend/app/models/schema.py`](../backend/app/models/schema.py).
- **Langkah Reproduksi:** Jalankan `ruff check backend` setelah menambahkan impor manual `from typing import Any`.
- **Akar Masalah:** Urutan baris impor modul pustaka standar tidak sesuai konvensi pengurutan alfabetis isort/ruff.
- **Perbaikan:** Menjalankan pemformatan otomatis `ruff check --fix backend` dan `ruff format backend`.
- **Tes Pencegah:** Pengecekan Ruff format dan lint pada `scripts/scan.py` lulus 100%.

---

### BUG-016
- **ID:** BUG-016
- **Tanggal:** 2026-10-07
- **Gejala:** Tampilan UI di browser tampak polos (*unstyled HTML* / font Times New Roman / tanpa CSS dark mode).
- **Langkah Reproduksi:** Jalankan `npm run build` (`next build`) saat proses `next dev` sedang aktif di latar belakang, lalu muat ulang halaman browser di `http://127.0.0.1:3000`.
- **Akar Masalah:** Perintah `next build` menimpa direktori artefak `.next` dengan bundle produksi, sehingga compiler in-memory `next dev` kehilangan pemetaan chunk dan request file stylesheet `/_next/static/css/app/layout.css` menghasilkan `404 Not Found`.
- **Perbaikan:**
  1. Menghentikan instance dev server yang terganggu.
  2. Membersihkan direktori cache `frontend/.next` (`Remove-Item -Recurse -Force frontend/.next`).
  3. Menjalankan ulang server Next.js dev secara bersih (`npm run dev`).
- **Tes Pencegah:** Verifikasi HTTP 200 pada request file stylesheet `layout.css` (51.503 bytes) dan inspeksi screenshot Chromium Playwright membuktikan seluruh tampilan dark mode ter-render sempurna.

---

### BUG-017
- **ID:** BUG-017
- **Tanggal:** 2026-10-08
- **Gejala:** `NameError: name 'jitter_speed' is not defined` / `ruff F821` pada `backend/app/audio/pipeline.py`.
- **Langkah Reproduksi:** Jalankan `ruff check --select F821 backend/app` atau picu sintesis kalimat multi-prosodi.
- **Akar Masalah:** Variabel lama `jitter_speed` dan `jitter_pitch` belum didefinisikan di dalam perulangan kalimat setelah refactoring stabilisasi parameter emosi.
- **Perbaikan:** Mengganti referensi variabel ke `sent_speed` dan `sent_pitch` yang terkalibrasi secara deterministik dari preset emosi.
- **Tes Pencegah:** `ruff check --select F821 backend/app` dijalankan di CI lint pipeline tanpa error F821.

---

### BUG-018
- **ID:** BUG-018
- **Tanggal:** 2026-10-08
- **Gejala:** Audio terdengar seperti nada dengung sintetis monoton (sine wave 125 Hz/195 Hz) tanpa suara manusia asli saat model ONNX tidak ditemukan.
- **Langkah Reproduksi:** Hapus file `.onnx` dari `backend/storage/models/` lalu panggil endpoint `/api/tts`.
- **Akar Masalah:** `PiperEngine._synthesize_fallback()` secara diam-diam (*silent fallback*) menghasilkan gelombang sinus daripada melaporkan ketiadaan model saraf ONNX ke pengguna.
- **Perbaikan:** Menghapus fallback diam-diam. Sistem kini melempar exception keras `FileNotFoundError` dan mengembalikan HTTP 503 dengan instruksi unduh model yang jelas, kecuali jika `settings.DEBUG_ALLOW_FALLBACK_TONE` diaktifkan secara eksplisit.
- **Tes Pencegah:** Verifikasi `/health` endpoint memvalidasi keberadaan model fisik dan pipeline menolak sintesis tanpa file ONNX valid.

---

### BUG-019
- **ID:** BUG-019
- **Tanggal:** 2026-10-08
- **Gejala:** Variasi preset emosi (gembira, sedih, marah) tidak mengubah warna suara, nada suara terdengar seragam dan datar.
- **Langkah Reproduksi:** Sintesis teks dengan emosi `gembira` dan bandingkan dengan `sedih`; spektrum frekuensi F0 dan intonasi vokal hampir identik.
- **Akar Masalah:** Piper ONNX murni hanya menerima parameter `length_scale`. Parameter `pitch` dari emosi diabaikan oleh engine, `pause_scale` tertimpa slider global, dan `noise_scale` / `noise_w_scale` tidak pernah dikirim ke `SynthesisConfig`.
- **Perbaikan:**
  1. Menambahkan eksposur `noise_scale` dan `noise_w_scale` pada `SynthesisConfig` PiperEngine serta memetakannya secara dinamis berdasarkan emosi (mis. gembira = noise_scale 0.88, noise_w_scale 1.15; sedih = 0.65 / 0.75).
  2. Menerapkan modulasi pitch lembut (-2.5 s/d +2.5 semitones) per kalimat via FFmpeg sebelum penggabungan audio.
  3. Mengalikan `pause_scale` emosi ke jeda inter-kalimat dan menerapkan efek akustik emosi ketika efek global bernilai "none".
- **Tes Pencegah:** Skrip `scripts/voice_report.py` memvalidasi perbedaan objektif Mean F0 dan Std F0 antar emosi (Std F0 meningkat hingga ±107.6 Hz pada emosi marah).

---

### BUG-020
- **ID:** BUG-020
- **Tanggal:** 2026-10-08
- **Gejala:** Kegagalan pengujian unit `test_lexicon_in_memory_default_rules` di `backend/tests/test_text.py` (`AssertionError: assert 'yu-tyub' in ...`).
- **Langkah Reproduksi:** Jalankan `pytest backend/tests/test_text.py`.
- **Akar Masalah:** Nilai transliterasi di `DEFAULT_LEXICON` menggunakan format tanpa tanda hubung (`"yutyub"`, `"tiktok"`, `"podkes"`) sedangkan assertion tes mengharuskan pelafalan berpemisah suku kata fonetik (`"yu-tyub"`, `"tik-tok"`, `"pod-kes"`).
- **Perbaikan:** Menyesuaikan entri default di `DEFAULT_LEXICON` pada `backend/app/text/lexicon.py` menjadi bentuk bersuku kata fonetik standar.
- **Tes Pencegah:** Seluruh 39 uji coba modul pemrosesan teks lulus 100%.

---

### BUG-021
- **ID:** BUG-021
- **Tanggal:** 2026-10-08
- **Gejala:** `AssertionError: assert 9512 == 3118` pada `test_equal_power_crossfade_continuity`.
- **Langkah Reproduksi:** Jalankan `pytest backend/tests/test_pipeline_tahap4.py::test_equal_power_crossfade_continuity`.
- **Akar Masalah:** Fungsi `crossfade_pcm` menyematkan parameter default `pause_ms = 250` yang menyisipkan sampel jeda hening antar chunk alih-alih melakukan overlapping crossfade bertenaga seimbang (*equal-power crossfade*).
- **Perbaikan:** Mengubah default `pause_ms = 0` pada `crossfade_pcm`. Jika `pause_ms == 0`, fungsi melakukan overlapping crossfade murni dengan kurva sinus-kosinus; jika `pause_ms > 0`, fungsi menerapkan micro fade-in/fade-out dengan jeda bernafas natural.
- **Tes Pencegah:** Test `test_equal_power_crossfade_continuity` dan tes sintesis naskah 2000 karakter lulus sempurna.





