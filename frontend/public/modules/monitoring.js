// Monitoring — daily status + period rekap with PDF/Excel export
import { getToken } from "/js/api.js";

const jkt = (d) => d.toLocaleDateString("en-CA", { timeZone: "Asia/Jakarta" });

function presetRange(mode) {
  const now = new Date();
  const today = jkt(now);
  const base = new Date(today + "T00:00:00");
  if (mode === "minggu") {
    const dow = (base.getDay() + 6) % 7; // Monday = 0
    const mon = new Date(base); mon.setDate(base.getDate() - dow);
    return { start: jkt(mon), end: today };
  }
  if (mode === "bulan") {
    return { start: today.slice(0, 8) + "01", end: today };
  }
  if (mode === "tahun") {
    return { start: today.slice(0, 4) + "-01-01", end: today };
  }
  return { start: today, end: today };
}

export async function render(root, ctx) {
  const { ui } = ctx;
  const today = jkt(new Date());
  let mode = "harian";
  let range = presetRange("harian");
  let rows = [];

  root.innerHTML = `
  <div class="space-y-6" data-testid="monitoring-page">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Monitoring Kehadiran</p>
        <h2 class="font-heading font-bold text-2xl text-slate-900">Status Karyawan</h2>
      </div>
      <div class="flex items-center gap-2">
        <button id="dl-pdf" data-testid="download-pdf-btn" class="px-3 py-2 rounded-lg text-sm font-medium bg-ink text-gold hover:bg-ink/90 transition-colors flex items-center gap-2"><i class="ph ph-file-pdf"></i> PDF</button>
        <button id="dl-xlsx" data-testid="download-excel-btn" class="px-3 py-2 rounded-lg text-sm font-medium bg-emerald-600 text-white hover:bg-emerald-700 transition-colors flex items-center gap-2"><i class="ph ph-file-xls"></i> Excel</button>
      </div>
    </div>

    <div class="bg-white border border-slate-200 rounded-xl p-4 flex flex-wrap items-end gap-3">
      <div>
        <label class="block text-xs text-slate-500 mb-1">Periode</label>
        <select id="mode" data-testid="monitoring-mode" class="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900">
          <option value="harian">Harian</option>
          <option value="rentang">Rentang Tanggal</option>
          <option value="minggu">Minggu Ini</option>
          <option value="bulan">Bulan Ini</option>
          <option value="tahun">Tahun Ini</option>
        </select>
      </div>
      <div id="single-date-wrap">
        <label class="block text-xs text-slate-500 mb-1">Tanggal</label>
        <input type="date" id="date-single" data-testid="monitoring-date" value="${today}" max="${today}"
          class="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-slate-900" />
      </div>
      <div id="range-wrap" class="hidden flex items-end gap-2">
        <div>
          <label class="block text-xs text-slate-500 mb-1">Dari</label>
          <input type="date" id="date-start" data-testid="monitoring-start" value="${range.start}" max="${today}"
            class="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-slate-900" />
        </div>
        <div>
          <label class="block text-xs text-slate-500 mb-1">Sampai</label>
          <input type="date" id="date-end" data-testid="monitoring-end" value="${range.end}" max="${today}"
            class="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-slate-900" />
        </div>
      </div>
      <div class="flex-1 min-w-[180px]">
        <label class="block text-xs text-slate-500 mb-1">Cari Karyawan</label>
        <input type="text" id="search" data-testid="monitoring-search" placeholder="Nama / departemen…"
          class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900" />
      </div>
      <div id="period-label" class="text-xs text-slate-400"></div>
    </div>

    <div id="summary" class="grid grid-cols-2 sm:grid-cols-4 gap-4"></div>
    <div id="table-wrap"></div>
  </div>`;

  const els = {
    mode: root.querySelector("#mode"),
    single: root.querySelector("#date-single"),
    start: root.querySelector("#date-start"),
    end: root.querySelector("#date-end"),
    singleWrap: root.querySelector("#single-date-wrap"),
    rangeWrap: root.querySelector("#range-wrap"),
    search: root.querySelector("#search"),
    summary: root.querySelector("#summary"),
    table: root.querySelector("#table-wrap"),
    label: root.querySelector("#period-label"),
  };

  function currentRange() {
    if (mode === "harian") return { start: els.single.value, end: els.single.value };
    if (mode === "rentang") return { start: els.start.value, end: els.end.value };
    return presetRange(mode);
  }

  function syncControls() {
    const isHarian = mode === "harian";
    const isRange = mode === "rentang";
    els.singleWrap.classList.toggle("hidden", !isHarian);
    els.rangeWrap.classList.toggle("hidden", isHarian);
    if (!isHarian && !isRange) {
      const r = presetRange(mode);
      els.start.value = r.start; els.end.value = r.end;
      els.start.disabled = true; els.end.disabled = true;
    } else {
      els.start.disabled = false; els.end.disabled = false;
    }
  }

  function buildQuery() {
    const r = currentRange();
    const q = els.search.value.trim();
    const p = new URLSearchParams({ start: r.start, end: r.end });
    if (q) p.set("q", q);
    return p.toString();
  }

  async function load() {
    range = currentRange();
    els.label.textContent = mode === "harian"
      ? `Tanggal ${range.start}`
      : `${range.start} s/d ${range.end}`;
    els.table.innerHTML = `<div class="flex justify-center py-20 text-slate-400"><i class="ph ph-circle-notch spin text-2xl"></i></div>`;
    try {
      if (mode === "harian") {
        rows = await ctx.api.get("/attendance?date=" + range.start);
        renderDailySummary();
        renderDailyTable();
      } else {
        const data = await ctx.api.get("/attendance/summary?" + buildQuery());
        renderRekapSummary(data);
        renderRekapTable(data);
      }
    } catch (e) {
      els.table.innerHTML = `<div class="p-8 text-center text-rose-600">${e.message}</div>`;
    }
  }

  function card(l, v, cls) {
    return `<div class="bg-white border border-slate-200 rounded-xl p-4">
      <p class="text-xs text-slate-500 uppercase tracking-widest">${l}</p>
      <p class="font-heading font-bold text-3xl ${cls} mt-1">${v}</p></div>`;
  }

  // ---- Daily (harian) ----
  function renderDailySummary() {
    const c = { present: 0, tolerance: 0, late: 0, absent: 0 };
    rows.forEach((r) => c[r.status] !== undefined && c[r.status]++);
    els.summary.className = "grid grid-cols-2 sm:grid-cols-5 gap-4";
    els.summary.innerHTML = [
      card("Total", rows.length, "text-slate-900"),
      card("Tepat Waktu", c.present, "text-emerald-600"),
      card("Toleransi", c.tolerance, "text-yellow-600"),
      card("Terlambat", c.late, "text-rose-600"),
      card("Tidak Hadir", c.absent, "text-slate-500"),
    ].join("");
  }

  function renderDailyTable() {
    const q = els.search.value.toLowerCase();
    const filtered = rows.filter((r) => !q || (r.name || "").toLowerCase().includes(q) || (r.department || "").toLowerCase().includes(q));
    const body = filtered.length ? filtered.map((r) => `
      <tr class="hover:bg-slate-50 transition-colors" data-testid="monitoring-row">
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
    els.table.innerHTML = tableShell(["Karyawan", "Departemen", "Role", "Masuk", "Keluar", "Metode", "Status"], body, 99);
  }

  // ---- Rekap (range) ----
  function renderRekapSummary(data) {
    const t = data.totals;
    els.summary.className = "grid grid-cols-2 sm:grid-cols-5 gap-4";
    els.summary.innerHTML = [
      card("Hari Kerja", data.workdays, "text-slate-900"),
      card("Tepat Waktu", t.present, "text-emerald-600"),
      card("Toleransi", t.tolerance ?? 0, "text-yellow-600"),
      card("Terlambat", t.late, "text-rose-600"),
      card("Tidak Hadir", t.absent, "text-slate-500"),
    ].join("");
  }

  function renderRekapTable(data) {
    const body = data.rows.length ? data.rows.map((r) => `
      <tr class="hover:bg-slate-50 transition-colors" data-testid="rekap-row">
        <td class="px-5 py-4">
          <div class="flex items-center gap-3">
            <div class="h-9 w-9 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-semibold">${ui.initials(r.name)}</div>
            <div><p class="text-sm font-medium text-slate-900">${r.name}</p><p class="text-xs text-slate-400 font-mono">${r.employee_id || ""}</p></div>
          </div>
        </td>
        <td class="px-5 py-4 text-sm text-slate-600">${r.department || "—"}</td>
        <td class="px-5 py-4 text-center text-sm font-medium text-emerald-600">${r.present}</td>
        <td class="px-5 py-4 text-center text-sm font-medium text-yellow-600">${r.tolerance ?? 0}</td>
        <td class="px-5 py-4 text-center text-sm font-medium text-rose-600">${r.late}</td>
        <td class="px-5 py-4 text-center text-sm font-medium text-slate-500">${r.absent}</td>
        <td class="px-5 py-4 text-center text-sm font-semibold text-slate-900">${r.attended}/${r.workdays}</td>
        <td class="px-5 py-4 text-center">
          <span class="inline-flex items-center gap-1 text-sm font-semibold ${r.rate >= 80 ? "text-emerald-600" : r.rate >= 50 ? "text-amber-600" : "text-rose-600"}">${r.rate}%</span>
        </td>
      </tr>`).join("") : `<tr><td colspan="8" class="px-5 py-12 text-center text-slate-400 text-sm">Tidak ada data.</td></tr>`;
    els.table.innerHTML = tableShell(["Karyawan", "Departemen", "Tepat Waktu", "Toleransi", "Terlambat", "Tidak Hadir", "Total Hadir", "Kehadiran"], body, 2);
  }

  function tableShell(heads, body, centerFrom = 99) {
    return `<div class="w-full overflow-x-auto border border-slate-200 rounded-xl bg-white">
      <table class="w-full">
        <thead class="bg-slate-50 border-b border-slate-200">
          <tr>${heads.map((t, i) => `<th class="px-5 py-3 ${i >= centerFrom ? "text-center" : "text-left"} text-xs font-medium text-slate-500 uppercase tracking-wider">${t}</th>`).join("")}</tr>
        </thead>
        <tbody class="divide-y divide-slate-100">${body}</tbody>
      </table></div>`;
  }

  // ---- Download ----
  async function download(fmt) {
    if (mode === "rentang" && (!els.start.value || !els.end.value)) {
      ui.toast("Pilih rentang tanggal dulu", "error"); return;
    }
    const btn = fmt === "pdf" ? root.querySelector("#dl-pdf") : root.querySelector("#dl-xlsx");
    const orig = btn.innerHTML;
    btn.innerHTML = `<i class="ph ph-circle-notch spin"></i> Menyiapkan…`;
    btn.disabled = true;
    try {
      const res = await fetch(window.location.origin + "/api/attendance/summary/export?format=" + fmt + "&" + buildQuery(),
        { headers: { Authorization: "Bearer " + getToken() } });
      if (!res.ok) throw new Error("Gagal mengunduh (" + res.status + ")");
      const blob = await res.blob();
      const r = currentRange();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rekap-absensi-${r.start}_sd_${r.end}.${fmt === "pdf" ? "pdf" : "xlsx"}`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
      ui.toast("Unduhan dimulai", "success");
    } catch (e) {
      ui.toast(e.message || "Gagal mengunduh", "error");
    } finally {
      btn.innerHTML = orig; btn.disabled = false;
    }
  }

  // ---- Events ----
  els.mode.onchange = () => { mode = els.mode.value; syncControls(); load(); };
  els.single.onchange = load;
  els.start.onchange = load;
  els.end.onchange = load;
  els.search.oninput = () => { mode === "harian" ? renderDailyTable() : load(); };
  root.querySelector("#dl-pdf").onclick = () => download("pdf");
  root.querySelector("#dl-xlsx").onclick = () => download("xlsx");

  syncControls();
  load();
}
