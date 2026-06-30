import { api, getToken, setToken, clearToken } from "/js/api.js";
import * as ui from "/js/ui.js";
import { ensurePushSubscribed } from "/js/push.js";

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: "ph-chart-line-up", roles: ui.MONITOR_ROLES },
  { id: "checkin", label: "Absensi", icon: "ph-fingerprint", roles: ui.ALL_USERS },
  { id: "history", label: "Riwayat Saya", icon: "ph-clock-counter-clockwise", roles: ui.ALL_USERS },
  { id: "monitoring", label: "Monitoring", icon: "ph-monitor", roles: ui.MONITOR_ROLES },
  { id: "employees", label: "Karyawan", icon: "ph-users-three", roles: ui.MONITOR_ROLES },
  { id: "approvals", label: "Persetujuan", icon: "ph-seal-check", roles: ui.HR_ROLES },
  { id: "offices", label: "Lokasi Kantor", icon: "ph-map-pin", roles: ui.MANAGE_ROLES },
  { id: "face", label: "Wajah Saya", icon: "ph-user-focus", roles: ui.ALL_USERS },
  { id: "profile", label: "Profil", icon: "ph-user-circle", roles: ui.ALL_USERS },
];

const state = { user: null, currentStream: null };

const ctx = {
  api, ui,
  get user() { return state.user; },
  navigate,
  setStream: (s) => { state.currentStream = s; },
  logout,
  refreshUser,
};

function allowedNav() {
  return NAV.filter((n) => n.roles.includes(state.user.role));
}

async function refreshUser() {
  state.user = await api.get("/auth/me");
  return state.user;
}

function logout() {
  clearToken();
  state.user = null;
  location.hash = "";
  renderLogin();
}

async function navigate(route) {
  // stop any active camera stream and face-detect loop when leaving a page
  if (window.__faceLoop) { clearInterval(window.__faceLoop); window.__faceLoop = null; }
  if (state.currentStream) { ui.stopCamera(state.currentStream); state.currentStream = null; }
  const allowed = allowedNav().map((n) => n.id);
  if (!allowed.includes(route)) route = allowed[0];
  if (location.hash !== "#" + route) { location.hash = route; return; }
  setActiveNav(route);
  const content = document.getElementById("app-content");
  content.innerHTML = `<div class="flex items-center justify-center py-32 text-slate-400"><i class="ph ph-circle-notch spin text-3xl"></i></div>`;
  try {
    const mod = await import(`/modules/${route}.js?v=11`);
    content.innerHTML = "";
    await mod.render(content, ctx);
  } catch (e) {
    console.error(e);
    content.innerHTML = `<div class="p-8 text-center text-rose-600">Gagal memuat modul: ${e.message}</div>`;
  }
}

function setActiveNav(route) {
  document.querySelectorAll("[data-nav]").forEach((el) => {
    el.classList.toggle("nav-active", el.getAttribute("data-nav") === route);
  });
  const cur = NAV.find((n) => n.id === route);
  const t = document.getElementById("topbar-title");
  if (t && cur) t.textContent = cur.label;
  // close mobile sidebar
  document.getElementById("sidebar")?.classList.add("-translate-x-full");
  document.getElementById("sidebar")?.classList.remove("translate-x-0");
}

