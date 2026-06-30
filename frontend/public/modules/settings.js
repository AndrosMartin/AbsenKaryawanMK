// Pengaturan jadwal kerja (global). Owner/Direksi terapkan langsung; HRD ajukan -> approval Direksi.
export async function render(root, ctx) {
  const { ui } = ctx;
  const isApprover = ui.APPROVER_ROLES.includes(ctx.user.role);
  let s;

  root.innerHTML = `<div class="flex items-center justify-center py-32 text-slate-400"><i class="ph ph-circle-notch spin text-3xl"></i></div>`;
  try {
    s = await ctx.api.get("/settings");
  } catch (e) {
    root.innerHTML = `<div class="p-8 text-center text-rose-600">${e.message}</div>`;
    return;
  }

  root.innerHTML = `
  <div class="max-w-2xl mx-auto space-y-6 stagger" data-testid="settings-page">
    <div>
      <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Pengaturan</p>
      <h2 class="font-heading font-bold text-2xl text-slate-900">Jadwal Kerja</h2>
      <p class="text-sm text-slate-500 mt-1">Berlaku global untuk seluruh perusahaan.
        ${isApprover ? "Perubahan langsung diterapkan." : "Perubahan Anda akan menunggu persetujuan Direksi."}</p>
    </div>

    <div class="bg-white border border-slate-200 rounded-xl p-6 space-y-5">
      <div class="grid sm:grid-cols-3 gap-4">
        <div>
          <label class="block text-xs text-slate-500 mb-1">Jam Masuk</label>
          <input type="time" id="work-start" data-testid="work-start" value="${s.work_start}"
            class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-slate-900" />
        </div>
        <div>
          <label class="block text-xs text-slate-500 mb-1">Jam Pulang</label>
          <input type="time" id="work-end" data-testid="work-end" value="${s.work_end}"
            class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-slate-900" />
        </div>
        <div>
          <label class="block text-xs text-slate-500 mb-1">Toleransi (menit)</label>
          <input type="number" id="tolerance" data-testid="tolerance" value="${s.tolerance_minutes}" min="0" max="120"
            class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-slate-900" />
        </div>
      </div>

      <div class="rounded-lg bg-slate-50 border border-slate-200 p-4 text-sm">
        <p class="font-medium text-slate-700 mb-2">Aturan status kehadiran</p>
        <div class="space-y-1.5 text-slate-600" id="rule-preview"></div>
      </div>

      <div class="flex justify-end">
        <button id="save-btn" data-testid="settings-save-btn" class="px-5 py-2.5 rounded-lg text-sm font-medium bg-ink text-gold hover:bg-ink/90 transition-colors">
          ${isApprover ? "Simpan Perubahan" : "Ajukan Perubahan"}
        </button>
      </div>
    </div>
  </div>`;

  const startEl = root.querySelector("#work-start");
  const endEl = root.querySelector("#work-end");
  const tolEl = root.querySelector("#tolerance");
  const preview = root.querySelector("#rule-preview");

  function addMinutes(hhmm, mins) {
    const [h, m] = hhmm.split(":").map(Number);
    const d = new Date(2000, 0, 1, h, m + Number(mins || 0));
    return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  }

  function renderRules() {
    const ws = startEl.value || "09:00";
    const tol = tolEl.value || "0";
    const grace = addMinutes(ws, tol);
    preview.innerHTML = `
      <p><span class="inline-block w-3 h-3 rounded-full bg-emerald-500 align-middle mr-2"></span><b>Tepat Waktu</b> — check-in sampai ${ws}</p>
      <p><span class="inline-block w-3 h-3 rounded-full bg-yellow-400 align-middle mr-2"></span><b>Toleransi</b> — ${ws} hingga ${grace} (${tol} menit)</p>
      <p><span class="inline-block w-3 h-3 rounded-full bg-rose-500 align-middle mr-2"></span><b>Terlambat</b> — setelah ${grace}</p>`;
  }
  renderRules();
  startEl.oninput = renderRules;
  tolEl.oninput = renderRules;

  root.querySelector("#save-btn").onclick = async () => {
    const btn = root.querySelector("#save-btn");
    const tol = parseInt(tolEl.value, 10);
    if (!startEl.value || !endEl.value) { ui.toast("Jam masuk & pulang wajib diisi", "error"); return; }
    if (isNaN(tol) || tol < 0 || tol > 120) { ui.toast("Toleransi harus 0–120 menit", "error"); return; }
    const orig = btn.textContent;
    btn.textContent = "Menyimpan…"; btn.disabled = true;
    try {
      const res = await ctx.api.put("/settings", {
        work_start: startEl.value, work_end: endEl.value, tolerance_minutes: tol,
      });
      if (res && res.applied) {
        ui.toast("Jadwal kerja berhasil disimpan", "success");
      } else {
        ui.toast("Pengajuan terkirim, menunggu persetujuan Direksi", "info");
        if (window.__refreshNotifs) window.__refreshNotifs();
      }
    } catch (e) {
      ui.toast(e.message || "Gagal menyimpan", "error");
    } finally {
      btn.textContent = orig; btn.disabled = false;
    }
  };
}
