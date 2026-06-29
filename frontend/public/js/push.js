// Web Push helper — VAPID subscription against FastAPI backend.
import { api } from "/js/api.js";

export function pushSupported() {
  return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

async function getRegistration() {
  return (await navigator.serviceWorker.getRegistration()) ||
         (await navigator.serviceWorker.register("/sw.js"));
}

export async function getPushState() {
  if (!pushSupported()) return { supported: false, subscribed: false, permission: "default" };
  let subscribed = false;
  try {
    const reg = await navigator.serviceWorker.getRegistration();
    if (reg) {
      const sub = await reg.pushManager.getSubscription();
      subscribed = !!sub;
    }
  } catch (e) { /* ignore */ }
  return { supported: true, subscribed, permission: Notification.permission };
}

// Returns true if subscribed successfully.
export async function subscribePush() {
  if (!pushSupported()) throw new Error("Browser tidak mendukung notifikasi push.");
  const permission = await Notification.requestPermission();
  if (permission !== "granted") throw new Error("Izin notifikasi ditolak.");

  const { key, configured } = await api.get("/push/vapid-public-key");
  if (!configured || !key) throw new Error("Server belum dikonfigurasi untuk push.");

  const reg = await getRegistration();
  await navigator.serviceWorker.ready;
  let sub = await reg.pushManager.getSubscription();
  if (!sub) {
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(key),
    });
  }
  await api.post("/push/subscribe", { subscription: sub.toJSON() });
  return true;
}

export async function unsubscribePush() {
  const reg = await navigator.serviceWorker.getRegistration();
  if (!reg) return true;
  const sub = await reg.pushManager.getSubscription();
  if (sub) {
    try { await api.post("/push/unsubscribe", { endpoint: sub.endpoint }); } catch (e) { /* ignore */ }
    await sub.unsubscribe();
  }
  return true;
}

// Silent refresh on login if user already granted permission.
export async function ensurePushSubscribed() {
  try {
    if (pushSupported() && Notification.permission === "granted") {
      await subscribePush();
    }
  } catch (e) { /* silent */ }
}