function renderShell() {
  const u = state.user;
  const navHtml = allowedNav().map((n) => `
    <a href="#${n.id}" data-nav="${n.id}" data-testid="nav-${n.id}"
       class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:bg-white/5 hover:text-white transition-colors">
      <i class="ph ${n.icon} text-lg"></i><span>${n.label}</span>
    </a>`).join("");

  document.getElementById("app").innerHTML = `
  <div class="min-h-screen flex bg-slate-50">
    <!-- Sidebar -->
    <aside id="sidebar" class="fixed lg:static inset-y-0 left-0 z-50 w-72 bg-ink flex flex-col transform -translate-x-full lg:translate-x-0 transition-transform duration-300">
      <div class="h-16 flex items-center gap-3 px-5 border-b border-white/10">
        <img src="/logo-mitra.jpg" alt="MitraKeuangan" class="h-10 w-10 rounded-lg object-cover ring-1 ring-gold/40" />
        <div>
          <p class="font-heading font-bold text-lg leading-none"><span class="text-white">Mitra</span><span class="text-gold">Keuangan</span></p>
          <p class="text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">Absensi & Monitoring</p>
        </div>
      </div>
      <nav class="flex-1 px-3 py-5 space-y-1 overflow-y-auto">${navHtml}</nav>
      ${ui.MONITOR_ROLES.includes(u.role) ? `
      <a href="/Manual_Book_AbsensiPro.pdf" target="_blank" rel="noopener" data-testid="manual-link"
         class="mx-3 mb-2 flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-300 hover:text-gold border border-white/10 hover:border-gold/40 transition-colors">
        <i class="ph ph-book-open-text text-lg"></i><span>Manual Book (PDF)</span>
      </a>` : ""}
      <div class="p-3 border-t border-white/10">
        <div class="flex items-center gap-3 px-3 py-2">
          <div class="h-9 w-9 rounded-full bg-gold/20 text-gold ring-1 ring-gold/40 flex items-center justify-center text-xs font-semibold">${ui.initials(u.name)}</div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-white truncate">${u.name}</p>
            <p class="text-[11px] text-slate-500 truncate">${ui.ROLE_LABELS[u.role]}</p>
          </div>
          <button data-testid="logout-btn" id="logout-btn" class="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-white/5"><i class="ph ph-sign-out text-lg"></i></button>
        </div>
      </div>
    </aside>
    <div id="sidebar-overlay" class="fixed inset-0 bg-black/40 z-40 hidden lg:hidden"></div>

    <!-- Main -->
    <div class="flex-1 flex flex-col min-w-0">
      <header class="h-16 bg-white border-b border-slate-200 flex items-center gap-4 px-4 sm:px-6 sticky top-0 z-30">
        <button id="menu-btn" class="lg:hidden text-slate-600 p-2 -ml-2"><i class="ph ph-list text-2xl"></i></button>
        <h1 id="topbar-title" class="font-heading font-bold text-lg text-slate-900">Dashboard</h1>
        <div class="ml-auto flex items-center gap-3">
          <div class="hidden sm:flex flex-col items-end">
            <span class="text-xs text-slate-400" id="topbar-date"></span>
            <span class="text-sm font-mono font-medium text-slate-700" id="topbar-clock"></span>
          </div>
          <div class="relative" id="notif-wrap">
            <button id="notif-btn" data-testid="notif-btn" class="relative h-10 w-10 rounded-lg border border-slate-200 hover:bg-slate-50 flex items-center justify-center text-slate-700 transition-colors">
              <i class="ph ph-bell text-xl"></i>
              <span id="notif-badge" data-testid="notif-badge" class="hidden absolute -top-1.5 -right-1.5 min-w-[18px] h-[18px] px-1 rounded-full bg-gold text-ink text-[10px] font-bold flex items-center justify-center notif-badge"></span>
            </button>
            <div id="notif-panel" class="hidden absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-xl shadow-xl z-50 overflow-hidden">
              <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                <span class="font-heading font-semibold text-slate-900">Notifikasi</span>
                <span id="notif-count-label" class="text-xs text-slate-400"></span>
              </div>
              <div id="notif-list" class="max-h-80 overflow-y-auto"></div>
            </div>
          </div>
          ${ui.roleBadge(u.role)}
        </div>
      </header>
      <main id="app-content" class="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1400px] w-full mx-auto"></main>
    </div>
  </div>`;

  document.getElementById("logout-btn").onclick = logout;
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebar-overlay");
  document.getElementById("menu-btn").onclick = () => {
    sidebar.classList.remove("-translate-x-full");
    overlay.classList.remove("hidden");
  };
  overlay.onclick = () => { sidebar.classList.add("-translate-x-full"); overlay.classList.add("hidden"); };

  startClock();
  setupNotifications();
}

const SEEN_KEY = "absensipro_seen_notifs";
let _notifTimer = null;

function getSeen() {
  try { return new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || "[]")); }
  catch (e) { return new Set(); }
}
function markSeen(ids) {
  const s = getSeen();
  ids.forEach((id) => s.add(id));
  localStorage.setItem(SEEN_KEY, JSON.stringify([...s].slice(-200)));
}

function notifIcon(type) {
  if (type === "approved") return ["ph-check-circle", "text-emerald-600", "bg-emerald-50"];
  if (type === "rejected") return ["ph-x-circle", "text-rose-600", "bg-rose-50"];
  return ["ph-bell-ringing", "text-gold-600", "bg-gold-50"];
}

