// Persetujuan perubahan karyawan (HRD mengajukan, Direksi/Owner menyetujui)
export async function render(root, ctx) {
  const { ui } = ctx;
  const isApprover = ui.APPROVER_ROLES.includes(ctx.user.role);
  let reqs = [];

  const ACTION = {
    create: ["Tambah Karyawan", "ph-user-plus", "text-emerald-600"],
    update: ["Ubah Data", "ph-pencil-simple", "text-sky-600"],
    delete: ["Hapus Karyawan", "ph-user-minus", "text-rose-600"],
  };
  const STATUS = {
    pending: ["Menunggu", "bg-amber-50 text-amber-700 border-amber-200", "ph-clock"],
    approved: ["Disetujui", "bg-emerald-50 text-emerald-700 border-emerald-200", "ph-check-circle"],
    rejected: ["Ditolak", "bg-rose-50 text-rose-700 border-rose-200", "ph-x-circle"],
  };

  root.innerHTML = `
  <div class="space-y-6" data-testid="approvals-page">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">${isApprover ? "Verifikasi" : "Status Pengajuan"}</p>
        <h2 class="font-heading font-bold text-2xl text-slate-900">Persetujuan Perubahan Karyawan</h2>
        <p class="text-sm text-slate-500 mt-1">${isApprover ? "Tinjau dan setujui/tolak permintaan yang diajukan oleh HRD." : "Pantau status permintaan perubahan karyawan yang Anda ajukan."}</p>
      </div>
      <div class="flex gap-1 bg-slate-100 p-1 rounded-lg" id="filter-tabs">
        ${[["pending", "Menunggu"], ["approved", "Disetujui"], ["rejected", "Ditolak"], ["", "Semua"]].map(([v, l], i) => `
          <button data-filter="${v}" data-testid="filter-${v || "all"}" class="filter-btn px-3 py-1.5 rounded-md text-sm font-medium ${i === 0 ? "bg-white text-slate-900 shadow-sm" : "text-slate-500"}">${l}</button>`).join("")}
      </div>
    </div>
    <div id="req-list" class="space-y-3"></div>
  </div>`;

  const listEl = root.querySelector("#req-list");
  let filter = "pending";

  async function load() {
    listEl.innerHTML = `<div class="flex justify-center py-16 text-slate-400"><i class="ph ph-circle-notch spin text-2xl"></i></div>`;
    try {
      reqs = await ctx.api.get("/employee-requests" + (filter ? "?status=" + filter : ""));
    } catch (e) {
      listEl.innerHTML = `<div class="p-8 text-center text-rose-600">${e.message}</div>`; return;
    }
    renderList();
  }

  function payloadPreview(r) {
    const p = r.payload || {};
    const parts = [];
    if (p.name) parts.push(`Nama: <span class="text-slate-700">${p.name}</span>`);
    if (p.email) parts.push(`Email: <span class="font-mono text-slate-700">${p.email}</span>`);
    if (p.role) parts.push(`Role: <span class="text-slate-700">${ui.ROLE_LABELS[p.role] || p.role}</span>`);
    if (p.department) parts.push(`Dept: <span class="text-slate-700">${p.department}</span>`);
    if (p.position) parts.push(`Posisi: <span class="text-slate-700">${p.position}</span>`);
    if (!parts.length) return "";
    return `<div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">${parts.join("")}</div>`;
  }

  function renderList() {
    if (!reqs.length) {
      listEl.innerHTML = `<div class="text-center py-16 text-slate-400 border border-dashed border-slate-300 rounded-xl">Tidak ada permintaan${filter ? " dengan status ini" : ""}.</div>`;
      return;
    }
    listEl.innerHTML = reqs.map((r) => {
      const [aLabel, aIcon, aColor] = ACTION[r.action] || ACTION.update;
      const [sLabel, sCls, sIcon] = STATUS[r.status] || STATUS.pending;
      return `
      <div class="bg-white border border-slate-200 rounded-xl p-5" data-testid="request-${r.id}">
        <div class="flex flex-wrap items-start gap-4">
          <div class="h-10 w-10 rounded-lg bg-slate-100 flex items-center justify-center ${aColor}"><i class="ph-fill ${aIcon} text-lg"></i></div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="font-heading font-semibold text-slate-900">${aLabel}</span>
              <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${sCls}"><i class="ph-fill ${sIcon}"></i>${sLabel}</span>
            </div>
            <p class="text-sm text-slate-600 mt-1">${r.summary || ""}</p>
            ${payloadPreview(r)}
            <p class="text-xs text-slate-400 mt-2">Diajukan oleh <span class="text-slate-600">${r.requested_by_name || "-"}</span> · ${ui.fmtDate(r.created_at)}
              ${r.reviewed_by_name ? ` · Ditinjau oleh <span class="text-slate-600">${r.reviewed_by_name}</span>` : ""}</p>
            ${r.reject_reason ? `<p class="text-xs text-rose-600 mt-1">Alasan: ${r.reject_reason}</p>` : ""}
          </div>
          ${isApprover && r.status === "pending" ? `
            <div class="flex gap-2">
              <button data-reject="${r.id}" data-testid="reject-${r.id}" class="px-3 py-2 rounded-lg text-sm font-medium border border-slate-200 text-slate-700 hover:bg-slate-50">Tolak</button>
              <button data-approve="${r.id}" data-testid="approve-${r.id}" class="px-3 py-2 rounded-lg text-sm font-medium bg-slate-900 text-white hover:bg-slate-800">Setujui</button>
            </div>` : ""}
        </div>
      </div>`;
    }).join("");

    if (isApprover) {
      listEl.querySelectorAll("[data-approve]").forEach((b) => b.onclick = () => doApprove(b.getAttribute("data-approve")));
      listEl.querySelectorAll("[data-reject]").forEach((b) => b.onclick = () => doReject(b.getAttribute("data-reject")));
    }
  }

  async function doApprove(id) {
    try {
      await ctx.api.post(`/employee-requests/${id}/approve`, {});
      ui.toast("Permintaan disetujui & diterapkan", "success");
      load();
    } catch (e) { ui.toast(e.message, "error"); }
  }

  async function doReject(id) {
    const reason = prompt("Alasan penolakan (opsional):") || "";
    try {
      await ctx.api.post(`/employee-requests/${id}/reject`, { reason });
      ui.toast("Permintaan ditolak", "info");
      load();
    } catch (e) { ui.toast(e.message, "error"); }
  }

  root.querySelectorAll(".filter-btn").forEach((b) => b.onclick = () => {
    filter = b.getAttribute("data-filter");
    root.querySelectorAll(".filter-btn").forEach((x) => {
      const on = x === b;
      x.classList.toggle("bg-white", on);
      x.classList.toggle("text-slate-900", on);
      x.classList.toggle("shadow-sm", on);
      x.classList.toggle("text-slate-500", !on);
    });
    load();
  });

  load();
}
