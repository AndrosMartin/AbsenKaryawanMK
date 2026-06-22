// User profile
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
    <div class="flex gap-3">
      <button id="go-face" data-testid="profile-face-btn" class="flex-1 bg-white border border-slate-200 hover:border-slate-900 text-slate-900 py-2.5 rounded-lg text-sm font-medium flex items-center justify-center gap-2"><i class="ph ph-user-focus"></i> ${u.face_enrolled ? "Perbarui Wajah" : "Daftarkan Wajah"}</button>
      <button id="logout2" data-testid="profile-logout-btn" class="flex-1 bg-rose-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-rose-700 flex items-center justify-center gap-2"><i class="ph ph-sign-out"></i> Keluar</button>
    </div>
  </div>`;

  root.querySelector("#go-face").onclick = () => ctx.navigate("face");
  root.querySelector("#logout2").onclick = () => ctx.logout();
}
