/**
 * api.js — MunchBot Admin Dashboard
 * Centralised API utilities: auth headers, request wrapper, endpoint calls.
 */

const BASE_URL = "";   // Same origin — FastAPI serves both API and frontend

// ── Token helpers ────────────────────────────────────────────────────────────
const Auth = {
  getToken: () => localStorage.getItem("mb_token"),
  setToken: (t) => localStorage.setItem("mb_token", t),
  removeToken: () => localStorage.removeItem("mb_token"),
  getAdminName: () => localStorage.getItem("mb_admin_name") || "Admin",
  setAdminName: (n) => localStorage.setItem("mb_admin_name", n),
  getStallName: () => localStorage.getItem("mb_stall_name") || "",
  setStallName: (s) => localStorage.setItem("mb_stall_name", s),
  getStallId: () => parseInt(localStorage.getItem("mb_stall_id") || "0") || null,
  setStallId: (id) => localStorage.setItem("mb_stall_id", id ?? ""),
  getProfileComplete: () => localStorage.getItem("mb_profile_complete") === "true",
  setProfileComplete: (v) => localStorage.setItem("mb_profile_complete", v ? "true" : "false"),
  isLoggedIn: () => !!localStorage.getItem("mb_token"),
  requireAuth: () => {
    if (!localStorage.getItem("mb_token")) {
      window.location.href = "/admin-dashboard/login.html";
    }
  },
  logout: () => {
    localStorage.removeItem("mb_token");
    localStorage.removeItem("mb_admin_name");
    localStorage.removeItem("mb_stall_name");
    localStorage.removeItem("mb_stall_id");
    localStorage.removeItem("mb_profile_complete");
    window.location.href = "/admin-dashboard/login.html";
  },
};

// ── Base fetch wrapper ────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const token = Auth.getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(BASE_URL + path, { ...options, headers });

  if (res.status === 401) {
    Auth.logout();
    return null;
  }

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const msg =
      data?.error?.message ||
      data?.detail ||
      `Request failed (${res.status})`;
    throw new Error(msg);
  }

  return data;
}

// ── Auth endpoints ────────────────────────────────────────────────────────────
const API = {
  login: async (registration_number, password) => {
    const form = new URLSearchParams({ username: registration_number, password });
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) throw new Error(data?.error?.message || data?.detail || "Login failed");
    return data; // { access_token, token_type }
  },

  me: () => apiFetch("/users/me"),

  // ── Orders ────────────────────────────────────────────────────────────────
  getPendingOrders: () => apiFetch("/admin/orders/pending"),

  // Fetch orders by individual statuses and merge
  getOrdersByStatus: async (statuses) => {
    // We'll fetch pending for now and get all orders via a broader call
    // Pending is the only bulk endpoint; individual status transitions update the UI
    const pending = await apiFetch("/admin/orders/pending");
    return pending || [];
  },

  confirmOrder:  (id) => apiFetch(`/admin/orders/${id}/confirm`,  { method: "PATCH" }),
  prepareOrder:  (id) => apiFetch(`/admin/orders/${id}/prepare`,  { method: "PATCH" }),
  readyOrder:    (id) => apiFetch(`/admin/orders/${id}/ready`,    { method: "PATCH" }),
  verifyOTP:     (id, otp) =>
    apiFetch(`/admin/orders/${id}/verify-otp`, {
      method: "POST",
      body: JSON.stringify({ otp }),
    }),
  cancelOrder: (id, reason) =>
    apiFetch(`/admin/orders/${id}/cancel`, {
      method: "PATCH",
      body: JSON.stringify({ cancel_reason: reason }),
    }),
  autoCancelCron: () =>
    apiFetch(
        "/admin/orders/cron/auto-cancel",
        {
            method: "POST",
        }
    ),

/* ==========================================================
   Pickup Slot Operations
========================================================== */

generatePickupSlots: (slotDate) =>
    apiFetch(
        "/admin/pickup-slots/generate",
        {
            method: "POST",
            body: JSON.stringify({
                slot_date: slotDate,
            }),
        }
    ),

/* ==========================================================
   Stall Operations
========================================================== */

  getStalls: () => apiFetch("/stalls/"),

  getUnassignedStalls: () => apiFetch("/admin/stalls/unassigned"),

  registerAdmin: (stallId) =>
    apiFetch(`/admin/register?stall_id=${stallId}`, { method: "POST" }),

  setupProfile: (name, phone_number) =>
    apiFetch("/admin/profile/setup", {
      method: "POST",
      body: JSON.stringify({ name, phone_number }),
    }),

  getMyStall: () => apiFetch("/admin/profile/stall"),

  getAllAdmins: () => apiFetch("/admin/list"),

  resetAdminLoginCode: (userId) =>
    apiFetch(`/admin/reset-login-code/${userId}`, { method: "POST" }),
};


// ── Formatting helpers ────────────────────────────────────────────────────────
function formatTime(isoString) {
  if (!isoString) return "";
  const d = new Date(isoString);
  return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

function formatCurrency(amount) {
  return `₹${parseFloat(amount).toFixed(2)}`;
}

function timeAgo(isoString) {
  if (!isoString) return "";
  const diff = Math.floor((Date.now() - new Date(isoString)) / 1000);
  if (diff < 60)  return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}
