#!/usr/bin/env python3
"""Generate the AbsensiPro (MitraKeuangan) self-hosting Deployment Guide as a branded PDF."""
from fpdf import FPDF
from datetime import datetime
import os

GOLD = (224, 177, 0)
GOLD_SOFT = (247, 236, 194)
INK = (11, 11, 12)
INK_SOFT = (22, 22, 24)
GREY = (90, 95, 105)
LIGHT = (245, 246, 248)
WHITE = (255, 255, 255)

FONT_DIR = "/usr/share/fonts/truetype/liberation"
LOGO = "/app/frontend/public/logo-mitra.jpg"
MARGIN = 18


class Guide(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(MARGIN, 18, MARGIN)
        self.add_font("Lib", "", f"{FONT_DIR}/LiberationSans-Regular.ttf")
        self.add_font("Lib", "B", f"{FONT_DIR}/LiberationSans-Bold.ttf")
        self.add_font("Lib", "I", f"{FONT_DIR}/LiberationSans-Italic.ttf")
        self.add_font("Mono", "", f"{FONT_DIR}/LiberationMono-Regular.ttf")
        self.add_font("Mono", "B", f"{FONT_DIR}/LiberationMono-Bold.ttf")
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
        self.cell(0, 3, "PANDUAN DEPLOYMENT  •  SELF-HOSTING", ln=0)
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
        self.cell(0, 5, "AbsensiPro by MitraKeuangan  —  Panduan Deployment", ln=0)
        self.set_y(-12)
        self.cell(0, 5, f"Halaman {self.page_no()}", align="R")

    def cover_page(self):
        self.cover = True
        self.add_page()
        self.set_fill_color(*INK)
        self.rect(0, 0, 210, 297, "F")
        self.set_fill_color(*INK_SOFT)
        self.rect(0, 150, 210, 147, "F")
        self.set_fill_color(*GOLD)
        self.rect(0, 148.5, 210, 1.4, "F")
        if os.path.exists(LOGO):
            self.image(LOGO, x=(210 - 34) / 2, y=44, w=34, h=34)
        self.set_xy(0, 86)
        self.set_font("Lib", "B", 11)
        self.set_text_color(*GOLD)
        self.cell(0, 6, "M I T R A   K E U A N G A N", align="C", ln=1)
        self.set_xy(0, 102)
        self.set_font("Lib", "B", 30)
        self.set_text_color(*WHITE)
        self.cell(0, 13, "PANDUAN DEPLOYMENT", align="C", ln=1)
        self.set_xy(0, 120)
        self.set_font("Lib", "", 13)
        self.set_text_color(220, 220, 224)
        self.cell(0, 7, "Self-Hosting di Server / Hosting Pribadi", align="C", ln=1)
        self.set_font("Lib", "B", 13)
        self.set_text_color(*GOLD)
        self.cell(0, 8, "AbsensiPro  (FastAPI + MongoDB + Frontend)", align="C", ln=1)
        self.set_xy(0, 196)
        self.set_font("Lib", "", 10)
        self.set_text_color(210, 210, 214)
        self.multi_cell(0, 6,
            "Langkah demi langkah memasang aplikasi pada VPS/Server Linux Anda sendiri:\n"
            "penyiapan database, backend, frontend, Nginx, domain, dan HTTPS.",
            align="C")
        self.set_xy(0, 252)
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
        self.set_x(self.l_margin)
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
            yy = self.get_y()
            self.set_fill_color(*INK)
            self.ellipse(x, yy + 0.3, 4.6, 4.6, "F")
            self.set_text_color(*GOLD)
            self.set_font("Lib", "B", 8)
            self.set_xy(x, yy + 0.7)
            self.cell(4.6, 3.6, str(i), align="C", ln=0)
            self.set_xy(x + 7, yy)
            self.set_text_color(55, 58, 64)
            self.set_font("Lib", "", 9.7)
            self.multi_cell(0, 5.0, it)
            self.set_x(x)
        self.ln(1.2)

    def code(self, text, title=None):
        self.ln(1)
        self.set_x(self.l_margin)
        if title:
            self.set_font("Mono", "B", 7.5)
            self.set_text_color(*GREY)
            self.cell(0, 4, "# " + title, ln=1)
            self.set_x(self.l_margin)
        self.set_font("Mono", "", 8.2)
        w = 210 - 2 * MARGIN
        lines = self.multi_cell(w - 8, 4.4, text, dry_run=True, output="LINES")
        h = len(lines) * 4.4 + 5
        if self.get_y() + h > 275:
            self.add_page()
        y0 = self.get_y()
        self.set_fill_color(*INK_SOFT)
        self.rect(MARGIN, y0, w, h, "F")
        self.set_fill_color(*GOLD)
        self.rect(MARGIN, y0, 2.0, h, "F")
        self.set_xy(MARGIN + 6, y0 + 2.5)
        self.set_text_color(232, 232, 232)
        self.multi_cell(w - 8, 4.4, text)
        self.set_y(y0 + h + 2)

    def note(self, text, kind="info"):
        colors = {"info": (GOLD_SOFT, (133, 99, 0)), "warn": ((255, 237, 213), (154, 52, 18))}
        bg, fg = colors.get(kind, colors["info"])
        self.set_font("Lib", "B", 9)
        self.ln(1)
        self.set_x(self.l_margin)
        w = 210 - 2 * MARGIN
        lines = self.multi_cell(w - 10, 4.8, text, dry_run=True, output="LINES")
        h = len(lines) * 4.8 + 4
        if self.get_y() + h > 275:
            self.add_page()
        y0 = self.get_y()
        self.set_fill_color(*bg)
        self.rect(MARGIN, y0, w, h, "F")
        self.set_fill_color(*GOLD)
        self.rect(MARGIN, y0, 2.0, h, "F")
        self.set_xy(MARGIN + 6, y0 + 2)
        self.set_text_color(*fg)
        self.multi_cell(w - 10, 4.8, text)
        self.set_y(y0 + h + 2)

    def table(self, headers, rows, widths):
        avail = 210 - 2 * MARGIN
        widths = [w / sum(widths) * avail for w in widths]
        self.ln(1)
        self.set_font("Lib", "B", 8.6)
        self.set_fill_color(*INK)
        self.set_text_color(*GOLD)
        for hh, w in zip(headers, widths):
            self.cell(w, 7, " " + hh, fill=True)
        self.ln(7)
        self.set_font("Lib", "", 8.5)
        fill = False
        for row in rows:
            heights = [max(1, len(self.multi_cell(w - 2, 4.4, str(t), dry_run=True, output="LINES")))
                       for t, w in zip(row, widths)]
            rh = max(heights) * 4.4 + 2.4
            if self.get_y() + rh > 275:
                self.add_page()
            self.set_fill_color(*LIGHT) if fill else self.set_fill_color(*WHITE)
            x0, y0 = self.get_x(), self.get_y()
            for t, w in zip(row, widths):
                self.rect(self.get_x(), y0, w, rh, "F")
                xc = self.get_x()
                self.set_xy(xc + 1.4, y0 + 1.2)
                self.set_text_color(50, 52, 58)
                self.multi_cell(w - 2.4, 4.4, str(t))
                self.set_xy(xc + w, y0)
            self.set_xy(x0, y0 + rh)
            fill = not fill
        self.set_draw_color(*GOLD)
        self.line(MARGIN, self.get_y(), 210 - MARGIN, self.get_y())
        self.ln(3)


def build():
    pdf = Guide()
    pdf.cover_page()
    pdf.add_page()

    pdf.h1("0", "Daftar Isi")
    pdf.bullets([
        "1.  Arsitektur Aplikasi",
        "2.  Prasyarat (Server, Software, Domain)",
        "3.  Menyiapkan Kode Sumber",
        "4.  Menyiapkan Database (MongoDB)",
        "5.  Deploy Backend (FastAPI)",
        "6.  Deploy Frontend (File Statis)",
        "7.  Konfigurasi Nginx (Reverse Proxy)",
        "8.  HTTPS / SSL — WAJIB untuk Kamera & GPS",
        "9.  Domain & DNS",
        "10. Keamanan Produksi",
        "11. Pemeliharaan & Backup",
        "12. Alternatif Deployment (Ringkas)",
        "13. Checklist & Troubleshooting",
    ])

    pdf.h1("1", "Arsitektur Aplikasi")
    pdf.para("AbsensiPro terdiri dari tiga komponen yang berjalan di server Anda:")
    pdf.bullets([
        "Backend API — FastAPI (Python), berjalan di port 8001, semua endpoint berawalan /api.",
        "Database — MongoDB (lokal di server, atau cloud MongoDB Atlas).",
        "Frontend — file statis (HTML, JS, Tailwind CDN) di folder frontend/public. "
        "TIDAK memerlukan proses build; cukup disajikan sebagai file statis.",
    ])
    pdf.para("Nginx bertindak sebagai pintu depan (port 80/443): menyajikan file frontend dan "
             "meneruskan permintaan /api ke backend FastAPI. Frontend memanggil API pada domain "
             "yang sama (origin) sehingga tidak perlu konfigurasi URL tambahan.")
    pdf.note("Penting: Fitur absen wajah (kamera) dan validasi lokasi (GPS) HANYA berfungsi pada "
             "koneksi HTTPS (secure context). Sertifikat SSL bersifat WAJIB, bukan opsional.", "warn")

    pdf.h1("2", "Prasyarat")
    pdf.bullets([
        "VPS / Server Linux (disarankan Ubuntu 22.04 LTS) dengan akses root/sudo.",
        "Nama domain (mis. absensi.perusahaan.co.id) yang diarahkan ke IP server.",
        "Python 3.11+ dan pip.",
        "MongoDB 6.0+ (lokal) ATAU akun MongoDB Atlas (gratis).",
        "Nginx sebagai web server / reverse proxy.",
        "Koneksi internet keluar pada server (frontend memuat Tailwind & pustaka wajah dari CDN).",
        "Spesifikasi minimum disarankan: 1–2 vCPU, RAM 2 GB, penyimpanan 20 GB.",
    ])
    pdf.code(
        "sudo apt update && sudo apt upgrade -y\n"
        "sudo apt install -y python3 python3-venv python3-pip nginx git",
        title="Instal paket dasar (Ubuntu)")

    pdf.h1("3", "Menyiapkan Kode Sumber")
    pdf.steps([
        "Di Emergent, klik 'Save to GitHub' lalu 'Push to GitHub' untuk menyimpan kode ke repositori Anda.",
        "SSH ke server, lalu clone repositori ke folder kerja, mis. /var/www/absensipro.",
        "Struktur penting: folder 'backend' (FastAPI) dan 'frontend/public' (file statis).",
    ])
    pdf.code(
        "sudo mkdir -p /var/www && cd /var/www\n"
        "sudo git clone <URL-REPOSITORI-ANDA> absensipro\n"
        "cd absensipro",
        title="Clone kode ke server")

    pdf.h1("4", "Menyiapkan Database (MongoDB)")
    pdf.h2("Opsi A — MongoDB Lokal")
    pdf.code(
        "sudo apt install -y mongodb-org   # atau ikuti panduan resmi MongoDB\n"
        "sudo systemctl enable --now mongod\n"
        "# URL koneksi lokal: mongodb://127.0.0.1:27017",
        title="Instal & jalankan MongoDB lokal")
    pdf.h2("Opsi B — MongoDB Atlas (Cloud)")
    pdf.bullets([
        "Buat cluster gratis di cloud.mongodb.com.",
        "Buat database user dan whitelist IP server Anda.",
        "Salin connection string, contoh: mongodb+srv://user:pass@cluster.mongodb.net",
    ])
    pdf.note("Database tidak perlu dibuat manual. Saat backend pertama kali dijalankan, sistem otomatis "
             "membuat koleksi, indeks, akun awal (admin/owner), 1 lokasi kantor, dan data contoh (seed).", "info")

    pdf.h1("5", "Deploy Backend (FastAPI)")
    pdf.steps([
        "Buat virtual environment Python dan pasang dependensi dari backend/requirements.txt.",
        "Buat berkas backend/.env berisi konfigurasi (lihat contoh di bawah).",
        "Jalankan backend memakai Gunicorn + Uvicorn worker, dikelola oleh systemd agar otomatis hidup.",
    ])
    pdf.code(
        "cd /var/www/absensipro/backend\n"
        "python3 -m venv venv\n"
        "source venv/bin/activate\n"
        "pip install -r requirements.txt\n"
        "pip install gunicorn uvicorn",
        title="Virtual environment & dependensi")
    pdf.code(
        'MONGO_URL="mongodb://127.0.0.1:27017"\n'
        'DB_NAME="absensipro"\n'
        'CORS_ORIGINS="https://absensi.perusahaan.co.id"\n'
        'JWT_SECRET="GANTI-dengan-string-acak-panjang-64-karakter"\n'
        'ADMIN_EMAIL="owner@perusahaan.co.id"\n'
        'ADMIN_PASSWORD="GANTI-password-kuat"\n'
        'WORK_START="09:00"\n'
        'SEED_DEMO="false"   # WAJIB false di produksi: hanya akun Owner yang dibuat',
        title="Contoh isi backend/.env")
    pdf.code(
        "python3 -c \"import secrets; print(secrets.token_hex(32))\"",
        title="Membuat nilai JWT_SECRET yang aman")
    pdf.para("Buat service systemd agar backend berjalan permanen dan otomatis restart:")
    pdf.code(
        "# /etc/systemd/system/absensipro.service\n"
        "[Unit]\n"
        "Description=AbsensiPro API\n"
        "After=network.target mongod.service\n\n"
        "[Service]\n"
        "WorkingDirectory=/var/www/absensipro/backend\n"
        "EnvironmentFile=/var/www/absensipro/backend/.env\n"
        "ExecStart=/var/www/absensipro/backend/venv/bin/gunicorn server:app \\\n"
        "  -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8001 -w 2\n"
        "Restart=always\n"
        "User=www-data\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target",
        title="Service systemd untuk backend")
    pdf.code(
        "sudo systemctl daemon-reload\n"
        "sudo systemctl enable --now absensipro\n"
        "sudo systemctl status absensipro\n"
        "curl http://127.0.0.1:8001/api/   # uji backend",
        title="Aktifkan & uji backend")

    pdf.h1("6", "Deploy Frontend (File Statis)")
    pdf.para("Frontend adalah HTML/JS statis di folder frontend/public — tidak perlu Node.js atau "
             "proses build. Nginx cukup menyajikan folder tersebut sebagai root situs.")
    pdf.bullets([
        "Root web: /var/www/absensipro/frontend/public",
        "Berisi: index.html, folder js/, folder modules/, logo, dan dokumen PDF.",
        "API dipanggil otomatis pada domain yang sama (origin) — tanpa konfigurasi URL tambahan.",
    ])

    pdf.h1("7", "Konfigurasi Nginx (Reverse Proxy)")
    pdf.para("Nginx menyajikan frontend dan meneruskan /api ke backend. Buat berkas konfigurasi:")
    pdf.code(
        "# /etc/nginx/sites-available/absensipro\n"
        "server {\n"
        "    listen 80;\n"
        "    server_name absensi.perusahaan.co.id;\n"
        "    root /var/www/absensipro/frontend/public;\n"
        "    index index.html;\n\n"
        "    # Frontend statis (SPA fallback ke index.html)\n"
        "    location / {\n"
        "        try_files $uri $uri/ /index.html;\n"
        "    }\n\n"
        "    # Teruskan API ke backend FastAPI\n"
        "    location /api/ {\n"
        "        proxy_pass http://127.0.0.1:8001;\n"
        "        proxy_set_header Host $host;\n"
        "        proxy_set_header X-Real-IP $remote_addr;\n"
        "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
        "        proxy_set_header X-Forwarded-Proto $scheme;\n"
        "    }\n"
        "}",
        title="Server block Nginx")
    pdf.code(
        "sudo ln -s /etc/nginx/sites-available/absensipro /etc/nginx/sites-enabled/\n"
        "sudo nginx -t && sudo systemctl reload nginx",
        title="Aktifkan konfigurasi")

    pdf.h1("8", "HTTPS / SSL — WAJIB")
    pdf.para("Kamera (verifikasi wajah) dan GPS (geofence) hanya berjalan pada HTTPS. Gunakan "
             "Let's Encrypt (gratis) via Certbot.")
    pdf.code(
        "sudo apt install -y certbot python3-certbot-nginx\n"
        "sudo certbot --nginx -d absensi.perusahaan.co.id\n"
        "# Certbot otomatis mengaktifkan HTTPS & memperbarui Nginx\n"
        "sudo systemctl status certbot.timer   # perpanjangan otomatis",
        title="Pasang sertifikat SSL")
    pdf.note("Setelah HTTPS aktif, perbarui CORS_ORIGINS di backend/.env menjadi alamat https Anda, "
             "lalu jalankan: sudo systemctl restart absensipro", "warn")

    pdf.h1("9", "Domain & DNS")
    pdf.steps([
        "Masuk ke panel pengelola domain Anda (registrar / DNS provider).",
        "Buat A record: nama 'absensi' (atau '@') diarahkan ke alamat IP publik server Anda.",
        "Tunggu propagasi DNS (umumnya 5–30 menit) sebelum menjalankan Certbot.",
    ])

    pdf.h1("10", "Keamanan Produksi")
    pdf.bullets([
        "WAJIB set SEED_DEMO=\"false\" agar akun demo (direksi/manager/hrd/staff contoh) TIDAK dibuat. "
        "Hanya akun Owner (dari ADMIN_EMAIL/ADMIN_PASSWORD) yang dibuat saat pertama kali jalan.",
        "WAJIB ganti JWT_SECRET dengan string acak panjang (token_hex 32).",
        "WAJIB ganti ADMIN_PASSWORD default dengan password kuat milik Anda.",
        "Set CORS_ORIGINS hanya ke domain resmi Anda (bukan '*').",
        "Aktifkan firewall: izinkan hanya port 80, 443, dan 22 (SSH). MongoDB jangan diekspos ke publik.",
        "Pertimbangkan menghapus/menonaktifkan akun demo bawaan setelah go-live.",
        "Lakukan pembaruan sistem & dependensi secara berkala.",
    ])
    pdf.code(
        "sudo ufw allow 22,80,443/tcp\n"
        "sudo ufw enable",
        title="Contoh firewall (UFW)")

    pdf.h1("11", "Pemeliharaan & Backup")
    pdf.bullets([
        "Backup database secara rutin (mongodump) dan simpan di lokasi aman.",
        "Pantau log backend: journalctl -u absensipro -f",
        "Pantau log Nginx: /var/log/nginx/access.log dan error.log",
    ])
    pdf.code(
        "# Backup\n"
        "mongodump --uri=\"$MONGO_URL\" --out /var/backups/absensipro_$(date +%F)\n\n"
        "# Update aplikasi setelah ada perubahan kode\n"
        "cd /var/www/absensipro && git pull\n"
        "cd backend && source venv/bin/activate && pip install -r requirements.txt\n"
        "sudo systemctl restart absensipro && sudo systemctl reload nginx",
        title="Backup & pembaruan")

    pdf.h1("12", "Alternatif Deployment (Ringkas)")
    pdf.table(
        ["Metode", "Cocok untuk", "Catatan"],
        [
            ["Emergent Deploy", "Tercepat, 1-klik + custom domain", "Managed, berbayar credits/bulan"],
            ["VPS + Nginx (panduan ini)", "Kontrol penuh, hosting pribadi", "Perlu setup manual, fleksibel"],
            ["Railway / Render", "Full-stack dari GitHub", "Auto-deploy, ada free tier terbatas"],
            ["MongoDB Atlas", "Database cloud", "Lepas dari beban server, mudah backup"],
        ],
        [1.3, 1.6, 1.6])

    pdf.h1("13", "Checklist & Troubleshooting")
    pdf.h2("Checklist Go-Live")
    pdf.bullets([
        "Backend aktif (systemctl status absensipro = running).",
        "curl http://127.0.0.1:8001/api/ memberi respons.",
        "Nginx menyajikan frontend pada domain.",
        "HTTPS aktif dan valid (gembok hijau di browser).",
        "JWT_SECRET, ADMIN_PASSWORD, CORS_ORIGINS, dan SEED_DEMO=false sudah diset untuk produksi.",
        "Login berhasil; kamera & GPS berfungsi pada HTTPS.",
    ])
    pdf.h2("Masalah Umum")
    faq = [
        ("Kamera/GPS tidak jalan", "Pastikan situs diakses via HTTPS (bukan http/IP). Ini syarat browser."),
        ("502 Bad Gateway di /api", "Backend mati atau salah port. Cek: systemctl status absensipro, "
         "pastikan proxy_pass ke 127.0.0.1:8001."),
        ("CORS error", "Set CORS_ORIGINS di backend/.env ke domain HTTPS Anda lalu restart backend."),
        ("Halaman blank/aset gagal", "Pastikan root Nginx menunjuk ke frontend/public dan file js/ "
         "serta modules/ dapat diakses."),
        ("Tailwind/wajah tidak termuat", "Server butuh akses internet keluar (CDN). Pastikan tidak "
         "diblokir firewall keluar."),
        ("Lupa kredensial admin", "Atur ADMIN_EMAIL/ADMIN_PASSWORD di .env; akun dibuat/diperbarui "
         "otomatis saat backend dijalankan."),
    ]
    for q, a in faq:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Lib", "B", 9.7)
        pdf.set_text_color(*INK)
        pdf.multi_cell(0, 5.2, "• " + q)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Lib", "", 9.7)
        pdf.set_text_color(55, 58, 64)
        pdf.multi_cell(0, 5.2, "   " + a)
        pdf.ln(1.4)

    pdf.ln(3)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Lib", "I", 9)
    pdf.set_text_color(*GREY)
    pdf.multi_cell(0, 5, "— Selesai —\nDokumen internal MitraKeuangan. Sesuaikan nama domain, path, dan "
                          "kredensial dengan lingkungan Anda.")

    out1 = "/app/frontend/public/Panduan_Deployment_AbsensiPro.pdf"
    out2 = "/app/Panduan_Deployment_AbsensiPro.pdf"
    pdf.output(out1)
    pdf.output(out2)
    print("PDF dibuat:", out1, "(", os.path.getsize(out1), "bytes )")


if __name__ == "__main__":
    build()