async function refreshNotifications() {
  const badge = document.getElementById("notif-badge");
  if (!badge) return;
  let data;
  try { data = await api.get("/notifications"); } catch (e) { return; }
  const seen = getSeen();
  const unread = data.items.filter((i) => !seen.has(i.id)).length;
  if (unread > 0) {
    badge.textContent = unread > 9 ? "9+" : String(unread);
    badge.classList.remove("hidden");
  } else {
    badge.classList.add("hidden");
  }
  const list = document.getElementById("notif-list");
  const label = document.getElementById("notif-count-label");
  if (label) label.textContent = data.items.length ? `${data.items.length} item` : "";
  if (list) {
    list.innerHTML = data.items.length ? data.items.map((i) => {
      const [icon, color, bg] = notifIcon(i.type);
      const isUnread = !seen.has(i.id);
      return `<button data-notif-item="${i.id}" class="w-full text-left px-4 py-3 border-b border-slate-100 last:border-0 hover:bg-slate-50 flex gap-3 ${isUnread ? "bg-gold-50/40" : ""}">
        <div class="h-8 w-8 rounded-lg ${bg} ${color} flex items-center justify-center shrink-0"><i class="ph-fill ${icon}"></i></div>
        <div class="min-w-0">
          <p class="text-sm font-medium text-slate-900">${i.title}</p>
          <p class="text-xs text-slate-500 truncate">${i.body || ""}</p>
          <p class="text-[11px] text-slate-400 mt-0.5">${i.by || ""} · ${ui.fmtDate(i.created_at)}</p>
        </div>
      </button>`;
    }).join("") : `<p class="px-4 py-10 text-center text-sm text-slate-400">Tidak ada notifikasi</p>`;
    list.querySelectorAll("[data-notif-item]").forEach((b) => b.onclick = () => {
      document.getElementById("notif-panel").classList.add("hidden");
      navigate("approvals");
    });
  }
  return data;
}

function setupNotifications() {
  const btn = document.getElementById("notif-btn");
  const panel = document.getElementById("notif-panel");
  if (!btn) return;
  btn.onclick = async (e) => {
    e.stopPropagation();
    const willOpen = panel.classList.contains("hidden");
    panel.classList.toggle("hidden");
    if (willOpen) {
      const data = await refreshNotifications();
      if (data) { markSeen(data.items.map((i) => i.id)); refreshNotifications(); }
    }
  };
  document.addEventListener("click", (e) => {
    if (!document.getElementById("notif-wrap")?.contains(e.target)) panel.classList.add("hidden");
  });
  refreshNotifications();
  window.__refreshNotifs = refreshNotifications;
  if (_notifTimer) clearInterval(_notifTimer);
  _notifTimer = setInterval(refreshNotifications, 25000);
}

function startClock() {
  const upd = () => {
    const now = new Date();
    const dEl = document.getElementById("topbar-date");
    const cEl = document.getElementById("topbar-clock");
    if (!dEl) return;
    dEl.textContent = now.toLocaleDateString("id-ID", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "Asia/Jakarta" });
    cEl.textContent = now.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", second: "2-digit", timeZone: "Asia/Jakarta" });
  };
  upd();
  setInterval(upd, 1000);
}

async function renderLogin() {
  document.getElementById("app").innerHTML = "";
  const mod = await import("/modules/login.js?v=10");
  await mod.render(document.getElementById("app"), {
    api, ui,
    onLogin: async (token, user) => {
      setToken(token);
      state.user = user;
      bootApp();
    },
  });
}

function bootApp() {
  renderShell();
  ensurePushSubscribed();
  const route = (location.hash || "").replace("#", "") || allowedNav()[0].id;
  navigate(route);
  window.onhashchange = () => {
    const r = (location.hash || "").replace("#", "");
    if (state.user && r) navigate(r);
  };
}

async function init() {
  const loader = document.getElementById("global-loader");
  try {
    if (getToken()) {
      state.user = await api.get("/auth/me");
      bootApp();
    } else {
      await renderLogin();
    }
  } catch (e) {
    clearToken();
    await renderLogin();
  } finally {
    loader.style.opacity = "0";
    setTimeout(() => loader.remove(), 300);
  }
}

init();
