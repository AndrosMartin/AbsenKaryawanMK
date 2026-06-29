// User profile
import { getPushState, subscribePush, unsubscribePush, pushSupported } from "/js/push.js";

export async function render(root, ctx) {
  const { ui } = ctx;
  const u = ctx.user;
  const field = (label, value) => `
    <div class="py-3 border-b border-slate-100 last:border-0 flex justify-between gap-4">
      <span class="text-sm text-slate-500">${label}</span>
      <span class="text-sm font-medium text-slate-900 text-right">${value || "—"}</span>
    </div>`;

  root.innerHTML = `
  <div class="max-w-2xl mx-auto space-y-6 stagger" data-testid="profile-page">
    <div>
      <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Akun</p>
      <h2 class="font-heading font-bold text-2xl text-slate-900">Profil Saya</h2>
    </div>
    <div class="bg-white border border-slate-200 rounded-xl overflow-hidden">
      <div class="bg-ink p-6 flex items-center gap-4">
        <div class="h-16 w-16 rounded-2xl bg-white/10 text-white flex items-center justify-center text-xl font-heading font-bold">${ui.initials(u.name)}</div>
        <div>
          <h3 class="font-heading font-bold text-xl text-white">${u.name}</h3>
          <p class="text-slate-400 text-sm">${u.position || ""} · ${u.department || ""}</p>
        </div>
        <div class="ml-auto">${ui.roleBadge(u.role)}</div>
      </div>
      <div class="p-6">
        ${field("ID Karyawan", `<span class="font-mono">${u.employee_id || "—"}</span>`)}
        ${field("Email", u.email)}
        ${field("Departemen", u.department)}
        ${field("Posisi", u.position)}
        ${field("Telepon", u.phone)}
        ${field("Status Wajah", u.face_enrolled ? '<span class="text-emerald-600">Terdaftar</span>' : '<span class="text-amber-600">Belum terdaftar</span>')}
      </div>
    </div>
    <div class="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid="push-card">
      <div class="p-6 flex items-start gap-4">
        <div class="h-11 w-11 rounded-xl bg-gold/15 text-gold-600 flex items-center justify-center shrink-0"><i class="ph-fill ph-bell-ringing text-xl"></i></div>
        <div class="flex-1 min-w-0">
          <h3 class="font-heading font-semibold text-slate-900">Notifikasi Push</h3>
          <p class="text-sm text-slate-500 mt-0.5">Terima pemberitahuan langsung di perangkat ini untuk pengajuan, persetujuan, keterlambatan, dan pengingat absen.</p>
          <p id="push-state" class="text-xs mt-2 font-medium"></p>
        </div>
        <button id="push-toggle" data-testid="push-toggle-btn" class="shrink-0 px-4 py-2 rounded-lg text-sm font-medium border border-slate-200 hover:border-slate-900 text-slate-900 transition-colors">Memuat…</button>
      </div>
    </div>

    <div class="flex gap-3">
      <button id="go-face" data-testid="profile-face-btn" class="flex-1 bg-white border border-slate-200 hover:border-slate-900 text-slate-900 py-2.5 rounded-lg text-sm font-medium flex items-center justify-center gap-2"><i class="ph ph-user-focus"></i> ${u.face_enrolled ? "Perbarui Wajah" : "Daftarkan Wajah"}</button>
      <button id="logout2" data-testid="profile-logout-btn" class="flex-1 bg-rose-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-rose-700 flex items-center justify-center gap-2"><i class="ph ph-sign-out"></i> Keluar</button>
    </div>
  </div>`;

  root.querySelector("#go-face").onclick = () => ctx.navigate("face");
  root.querySelector("#logout2").onclick = () => ctx.logout();

  // --- Push notification toggle ---
  const toggle = root.querySelector("#push-toggle");
  const stateEl = root.querySelector("#push-state");

  async function paint() {
    const st = await getPushState();
    if (!st.supported) {
      toggle.disabled = true;
      toggle.textContent = "Tidak didukung";
      toggle.className = "shrink-0 px-4 py-2 rounded-lg text-sm font-medium border border-slate-200 text-slate-400 cursor-not-allowed";
      stateEl.textContent = "Browser ini tidak mendukung notifikasi push.";
      stateEl.className = "text-xs mt-2 font-medium text-slate-400";
      return;
    }
    if (st.permission === "denied") {
      toggle.disabled = true;
      toggle.textContent = "Diblokir";
      toggle.className = "shrink-0 px-4 py-2 rounded-lg text-sm font-medium border border-slate-200 text-slate-400 cursor-not-allowed";
      stateEl.textContent = "Notifikasi diblokir di pengaturan browser. Aktifkan kembali lalu muat ulang.";
      stateEl.className = "text-xs mt-2 font-medium text-amber-600";
      return;
    }
    toggle.disabled = false;
    if (st.subscribed) {
      toggle.textContent = "Nonaktifkan";
      toggle.className = "shrink-0 px-4 py-2 rounded-lg text-sm font-medium bg-rose-50 border border-rose-200 text-rose-700 hover:bg-rose-100 transition-colors";
      stateEl.textContent = "● Aktif di perangkat ini";
      stateEl.className = "text-xs mt-2 font-medium text-emerald-600";
    } else {
      toggle.textContent = "Aktifkan";
      toggle.className = "shrink-0 px-4 py-2 rounded-lg text-sm font-medium bg-ink text-gold hover:bg-ink/90 transition-colors";
      stateEl.textContent = "○ Nonaktif";
      stateEl.className = "text-xs mt-2 font-medium text-slate-400";
    }
  }

  toggle.onclick = async () => {
    const st = await getPushState();
    toggle.disabled = true;
    toggle.textContent = "Memproses…";
    try {
      if (st.subscribed) {
        await unsubscribePush();
        ui.toast("Notifikasi push dinonaktifkan", "info");
      } else {
        await subscribePush();
        ui.toast("Notifikasi push diaktifkan", "success");
      }
    } catch (e) {
      ui.toast(e.message || "Gagal mengubah notifikasi", "error");
    }
    await paint();
  };

  paint();
}
