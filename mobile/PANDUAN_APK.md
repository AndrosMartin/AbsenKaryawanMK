# 📱 Panduan Membuat APK AbsensiPro

Ada **2 cara** menjadikan AbsensiPro sebagai aplikasi di HP. Pilih sesuai kebutuhan.

---

## ✅ CARA 1 — PWA (Paling Cepat, TANPA Android Studio) — SUDAH AKTIF

Aplikasi sekarang sudah jadi **PWA (Progressive Web App)**. Artinya bisa langsung
di-"install" ke layar HP seperti aplikasi biasa, **tanpa Play Store dan tanpa coding**.

### Cara install di HP Android (Chrome):
1. Buka aplikasi AbsensiPro di **Google Chrome** di HP.
2. Tekan menu titik tiga (⋮) di pojok kanan atas.
3. Pilih **"Tambahkan ke layar Utama" / "Install aplikasi"**.
4. Ikon AbsensiPro muncul di home screen — buka layaknya aplikasi (fullscreen, tanpa address bar).

### Cara install di iPhone (Safari):
1. Buka aplikasi di **Safari**.
2. Tekan tombol **Share** (kotak dengan panah ke atas).
3. Pilih **"Add to Home Screen"**.

> Kamera (wajah & QR), GPS, dan notifikasi tetap berfungsi normal di mode PWA selama HP online.

---

## 📦 CARA 2 — File APK Asli (.apk) menggunakan Capacitor

Cara ini menghasilkan file `.apk` yang bisa dibagikan/di-install manual atau diunggah ke Play Store.
File `.apk` **harus di-build di komputer Anda** (server Emergent tidak punya Android SDK).

### Prasyarat di komputer Anda:
- **Node.js** (v18+)
- **Java JDK 17**
- **Android Studio** (termasuk Android SDK)

### Langkah-langkah:

```bash
# 1. Salin folder mobile/ ini ke komputer Anda, lalu masuk ke dalamnya
cd mobile

# 2. Install dependency Capacitor
npm install        # atau: yarn install

# 3. Siapkan folder web kosong (karena app me-load server live)
mkdir -p www && echo "AbsensiPro" > www/index.html

# 4. Tambahkan platform Android
npx cap add android

# 5. Sinkronkan konfigurasi
npx cap sync android
```

### Tambahkan izin (PENTING):
Buka file `android/app/src/main/AndroidManifest.xml`, lalu salin isi dari
`AndroidManifest.permissions.xml` (di folder ini) ke dalam tag `<manifest>`
(sebelum `<application>`). Ini agar **Kamera & GPS** diizinkan.

### Build APK:

**Opsi A — lewat terminal (APK debug, untuk testing):**
```bash
cd android
./gradlew assembleDebug
# Hasil: android/app/build/outputs/apk/debug/app-debug.apk
```

**Opsi B — lewat Android Studio (disarankan untuk rilis):**
```bash
npx cap open android
# Di Android Studio: Build > Build Bundle(s)/APK(s) > Build APK(s)
```

### ⚠️ Ganti URL Server
Pada file `capacitor.config.json`, ubah `server.url` ke **domain PRODUKSI** Anda
(bukan URL preview) setelah aplikasi di-deploy:

```json
"server": { "url": "https://DOMAIN-PRODUKSI-ANDA.com" }
```

Lalu jalankan lagi `npx cap sync android` sebelum build.

---

## Ringkasan
| | PWA (Cara 1) | APK Capacitor (Cara 2) |
|---|---|---|
| Butuh Android Studio | ❌ Tidak | ✅ Ya |
| Hasil file `.apk` | ❌ Tidak | ✅ Ya |
| Bisa upload Play Store | ❌ | ✅ |
| Kecepatan setup | ⚡ Instan | 🛠️ 15–30 menit |
| Status | ✅ Sudah aktif | 📋 Tinggal build |
