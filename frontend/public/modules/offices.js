// Office locations + geofence settings + printable QR codes
export async function render(root, ctx) {
  const { ui } = ctx;
  let offices = [];

  root.innerHTML = `
  <div class="space-y-6" data-testid="offices-page">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-xs font-medium text-slate-500 uppercase tracking-widest">Konfigurasi</p>
        <h2 class="font-heading font-bold text-2xl text-slate-900">Lokasi Kantor & Geofence</h2>
        <p class="text-sm text-slate-500 mt-1">Tetapkan titik kantor dan radius. Karyawan hanya bisa absen di dalam radius.</p>
      </div>
      <button id="add-office" data-testid="add-office-btn" class="bg-gold text-ink px-4 py-2.5 rounded-lg text-sm font-semibold hover:bg-gold-500 flex items-center gap-2"><i class="ph ph-plus"></i> Tambah Lokasi</button>
    </div>
    <div id="office-list" class="grid md:grid-cols-2 gap-5"></div>
  </div>
  <div id="modal-root"></div>`;

  const listEl = root.querySelector("#office-list");
  const modalRoot = root.querySelector("#modal-root");

  async function load() {
    listEl.innerHTML = `<div class="col-span-2 flex justify-center py-20 text-slate-400"><i class="ph ph-circle-notch spin text-2xl"></i></div>`;
    offices = await ctx.api.get("/offices");
    renderList();
  }

  function renderList() {
    if (!offices.length) {
      listEl.innerHTML = `<div class="col-span-2 text-center py-16 text-slate-400 border border-dashed border-slate-300 rounded-xl">Belum ada lokasi kantor. Tambahkan satu untuk mengaktifkan absensi.</div>`;
      return;
    }
    listEl.innerHTML = offices.map((o) => `
      <div class="bg-white border border-slate-200 rounded-xl p-5">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div class="h-11 w-11 rounded-xl bg-ink text-white flex items-center justify-center"><i class="ph-fill ph-buildings text-xl"></i></div>
            <div>
              <h3 class="font-heading font-semibold text-slate-900">${o.name}</h3>
              <p class="text-xs text-slate-400 font-mono">${o.lat.toFixed(5)}, ${o.lng.toFixed(5)}</p>
            </div>
          </div>
          <div class="flex gap-1">
            <button data-edit="${o.id}" class="text-slate-500 hover:text-slate-900 p-1.5"><i class="ph ph-pencil-simple"></i></button>
            <button data-del="${o.id}" class="text-slate-500 hover:text-rose-600 p-1.5"><i class="ph ph-trash"></i></button>
          </div>
        </div>
        <div class="flex items-center gap-4 mt-4">
          <div id="qr-${o.id}" class="bg-white p-2 border border-slate-200 rounded-lg"></div>
          <div class="text-sm">
            <p class="text-slate-500">Radius geofence</p>
            <p class="font-mono font-semibold text-slate-900">${o.radius_m} meter</p>
            <p class="text-slate-500 mt-2">QR Code Absensi</p>
            <p class="font-mono text-xs text-slate-700">${o.qr_code}</p>
          </div>
        </div>
      </div>`).join("");

    offices.forEach((o) => {
      const box = document.getElementById("qr-" + o.id);
      if (box && typeof QRCode !== "undefined") {
        box.innerHTML = "";
        new QRCode(box, { text: o.qr_code, width: 84, height: 84, colorDark: "#0f172a", colorLight: "#ffffff" });
      }
    });
    listEl.querySelectorAll("[data-edit]").forEach((b) => b.onclick = () => openModal(offices.find((x) => x.id === b.getAttribute("data-edit"))));
    listEl.querySelectorAll("[data-del]").forEach((b) => b.onclick = () => doDelete(b.getAttribute("data-del")));
  }

  function openModal(office) {
    const isEdit = !!office;
    modalRoot.innerHTML = `
      <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 fade-in">
        <div class="bg-white rounded-2xl w-full max-w-md p-6" data-testid="office-modal">
          <div class="flex items-center justify-between mb-5">
            <h3 class="font-heading font-bold text-xl text-slate-900">${isEdit ? "Edit Lokasi" : "Tambah Lokasi"}</h3>
            <button id="close-modal" class="text-slate-400 hover:text-slate-900"><i class="ph ph-x text-xl"></i></button>
          </div>
          <form id="office-form" class="space-y-3">
            <div><label class="block text-sm font-medium text-slate-700 mb-1">Nama Lokasi</label><input id="o-name" data-testid="office-name" required value="${office?.name || ""}" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-900 focus:outline-none" /></div>
            <div class="grid grid-cols-2 gap-3">
              <div><label class="block text-sm font-medium text-slate-700 mb-1">Latitude</label><input id="o-lat" data-testid="office-lat" type="number" step="any" required value="${office?.lat ?? ""}" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-slate-900 focus:outline-none" /></div>
              <div><label class="block text-sm font-medium text-slate-700 mb-1">Longitude</label><input id="o-lng" data-testid="office-lng" type="number" step="any" required value="${office?.lng ?? ""}" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-slate-900 focus:outline-none" /></div>
            </div>
            <div><label class="block text-sm font-medium text-slate-700 mb-1">Radius (meter)</label><input id="o-radius" data-testid="office-radius" type="number" required value="${office?.radius_m ?? 200}" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-slate-900 focus:outline-none" /></div>
            <button type="button" id="use-my-loc" class="text-xs font-medium text-slate-900 hover:underline flex items-center gap-1"><i class="ph ph-crosshair"></i> Gunakan lokasi saya saat ini</button>
            <p id="modal-err" class="text-sm text-rose-600 hidden"></p>
            <button type="submit" data-testid="save-office-btn" class="w-full bg-gold text-ink py-2.5 rounded-lg text-sm font-semibold hover:bg-gold-500 flex items-center justify-center gap-2"><span id="save-text">${isEdit ? "Simpan" : "Tambah Lokasi"}</span></button>
          </form>
        </div>
      </div>`;

    const close = () => modalRoot.innerHTML = "";
    modalRoot.querySelector("#close-modal").onclick = close;
    modalRoot.querySelector("#use-my-loc").onclick = async () => {
      try {
        const p = await ui.getPosition();
        modalRoot.querySelector("#o-lat").value = p.lat.toFixed(6);
        modalRoot.querySelector("#o-lng").value = p.lng.toFixed(6);
        ui.toast("Lokasi terisi", "success");
      } catch (e) { ui.toast(e.message, "error"); }
    };
    modalRoot.querySelector("#office-form").onsubmit = async (ev) => {
      ev.preventDefault();
      const err = modalRoot.querySelector("#modal-err");
      const saveText = modalRoot.querySelector("#save-text");
      err.classList.add("hidden");
      saveText.innerHTML = `<i class="ph ph-circle-notch spin"></i>`;
      const payload = {
        name: modalRoot.querySelector("#o-name").value.trim(),
        lat: parseFloat(modalRoot.querySelector("#o-lat").value),
        lng: parseFloat(modalRoot.querySelector("#o-lng").value),
        radius_m: parseInt(modalRoot.querySelector("#o-radius").value),
      };
      try {
        if (isEdit) await ctx.api.put("/offices/" + office.id, payload);
        else await ctx.api.post("/offices", payload);
        ui.toast(isEdit ? "Lokasi diperbarui" : "Lokasi ditambahkan", "success");
        close(); load();
      } catch (e) { err.textContent = e.message; err.classList.remove("hidden"); saveText.textContent = isEdit ? "Simpan" : "Tambah Lokasi"; }
    };
  }

  async function doDelete(id) {
    const o = offices.find((x) => x.id === id);
    if (!confirm(`Hapus lokasi "${o.name}"?`)) return;
    try { await ctx.api.del("/offices/" + id); ui.toast("Lokasi dihapus", "success"); load(); }
    catch (e) { ui.toast(e.message, "error"); }
  }

  root.querySelector("#add-office").onclick = () => openModal(null);
  load();
}
