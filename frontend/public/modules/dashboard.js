// Monitoring dashboard — KPIs, trend chart, department breakdown, recent activity
export async function render(root, ctx) {
  const { ui } = ctx;
  root.innerHTML = `<div class="flex items-center justify-center py-32 text-slate-400"><i class="ph ph-circle-notch spin text-3xl"></i></div>`;
  let s;
  try {
    s = await ctx.api.get("/dashboard/stats");
  } catch (e) {
    root.innerHTML = `<div class="p-8 text-center text-rose-600">${e.message}</div>`;
    return;
  }

  const stat = (label, value, sub, icon, accent) => `
    <div class="bg-white border border-slate-200 rounded-xl p-5 relative overflow-hidden">
      <div class="flex items-start justify-between">
        <div>
          <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">${label}</p>
          <p class="font-heading font-bold text-4xl text-slate-900 mt-2 tracking-tight">${value}</p>
          <p class="text-xs text-slate-400 mt-1">${sub}</p>
        </div>
        <div class="h-10 w-10 rounded-lg ${accent} flex items-center justify-center"><i class="ph-fill ${icon} text-lg"></i></div>
      </div>
    </div>`;

  // trend chart geometry
  const maxT = Math.max(1, ...s.trend.map((t) => t.total));
  const bars = s.trend.map((t, i) => {
    const ph = (t.present / maxT) * 100;
    const lh = (t.late / maxT) * 100;
    return `<div class="flex-1 flex flex-col items-center gap-2">
      <div class="w-full flex flex-col justify-end items-center gap-0.5 h-40">
        <div class="w-7 rounded-t bg-amber-400" style="height:${lh}%" title="Terlambat: ${t.late}"></div>
        <div class="w-7 rounded-t bg-ink" style="height:${ph}%" title="Hadir: ${t.present}"></div>
      </div>
      <span class="text-[11px] text-slate-400 font-medium">${t.label}</span>
    </div>`;
  }).join("");

  const deptBars = s.departments.map((d) => {
    const pct = d.total ? Math.round((d.hadir / d.total) * 100) : 0;
    return `<div>
      <div class="flex justify-between text-sm mb-1">
        <span class="font-medium text-slate-700">${d.department}</span>
        <span class="text-slate-500 font-mono">${d.hadir}/${d.total} · ${pct}%</span>
      </div>
      <div class="h-2.5 bg-slate-100 rounded-full overflow-hidden">
        <div class="h-full bg-ink rounded-full transition-all" style="width:${pct}%"></div>
      </div>
    </div>`;
  }).join("");

  const recent = s.recent.length ? s.recent.map((r) => `
    <div class="flex items-center gap-3 py-3 border-b border-slate-100 last:border-0">
      <div class="h-9 w-9 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-semibold">${ui.initials(r.name)}</div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-slate-900 truncate">${r.name}</p>
        <p class="text-xs text-slate-400">${r.department} · ${r.method === "face" ? "Wajah" : "QR"} · ${r.office_name || "-"}</p>
      </div>
      <div class="text-right">
        <p class="text-sm font-mono font-medium text-slate-700">${ui.fmtTime(r.check_in)}</p>
        ${ui.statusPill(r.status)}
      </div>
    </div>`).join("") : `<p class="text-sm text-slate-400 py-8 text-center">Belum ada aktivitas check-in hari ini.</p>`;

  root.innerHTML = `
  <div class="space-y-6 stagger" data-testid="dashboard-page">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Ringkasan Hari Ini</p>
        <h2 class="font-heading font-bold text-2xl text-slate-900">${ui.fmtDate(s.date)}</h2>
      </div>
      <div class="flex items-center gap-2 text-sm">
        <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200">
          <i class="ph-fill ph-chart-pie-slice text-slate-900"></i>
          <span class="text-slate-500">Tingkat Kehadiran</span>
          <span class="font-mono font-semibold text-slate-900">${s.attendance_rate}%</span>
        </span>
      </div>
    </div>

    <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
      ${stat("Total Karyawan", s.total, "Seluruh tim terdaftar", "ph-users-three", "bg-slate-100 text-slate-700")}
      ${stat("Tepat Waktu", s.present, "Hadir sesuai jadwal", "ph-check-circle", "bg-emerald-100 text-emerald-700")}
      ${stat("Toleransi", s.tolerance ?? 0, "Dalam masa toleransi", "ph-clock-clockwise", "bg-yellow-100 text-yellow-700")}
      ${stat("Terlambat", s.late, "Melewati toleransi", "ph-clock-countdown", "bg-rose-100 text-rose-700")}
      ${stat("Tidak Hadir", s.absent, "Belum check-in hari ini", "ph-x-circle", "bg-slate-100 text-slate-500")}
    </div>

    <div class="grid lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-6">
        <div class="flex items-center justify-between mb-5">
          <div>
            <h3 class="font-heading font-semibold text-lg text-slate-900">Tren Kehadiran 7 Hari</h3>
            <p class="text-xs text-slate-400">Jumlah check-in per hari</p>
          </div>
          <div class="flex items-center gap-4 text-xs">
            <span class="flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-sm bg-ink"></span>Tepat waktu</span>
            <span class="flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-sm bg-amber-400"></span>Terlambat</span>
          </div>
        </div>
        <div class="flex items-end gap-3">${bars}</div>
      </div>

      <div class="bg-white border border-slate-200 rounded-xl p-6">
        <h3 class="font-heading font-semibold text-lg text-slate-900 mb-1">Per Departemen</h3>
        <p class="text-xs text-slate-400 mb-5">Kehadiran hari ini</p>
        <div class="space-y-4">${deptBars || '<p class="text-sm text-slate-400">Tidak ada data.</p>'}</div>
      </div>
    </div>

    <div class="bg-white border border-slate-200 rounded-xl p-6">
      <h3 class="font-heading font-semibold text-lg text-slate-900 mb-1">Aktivitas Terbaru</h3>
      <p class="text-xs text-slate-400 mb-2">Check-in terakhir dari karyawan</p>
      <div>${recent}</div>
    </div>

    ${ui.MONITOR_ROLES.includes(ctx.user.role) ? `<div id="late-approval-section"></div>` : ""}
    ${(["owner", "direksi", "hrd"].includes(ctx.user.role) || (ctx.user.role === "manager" && ctx.user.kpi_access)) ? `<div id="kpi-section"></div>` : ""}
  </div>`;

  const role = ctx.user.role;
  const canLateApprove = ui.MONITOR_ROLES.includes(role);
  const canKpi = ["owner", "direksi", "hrd"].includes(role) || (role === "manager" && ctx.user.kpi_access);

  async function loadLateApprovals() {
    const el = root.querySelector("#late-approval-section");
    if (!el) return;
    let data;
    try { data = await ctx.api.get("/late/pending"); } catch (e) { return; }
    if (!data.items.length) { el.innerHTML = ""; return; }
    el.innerHTML = `<div class="bg-white border border-slate-200 rounded-xl p-6" data-testid="late-approval-section">
      <h3 class="font-heading font-semibold text-lg text-slate-900 mb-1">Persetujuan Keterlambatan <span class="ml-1 text-xs bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full">${data.items.length}</span></h3>
      <p class="text-xs text-slate-400 mb-4">Setujui (check-in ≤ 10:00 → dihitung Hadir) atau tolak (→ Kartu Kuning).</p>
      <div class="space-y-3">${data.items.map((it) => `
        <div class="flex items-center justify-between gap-3 border border-slate-100 rounded-lg p-3" data-testid="late-pending-row">
          <div class="min-w-0">
            <p class="text-sm font-semibold text-slate-900">${it.name} <span class="text-xs text-slate-400 font-mono">${it.date} · ${it.check_in_time}</span></p>
            <p class="text-xs text-slate-500">${it.reason ? "Alasan: " + it.reason : "<i>Belum ada alasan</i>"}</p>
          </div>
          <div class="flex gap-2 shrink-0">
            <button data-la-ap="${it.id}" data-testid="late-approve-${it.id}" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700">Setujui</button>
            <button data-la-rj="${it.id}" data-testid="late-reject-${it.id}" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 text-white hover:bg-rose-700">Tolak</button>
          </div>
        </div>`).join("")}</div></div>`;
    el.querySelectorAll("[data-la-ap]").forEach((b) => b.onclick = () => lateDecide(b.getAttribute("data-la-ap"), "approve"));
    el.querySelectorAll("[data-la-rj]").forEach((b) => b.onclick = () => lateDecide(b.getAttribute("data-la-rj"), "reject"));
  }

  async function lateDecide(id, action) {
    let note = "";
    if (action === "reject") note = prompt("Catatan penolakan (opsional):") || "";
    try {
      const res = await ctx.api.post(`/late/${id}/${action}`, { note });
      ui.toast(action === "approve" ? (res.compensated ? "Disetujui — dihitung Hadir" : "Disetujui") : "Ditolak — Kartu Kuning", action === "approve" ? "success" : "info");
      loadLateApprovals();
      if (canKpi) loadKpi();
      if (window.__refreshNotifs) window.__refreshNotifs();
    } catch (e) { ui.toast(e.message, "error"); }
  }

  async function loadKpi() {
    const el = root.querySelector("#kpi-section");
    if (!el) return;
    let data;
    try { data = await ctx.api.get("/kpi/discipline"); } catch (e) { return; }
    const rows = data.rows.filter((r) => r.yellow_cards > 0 || r.leave_deducted > 0 || r.late_count > 0);
    el.innerHTML = `<div class="bg-white border border-slate-200 rounded-xl p-6" data-testid="kpi-section">
      <div class="flex items-center justify-between mb-1">
        <h3 class="font-heading font-semibold text-lg text-slate-900">Papan Kedisiplinan — Kartu Kuning</h3>
        <span class="text-xs text-slate-400 font-mono">${data.month}</span>
      </div>
      <p class="text-xs text-slate-400 mb-4">Ranking pelanggaran keterlambatan bulan berjalan (untuk evaluasi KPI).</p>
      ${rows.length ? `<div class="w-full overflow-x-auto"><table class="w-full"><thead class="bg-slate-50"><tr>
        ${["#", "Karyawan", "Departemen", "Kartu Kuning", "Telat", "Potong Cuti"].map((t, i) => `<th class="px-4 py-2 ${i >= 3 ? "text-center" : "text-left"} text-xs font-medium text-slate-500 uppercase tracking-wider">${t}</th>`).join("")}
      </tr></thead><tbody class="divide-y divide-slate-100">${rows.map((r, i) => `
        <tr data-testid="kpi-row"><td class="px-4 py-3 text-sm text-slate-400">${i + 1}</td>
          <td class="px-4 py-3"><div class="flex items-center gap-2"><div class="h-8 w-8 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-semibold">${ui.initials(r.name)}</div><span class="text-sm font-medium text-slate-900">${r.name}</span></div></td>
          <td class="px-4 py-3 text-sm text-slate-600">${r.department || "—"}</td>
          <td class="px-4 py-3 text-center"><span class="inline-flex items-center justify-center min-w-[1.75rem] px-2 py-0.5 rounded-full text-xs font-bold ${r.yellow_cards > 0 ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-400"}">${r.yellow_cards}</span></td>
          <td class="px-4 py-3 text-center text-sm text-slate-600">${r.late_count}</td>
          <td class="px-4 py-3 text-center text-sm font-medium ${r.leave_deducted > 0 ? "text-rose-600" : "text-slate-400"}">${r.leave_deducted} hari</td>
        </tr>`).join("")}</tbody></table></div>`
        : `<p class="text-sm text-slate-400 py-6 text-center">Belum ada pelanggaran bulan ini. 🎉</p>`}</div>`;
  }

  if (canLateApprove) loadLateApprovals();
  if (canKpi) loadKpi();
}
