// Login / Authentication module
export async function render(root, ctx) {
  const { ui } = ctx;
  const bg = "https://images.unsplash.com/photo-1715593949273-09009558300a?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400";

  root.innerHTML = `
  <div class="min-h-screen grid lg:grid-cols-2 fade-in">
    <!-- Left: brand / image -->
    <div class="relative hidden lg:flex flex-col justify-between p-12 bg-slate-900 overflow-hidden">
      <img src="${bg}" alt="Kantor" class="absolute inset-0 w-full h-full object-cover opacity-30" />
      <div class="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/70 to-slate-900/30"></div>
      <div class="relative flex items-center gap-3">
        <div class="h-10 w-10 rounded-lg bg-white flex items-center justify-center">
          <i class="ph-fill ph-fingerprint text-slate-900 text-2xl"></i>
        </div>
        <span class="text-white font-heading font-bold text-xl">AbsensiPro</span>
      </div>
      <div class="relative max-w-md">
        <h2 class="font-heading font-bold text-4xl text-white leading-tight">Kehadiran terverifikasi, monitoring tanpa batas.</h2>
        <p class="text-slate-300 mt-4 text-base">Absensi dengan verifikasi wajah, QR code, dan validasi lokasi GPS. Pantau kehadiran seluruh tim secara real-time.</p>
        <div class="flex gap-6 mt-8">
          <div><p class="font-heading font-bold text-2xl text-white">Face</p><p class="text-xs text-slate-400 uppercase tracking-widest">Recognition</p></div>
          <div><p class="font-heading font-bold text-2xl text-white">GPS</p><p class="text-xs text-slate-400 uppercase tracking-widest">Geofence</p></div>
          <div><p class="font-heading font-bold text-2xl text-white">QR</p><p class="text-xs text-slate-400 uppercase tracking-widest">Scan</p></div>
        </div>
      </div>
      <div class="relative text-xs text-slate-500">© 2026 AbsensiPro · Workforce Monitoring System</div>
    </div>

    <!-- Right: form -->
    <div class="flex items-center justify-center p-6 sm:p-12 bg-slate-50">
      <div class="w-full max-w-sm">
        <div class="lg:hidden flex items-center gap-3 mb-8">
          <div class="h-10 w-10 rounded-lg bg-slate-900 flex items-center justify-center"><i class="ph-fill ph-fingerprint text-white text-2xl"></i></div>
          <span class="font-heading font-bold text-xl text-slate-900">AbsensiPro</span>
        </div>
        <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Selamat datang</p>
        <h1 class="font-heading font-bold text-3xl text-slate-900 mt-1">Masuk ke akun Anda</h1>
        <p class="text-sm text-slate-500 mt-2">Gunakan kredensial perusahaan untuk melanjutkan.</p>

        <form id="login-form" class="mt-8 space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Email</label>
            <input data-testid="login-email" id="email" type="email" required placeholder="nama@company.com"
              class="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
            <input data-testid="login-password" id="password" type="password" required placeholder="••••••••"
              class="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent" />
          </div>
          <p id="login-error" class="text-sm text-rose-600 hidden"></p>
          <button data-testid="login-submit" type="submit"
            class="w-full bg-slate-900 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors flex items-center justify-center gap-2">
            <span id="login-btn-text">Masuk</span>
          </button>
        </form>

        <div class="mt-8">
          <p class="text-xs font-medium text-slate-400 uppercase tracking-widest mb-3">Akun demo</p>
          <div class="grid grid-cols-2 gap-2">
            ${[
              ["owner@company.com", "Owner"],
              ["direksi@company.com", "Direksi"],
              ["manager@company.com", "Manager"],
              ["dewi@company.com", "Staff"],
            ].map(([em, lbl]) => `
              <button data-demo="${em}" data-testid="demo-${lbl.toLowerCase()}"
                class="text-left px-3 py-2 rounded-lg border border-slate-200 bg-white hover:border-slate-900 transition-colors">
                <p class="text-xs font-semibold text-slate-900">${lbl}</p>
                <p class="text-[10px] text-slate-400 truncate font-mono">${em}</p>
              </button>`).join("")}
          </div>
          <p class="text-[11px] text-slate-400 mt-3">Password semua akun demo: <span class="font-mono text-slate-600">password123</span></p>
        </div>
      </div>
    </div>
  </div>`;

  const form = root.querySelector("#login-form");
  const errEl = root.querySelector("#login-error");
  const btnText = root.querySelector("#login-btn-text");

  root.querySelectorAll("[data-demo]").forEach((b) => {
    b.onclick = () => {
      root.querySelector("#email").value = b.getAttribute("data-demo");
      root.querySelector("#password").value = "password123";
    };
  });

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
