# PRD — AbsensiPro (Sistem Absensi Karyawan)

## Original Problem Statement
Website aplikasi sistem absensi karyawan kantor untuk monitoring Owner, Direksi, dan Manager atas
kehadiran Staff. Fitur utama: absensi fleksibel dengan verifikasi wajah (face recognition asli) atau
scan QR, validasi berada di lokasi kantor (GPS geofence). Teknologi: HTML responsive + Tailwind CSS
Play CDN native, modul dipanggil dinamis dalam 1 index. Desain dashboard profesional, modern, formil.

## User Choices
- Backend + database asli (FastAPI + MongoDB)
- Face recognition asli (face-api.js, descriptor 128-d)
- GPS geofence (radius kantor)
- Role: Owner, Direksi, Manager (monitoring) + Staff
- Auth: JWT (Bearer token)

## Architecture
- Frontend: Vanilla HTML + Tailwind Play CDN, single `public/index.html` shell, ES dynamic `import()`
  modul (`/public/js`, `/public/modules`). React entry dijadikan no-op; CRA dev server menyajikan static.
- Backend: FastAPI `/api/*`, MongoDB (motor), JWT (bcrypt), RBAC (MONITOR_ROLES, MANAGE_ROLES).
- Libs: face-api.js (@vladmandic), html5-qrcode, qrcodejs, Phosphor Icons.

## User Personas
- Owner/Direksi: monitoring penuh + kelola karyawan & lokasi kantor.
- Manager: monitoring kehadiran tim.
- Staff: absen (wajah/QR), riwayat pribadi, daftar wajah.

## Implemented (2026-06-21)
- JWT auth (login/register/me) + RBAC + seed 7 demo users & 1 kantor + riwayat 7 hari.
- Absensi check-in/out: verifikasi wajah (Euclidean match) atau QR, enforce geofence (Haversine), status present/late.
- Pendaftaran wajah (descriptor 128-d disimpan di DB).
- Dashboard monitoring: KPI, tren 7 hari (SVG), breakdown departemen, aktivitas terbaru.
- Monitoring harian seluruh karyawan (filter tanggal + cari).
- CRUD Karyawan (modal) & CRUD Lokasi Kantor + QR generate.
- Riwayat pribadi, Profil.
- Verified: backend 31/31 pytest, frontend happy-paths 100% (testing agent iteration_1).

## Implemented (2026-06-22)
- Code-review fixes: `secrets` untuk seed, refactor kompleksitas (check_in/dashboard/seed), perbaikan React hook deps, hapus console statements, patch craco wds v5.
- **Role HRD + workflow persetujuan**: HRD bisa ajukan CRUD karyawan (tidak bisa set role owner/direksi); perubahan masuk antrian `employee_requests` (pending) dan baru berlaku setelah disetujui Owner/Direksi. Owner/Direksi tetap langsung. Endpoint: `GET /api/employee-requests`, `/approve`, `/reject`, `/pending-count`. Halaman frontend "Persetujuan" (approvals.js). Seed user hrd@company.com.
- Verified: backend curl + pytest 31/31; frontend testing agent iteration_2 (HRD nav bug ditemukan & diperbaiki).

## Backlog (next)
- P1: Export laporan (CSV/PDF) kehadiran per periode.
- P1: Jam kerja/shift & toleransi keterlambatan yang dapat dikonfigurasi via UI.
- P2: Peta Leaflet untuk visualisasi titik kantor & posisi check-in.
- P2: Notifikasi (email/Telegram) untuk keterlambatan/absen.
- P2: Migrasi `on_event` ke lifespan; pisahkan server.py menjadi modul.

## Next Tasks
- Tunggu feedback user; prioritaskan export laporan & konfigurasi jam kerja.
