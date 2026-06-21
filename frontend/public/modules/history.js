// My attendance history
export async function render(root, ctx) {
  const { ui } = ctx;
  root.innerHTML = `<div class="flex justify-center py-32 text-slate-400"><i class="ph ph-circle-notch spin text-3xl"></i></div>`;
  let recs = [];
  try { recs = await ctx.api.get("/attendance/me"); } catch (e) {
    root.innerHTML = `<div class="p-8 text-center text-rose-600">${e.message}</div>`; return;
  }

  const present = recs.filter((r) => r.status === "present").length;
  const late = recs.filter((r) => r.status === "late").length;

  const rows = recs.length ? recs.map((r) => `
    <tr class="hover:bg-slate-50 transition-colors">
      <td class="px-5 py-4 text-sm text-slate-700">${ui.fmtDate(r.date)}</td>
      <td class="px-5 py-4 font-mono text-sm text-slate-700">${ui.fmtTime(r.check_in)}</td>
      <td class="px-5 py-4 font-mono text-sm text-slate-700">${ui.fmtTime(r.check_out)}</td>
      <td class="px-5 py-4 text-sm text-slate-500">${r.method === "face" ? "Wajah" : r.method === "qr" ? "QR" : "—"}</td>
      <td class="px-5 py-4 text-sm text-slate-500">${r.office_name || "—"}</td>
      <td class="px-5 py-4">${ui.statusPill(r.status)}</td>
    </tr>`).join("") : `<tr><td colspan="6" class="px-5 py-12 text-center text-slate-400 text-sm">Belum ada riwayat absensi.</td></tr>`;

  root.innerHTML = `
  <div class="space-y-6 stagger" data-testid="history-page">
    <div>
      <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Riwayat Kehadiran</p>
      <h2 class="font-heading font-bold text-2xl text-slate-900">Absensi Saya</h2>
    </div>
    <div class="grid grid-cols-3 gap-4">
      <div class="bg-white border border-slate-200 rounded-xl p-5"><p class="text-xs text-slate-500 uppercase tracking-widest">Total Hari</p><p class="font-heading font-bold text-3xl text-slate-900 mt-1">${recs.length}</p></div>
      <div class="bg-white border border-slate-200 rounded-xl p-5"><p class="text-xs text-slate-500 uppercase tracking-widest">Tepat Waktu</p><p class="font-heading font-bold text-3xl text-emerald-600 mt-1">${present}</p></div>
      <div class="bg-white border border-slate-200 rounded-xl p-5"><p class="text-xs text-slate-500 uppercase tracking-widest">Terlambat</p><p class="font-heading font-bold text-3xl text-amber-600 mt-1">${late}</p></div>
    </div>
    <div class="w-full overflow-x-auto border border-slate-200 rounded-xl bg-white">
      <table class="w-full">
        <thead class="bg-slate-50 border-b border-slate-200">
          <tr>
            ${["Tanggal", "Masuk", "Keluar", "Metode", "Lokasi", "Status"].map((t) => `<th class="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">${t}</th>`).join("")}
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">${rows}</tbody>
      </table>
    </div>
  </div>`;
}
