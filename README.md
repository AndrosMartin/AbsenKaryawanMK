# AbsensiPro — Sistem Absensi Karyawan

Sistem absensi karyawan modern untuk monitoring kehadiran oleh **Owner, Direksi, dan Manager**.
Karyawan melakukan absensi secara fleksibel dengan **verifikasi wajah (face recognition)** atau
**scan QR code**, divalidasi dengan **lokasi GPS (geofence)** agar memastikan benar-benar berada di kantor.

## Teknologi
- **Frontend**: HTML responsive + **Tailwind CSS Play CDN (native)** + Vanilla JS. Modul dipanggil
  secara **dinamis** (native ES `import()`) ke dalam **satu `index.html`** sebagai shell.
- **Backend**: FastAPI (Python) + MongoDB (Motor async).
- **Auth**: JWT (Bearer token) dengan hashing bcrypt + Role-Based Access Control.
- **Face Recognition**: `face-api.js` (@vladmandic) — descriptor wajah 128 dimensi, dibandingkan
  dengan Euclidean distance (asli, berjalan di browser).
- **QR**: `html5-qrcode` (scan) + `qrcodejs` (generate QR kantor).
- **GPS**: Browser Geolocation API + perhitungan Haversine untuk validasi radius geofence.

## Peran (Role) & Hak Akses
| Role | Absen | Riwayat sendiri | Dashboard & Monitoring | Lihat Karyawan | Kelola Karyawan & Lokasi |
|------|:---:|:---:|:---:|:---:|:---:|
| Owner | ✅ | ✅ | ✅ | ✅ | ✅ |
| Direksi | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manager | ✅ | ✅ | ✅ | ✅ | ❌ |
| Staff | ✅ | ✅ | ❌ | ❌ | ❌ |

## Fitur Utama
1. **Absensi Fleksibel** — Check-in & Check-out dengan dua metode: Wajah atau QR Code.
2. **Verifikasi Wajah** — Pendaftaran wajah sekali, lalu verifikasi identitas saat absen.
3. **Validasi Lokasi (Geofence)** — Absen hanya diterima bila berada dalam radius kantor.
4. **Penentuan Status Otomatis** — Tepat Waktu / Terlambat (berdasar jam masuk `WORK_START`).
5. **Dashboard Monitoring** — KPI hari ini, tren 7 hari, breakdown departemen, aktivitas terbaru.
6. **Monitoring Real-time** — Tabel status seluruh karyawan per tanggal (hadir/terlambat/absen).
7. **Manajemen Karyawan** — CRUD karyawan dengan role, departemen, posisi.
8. **Manajemen Lokasi Kantor** — Titik GPS + radius + QR code absensi (printable).
9. **Riwayat Pribadi** — Rekap kehadiran tiap karyawan.

## Struktur Folder & File
```
/app
├── backend/
│   ├── server.py            # FastAPI: auth, attendance, face, offices, employees, dashboard, seed
│   ├── requirements.txt
│   └── .env                 # MONGO_URL, DB_NAME, JWT_SECRET, ADMIN_*, WORK_START
│
├── frontend/
│   ├── public/
│   │   ├── index.html       # SHELL tunggal: Tailwind CDN, fonts, libs, loader
│   │   ├── js/
│   │   │   ├── api.js        # Lapisan API (fetch + Bearer token)
│   │   │   ├── ui.js         # Helper UI, format, face-api & kamera & GPS
│   │   │   └── main.js       # Shell: auth, sidebar/topbar, router, dynamic module loader
│   │   └── modules/          # Modul dimuat dinamis sesuai navigasi
│   │       ├── login.js      # Halaman login (split-screen korporat)
│   │       ├── dashboard.js  # Dashboard monitoring + chart
│   │       ├── checkin.js    # Absensi: kamera wajah, scan QR, status GPS
│   │       ├── history.js    # Riwayat absensi pribadi
│   │       ├── monitoring.js # Tabel monitoring seluruh karyawan
│   │       ├── employees.js  # Manajemen karyawan (CRUD)
│   │       ├── offices.js    # Lokasi kantor + geofence + QR
│   │       ├── face.js       # Pendaftaran wajah
│   │       └── profile.js    # Profil pengguna
│   ├── src/index.js          # No-op (shell vanilla yang mengontrol halaman)
│   └── craco.config.js       # Patch kompatibilitas webpack-dev-server v5
│
└── README.md
```

## API Endpoints (prefix `/api`)
- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `POST /face/enroll`
- `GET/POST/PUT/DELETE /offices`
- `POST /attendance/check-in`, `POST /attendance/check-out`
- `GET /attendance/today`, `GET /attendance/me`, `GET /attendance?date=`
- `GET /dashboard/stats`
- `GET/POST/PUT/DELETE /employees`

## Akun Demo (password: `password123`)
- Owner: `owner@company.com`
- Direksi: `direksi@company.com`
- Manager: `manager@company.com`
- Staff: `dewi@company.com`, `rizki@company.com`, `nina@company.com`, `eko@company.com`

> Catatan: Verifikasi wajah & scan QR memerlukan izin **kamera**; geofence memerlukan izin **lokasi (GPS)**.
> Lokasi kantor default: "Kantor Pusat Jakarta" (-6.208763, 106.845599), radius 250m.
> Owner/Direksi dapat menambah lokasi dan menekan "Gunakan lokasi saya" agar geofence sesuai posisi nyata.
