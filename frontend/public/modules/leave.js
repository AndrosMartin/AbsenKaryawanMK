// Pengajuan Cuti — submit + multi-layer approval (HRD -> Direksi/Manager -> Reviewer)
const TYPES = [["tahunan", "Cuti Tahunan"], ["sakit", "Sakit"], ["izin", "Izin"]];

export async function render(root, ctx) {
  const { ui } = ctx;
  const role = ctx.user.role;
  const canApprove = ui.MONITOR_ROLES.includes(role) || ctx.user.is_reviewer;
  let tab = "mine";
  let balance = null;
  let items = [];

  root.innerHTML = `
  <div class="space-y-6" data-testid="leave-page">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Manajemen Cuti</p>
        <h2 class="font-heading font-bold text-2xl text-slate-900">Pengajuan Cuti</h2>
      </div>
    </div>

    <div id="balance" class="grid grid-cols-2 sm:grid-cols-4 gap-4"></div>

    <div class="grid lg:grid-cols-3 gap-6">
      <div class="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-6 h-fit" data-testid="leave-form-card">
        <h3 class="font-heading font-semibold text-slate-900 mb-4">Ajukan Cuti</h3>
        <form id="leave-form" class="space-y-3">
          <div>
            <label class="block text-xs text-slate-500 mb-1">Jenis</label>
            <select id="lv-type" data-testid="lv-type" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900">
              ${TYPES.map(([v, l]) => `<option value="${v}">${l}</option>`).join("")}
            </select>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="block text-xs text-slate-500 mb-1">Mulai</label>
              <input type="date" id="lv-start" data-testid="lv-start" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-slate-900" /></div>
            <div><label class="block text-xs text-slate-500 mb-1">Selesai</label>
              <input type="date" id="lv-end" data-testid="lv-end" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-slate-900" /></div>
          </div>
          <p id="lv-days" class="text-xs text-slate-400"></p>
          <div><label class="block text-xs text-slate-500 mb-1">Alasan</label>
            <textarea id="lv-reason" data-testid="lv-reason" rows="2" class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900" placeholder="Keperluan cuti…"></textarea></div>
          <button type="submit" data-testid="lv-submit-btn" class="w-full px-4 py-2.5 rounded-lg text-sm font-semibold bg-ink text-gold hover:bg-ink/90 transition-colors">Ajukan</button>
        </form>
        <p class="text-[11px] text-slate-400 mt-3">Alur persetujuan: HRD → Direksi/Manager → Reviewer. Ketiga tahap harus menyetujui.</p>
      </div>

      <div class="lg:col-span-2 space-y-4">
        <div class="flex items-center gap-2">
          <button data-tab="mine" data-testid="tab-mine" class="lv-tab px-3 py-1.5 rounded-lg text-sm font-medium">Pengajuan Saya</button>
          ${canApprove ? `<button data-tab="approve" data-testid="tab-approve" class="lv-tab px-3 py-1.5 rounded-lg text-sm font-medium">Perlu Persetujuan</button>
          <button data-tab="all" data-testid="tab-all" class="lv-tab px-3 py-1.5 rounded-lg text-sm font-medium">Semua</button>` : ""}
        </div>
        <div id="lv-list"></div>
      </div>
    </div>
  </div>`;

  const listEl = root.querySelector("#lv-list");
  const balEl = root.querySelector("#balance");
  const startEl = root.querySelector("#lv-start");
  const endEl = root.querySelector("#lv-end");
  const daysEl = root.querySelector("#lv-days");

  function paintTabs() {
    root.querySelectorAll(".lv-tab").forEach((b) => {
      const active = b.getAttribute("data-tab") === tab;
      b.className = "lv-tab px-3 py-1.5 rounded-lg text-sm font-medium " +
        (active ? "bg-ink text-gold" : "bg-white border border-slate-200 text-slate-600 hover:border-slate-900");
    });
  }

  function weekdaysBetween(a, b) {
    if (!a || !b) return 0;
    const s = new Date(a + "T00:00:00"), e = new Date(b + "T00:00:00");
    if (e < s) return 0;
    let n = 0, d = new Date(s);
    while (d <= e) { const w = d.getDay(); if (w !== 0 && w !== 6) n++; d.setDate(d.getDate() + 1); }
    return n;
  }
  function updateDays() {
    const n = weekdaysBetween(startEl.value, endEl.value);
    daysEl.textContent = n ? `${n} hari kerja` : "";
  }
  startEl.oninput = updateDays;
  endEl.oninput = updateDays;

  function statusBadge(it) {
    if (it.status === "approved") return `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border bg-emerald-50 text-emerald-700 border-emerald-200"><i class="ph-fill ph-check-circle"></i>Disetujui</span>`;
    if (it.status === "rejected") return `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border bg-rose-50 text-rose-700 border-rose-200"><i class="ph-fill ph-x-circle"></i>Ditolak</span>`;
    return `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border bg-yellow-50 text-yellow-700 border-yellow-200"><i class="ph-fill ph-hourglass-medium"></i>Menunggu: ${it.stage_label}</span>`;
  }

  function bCard(l, v, cls) {
    return `<div class="bg-white border border-slate-200 rounded-xl p-4"><p class="text-xs text-slate-500 uppercase tracking-widest">${l}</p><p class="font-heading font-bold text-3xl ${cls} mt-1">${v}</p></div>`;
  }

  async function loadBalance() {
    balance = await ctx.api.get("/leave/balance");
    balEl.innerHTML = [
      bCard("Jatah Tahunan", balance.quota, "text-slate-900"),
      bCard("Terpakai", balance.used, "text-rose-600"),
      bCard("Menunggu", balance.pending, "text-yellow-600"),
      bCard("Sisa", balance.remaining, "text-emerald-600"),
    ].join("");
  }

  async function loadList() {
    listEl.innerHTML = `<div class="flex justify-center py-16 text-slate-400"><i class="ph ph-circle-notch spin text-2xl"></i></div>`;
    const scope = tab === "mine" ? "mine" : "all";
    const data = await ctx.api.get("/leave-requests?scope=" + scope);
    items = data.items;
    if (tab === "approve") items = items.filter((i) => i.can_act);
    renderList();
  }

  function renderList() {
    if (!items.length) {
      listEl.innerHTML = `<div class="bg-white border border-slate-200 rounded-xl p-10 text-center text-slate-400 text-sm">Belum ada data.</div>`;
      return;
    }
    listEl.innerHTML = items.map((it) => `
      <div class="bg-white border border-slate-200 rounded-xl p-4 mb-3" data-testid="leave-row">
        <div class="flex items-start justify-between gap-3 flex-wrap">
          <div class="min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <p class="text-sm font-semibold text-slate-900">${it.user_name}</p>
              <span class="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">${it.leave_type_label}</span>
            </div>
            <p class="text-sm text-slate-600 mt-1 font-mono">${it.start_date} → ${it.end_date} · <b>${it.days} hari</b></p>
            ${it.reason ? `<p class="text-xs text-slate-500 mt-1">${it.reason}</p>` : ""}
            ${it.reject_reason ? `<p class="text-xs text-rose-600 mt-1">Catatan: ${it.reject_reason}</p>` : ""}
            ${(it.approvals || []).length ? `<p class="text-[11px] text-slate-400 mt-1">Disetujui: ${it.approvals.filter(a=>a.decision==='approved').map(a=>a.by_name).join(", ") || "-"}</p>` : ""}
          </div>
          <div class="flex flex-col items-end gap-2">
            ${statusBadge(it)}
            ${it.can_act ? `<div class="flex gap-2">
              <button data-approve="${it.id}" data-testid="approve-${it.id}" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700">Setujui</button>
              <button data-reject="${it.id}" data-testid="reject-${it.id}" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 text-white hover:bg-rose-700">Tolak</button>
            </div>` : ""}
          </div>
        </div>
      </div>`).join("");

    listEl.querySelectorAll("[data-approve]").forEach((b) => b.onclick = () => decide(b.getAttribute("data-approve"), "approve"));
    listEl.querySelectorAll("[data-reject]").forEach((b) => b.onclick = () => decide(b.getAttribute("data-reject"), "reject"));
  }

  async function decide(id, action) {
    let note = "";
    if (action === "reject") {
      note = prompt("Alasan penolakan (opsional):") || "";
    }
    try {
      await ctx.api.post(`/leave-requests/${id}/${action}`, { note });
      ui.toast(action === "approve" ? "Pengajuan disetujui" : "Pengajuan ditolak", action === "approve" ? "success" : "info");
      await loadList();
      if (window.__refreshNotifs) window.__refreshNotifs();
    } catch (e) { ui.toast(e.message || "Gagal memproses", "error"); }
  }

  root.querySelector("#leave-form").onsubmit = async (e) => {
    e.preventDefault();
    const payload = {
      leave_type: root.querySelector("#lv-type").value,
      start_date: startEl.value,
      end_date: endEl.value,
      reason: root.querySelector("#lv-reason").value.trim(),
    };
    if (!payload.start_date || !payload.end_date) { ui.toast("Tanggal mulai & selesai wajib diisi", "error"); return; }
    try {
      await ctx.api.post("/leave-requests", payload);
      ui.toast("Pengajuan cuti terkirim", "success");
      root.querySelector("#leave-form").reset();
      daysEl.textContent = "";
      await loadBalance();
      await loadList();
      if (window.__refreshNotifs) window.__refreshNotifs();
    } catch (err) { ui.toast(err.message || "Gagal mengajukan", "error"); }
  };

  root.querySelectorAll(".lv-tab").forEach((b) => b.onclick = () => { tab = b.getAttribute("data-tab"); paintTabs(); loadList(); });

  paintTabs();
  await loadBalance();
  await loadList();
}
