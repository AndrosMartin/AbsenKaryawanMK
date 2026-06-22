// Shared UI helpers, formatting, icons, and face-recognition utilities.

export const ROLE_LABELS = {
  owner: "Owner / CEO",
  direksi: "Direksi",
  manager: "Manager",
  hrd: "HRD",
  staff: "Staff",
};

export const ROLE_BADGE = {
  owner: "bg-slate-900 text-white border-slate-900",
  direksi: "bg-indigo-50 text-indigo-700 border-indigo-200",
  manager: "bg-sky-50 text-sky-700 border-sky-200",
  hrd: "bg-violet-50 text-violet-700 border-violet-200",
  staff: "bg-slate-100 text-slate-700 border-slate-200",
};

export const MONITOR_ROLES = ["owner", "direksi", "manager", "hrd"];
export const MANAGE_ROLES = ["owner", "direksi"];
export const HR_ROLES = ["owner", "direksi", "hrd"];
export const APPROVER_ROLES = ["owner", "direksi"];
export const HRD_ASSIGNABLE_ROLES = ["manager", "hrd", "staff"];

export function h(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

export function fmtTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("id-ID", {
    hour: "2-digit", minute: "2-digit", timeZone: "Asia/Jakarta",
  });
}

export function fmtDate(d) {
  if (!d) return "—";
  const date = typeof d === "string" && d.length === 10 ? new Date(d + "T00:00:00") : new Date(d);
  return date.toLocaleDateString("id-ID", {
    weekday: "short", day: "numeric", month: "short", year: "numeric",
  });
}

export function statusPill(status) {
  const map = {
    present: ["Tepat Waktu", "bg-emerald-50 text-emerald-700 border-emerald-200", "ph-check-circle"],
    late: ["Terlambat", "bg-amber-50 text-amber-700 border-amber-200", "ph-clock-countdown"],
    absent: ["Tidak Hadir", "bg-rose-50 text-rose-700 border-rose-200", "ph-x-circle"],
  };
  const [label, cls, icon] = map[status] || map.absent;
  return `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${cls}">
    <i class="ph-fill ${icon}"></i>${label}</span>`;
}

export function roleBadge(role) {
  return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${ROLE_BADGE[role] || ROLE_BADGE.staff}">${ROLE_LABELS[role] || role}</span>`;
}

export function initials(name) {
  return (name || "?").split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase();
}

export function toast(message, type = "info") {
  const colors = {
    success: "border-emerald-200 bg-white text-emerald-800",
    error: "border-rose-200 bg-white text-rose-800",
    info: "border-slate-200 bg-white text-slate-800",
  };
  const icons = { success: "ph-check-circle", error: "ph-warning-circle", info: "ph-info" };
  const el = h(`<div class="fade-in flex items-start gap-3 min-w-[280px] max-w-sm border ${colors[type]} shadow-lg rounded-xl px-4 py-3">
      <i class="ph-fill ${icons[type]} text-lg mt-0.5"></i>
      <p class="text-sm font-medium flex-1">${message}</p>
    </div>`);
  document.getElementById("toast-root").appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; setTimeout(() => el.remove(), 300); }, 3800);
}

export function btnSpinner() {
  return `<i class="ph ph-circle-notch spin"></i>`;
}

export function getPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error("Browser tidak mendukung GPS"));
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude, accuracy: pos.coords.accuracy }),
      (err) => reject(new Error("Gagal mengakses lokasi: " + err.message)),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
    );
  });
}

// ---- Face recognition (face-api.js / @vladmandic) ----
const MODEL_URL = "https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model";
let _faceModelsPromise = null;

export function loadFaceModels() {
  if (_faceModelsPromise) return _faceModelsPromise;
  _faceModelsPromise = (async () => {
    // wait for global faceapi to be ready (deferred script)
    let tries = 0;
    while (typeof window.faceapi === "undefined" && tries < 60) {
      await new Promise((r) => setTimeout(r, 100)); tries++;
    }
    if (typeof window.faceapi === "undefined") throw new Error("Library wajah gagal dimuat");
    const fa = window.faceapi;
    await Promise.all([
      fa.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
      fa.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
      fa.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
    ]);
    return fa;
  })();
  return _faceModelsPromise;
}

export async function detectDescriptor(videoEl) {
  const fa = await loadFaceModels();
  const det = await fa
    .detectSingleFace(videoEl, new fa.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.4 }))
    .withFaceLandmarks()
    .withFaceDescriptor();
  if (!det) return null;
  return Array.from(det.descriptor);
}

export async function startCamera(videoEl) {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
    audio: false,
  });
  videoEl.srcObject = stream;
  await videoEl.play();
  return stream;
}

export function stopCamera(stream) {
  if (stream) stream.getTracks().forEach((t) => t.stop());
}
