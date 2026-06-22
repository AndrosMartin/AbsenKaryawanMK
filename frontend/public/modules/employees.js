// Employee management (list + add/edit/delete for owner & direksi)
export async function render(root, ctx) {
  const { ui } = ctx;
  const role = ctx.user.role;
  const canManage = ui.HR_ROLES.includes(role);
  const isHrd = role === "hrd";
  const roleOptions = isHrd ? ["staff", "manager", "hrd"] : ["staff", "manager", "hrd", "direksi", "owner"];
  let list = [];

  root.innerHTML = `
  <div class="space-y-6" data-testid="employees-page">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Manajemen</p>
        <h2 class="font-heading font-bold text-2xl text-slate-900">Data Karyawan</h2>
      </div>
      ${canManage ? `<button id="add-btn" data-testid="add-employee-btn" class="bg-slate-900 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-slate-800 flex items-center gap-2"><i class="ph ph-plus"></i> Tambah Karyawan</button>` : ""}
    </div>
    ${isHrd ? `<div data-testid="hrd-notice" class="flex items-start gap-3 bg-violet-50 border border-violet-200 rounded-xl px-4 py-3">
      <i class="ph-fill ph-info text-violet-600 text-lg mt-0.5"></i>
      <p class="text-sm text-violet-800">Sebagai <strong>HRD</strong>, setiap penambahan, perubahan, atau penghapusan karyawan akan dikirim sebagai <strong>permintaan</strong> dan baru berlaku setelah <strong>disetujui Direksi/Owner</strong>. Pantau status di menu <strong>Persetujuan</strong>.</p>
    </div>` : ""}
    <div id="emp-table"></div>
  </div>
  <div id="modal-root"></div>`;

  const tableEl = root.querySelector("#emp-table");
  const modalRoot = root.querySelector("#modal-root");

  async function load() {
    tableEl.innerHTML = `<div class="flex justify-center py-20 text-slate-400"><i class="ph ph-circle-notch spin text-2xl"></i></div>`;
    list = await ctx.api.get("/employees");
    renderTable();
  }

  function renderTable() {
    const rows = list.map((e) => `
      <tr class="hover:bg-slate-50 transition-colors">
        <td class="px-5 py-4">
          <div class="flex items-center gap-3">
            <div class="h-9 w-9 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-semibold">${ui.initials(e.name)}</div>
            <div><p class="text-sm font-medium text-slate-900">${e.name}</p><p class="text-xs text-slate-400">${e.email}</p></div>
          </div>
        </td>
        <td class="px-5 py-4 font-mono text-xs text-slate-500">${e.employee_id || "—"}</td>
        <td class="px-5 py-4 text-sm text-slate-600">${e.department || "—"}</td>
        <td class="px-5 py-4 text-sm text-slate-600">${e.position || "—"}</td>
        <td class="px-5 py-4">${ui.roleBadge(e.role)}</td>
        <td class="px-5 py-4">${e.face_enrolled ? '<span class="inline-flex items-center gap-1 text-emerald-600 text-xs font-medium"><i class="ph-fill ph-check-circle"></i> Terdaftar</span>' : '<span class="text-slate-400 text-xs">Belum</span>'}</td>
        ${canManage ? `<td class="px-5 py-4 text-right">
          <button data-edit="${e.id}" data-testid="edit-${e.id}" class="text-slate-500 hover:text-slate-900 p-1.5"><i class="ph ph-pencil-simple"></i></button>
          <button data-del="${e.id}" data-testid="delete-${e.id}" class="text-slate-500 hover:text-rose-600 p-1.5"><i class="ph ph-trash"></i></button>
        </td>` : ""}
      </tr>`).join("");

    tableEl.innerHTML = `
      <div class="w-full overflow-x-auto border border-slate-200 rounded-xl bg-white">
        <table class="w-full">
          <thead class="bg-slate-50 border-b border-slate-200"><tr>
            ${["Nama", "ID", "Departemen", "Posisi", "Role", "Wajah", canManage ? "" : null].filter((x) => x !== null).map((t) => `<th class="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">${t}</th>`).join("")}
          </tr></thead>
          <tbody class="divide-y divide-slate-100">${rows}</tbody>
        </table>
      </div>`;

    if (canManage) {
      tableEl.querySelectorAll("[data-edit]").forEach((b) => b.onclick = () => openModal(list.find((x) => x.id === b.getAttribute("data-edit"))));
      tableEl.querySelectorAll("[data-del]").forEach((b) => b.onclick = () => doDelete(b.getAttribute("data-del")));
    }
  }

  function openModal(emp) {
    const isEdit = !!emp;
    modalRoot.innerHTML = `
      <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 fade-in">
        <div class="bg-white rounded-2xl w-full max-w-md p-6" data-testid="employee-modal">
          <div class="flex items-center justify-between mb-5">
            <h3 class="font-heading font-bold text-xl text-slate-900">${isEdit ? "Edit Karyawan" : "Tambah Karyawan"}</h3>
            <button id="close-modal" class="text-slate-400 hover:text-slate-900"><i class="ph ph-x text-xl"></i></button>
          </div>
          <form id="emp-form" class="space-y-3">
            <div><label class="block text-sm font-medium text-slate-700 mb-1">Nama</label><input id="f-name" data-testid="emp-name" required value="${emp?.name || ""}" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-900 focus:outline-none" /></div>
            <div><label class="block text-sm font-medium text-slate-700 mb-1">Email</label><input id="f-email" data-testid="emp-email" type="email" required ${isEdit ? "disabled" : ""} value="${emp?.email || ""}" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-900 focus:outline-none disabled:bg-slate-50 disabled:text-slate-400" /></div>
            <div class="grid grid-cols-2 gap-3">
              <div><label class="block text-sm font-medium text-slate-700 mb-1">Departemen</label><input id="f-dept" value="${emp?.department || ""}" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-900 focus:outline-none" /></div>
              <div><label class="block text-sm font-medium text-slate-700 mb-1">Posisi</label><input id="f-pos" value="${emp?.position || ""}" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-900 focus:outline-none" /></div>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Role</label>
              <select id="f-role" data-testid="emp-role" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-900 focus:outline-none bg-white">
                ${roleOptions.map((r) => `<option value="${r}" ${emp?.role === r ? "selected" : ""}>${ui.ROLE_LABELS[r]}</option>`).join("")}
              </select>
            </div>
            <div><label class="block text-sm font-medium text-slate-700 mb-1">${isEdit ? "Reset Password (opsional)" : "Password"}</label><input id="f-pass" data-testid="emp-password" type="text" ${isEdit ? "" : "required"} placeholder="${isEdit ? "Kosongkan jika tidak diubah" : "password123"}" value="${isEdit ? "" : "password123"}" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-900 focus:outline-none" /></div>
            <p id="modal-err" class="text-sm text-rose-600 hidden"></p>
            <button type="submit" data-testid="save-employee-btn" class="w-full bg-slate-900 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-slate-800 flex items-center justify-center gap-2"><span id="save-text">${isEdit ? "Simpan Perubahan" : "Tambah Karyawan"}</span></button>
          </form>
        </div>
      </div>`;

    const close = () => modalRoot.innerHTML = "";
    modalRoot.querySelector("#close-modal").onclick = close;
    modalRoot.querySelector("#emp-form").onsubmit = async (ev) => {
      ev.preventDefault();
      const err = modalRoot.querySelector("#modal-err");
      const saveText = modalRoot.querySelector("#save-text");
      err.classList.add("hidden");
      saveText.innerHTML = `<i class="ph ph-circle-notch spin"></i>`;
      const payload = {
        name: modalRoot.querySelector("#f-name").value.trim(),
        department: modalRoot.querySelector("#f-dept").value.trim(),
        position: modalRoot.querySelector("#f-pos").value.trim(),
        role: modalRoot.querySelector("#f-role").value,
      };
      const pass = modalRoot.querySelector("#f-pass").value;
      try {
        let res;
        if (isEdit) {
          if (pass) payload.password = pass;
          res = await ctx.api.put("/employees/" + emp.id, payload);
        } else {
          payload.email = modalRoot.querySelector("#f-email").value.trim();
          payload.password = pass;
          res = await ctx.api.post("/employees", payload);
        }
        if (res && res.pending) {
          ui.toast("Permintaan dikirim. Menunggu verifikasi Direksi/Owner.", "info");
        } else {
          ui.toast(isEdit ? "Karyawan diperbarui" : "Karyawan ditambahkan", "success");
        }
        close();
        load();
      } catch (e) {
        err.textContent = e.message; err.classList.remove("hidden");
        saveText.textContent = isEdit ? "Simpan Perubahan" : "Tambah Karyawan";
      }
    };
  }

  async function doDelete(id) {
    const emp = list.find((x) => x.id === id);
    const msg = isHrd
      ? `Ajukan penghapusan karyawan "${emp.name}" untuk disetujui Direksi?`
      : `Hapus karyawan "${emp.name}"? Data absensinya juga akan terhapus.`;
    if (!confirm(msg)) return;
    try {
      const res = await ctx.api.del("/employees/" + id);
      if (res && res.pending) ui.toast("Permintaan hapus dikirim. Menunggu verifikasi Direksi/Owner.", "info");
      else ui.toast("Karyawan dihapus", "success");
      load();
    } catch (e) { ui.toast(e.message, "error"); }
  }

  if (canManage) root.querySelector("#add-btn").onclick = () => openModal(null);
  load();
}
