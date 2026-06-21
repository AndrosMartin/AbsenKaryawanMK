// Monitoring — all employees' attendance for a selected date
export async function render(root, ctx) {
  const { ui } = ctx;
  const todayStr = new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Jakarta" });
  let date = todayStr;

  root.innerHTML = `
  <div class="space-y-6" data-testid="monitoring-page">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Monitoring Kehadiran</p>
        <h2 class="font-heading font-bold text-2xl text-slate-900">Status Karyawan</h2>
      </div>
      <div class="flex items-center gap-2">
        <input type="date" id="date-filter" data-testid="monitoring-date" value="${date}" max="${todayStr}"
          class="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-slate-900" />
        <input type="text" id="search" data-testid="monitoring-search" placeholder="Cari nama / departemen…"
          class="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 w-56" />
      </div>
    </div>
    <div id="summary" class="grid grid-cols-2 sm:grid-cols-4 gap-4"></div>
    <div id="table-wrap"></div>
  </div>`;

  const tableWrap = root.querySelector("#table-wrap");
  const summary = root.querySelector("#summary");
  const searchEl = root.querySelector("#search");
  let rows = [];

  async function load() {
    tableWrap.innerHTML = `<div class="flex justify-center py-20 text-slate-400"><i class="ph ph-circle-notch spin text-2xl"></i></div>`;
    try { rows = await ctx.api.get("/attendance?date=" + date); } catch (e) {
      tableWrap.innerHTML = `<div class="p-8 text-center text-rose-600">${e.message}</div>`; return;
    }
    renderSummary();
    renderTable();
  }

  function renderSummary() {
    const c = { present: 0, late: 0, absent: 0 };
    rows.forEach((r) => c[r.status] !== undefined && c[r.status]++);
    const cards = [
      ["Total", rows.length, "text-slate-900"],
      ["Tepat Waktu", c.present, "text-emerald-600"],
      ["Terlambat", c.late, "text-amber-600"],
      ["Tidak Hadir", c.absent, "text-rose-600"],
    ];
    summary.innerHTML = cards.map(([l, v, cls]) => `
      <div class="bg-white border border-slate-200 rounded-xl p-4">
        <p class="text-xs text-slate-500 uppercase tracking-widest">${l}</p>
        <p class="font-heading font-bold text-3xl ${cls} mt-1">${v}</p>
      </div>`).join("");
  }

  function renderTable() {
    const q = searchEl.value.toLowerCase();
    const filtered = rows.filter((r) => !q || (r.name || "").toLowerCase().includes(q) || (r.department || "").toLowerCase().includes(q));
    const body = filtered.length ? filtered.map((r) => `
      <tr class="hover:bg-slate-50 transition-colors">
        <td class="px-5 py-4">
          <div class="flex items-center gap-3">
            <div class="h-9 w-9 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-semibold">${ui.initials(r.name)}</div>
            <div><p class="text-sm font-medium text-slate-900">${r.name}</p><p class="text-xs text-slate-400 font-mono">${r.employee_id || ""}</p></div>
          </div>
        </td>
        <td class="px-5 py-4 text-sm text-slate-600">${r.department || "—"}</td>
        <td class="px-5 py-4">${ui.roleBadge(r.role)}</td>
        <td class="px-5 py-4 font-mono text-sm text-slate-700">${ui.fmtTime(r.check_in)}</td>
        <td class="px-5 py-4 font-mono text-sm text-slate-700">${ui.fmtTime(r.check_out)}</td>
        <td class="px-5 py-4 text-sm text-slate-500">${r.method === "face" ? "Wajah" : r.method === "qr" ? "QR" : "—"}</td>
        <td class="px-5 py-4">${ui.statusPill(r.status)}</td>
      </tr>`).join("") : `<tr><td colspan="7" class="px-5 py-12 text-center text-slate-400 text-sm">Tidak ada data.</td></tr>`;

    tableWrap.innerHTML = `
      <div class="w-full overflow-x-auto border border-slate-200 rounded-xl bg-white">
        <table class="w-full">
          <thead class="bg-slate-50 border-b border-slate-200">
            <tr>${["Karyawan", "Departemen", "Role", "Masuk", "Keluar", "Metode", "Status"].map((t) => `<th class="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">${t}</th>`).join("")}</tr>
          </thead>
          <tbody class="divide-y divide-slate-100">${body}</tbody>
        </table>
      </div>`;
  }

  root.querySelector("#date-filter").onchange = (e) => { date = e.target.value; load(); };
  searchEl.oninput = renderTable;
  load();
}
