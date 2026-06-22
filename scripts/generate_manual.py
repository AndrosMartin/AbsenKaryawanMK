#!/usr/bin/env python3
"""Generate the AbsensiPro (MitraKeuangan) user Manual Book as a branded PDF."""
from fpdf import FPDF
from datetime import datetime
import os

GOLD = (224, 177, 0)
GOLD_SOFT = (247, 236, 194)
INK = (11, 11, 12)
INK_SOFT = (34, 34, 37)
GREY = (90, 95, 105)
LIGHT = (245, 246, 248)
WHITE = (255, 255, 255)

FONT_DIR = "/usr/share/fonts/truetype/liberation"
LOGO = "/app/frontend/public/logo-mitra.jpg"
MARGIN = 18


class Manual(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(MARGIN, 18, MARGIN)
        self.add_font("Lib", "", f"{FONT_DIR}/LiberationSans-Regular.ttf")
        self.add_font("Lib", "B", f"{FONT_DIR}/LiberationSans-Bold.ttf")
        self.add_font("Lib", "I", f"{FONT_DIR}/LiberationSans-Italic.ttf")
        self.cover = False

    def header(self):
        if self.cover:
            return
        self.set_fill_color(*INK)
        self.rect(0, 0, 210, 13, "F")
        self.set_fill_color(*GOLD)
        self.rect(0, 13, 210, 1.1, "F")
        if os.path.exists(LOGO):
            self.image(LOGO, x=MARGIN, y=2.2, w=8.6, h=8.6)
        self.set_xy(MARGIN + 11, 3.4)
        self.set_font("Lib", "B", 9)
        self.set_text_color(*WHITE)
        self.cell(0, 3, "Mitra", ln=0)
        w = self.get_string_width("Mitra")
        self.set_xy(MARGIN + 11 + w, 3.4)
        self.set_text_color(*GOLD)
        self.cell(0, 3, "Keuangan", ln=0)
        self.set_xy(MARGIN + 11, 6.8)
        self.set_font("Lib", "", 6.5)
        self.set_text_color(180, 180, 185)
        self.cell(0, 3, "MANUAL BOOK  •  SISTEM ABSENSI & MONITORING", ln=0)
        self.set_y(22)

    def footer(self):
        if self.cover:
            return
        self.set_y(-15)
        self.set_draw_color(225, 225, 228)
        self.line(MARGIN, self.get_y(), 210 - MARGIN, self.get_y())
        self.set_y(-12)
        self.set_font("Lib", "", 7.5)
        self.set_text_color(*GREY)
        self.cell(0, 5, "AbsensiPro by MitraKeuangan  —  Dokumen Internal", ln=0)
        self.set_y(-12)
        self.cell(0, 5, f"Halaman {self.page_no()}", align="R")

    # ---- content helpers ----
    def cover_page(self):
        self.cover = True
        self.add_page()
        self.set_fill_color(*INK)
        self.rect(0, 0, 210, 297, "F")
        self.set_fill_color(*INK_SOFT)
        self.rect(0, 150, 210, 147, "F")
        # gold glow strips
        self.set_fill_color(*GOLD)
        self.rect(0, 148.5, 210, 1.4, "F")
        if os.path.exists(LOGO):
            self.image(LOGO, x=(210 - 34) / 2, y=44, w=34, h=34)
        self.set_xy(0, 86)
        self.set_font("Lib", "B", 11)
        self.set_text_color(*GOLD)
        self.cell(0, 6, "M I T R A   K E U A N G A N", align="C", ln=1)
        self.set_xy(0, 104)
        self.set_font("Lib", "B", 34)
        self.set_text_color(*WHITE)
        self.cell(0, 14, "MANUAL BOOK", align="C", ln=1)
        self.set_xy(0, 122)
        self.set_font("Lib", "", 13)
        self.set_text_color(220, 220, 224)
        self.cell(0, 7, "Sistem Absensi & Monitoring Karyawan", align="C", ln=1)
        self.set_font("Lib", "B", 13)
        self.set_text_color(*GOLD)
        self.cell(0, 8, "AbsensiPro", align="C", ln=1)
        # bottom box
        self.set_xy(0, 200)
        self.set_font("Lib", "", 10)
        self.set_text_color(210, 210, 214)
        self.multi_cell(0, 6,
            "Panduan lengkap penggunaan aplikasi: fitur, alur kerja, dan fungsi\n"
            "untuk setiap peran (Owner, Direksi, Manager, HRD, dan Staff).",
            align="C")
        self.set_xy(0, 250)
        self.set_font("Lib", "", 9)
        self.set_text_color(150, 150, 156)
        self.cell(0, 5, "Versi 1.0", align="C", ln=1)
        self.cell(0, 5, datetime.now().strftime("Diterbitkan: %d %B %Y"), align="C", ln=1)
        self.cover = False

    def h1(self, num, title):
        if self.get_y() > 235:
            self.add_page()
        self.ln(3)
        self.set_fill_color(*INK)
        y = self.get_y()
        self.rect(MARGIN, y, 210 - 2 * MARGIN, 11, "F")
        self.set_fill_color(*GOLD)
        self.rect(MARGIN, y, 2.2, 11, "F")
        self.set_xy(MARGIN + 6, y + 1)
        self.set_font("Lib", "B", 8)
        self.set_text_color(*GOLD)
        self.cell(0, 4, f"BAGIAN {num}", ln=1)
        self.set_xy(MARGIN + 6, y + 4.6)
        self.set_font("Lib", "B", 12.5)
        self.set_text_color(*WHITE)
        self.cell(0, 6, title, ln=1)
        self.set_y(y + 14)

    def h2(self, title):
        if self.get_y() > 250:
            self.add_page()
        self.ln(2.5)
        self.set_font("Lib", "B", 11)
        self.set_text_color(*INK)
        self.cell(3.5, 6, "", ln=0)
        self.set_fill_color(*GOLD)
        self.rect(MARGIN, self.get_y() + 1, 2.4, 4.4, "F")
        self.cell(0, 6, title, ln=1)
        self.ln(1)

    def para(self, text):
        self.set_x(self.l_margin)
        self.set_font("Lib", "", 9.7)
        self.set_text_color(55, 58, 64)
        self.multi_cell(0, 5.2, text)
        self.ln(1)

    def bullets(self, items):
        self.set_font("Lib", "", 9.7)
        self.set_text_color(55, 58, 64)
        for it in items:
            self.set_x(self.l_margin)
            x = self.get_x()
            self.set_text_color(*GOLD)
            self.set_font("Lib", "B", 9.7)
            self.cell(5, 5.0, "•", ln=0)
            self.set_text_color(55, 58, 64)
            self.set_font("Lib", "", 9.7)
            self.multi_cell(0, 5.0, it)
            self.set_x(x)
        self.ln(1.2)

    def steps(self, items):
        self.set_font("Lib", "", 9.7)
        for i, it in enumerate(items, 1):
            self.set_x(self.l_margin)
            x = self.get_x()
            self.set_fill_color(*INK)
            self.set_text_color(*GOLD)
            self.set_font("Lib", "B", 8)
            yy = self.get_y()
            self.ellipse(x, yy + 0.3, 4.6, 4.6, "F")
            self.set_xy(x, yy + 0.7)
            self.cell(4.6, 3.6, str(i), align="C", ln=0)
            self.set_xy(x + 7, yy)
            self.set_text_color(55, 58, 64)
            self.set_font("Lib", "", 9.7)
            self.multi_cell(0, 5.0, it)
            self.set_x(x)
        self.ln(1.2)

    def note(self, text, kind="info"):
        colors = {"info": (GOLD_SOFT, (133, 99, 0)), "warn": ((255, 237, 213), (154, 52, 18))}
        bg, fg = colors.get(kind, colors["info"])
        self.set_font("Lib", "", 9)
        self.ln(1)
        self.set_x(self.l_margin)
        y0 = self.get_y()
        # measure height
        self.set_xy(MARGIN + 6, y0 + 2)
        # draw box later: estimate using split
        lines = self.multi_cell(210 - 2 * MARGIN - 10, 4.8, text, dry_run=True, output="LINES")
        h = len(lines) * 4.8 + 4
        self.set_fill_color(*bg)
        self.rect(MARGIN, y0, 210 - 2 * MARGIN, h, "F")
        self.set_fill_color(*GOLD)
        self.rect(MARGIN, y0, 2.0, h, "F")
        self.set_xy(MARGIN + 6, y0 + 2)
        self.set_text_color(*fg)
        self.multi_cell(210 - 2 * MARGIN - 10, 4.8, text)
        self.set_y(y0 + h + 2)

    def table(self, headers, rows, widths):
        avail = 210 - 2 * MARGIN
        widths = [w / sum(widths) * avail for w in widths]
        self.ln(1)
        # header
        self.set_font("Lib", "B", 8.6)
        self.set_fill_color(*INK)
        self.set_text_color(*GOLD)
        for h, w in zip(headers, widths):
            self.cell(w, 7, " " + h, border=0, fill=True, align="L")
        self.ln(7)
        self.set_font("Lib", "", 8.5)
        fill = False
        for row in rows:
            # compute row height
            heights = []
            for txt, w in zip(row, widths):
                lines = self.multi_cell(w - 2, 4.4, str(txt), dry_run=True, output="LINES")
                heights.append(max(1, len(lines)))
            rh = max(heights) * 4.4 + 2.4
            if self.get_y() + rh > 275:
                self.add_page()
                self.set_font("Lib", "B", 8.6)
                self.set_fill_color(*INK); self.set_text_color(*GOLD)
                for h, w in zip(headers, widths):
                    self.cell(w, 7, " " + h, fill=True)
                self.ln(7)
                self.set_font("Lib", "", 8.5)
            self.set_fill_color(*LIGHT) if fill else self.set_fill_color(*WHITE)
            x0, y0 = self.get_x(), self.get_y()
            for txt, w in zip(row, widths):
                self.rect(self.get_x(), y0, w, rh, "F")
                xc = self.get_x()
                self.set_xy(xc + 1.4, y0 + 1.2)
                self.set_text_color(50, 52, 58)
                self.multi_cell(w - 2.4, 4.4, str(txt))
                self.set_xy(xc + w, y0)
            self.set_xy(x0, y0 + rh)
            fill = not fill
        # bottom border
        self.set_draw_color(*GOLD)
        self.line(MARGIN, self.get_y(), 210 - MARGIN, self.get_y())
        self.ln(3)


def build():
    pdf = Manual()
    pdf.cover_page()
    pdf.add_page()

    # ---------- TABLE OF CONTENTS ----------
    pdf.h1("0", "Daftar Isi")
    toc = [
        "1.  Pendahuluan",
        "2.  Memulai — Cara Masuk (Login)",
        "3.  Peran (Role) & Hak Akses",
        "4.  Panduan Setiap Fitur",
        "5.  Panduan Kerja per Role",
        "6.  Notifikasi & Persetujuan",
        "7.  Tanya Jawab & Pemecahan Masalah",
        "8.  Keamanan & Privasi Data",
    ]
    pdf.bullets(toc)

    # ---------- 1. PENDAHULUAN ----------
    pdf.h1("1", "Pendahuluan")
    pdf.para(
        "AbsensiPro adalah aplikasi absensi karyawan milik MitraKeuangan yang dirancang untuk "
        "memudahkan pencatatan kehadiran sekaligus memberikan sarana monitoring bagi Owner, Direksi, "
        "dan Manager. Karyawan dapat melakukan absensi secara fleksibel dengan verifikasi yang akurat.")
    pdf.h2("Fitur Inti")
    pdf.bullets([
        "Verifikasi Wajah (Face Recognition): identitas karyawan dipastikan melalui pengenalan wajah.",
        "Scan QR Code: absensi cepat dengan memindai QR resmi yang terpasang di kantor.",
        "Validasi Lokasi GPS (Geofence): absensi hanya diterima bila berada di dalam radius kantor.",
        "Status Otomatis: sistem menentukan Tepat Waktu atau Terlambat berdasarkan jam masuk.",
        "Dashboard & Monitoring: ringkasan kehadiran real-time, tren, dan rekap per departemen.",
        "Manajemen Karyawan dengan alur persetujuan untuk peran HRD.",
        "Notifikasi: pemberitahuan permintaan dan persetujuan perubahan data karyawan.",
    ])
    pdf.note(
        "Catatan: Fitur wajah dan QR membutuhkan izin Kamera, sedangkan validasi lokasi membutuhkan "
        "izin Lokasi (GPS) pada peramban. Pastikan kedua izin diaktifkan saat diminta.", "info")

    # ---------- 2. LOGIN ----------
    pdf.h1("2", "Memulai — Cara Masuk (Login)")
    pdf.steps([
        "Buka aplikasi AbsensiPro melalui peramban (browser) di komputer atau ponsel.",
        "Masukkan Email dan Password perusahaan Anda pada halaman login.",
        "Klik tombol 'Masuk'. Bila berhasil, Anda diarahkan ke halaman utama sesuai peran Anda.",
        "Untuk keluar, klik ikon keluar di pojok kiri bawah atau menu Profil > Keluar.",
    ])
    pdf.h2("Akun Demo (untuk uji coba)")
    pdf.table(
        ["Peran", "Email", "Password"],
        [
            ["Owner", "owner@company.com", "password123"],
            ["Direksi", "direksi@company.com", "password123"],
            ["Manager", "manager@company.com", "password123"],
            ["HRD", "hrd@company.com", "password123"],
            ["Staff", "dewi@company.com", "password123"],
        ],
        [1.2, 2.4, 1.4])
    pdf.note("Keamanan: Sesi login diamankan dengan token. Jangan bagikan email/password Anda kepada "
             "orang lain. Gantilah password awal melalui Admin (Owner/Direksi).", "warn")

    # ---------- 3. ROLE MATRIX ----------
    pdf.h1("3", "Peran (Role) & Hak Akses")
    pdf.para("Terdapat 5 peran dengan kewenangan berbeda. Tabel berikut merangkum akses tiap peran "
             "terhadap fitur utama aplikasi.")
    pdf.table(
        ["Fitur", "Owner", "Direksi", "Manager", "HRD", "Staff"],
        [
            ["Absensi (Check-in/out)", "Ya", "Ya", "Ya", "Ya", "Ya"],
            ["Riwayat Pribadi", "Ya", "Ya", "Ya", "Ya", "Ya"],
            ["Pendaftaran Wajah", "Ya", "Ya", "Ya", "Ya", "Ya"],
            ["Dashboard Monitoring", "Ya", "Ya", "Ya", "Ya", "-"],
            ["Monitoring Karyawan", "Ya", "Ya", "Ya", "Ya", "-"],
            ["Lihat Data Karyawan", "Ya", "Ya", "Ya", "Ya", "-"],
            ["Kelola Karyawan (langsung)", "Ya", "Ya", "-", "-", "-"],
            ["Ajukan Kelola Karyawan", "-", "-", "-", "Ya*", "-"],
            ["Menyetujui Permintaan", "Ya", "Ya", "-", "-", "-"],
            ["Lokasi Kantor & Geofence", "Ya", "Ya", "-", "-", "-"],
            ["Notifikasi", "Ya", "Ya", "-", "Ya", "-"],
        ],
        [2.2, 1, 1, 1.1, 1, 1])
    pdf.note("*HRD dapat menambah/mengubah/menghapus karyawan, tetapi setiap perubahan WAJIB disetujui "
             "Direksi/Owner terlebih dahulu. HRD tidak dapat mengatur peran Owner/Direksi.", "info")

    # ---------- 4. FITUR ----------
    pdf.h1("4", "Panduan Setiap Fitur")

    pdf.h2("4.1  Dashboard Monitoring")
    pdf.para("Akses: Owner, Direksi, Manager, HRD. Menyajikan ringkasan kehadiran hari ini.")
    pdf.bullets([
        "Kartu KPI: Total Karyawan, Tepat Waktu, Terlambat, dan Tidak Hadir.",
        "Tingkat Kehadiran (persentase) hari berjalan.",
        "Grafik Tren Kehadiran 7 hari terakhir (tepat waktu vs terlambat).",
        "Kehadiran per Departemen dan daftar Aktivitas Terbaru (check-in terakhir).",
    ])

    pdf.h2("4.2  Absensi — Check-in & Check-out")
    pdf.para("Akses: semua peran. Inti dari aplikasi. Tersedia dua metode verifikasi: Wajah dan QR Code, "
             "keduanya divalidasi dengan lokasi GPS.")
    pdf.steps([
        "Buka menu 'Absensi'. Sistem otomatis mengambil lokasi GPS Anda (klik 'Perbarui lokasi' bila perlu).",
        "Pilih tab 'Wajah' lalu 'Aktifkan Kamera', posisikan wajah di dalam bingkai, dan klik "
        "'Verifikasi Wajah & Check-in'. ATAU pilih tab 'QR Code' lalu 'Mulai Scan' dan arahkan ke QR kantor.",
        "Bila berada dalam radius kantor dan identitas cocok, kehadiran tercatat beserta statusnya "
        "(Tepat Waktu / Terlambat).",
        "Saat selesai bekerja, kembali ke menu 'Absensi' dan klik 'Check-out Sekarang'.",
    ])
    pdf.note("Jika muncul pesan 'Anda berada X m dari kantor', artinya Anda di luar radius geofence. "
             "Mendekatlah ke lokasi kantor lalu coba lagi.", "warn")

    pdf.h2("4.3  Wajah Saya (Pendaftaran Wajah)")
    pdf.para("Akses: semua peran. Wajib dilakukan sekali sebelum dapat absen menggunakan metode wajah.")
    pdf.steps([
        "Buka menu 'Wajah Saya' dan klik 'Aktifkan Kamera'.",
        "Posisikan wajah pada bingkai dengan pencahayaan cukup, lalu klik 'Daftarkan Wajah'.",
        "Bila berhasil, status berubah menjadi 'Wajah sudah terdaftar'. Anda dapat memperbaruinya kapan saja.",
    ])
    pdf.note("Privasi: Wajah Anda disimpan sebagai vektor matematis (angka), BUKAN sebagai foto.", "info")

    pdf.h2("4.4  Riwayat Saya")
    pdf.para("Akses: semua peran. Menampilkan rekap kehadiran pribadi: tanggal, jam masuk/keluar, "
             "metode, lokasi, dan status. Dilengkapi ringkasan Total Hari, Tepat Waktu, dan Terlambat.")

    pdf.h2("4.5  Monitoring Karyawan")
    pdf.para("Akses: Owner, Direksi, Manager, HRD. Menampilkan status kehadiran SELURUH karyawan pada "
             "tanggal tertentu.")
    pdf.bullets([
        "Filter berdasarkan tanggal untuk meninjau hari tertentu.",
        "Kotak pencarian untuk mencari nama atau departemen.",
        "Ringkasan jumlah Tepat Waktu, Terlambat, dan Tidak Hadir.",
    ])

    pdf.h2("4.6  Karyawan (Manajemen Data)")
    pdf.para("Akses melihat: Owner, Direksi, Manager, HRD. Akses mengelola: Owner, Direksi (langsung) "
             "dan HRD (melalui persetujuan).")
    pdf.steps([
        "Buka menu 'Karyawan'. Klik 'Tambah Karyawan' untuk menambah, atau ikon pensil/keranjang "
        "pada baris untuk mengubah/menghapus.",
        "Isi data: Nama, Email, Departemen, Posisi, Peran, dan Password.",
        "Owner/Direksi: perubahan langsung berlaku. HRD: perubahan dikirim sebagai 'Permintaan' dan "
        "menunggu persetujuan Direksi/Owner.",
    ])
    pdf.note("Batasan HRD: tidak dapat membuat/mengubah/menghapus akun berperan Owner atau Direksi.", "warn")

    pdf.h2("4.7  Persetujuan (Approval)")
    pdf.para("Akses: Owner, Direksi (menyetujui), dan HRD (memantau status pengajuannya).")
    pdf.steps([
        "HRD mengajukan perubahan karyawan; permintaan masuk dengan status 'Menunggu'.",
        "Owner/Direksi membuka menu 'Persetujuan', meninjau detail permintaan.",
        "Klik 'Setujui' untuk menerapkan perubahan, atau 'Tolak' (dengan alasan) untuk membatalkan.",
        "HRD menerima notifikasi hasil (disetujui/ditolak) dan dapat melihat status di menu Persetujuan.",
    ])

    pdf.h2("4.8  Lokasi Kantor & Geofence")
    pdf.para("Akses: Owner, Direksi. Mengatur titik kantor (koordinat) dan radius yang diizinkan untuk "
             "absensi.")
    pdf.steps([
        "Buka menu 'Lokasi Kantor' dan klik 'Tambah Lokasi'.",
        "Isi nama, Latitude, Longitude (bisa pakai 'Gunakan lokasi saya saat ini'), dan Radius (meter).",
        "Setiap lokasi otomatis memiliki QR Code absensi yang dapat dicetak dan dipasang di kantor.",
    ])

    pdf.h2("4.9  Notifikasi")
    pdf.para("Ikon lonceng di kanan atas menampilkan badge jumlah notifikasi belum dibaca.")
    pdf.bullets([
        "Owner/Direksi: pemberitahuan setiap permintaan baru dari HRD yang menunggu persetujuan.",
        "HRD: pemberitahuan saat permintaannya disetujui atau ditolak.",
        "Klik lonceng untuk membuka daftar; klik salah satu item untuk menuju halaman Persetujuan.",
    ])

    pdf.h2("4.10  Profil")
    pdf.para("Akses: semua peran. Menampilkan data diri (ID karyawan, email, departemen, posisi, status "
             "wajah) serta pintasan untuk mendaftarkan/memperbarui wajah dan keluar dari aplikasi.")

    # ---------- 5. PER ROLE ----------
    pdf.h1("5", "Panduan Kerja per Role")

    pdf.h2("Owner / Direksi")
    pdf.bullets([
        "Memantau seluruh kehadiran melalui Dashboard dan Monitoring.",
        "Mengelola karyawan secara langsung (tambah/ubah/hapus) tanpa persetujuan.",
        "Menyetujui atau menolak permintaan perubahan dari HRD melalui menu Persetujuan.",
        "Mengatur Lokasi Kantor dan radius Geofence serta mencetak QR absensi.",
        "Tetap dapat melakukan absensi pribadi seperti karyawan lain.",
    ])
    pdf.h2("Manager")
    pdf.bullets([
        "Memantau kehadiran tim melalui Dashboard dan Monitoring.",
        "Melihat data karyawan (tanpa kewenangan mengubah).",
        "Melakukan absensi pribadi (wajah/QR + GPS).",
    ])
    pdf.h2("HRD")
    pdf.bullets([
        "Mengajukan penambahan, perubahan, atau penghapusan data karyawan (perlu persetujuan Direksi).",
        "Memantau status pengajuan di menu Persetujuan dan menerima notifikasi hasilnya.",
        "Memantau kehadiran melalui Dashboard dan Monitoring.",
        "Melakukan absensi pribadi.",
    ])
    pdf.h2("Staff / Karyawan")
    pdf.bullets([
        "Mendaftarkan wajah satu kali melalui menu 'Wajah Saya'.",
        "Melakukan Check-in dan Check-out harian (wajah atau QR) di lokasi kantor.",
        "Melihat rekap kehadiran pribadi di menu 'Riwayat Saya'.",
        "Mengelola profil pribadi.",
    ])

    # ---------- 6. ALUR PERSETUJUAN ----------
    pdf.h1("6", "Notifikasi & Alur Persetujuan (Ringkas)")
    pdf.steps([
        "HRD melakukan aksi kelola karyawan -> sistem membuat 'Permintaan' berstatus Menunggu.",
        "Owner/Direksi menerima notifikasi (lonceng) bahwa ada permintaan baru.",
        "Owner/Direksi meninjau di menu Persetujuan, lalu Menyetujui atau Menolak.",
        "Jika disetujui, perubahan data karyawan langsung diterapkan ke sistem.",
        "HRD menerima notifikasi hasil dan status permintaan diperbarui (Disetujui/Ditolak).",
    ])

    # ---------- 7. FAQ ----------
    pdf.h1("7", "Tanya Jawab & Pemecahan Masalah")
    faq = [
        ("Kamera tidak aktif?", "Pastikan Anda memberi izin Kamera pada peramban. Tutup aplikasi lain "
         "yang sedang memakai kamera, lalu muat ulang halaman."),
        ("Lokasi GPS gagal terdeteksi?", "Aktifkan layanan Lokasi pada perangkat dan beri izin Lokasi "
         "pada peramban. Tekan 'Perbarui lokasi'. Gunakan jaringan/sinyal yang stabil."),
        ("Muncul 'Anda berada X m dari kantor'?", "Anda berada di luar radius geofence. Dekati lokasi "
         "kantor. Bila titik kantor salah, minta Owner/Direksi memperbarui Lokasi Kantor."),
        ("Wajah tidak cocok saat absen?", "Pastikan pencahayaan cukup dan wajah berada penuh di bingkai. "
         "Bila tetap gagal, daftarkan ulang wajah di menu 'Wajah Saya'."),
        ("QR Code tidak valid?", "Pastikan memindai QR resmi kantor yang sesuai lokasi Anda saat ini, "
         "dan Anda berada di dalam radius kantor."),
        ("Sudah check-in tapi ingin check-in lagi?", "Check-in hanya sekali per hari. Gunakan 'Check-out' "
         "saat selesai bekerja."),
        ("Lupa password?", "Hubungi Owner/Direksi (atau HRD melalui pengajuan) untuk mereset password Anda."),
    ]
    for q, a in faq:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Lib", "B", 9.7)
        pdf.set_text_color(*INK)
        pdf.multi_cell(0, 5.2, "Q:  " + q)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Lib", "", 9.7)
        pdf.set_text_color(55, 58, 64)
        pdf.multi_cell(0, 5.2, "A:  " + a)
        pdf.ln(1.6)

    # ---------- 8. KEAMANAN ----------
    pdf.h1("8", "Keamanan & Privasi Data")
    pdf.bullets([
        "Autentikasi menggunakan token; akses fitur dibatasi sesuai peran (Role-Based Access Control).",
        "Data wajah disimpan sebagai vektor numerik (bukan foto) dan hanya dipakai untuk verifikasi.",
        "Lokasi GPS digunakan hanya untuk validasi geofence saat absensi.",
        "Perubahan data sensitif oleh HRD selalu melewati persetujuan Direksi/Owner.",
        "Jaga kerahasiaan kredensial; selalu keluar (logout) pada perangkat bersama.",
    ])
    pdf.ln(4)
    pdf.set_font("Lib", "I", 9)
    pdf.set_text_color(*GREY)
    pdf.multi_cell(0, 5, "— Selesai —\nDokumen ini diterbitkan untuk keperluan internal MitraKeuangan. "
                          "Tampilan antarmuka dapat berbeda mengikuti pembaruan aplikasi.")

    out1 = "/app/frontend/public/Manual_Book_AbsensiPro.pdf"
    out2 = "/app/Manual_Book_AbsensiPro.pdf"
    pdf.output(out1)
    pdf.output(out2)
    print("PDF dibuat:", out1, "(", os.path.getsize(out1), "bytes )")


if __name__ == "__main__":
    build()
