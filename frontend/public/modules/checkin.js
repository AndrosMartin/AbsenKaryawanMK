// Attendance check-in / check-out with Face recognition, QR scan, and GPS geofence
export async function render(root, ctx) {
  const { ui } = ctx;
  let today = { checked_in: false };
  try { today = await ctx.api.get("/attendance/today"); } catch (e) {}

  const u = ctx.user;
  let gps = null;       // {lat,lng,accuracy}
  let stream = null;    // camera stream
  let qrScanner = null; // Html5Qrcode instance
  let busy = false;

  root.innerHTML = `
  <div class="max-w-5xl mx-auto space-y-6 stagger" data-testid="checkin-page">
    <div>
      <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Absensi Kehadiran</p>
      <h2 class="font-heading font-bold text-2xl text-slate-900">Halo, ${u.name.split(" ")[0]} 👋</h2>
      <p class="text-sm text-slate-500 mt-1">Pastikan Anda berada di lokasi kantor, lalu verifikasi dengan wajah atau QR code.</p>
    </div>

    <!-- Today status -->
    <div id="today-card"></div>

    <div class="grid lg:grid-cols-3 gap-6">
      <!-- GPS card -->
      <div class="bg-white border border-slate-200 rounded-xl p-5">
        <div class="flex items-center gap-2 mb-3">
          <i class="ph-fill ph-map-pin text-slate-900 text-lg"></i>
          <h3 class="font-heading font-semibold text-slate-900">Lokasi GPS</h3>
        </div>
        <div id="gps-status" class="text-sm text-slate-500">Mengambil lokasi…</div>
        <button id="gps-refresh" data-testid="gps-refresh" class="mt-3 text-xs font-medium text-slate-900 hover:underline flex items-center gap-1">
          <i class="ph ph-arrows-clockwise"></i> Perbarui lokasi
        </button>
      </div>

      <!-- Verification panel -->
      <div class="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5">
        <div class="flex gap-2 mb-4 bg-slate-100 p-1 rounded-lg w-fit">
          <button data-tab="face" data-testid="tab-face" class="tab-btn px-4 py-1.5 rounded-md text-sm font-medium transition-colors">
            <i class="ph ph-user-focus"></i> Wajah
          </button>
          <button data-tab="qr" data-testid="tab-qr" class="tab-btn px-4 py-1.5 rounded-md text-sm font-medium transition-colors">
            <i class="ph ph-qr-code"></i> QR Code
          </button>
        </div>
        <div id="verify-body"></div>
      </div>
    </div>
  </div>`;

  const todayCard = root.querySelector("#today-card");
  const gpsStatus = root.querySelector("#gps-status");
  const verifyBody = root.querySelector("#verify-body");
  let activeTab = "face";

  function renderToday() {
    if (today.checked_in) {
      const out = today.check_out;
      todayCard.innerHTML = `
        <div class="bg-white border border-slate-200 rounded-xl p-5 flex flex-wrap items-center gap-5">
          <div class="h-12 w-12 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center"><i class="ph-fill ph-check-circle text-2xl"></i></div>
          <div class="flex-1">
            <p class="font-heading font-semibold text-slate-900">Anda sudah check-in hari ini</p>
            <p class="text-sm text-slate-500">${today.office_name} · ${today.method === "face" ? "Verifikasi Wajah" : "QR Code"}</p>
          </div>
          <div class="flex gap-6">
            <div><p class="text-xs text-slate-400 uppercase tracking-widest">Masuk</p><p class="font-mono font-semibold text-slate-900">${ui.fmtTime(today.check_in)}</p></div>
            <div><p class="text-xs text-slate-400 uppercase tracking-widest">Keluar</p><p class="font-mono font-semibold text-slate-900">${out ? ui.fmtTime(out) : "—"}</p></div>
            <div class="flex items-center">${ui.statusPill(today.status)}</div>
          </div>
          ${!out ? `<button id="checkout-btn" data-testid="checkout-btn" class="bg-gold text-ink px-4 py-2.5 rounded-lg text-sm font-semibold hover:bg-gold-500">Check-out Sekarang</button>` : ""}
        </div>
        ${lateBanner()}`;
      if (!out) root.querySelector("#checkout-btn").onclick = doCheckout;
      bindLateForm();
    } else {
      todayCard.innerHTML = `
        <div class="bg-ink rounded-xl p-5 flex items-center gap-4 text-white">
          <i class="ph-fill ph-clock text-2xl"></i>
          <div><p class="font-heading font-semibold">Belum check-in hari ini</p><p class="text-sm text-slate-400">Selesaikan verifikasi di bawah untuk mencatat kehadiran.</p></div>
        </div>`;
    }
  }

  function lateBanner() {
    if (today.status !== "late" && !today.late_compensated) return "";
    if (today.late_category === "potong_cuti") {
      return `<div class="mt-3 flex items-start gap-3 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3" data-testid="late-deduct-banner">
        <i class="ph-fill ph-warning-octagon text-rose-600 text-lg mt-0.5"></i>
        <p class="text-sm text-rose-800">Anda check-in melewati pukul 12:00. Sesuai kebijakan, <strong>cuti Anda dipotong 0,5 hari</strong>.</p></div>`;
    }
    if (today.late_category === "perlu_approval") {
      if (today.late_review_status === "approved") {
        return `<div class="mt-3 flex items-start gap-3 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3">
          <i class="ph-fill ph-check-circle text-emerald-600 text-lg mt-0.5"></i>
          <p class="text-sm text-emerald-800">Keterlambatan Anda telah <strong>disetujui</strong>${today.late_compensated ? " dan dihitung HADIR" : ""}.</p></div>`;
      }
      if (today.late_review_status === "rejected") {
        return `<div class="mt-3 flex items-start gap-3 bg-amber-50 border border-amber-300 rounded-xl px-4 py-3">
          <i class="ph-fill ph-flag text-amber-600 text-lg mt-0.5"></i>
          <p class="text-sm text-amber-800">Keterlambatan ditolak — Anda mendapat <strong>Kartu Kuning</strong> (berdampak pada KPI).</p></div>`;
      }
      if (today.late_reason) {
        return `<div class="mt-3 flex items-start gap-3 bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3">
          <i class="ph-fill ph-hourglass-medium text-yellow-600 text-lg mt-0.5"></i>
          <p class="text-sm text-yellow-800">Alasan terkirim, menunggu persetujuan atasan. Jika tidak disetujui, akan menjadi <strong>Kartu Kuning</strong>.</p></div>`;
      }
      return `<div class="mt-3 bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3" data-testid="late-reason-card">
        <p class="text-sm text-yellow-800 mb-2"><i class="ph-fill ph-warning text-yellow-600"></i> Anda terlambat. Masukkan <strong>alasan keterlambatan</strong> agar dapat ditinjau atasan (HRD/Manager/Direksi).</p>
        <div class="flex gap-2">
          <input id="late-reason-input" data-testid="late-reason-input" placeholder="Contoh: kendala transportasi…" class="flex-1 px-3 py-2 border border-yellow-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500" />
          <button id="late-reason-submit" data-testid="late-reason-submit" class="px-4 py-2 rounded-lg text-sm font-semibold bg-ink text-gold hover:bg-ink/90">Kirim</button>
        </div></div>`;
    }
    return "";
  }

  function bindLateForm() {
    const btn = root.querySelector("#late-reason-submit");
    if (!btn) return;
    btn.onclick = async () => {
      const val = root.querySelector("#late-reason-input").value.trim();
      if (!val) { ui.toast("Alasan tidak boleh kosong", "error"); return; }
      try {
        await ctx.api.post("/late/reason", { reason: val });
        today.late_reason = val;
        ui.toast("Alasan keterlambatan terkirim", "success");
        renderToday();
      } catch (e) { ui.toast(e.message, "error"); }
    };
  }

  async function loadGps() {
    gpsStatus.innerHTML = `<span class="flex items-center gap-2"><i class="ph ph-circle-notch spin"></i> Mengambil lokasi…</span>`;
    try {
      gps = await ui.getPosition();
      gpsStatus.innerHTML = `
        <div class="flex items-center gap-2 text-emerald-700"><i class="ph-fill ph-check-circle"></i><span class="font-medium">Lokasi terdeteksi</span></div>
        <p class="font-mono text-xs text-slate-500 mt-2">${gps.lat.toFixed(5)}, ${gps.lng.toFixed(5)}</p>
        <p class="text-xs text-slate-400 mt-0.5">Akurasi ±${Math.round(gps.accuracy)}m</p>`;
    } catch (e) {
      gps = null;
      gpsStatus.innerHTML = `<div class="flex items-center gap-2 text-rose-600"><i class="ph-fill ph-warning-circle"></i><span class="text-sm">${e.message}</span></div>`;
    }
  }

  // ---- FACE TAB ----
  async function renderFaceTab() {
    if (!u.face_enrolled) {
      verifyBody.innerHTML = `
        <div class="aspect-video rounded-xl bg-ink flex flex-col items-center justify-center text-center p-6">
          <i class="ph ph-user-focus text-4xl text-slate-500"></i>
          <p class="text-white font-medium mt-3">Wajah belum didaftarkan</p>
          <p class="text-slate-400 text-sm mt-1">Daftarkan wajah Anda dulu di menu "Wajah Saya".</p>
          <button data-testid="goto-face-enroll" id="goto-enroll" class="mt-4 bg-white text-slate-900 px-4 py-2 rounded-lg text-sm font-medium">Daftarkan Wajah</button>
        </div>`;
      verifyBody.querySelector("#goto-enroll").onclick = () => ctx.navigate("face");
      return;
    }
    verifyBody.innerHTML = `
      <div class="relative aspect-video rounded-xl bg-ink overflow-hidden border border-slate-800 flex items-center justify-center">
        <video id="cam" autoplay muted playsinline class="w-full h-full object-cover"></video>
        <canvas id="face-canvas" class="absolute inset-0 w-full h-full pointer-events-none"></canvas>
        <div id="scan-hint" class="absolute top-3 left-1/2 -translate-x-1/2 hidden">
          <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-ink/70 text-gold text-xs font-medium backdrop-blur">
            <i class="ph ph-scan"></i><span id="scan-hint-text">Mencari wajah…</span></span>
        </div>
        <div id="cam-overlay" class="absolute inset-0 bg-ink/80 flex flex-col items-center justify-center text-center text-white p-4">
          <i class="ph ph-user-focus text-3xl text-gold"></i>
          <p class="text-sm mt-2 text-slate-300">Aktifkan kamera untuk deteksi otomatis</p>
          <button id="start-cam" data-testid="start-camera" class="mt-3 bg-gold text-ink px-4 py-2 rounded-lg text-sm font-semibold hover:bg-gold-500">Aktifkan Kamera</button>
        </div>
      </div>
      <button id="face-checkin" data-testid="face-checkin-btn" disabled
        class="mt-4 w-full bg-gold disabled:bg-slate-200 disabled:text-slate-400 text-ink py-3 rounded-lg text-sm font-semibold hover:bg-gold-500 flex items-center justify-center gap-2">
        <i class="ph ph-fingerprint"></i> Check-in Manual
      </button>
      <p id="face-msg" class="text-xs text-slate-400 mt-2 text-center">Deteksi wajah otomatis — wajah Anda akan dipindai begitu kamera aktif.</p>`;

    const video = verifyBody.querySelector("#cam");
    const canvas = verifyBody.querySelector("#face-canvas");
    const overlay = verifyBody.querySelector("#cam-overlay");
    const hint = verifyBody.querySelector("#scan-hint");
    const hintText = verifyBody.querySelector("#scan-hint-text");
    const btn = verifyBody.querySelector("#face-checkin");
    const msg = verifyBody.querySelector("#face-msg");

    let lastDescriptor = null;
    let stableCount = 0;
    let autoFired = false;

    function stopLoop() {
      if (window.__faceLoop) { clearInterval(window.__faceLoop); window.__faceLoop = null; }
    }

    async function doFaceCheckin(descriptor) {
      if (busy) return;
      if (today.checked_in) return;
      if (!gps) { ui.toast("Lokasi GPS belum tersedia", "error"); autoFired = false; return; }
      busy = true; btn.disabled = true;
      msg.textContent = "Wajah terdeteksi — memverifikasi & mencatat kehadiran…";
      try {
        const desc = descriptor || await ui.detectDescriptor(video);
        if (!desc) { msg.textContent = "Wajah tidak terdeteksi, coba lagi."; busy = false; autoFired = false; btn.disabled = false; return; }
        const res = await ctx.api.post("/attendance/check-in", {
          method: "face", lat: gps.lat, lng: gps.lng, descriptor: desc,
        });
        stopLoop();
        ui.stopCamera(stream); stream = null;
        ui.toast("Check-in berhasil! " + (res.status === "late" ? "(Terlambat)" : "(Tepat waktu)"), "success");
        today = { checked_in: true, ...res };
        renderToday();
        renderFaceTab();
      } catch (e) {
        msg.innerHTML = `<span class="text-rose-600">${e.message}</span>`;
        ui.toast(e.message, "error");
        busy = false; autoFired = false; btn.disabled = false;
      }
    }

    function startDetectLoop() {
      stopLoop();
      window.__faceLoop = setInterval(async () => {
        if (busy || !stream) return;
        let det;
        try { det = await ui.detectFaceFull(video); } catch (e) { return; }
        ui.drawFaceBox(canvas, video, det);
        hint.classList.remove("hidden");
        if (det && det.detection.score > 0.55) {
          lastDescriptor = Array.from(det.descriptor);
          btn.disabled = false;
          stableCount++;
          if (today.checked_in) {
            hintText.textContent = "Sudah check-in";
          } else if (stableCount < 3) {
            hintText.textContent = "Wajah terdeteksi…";
            msg.textContent = "Wajah terdeteksi, tahan posisi…";
          } else if (!autoFired) {
            autoFired = true;
            hintText.textContent = "Memproses…";
            doFaceCheckin(lastDescriptor);
          }
        } else {
          stableCount = 0;
          hintText.textContent = "Mencari wajah…";
        }
      }, 320);
    }

    verifyBody.querySelector("#start-cam").onclick = async () => {
      try {
        msg.textContent = "Memuat model pengenalan wajah…";
        await ui.loadFaceModels();
        stream = await ui.startCamera(video);
        ctx.setStream(stream);
        overlay.style.display = "none";
        msg.textContent = "Kamera aktif — deteksi otomatis berjalan. Posisikan wajah Anda.";
        startDetectLoop();
      } catch (e) {
        msg.textContent = "Gagal mengakses kamera: " + e.message;
      }
    };

    btn.onclick = () => doFaceCheckin(lastDescriptor);
  }

  // ---- QR TAB ----
  async function renderQrTab() {
    verifyBody.innerHTML = `
      <div id="qr-reader" data-testid="qr-reader" class="rounded-xl overflow-hidden border border-slate-200 bg-ink min-h-[260px]"></div>
      <button id="start-qr" data-testid="start-qr" class="mt-4 w-full bg-gold text-ink py-3 rounded-lg text-sm font-semibold hover:bg-gold-500 flex items-center justify-center gap-2">
        <i class="ph ph-qr-code"></i> Mulai Scan QR Kantor
      </button>
      <p id="qr-msg" class="text-xs text-slate-400 mt-2 text-center">Arahkan kamera ke QR code yang terpasang di kantor.</p>`;

    const startBtn = verifyBody.querySelector("#start-qr");
    const qrMsg = verifyBody.querySelector("#qr-msg");

    startBtn.onclick = async () => {
      if (today.checked_in) return ui.toast("Anda sudah check-in hari ini", "info");
      if (!gps) return ui.toast("Lokasi GPS belum tersedia", "error");
      if (typeof Html5Qrcode === "undefined") return ui.toast("Library QR gagal dimuat", "error");
      startBtn.disabled = true;
      qrMsg.textContent = "Mengaktifkan kamera…";
      try {
        qrScanner = new Html5Qrcode("qr-reader");
        await qrScanner.start(
          { facingMode: "environment" },
          { fps: 10, qrbox: 220 },
          async (decoded) => {
            if (busy) return; busy = true;
            try { await qrScanner.stop(); } catch (e) {}
            qrMsg.textContent = "Memverifikasi…";
            try {
              const res = await ctx.api.post("/attendance/check-in", {
                method: "qr", lat: gps.lat, lng: gps.lng, qr_code: decoded,
              });
              ui.toast("Check-in berhasil via QR!", "success");
              today = { checked_in: true, ...res };
              renderToday(); renderQrTab();
            } catch (e) {
              qrMsg.innerHTML = `<span class="text-rose-600">${e.message}</span>`;
              ui.toast(e.message, "error");
              startBtn.disabled = false;
            } finally { busy = false; }
          },
          () => {}
        );
      } catch (e) {
        qrMsg.textContent = "Gagal: " + e.message;
        startBtn.disabled = false;
      }
    };
  }

  async function switchTab(tab) {
    activeTab = tab;
    root.querySelectorAll(".tab-btn").forEach((b) => {
      const on = b.getAttribute("data-tab") === tab;
      b.classList.toggle("bg-white", on);
      b.classList.toggle("text-slate-900", on);
      b.classList.toggle("shadow-sm", on);
      b.classList.toggle("text-slate-500", !on);
    });
    if (window.__faceLoop) { clearInterval(window.__faceLoop); window.__faceLoop = null; }
    if (stream) { ui.stopCamera(stream); stream = null; }
    if (qrScanner) { try { await qrScanner.stop(); } catch (e) {} qrScanner = null; }
    if (tab === "face") renderFaceTab(); else renderQrTab();
  }

  async function doCheckout() {
    try {
      const res = await ctx.api.post("/attendance/check-out", gps || {});
      today = { checked_in: true, ...res };
      ui.toast("Check-out berhasil. Selamat beristirahat!", "success");
      renderToday();
    } catch (e) { ui.toast(e.message, "error"); }
  }

  root.querySelectorAll(".tab-btn").forEach((b) => b.onclick = () => switchTab(b.getAttribute("data-tab")));
  root.querySelector("#gps-refresh").onclick = loadGps;

  renderToday();
  switchTab("face");
  loadGps();
}
