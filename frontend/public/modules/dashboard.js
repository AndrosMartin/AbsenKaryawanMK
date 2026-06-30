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
  </div>`;
}
