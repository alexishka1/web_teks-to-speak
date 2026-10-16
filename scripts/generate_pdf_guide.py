"""
Script untuk menghasilkan Panduan Menghidupkan Server TaSTP Studio dalam format PDF
menggunakan ReportLab dengan tata letak profesional dan bersih.
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas khusus untuk menambahkan running header dan footer halaman 'Hal X dari Y'."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (mulai halaman 2)
        if self._pageNumber > 1:
            self.drawString(54, 800, "TaSTP Studio - Panduan Menghidupkan Server")
            self.drawRightString(A4[0] - 54, 800, "Self-Hosted Voice Clone & TTS")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 792, A4[0] - 54, 792)

        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, A4[0] - 54, 45)
        self.drawString(54, 32, "Dokumen Panduan Teknis | TaSTP Studio v1.0")
        self.drawRightString(A4[0] - 54, 32, f"Halaman {self._pageNumber} dari {page_count}")
        self.restoreState()


def build_pdf_guide(output_pdf_path: Path):
    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Warna Tema
    c_primary = colors.HexColor("#0F172A")    # Slate 900
    c_secondary = colors.HexColor("#2563EB")  # Blue 600
    c_dark = colors.HexColor("#1E293B")       # Slate 800
    c_muted = colors.HexColor("#475569")      # Slate 600
    c_bg_code = colors.HexColor("#F8FAFC")    # Slate 50
    c_border = colors.HexColor("#E2E8F0")     # Slate 200
    c_accent_bg = colors.HexColor("#EFF6FF")  # Blue 50

    # Custom Paragraph Styles
    style_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=4,
    )

    style_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=c_secondary,
        spaceAfter=14,
    )

    style_h1 = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    style_h2 = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=c_dark,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    style_body = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=c_dark,
        spaceAfter=6,
    )

    style_body_bold = ParagraphStyle(
        "BodyDarkBold",
        parent=style_body,
        fontName="Helvetica-Bold",
    )

    style_code = ParagraphStyle(
        "CodeBlock",
        parent=styles["Normal"],
        fontName="Courier-Bold",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0F172A"),
    )

    style_callout = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#1E3A8A"),
    )

    style_th = ParagraphStyle(
        "TableHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    style_td = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=c_dark,
    )

    story = []

    story.append(Paragraph("TaSTP Studio - Panduan Menghidupkan Server", style_title))
    story.append(Paragraph("Panduan Operasional Lengkap: Backend FastAPI & Frontend Next.js", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceAfter=12))

    # Ringkasan Eksekutif Box
    intro_html = (
        "<b>TaSTP Studio</b> adalah sistem produksi suara berbasis web yang menggabungkan backend "
        "<b>FastAPI (Python)</b> untuk pipeline pemrosesan audio & AI, serta frontend <b>Next.js (React)</b> "
        "untuk antarmuka visual studio. Dokumen ini menjelaskan cara menghidupkan dan mengelola kedua server tersebut."
    )
    story.append(
        Table(
            [[Paragraph(intro_html, style_callout)]],
            colWidths=[A4[0] - 108],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), c_accent_bg),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#BFDBFE")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]),
        )
    )
    story.append(Spacer(1, 10))

    # ==========================
    # 1. ARSITEKTUR & PORT
    # ==========================
    story.append(Paragraph("1. Arsitektur Komponen & Port Jaringan", style_h1))
    story.append(Paragraph("Sebelum menjalankan aplikasi, pastikan port jaringan berikut tersedia di komputer Anda:", style_body))

    arch_data = [
        [Paragraph("Komponen", style_th), Paragraph("Teknologi", style_th), Paragraph("Port / URL", style_th), Paragraph("Fungsi Utama", style_th)],
        [
            Paragraph("<b>Backend API</b>", style_td),
            Paragraph("FastAPI / Uvicorn", style_td),
            Paragraph("<b>127.0.0.1:8000</b>", style_td),
            Paragraph("Pipeline sintesis suara, integrasi Gemini AI, Piper ONNX, SQLite DB", style_td),
        ],
        [
            Paragraph("<b>Frontend UI</b>", style_td),
            Paragraph("Next.js 14 / React", style_td),
            Paragraph("<b>127.0.0.1:3000</b>", style_td),
            Paragraph("Studio editor naskah, perekam suara, library klon, pemutar audio", style_td),
        ],
        [
            Paragraph("<b>Dokumentasi API</b>", style_td),
            Paragraph("Swagger UI", style_td),
            Paragraph("<b>127.0.0.1:8000/docs</b>", style_td),
            Paragraph("Dokumentasi interaktif endpoint REST API TaSTP", style_td),
        ],
    ]
    t_arch = Table(arch_data, colWidths=[105, 95, 115, 172])
    t_arch.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_code]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 12))

    # ==========================
    # 2. METODE CEPAT (1 KLIK)
    # ==========================
    story.append(Paragraph("2. Cara Praktis: Menjalankan dengan 1 Klik (Rekomendasi)", style_h1))
    story.append(Paragraph(
        "Di dalam folder utama proyek sudah disediakan file skrip otomasi <b>start_dev.bat</b>. "
        "Skrip ini secara otomatis menyalakan Backend FastAPI di jendela terminal baru, kemudian "
        "menjalankan Frontend Next.js dan langsung membuka browser ke alamat studio.",
        style_body
    ))

    step1_box = [
        [Paragraph(
            "<b>Langkah Menjalankan:</b><br/>"
            "1. Buka folder proyek di File Explorer: <code>c:\\Users\\ASUS\\Downloads\\web_teks-to-speak</code><br/>"
            "2. Klik ganda (double-click) pada file <b>start_dev.bat</b>.<br/>"
            "3. Dua terminal otomatis aktif (Backend & Frontend) dan browser akan membuka <b>http://127.0.0.1:3000/</b>.<br/>"
            "4. Biarkan kedua jendela terminal tetap terbuka selama Anda menggunakan studio.",
            style_body
        )]
    ]
    t_step1 = Table(step1_box, colWidths=[A4[0] - 108])
    t_step1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_step1)
    story.append(Spacer(1, 14))

    # Pindah halaman secara teratur agar Bagian 3 Manual & Troubleshooting utuh di Halaman 2
    from reportlab.platypus import PageBreak
    story.append(PageBreak())

    # ==========================
    # 3. METODE MANUAL (DUA TERMINAL)
    # ==========================
    story.append(Paragraph("3. Cara Manual: Melalui Terminal (Command Prompt / PowerShell)", style_h1))
    story.append(Paragraph(
        "Jika Anda ingin memantau log sistem secara langsung atau melakukan debugging, jalankan kedua server "
        "menggunakan 2 jendela terminal terpisah sebagai berikut:",
        style_body
    ))

    # Terminal 1: Backend
    story.append(Paragraph("Langkah A: Menghidupkan Backend FastAPI (Terminal 1)", style_h2))
    story.append(Paragraph("Buka Terminal 1 (PowerShell atau CMD) lalu jalankan baris perintah berikut:", style_body))

    cmd_backend = (
        "cd c:\\Users\\ASUS\\Downloads\\web_teks-to-speak\\backend<br/>"
        "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
    )
    t_cmd1 = Table([[Paragraph(cmd_backend, style_code)]], colWidths=[A4[0] - 108])
    t_cmd1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_bg_code),
        ("BOX", (0, 0), (-1, -1), 1, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_cmd1)
    story.append(Paragraph(
        "<i>Tanda Berhasil:</i> Muncul pesan <code>Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)</code>.",
        style_body
    ))
    story.append(Spacer(1, 6))

    # Terminal 2: Frontend
    story.append(Paragraph("Langkah B: Menghidupkan Frontend Next.js (Terminal 2)", style_h2))
    story.append(Paragraph("Buka Terminal 2 baru (jangan menutup Terminal 1) lalu jalankan perintah berikut:", style_body))

    cmd_frontend = (
        "cd c:\\Users\\ASUS\\Downloads\\web_teks-to-speak\\frontend<br/>"
        "npm run dev"
    )
    t_cmd2 = Table([[Paragraph(cmd_frontend, style_code)]], colWidths=[A4[0] - 108])
    t_cmd2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_bg_code),
        ("BOX", (0, 0), (-1, -1), 1, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_cmd2)
    story.append(Paragraph(
        "<i>Tanda Berhasil:</i> Muncul pesan <code>Ready in ...ms - Local: http://localhost:3000</code>.<br/>"
        "Sekarang buka browser Google Chrome / Edge ke alamat: <b>http://127.0.0.1:3000</b>.",
        style_body
    ))
    story.append(Spacer(1, 10))

    # ==========================
    # 4. KONFIGURASI .ENV & API KEY
    # ==========================
    story.append(Paragraph("4. Pengaturan API Key & Konfigurasi (.env)", style_h1))
    story.append(Paragraph(
        "Sistem menyimpan konfigurasi koneksi Google Gemini TTS pada file <b>backend/.env</b>. "
        "Pastikan isi file memuat baris konfigurasi berikut agar fitur Gemini Studio TTS berfungsi optimal:",
        style_body
    ))

    env_content = (
        "# backend/.env<br/>"
        "ONLINE_ENGINES_ENABLED=true<br/>"
        "GEMINI_API_KEY=masukkan_gemini_api_key_anda_disini<br/>"
        "GEMINI_MODEL=gemini-3.8-flash-tts"
    )
    t_env = Table([[Paragraph(env_content, style_code)]], colWidths=[A4[0] - 108])
    t_env.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FCD34D")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_env)
    story.append(Spacer(1, 10))

    # ==========================
    # 5. TROUBLESHOOTING & SOLUSI
    # ==========================
    story.append(Paragraph("5. Solusi Kendala & Masalah Umum (Troubleshooting)", style_h1))

    trouble_data = [
        [Paragraph("Gejala / Masalah", style_th), Paragraph("Penyebab", style_th), Paragraph("Solusi Cepat", style_th)],
        [
            Paragraph("<b>Error: Port 8000 / 3000 Already in Use</b>", style_td),
            Paragraph("Ada proses server sebelumnya yang belum tertutup dengan sempurna.", style_td),
            Paragraph("Buka CMD administrator lalu jalankan:<br/><code>taskkill /F /IM python.exe</code><br/><code>taskkill /F /IM node.exe</code>", style_td),
        ],
        [
            Paragraph("<b>Halaman Web Loading Terus / Blank</b>", style_td),
            Paragraph("Backend FastAPI belum aktif atau terhenti.", style_td),
            Paragraph("Pastikan terminal backend menampilkan status <code>Uvicorn running on http://127.0.0.1:8000</code>.", style_td),
        ],
        [
            Paragraph("<b>Suara Hasil Sintesis Hening / Gagal</b>", style_td),
            Paragraph("FFmpeg belum terdeteksi atau koneksi internet terputus saat memakai Gemini.", style_td),
            Paragraph("Periksa koneksi internet untuk Gemini AI, atau ganti engine ke <b>Piper ONNX</b> untuk mode 100% offline.", style_td),
        ],
        [
            Paragraph("<b>Cara Mematikan Server</b>", style_td),
            Paragraph("Pengguna ingin mengakhiri sesi studio.", style_td),
            Paragraph("Arahkan kursor ke masing-masing jendela terminal (Backend & Frontend) lalu tekan <b>Ctrl + C</b>.", style_td),
        ],
    ]
    t_trouble = Table(trouble_data, colWidths=[120, 120, 247])
    t_trouble.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_code]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_trouble)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[PDF Generator] Panduan berhasil dibuat: {output_pdf_path}")

    # Render PNG untuk verifikasi visual
    try:
        import pymupdf
        pdf_doc = pymupdf.open(str(output_pdf_path))
        art_dir = Path(r"C:\Users\ASUS\.gemini\antigravity-ide\brain\30561248-ca91-4973-9c1e-80029e96d2e1")
        for i, page in enumerate(pdf_doc):
            pix = page.get_pixmap(dpi=150)
            img_path = art_dir / f"pdf_guide_page_{i+1}.png"
            pix.save(str(img_path))
            print(f"[PDF Generator] Preview tersimpan: {img_path}")
    except Exception as e:
        print(f"[PDF Generator] Gagal render preview: {e}")

if __name__ == "__main__":
    out_file = Path(r"c:\Users\ASUS\Downloads\web_teks-to-speak\PANDUAN_MENJALANKAN_SERVER_TASTP.pdf")
    build_pdf_guide(out_file)
