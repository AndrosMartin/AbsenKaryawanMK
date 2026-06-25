// Face enrollment — capture and store a 128-d descriptor for the logged-in user
export async function render(root, ctx) {
  const { ui } = ctx;
  let stream = null;
  let descriptor = null;
  const enrolled = ctx.user.face_enrolled;

  root.innerHTML = `
  <div class="max-w-3xl mx-auto space-y-6 stagger" data-testid="face-page">
    <div>
      <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Biometrik</p>
      <h2 class="font-heading font-bold text-2xl text-slate-900">Pendaftaran Wajah</h2>
      <p class="text-sm text-slate-500 mt-1">Wajah Anda digunakan untuk verifikasi saat absensi. Data disimpan sebagai vektor matematis, bukan foto.</p>
    </div>

    <div class="bg-white border border-slate-200 rounded-xl p-6">
      <div class="flex items-center gap-2 mb-4 text-sm">
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${enrolled ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-amber-50 text-amber-700 border-amber-200"}">
          <i class="ph-fill ${enrolled ? "ph-check-circle" : "ph-warning"}"></i>${enrolled ? "Wajah sudah terdaftar" : "Belum terdaftar"}
        </span>
      </div>

      <div class="grid md:grid-cols-2 gap-6">
        <div class="relative aspect-square rounded-xl bg-ink overflow-hidden border border-slate-800 flex items-center justify-center">
          <video id="cam" autoplay muted playsinline class="w-full h-full object-cover"></video>
          <canvas id="face-canvas" class="absolute inset-0 w-full h-full pointer-events-none"></canvas>
          <div id="overlay" class="absolute inset-0 bg-ink/85 flex flex-col items-center justify-center text-center p-4">
            <i class="ph ph-user-focus text-4xl text-slate-500"></i>
            <p class="text-slate-300 text-sm mt-2">Aktifkan kamera untuk mendaftar</p>
            <button id="start-cam" data-testid="start-camera" class="mt-3 bg-white text-slate-900 px-4 py-2 rounded-lg text-sm font-medium">Aktifkan Kamera</button>
          </div>
        </div>

        <div class="flex flex-col justify-center">
          <ol class="space-y-3 text-sm text-slate-600 mb-6">
            <li class="flex gap-3"><span class="h-6 w-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-semibold shrink-0">1</span> Pastikan pencahayaan cukup terang.</li>
            <li class="flex gap-3"><span class="h-6 w-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-semibold shrink-0">2</span> Posisikan wajah di dalam bingkai.</li>
            <li class="flex gap-3"><span class="h-6 w-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-semibold shrink-0">3</span> Tekan "Daftarkan Wajah" dan tahan posisi.</li>
          </ol>
          <button id="enroll-btn" data-testid="enroll-face-btn" disabled
            class="w-full bg-gold disabled:bg-slate-200 disabled:text-slate-400 text-ink py-3 rounded-lg text-sm font-semibold hover:bg-gold-500 flex items-center justify-center gap-2">
            <i class="ph ph-user-plus"></i> ${enrolled ? "Perbarui Wajah" : "Daftarkan Wajah"}
          </button>
          <p id="face-msg" class="text-xs text-slate-400 mt-3 text-center">Aktifkan kamera terlebih dahulu.</p>
        </div>
      </div>
    </div>
  </div>`;

  const video = root.querySelector("#cam");
  const canvas = root.querySelector("#face-canvas");
  const overlay = root.querySelector("#overlay");
  const enrollBtn = root.querySelector("#enroll-btn");
  const msg = root.querySelector("#face-msg");

  function stopLoop() {
    if (window.__faceLoop) { clearInterval(window.__faceLoop); window.__faceLoop = null; }
  }

  root.querySelector("#start-cam").onclick = async () => {
    try {
      msg.textContent = "Memuat model pengenalan wajah…";
      await ui.loadFaceModels();
      stream = await ui.startCamera(video);
      ctx.setStream(stream);
      overlay.style.display = "none";
      msg.textContent = "Kamera aktif — mendeteksi wajah secara otomatis…";
      stopLoop();
      window.__faceLoop = setInterval(async () => {
        if (!stream) return;
        let det;
        try { det = await ui.detectFaceFull(video); } catch (e) { return; }
        ui.drawFaceBox(canvas, video, det);
        if (det && det.detection.score > 0.55) {
          descriptor = Array.from(det.descriptor);
          enrollBtn.disabled = false;
          msg.innerHTML = `<span class="text-emerald-600 font-medium">Wajah terdeteksi</span> — klik "${enrolled ? "Perbarui" : "Daftarkan"} Wajah".`;
        } else {
          descriptor = null;
          enrollBtn.disabled = true;
          msg.textContent = "Mencari wajah… posisikan wajah di dalam bingkai.";
        }
      }, 320);
    } catch (e) { msg.textContent = "Gagal mengakses kamera: " + e.message; }
  };

  enrollBtn.onclick = async () => {
    enrollBtn.disabled = true;
    msg.textContent = "Mendaftarkan wajah…";
    try {
      const desc = descriptor || await ui.detectDescriptor(video);
      if (!desc) { msg.textContent = "Wajah tidak terdeteksi, coba lagi."; enrollBtn.disabled = false; return; }
      await ctx.api.post("/face/enroll", { descriptor: desc });
      await ctx.refreshUser();
      ui.toast("Wajah berhasil didaftarkan!", "success");
      stopLoop();
      ui.stopCamera(stream); stream = null;
      ctx.navigate("face");
    } catch (e) {
      msg.innerHTML = `<span class="text-rose-600">${e.message}</span>`;
      enrollBtn.disabled = false;
    }
  };
}
