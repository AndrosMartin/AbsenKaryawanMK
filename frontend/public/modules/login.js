// Login / Authentication module — MitraKeuangan brand (black / gold / white)
export async function render(root, ctx) {
  const { ui } = ctx;

  root.innerHTML = `
  <div class="min-h-screen grid lg:grid-cols-2 fade-in">
    <!-- Left: brand -->
    <div class="relative hidden lg:flex flex-col justify-between p-12 bg-hero-dark overflow-hidden">
      <div class="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-gold/10 blur-3xl"></div>
      <div class="absolute -left-16 bottom-10 h-56 w-56 rounded-full bg-gold/5 blur-3xl"></div>
      <div class="relative flex items-center gap-3">
        <img src="/logo-mitra.jpg" alt="MitraKeuangan" class="h-12 w-12 rounded-xl object-cover ring-1 ring-gold/40" />
        <span class="font-heading font-bold text-xl"><span class="text-white">Mitra</span><span class="text-gold">Keuangan</span></span>
      </div>
      <div class="relative max-w-md">
        <p class="text-gold text-xs font-medium uppercase tracking-[0.3em] mb-4">Opportunity Seekers</p>
        <h2 class="font-heading font-bold text-4xl text-white leading-tight">Kehadiran terverifikasi, monitoring tanpa batas.</h2>
        <p class="text-slate-300 mt-4 text-base">Absensi dengan verifikasi wajah, QR code, dan validasi lokasi GPS. Pantau kehadiran seluruh tim secara real-time.</p>
        <div class="flex gap-8 mt-8">
          <div><p class="font-heading font-bold text-2xl text-gold">Face</p><p class="text-xs text-slate-400 uppercase tracking-widest">Recognition</p></div>
          <div><p class="font-heading font-bold text-2xl text-gold">GPS</p><p class="text-xs text-slate-400 uppercase tracking-widest">Geofence</p></div>
          <div><p class="font-heading font-bold text-2xl text-gold">QR</p><p class="text-xs text-slate-400 uppercase tracking-widest">Scan</p></div>
        </div>
      </div>
      <div class="relative text-xs text-slate-500">© 2026 MitraKeuangan · Sistem Absensi & Monitoring</div>
    </div>

    <!-- Right: form -->
    <div class="flex items-center justify-center p-6 sm:p-12 bg-slate-50">
      <div class="w-full max-w-sm">
        <div class="lg:hidden flex items-center gap-3 mb-8">
          <img src="/logo-mitra.jpg" alt="MitraKeuangan" class="h-11 w-11 rounded-xl object-cover" />
          <span class="font-heading font-bold text-xl"><span class="text-ink">Mitra</span><span class="text-gold-600">Keuangan</span></span>
        </div>
        <p class="text-xs font-medium text-gold-600 uppercase tracking-widest">Selamat datang</p>
        <h1 class="font-heading font-bold text-3xl text-slate-900 mt-1">Masuk ke akun Anda</h1>
        <p class="text-sm text-slate-500 mt-2">Gunakan kredensial perusahaan untuk melanjutkan.</p>

        <form id="login-form" class="mt-8 space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Email</label>
            <input data-testid="login-email" id="email" type="email" required placeholder="nama@company.com"
              class="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gold focus:border-transparent" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
            <input data-testid="login-password" id="password" type="password" required placeholder="••••••••"
              class="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gold focus:border-transparent" />
          </div>
          <p id="login-error" class="text-sm text-rose-600 hidden"></p>
          <button data-testid="login-submit" type="submit"
            class="w-full bg-gold text-ink py-2.5 rounded-lg text-sm font-semibold hover:bg-gold-500 transition-colors flex items-center justify-center gap-2 shadow-sm shadow-gold/30">
            <span id="login-btn-text">Masuk</span>
          </button>
        </form>
      </div>
    </div>
  </div>`;

  const form = root.querySelector("#login-form");
  const errEl = root.querySelector("#login-error");
  const btnText = root.querySelector("#login-btn-text");

  form.onsubmit = async (e) => {
    e.preventDefault();
    errEl.classList.add("hidden");
    btnText.innerHTML = `<i class="ph ph-circle-notch spin"></i>`;
    try {
      const email = root.querySelector("#email").value.trim();
      const password = root.querySelector("#password").value;
      const res = await ctx.api.post("/auth/login", { email, password });
      ui.toast(`Selamat datang, ${res.user.name}`, "success");
      await ctx.onLogin(res.token, res.user);
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
      btnText.textContent = "Masuk";
    }
  };
}
