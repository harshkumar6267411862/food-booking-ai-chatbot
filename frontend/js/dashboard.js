/**
 * dashboard.js — MunchBot Admin Dashboard
 * Kanban board logic: polling, rendering, state transitions, modals, toasts.
 */

// ── State ─────────────────────────────────────────────────────────────────────
// We maintain a local snapshot of all active orders so the board is accurate
// between polling cycles. Orders move through columns as actions are performed.
const STATE = {
  orders: {},       // id → order object
  otpMap: {},       // id → plain-text OTP (only set when admin marks ready)
  pollingTimer: null,
  pendingOtpModal: null,  // { orderId }
  pendingCancelModal: null, // { orderId }
};

// ── DOM refs ─────────────────────────────────────────────────────────────────
const cols = {
  PENDING:   document.getElementById("col-PENDING"),
  CONFIRMED: document.getElementById("col-CONFIRMED"),
  PREPARING: document.getElementById("col-PREPARING"),
  READY:     document.getElementById("col-READY"),
};
const counts = {
  PENDING:   document.getElementById("cnt-PENDING"),
  CONFIRMED: document.getElementById("cnt-CONFIRMED"),
  PREPARING: document.getElementById("cnt-PREPARING"),
  READY:     document.getElementById("cnt-READY"),
};
const stats = {
  PENDING:   document.getElementById("stat-PENDING"),
  CONFIRMED: document.getElementById("stat-CONFIRMED"),
  PREPARING: document.getElementById("stat-PREPARING"),
  READY:     document.getElementById("stat-READY"),
};

const otpModal    = document.getElementById("otpModal");
const cancelModal = document.getElementById("cancelModal");
const lastUpdEl   = document.getElementById("lastUpdated");
const refreshBtn  = document.getElementById("refreshBtn");
const toastCont   = document.getElementById("toastContainer");

/* ── Operations Panel ───────────────────────────────────────── */

const todayDateEl = document.getElementById("todayDate");

const generateSlotsBtn =
    document.getElementById("generateSlotsBtn");

// ── Init ─────────────────────────────────────────────────────────────────────
Auth.requireAuth();

// Redirect if profile not yet complete (new admin first login)
if (!Auth.getProfileComplete()) {
  window.location.href = "/admin-dashboard/setup.html";
}

document.getElementById("adminName").textContent = Auth.getAdminName();
document.getElementById("adminInitial").textContent = Auth.getAdminName().charAt(0).toUpperCase();
document.getElementById("logoutBtn").addEventListener("click", Auth.logout);

// Show stall name in header if available
const stallName = Auth.getStallName();
const stallNameEl = document.getElementById("stallNameDisplay");
if (stallNameEl) {
  stallNameEl.textContent = stallName ? `🏪 ${stallName}` : "";
}

// OTP modal — digit-by-digit navigation
const otpInputs = document.querySelectorAll(".otp-digit");
otpInputs.forEach((inp, i) => {
  inp.addEventListener("input", () => {
    inp.value = inp.value.replace(/\D/g, "").slice(-1);
    if (inp.value && i < otpInputs.length - 1) otpInputs[i + 1].focus();
  });
  inp.addEventListener("keydown", (e) => {
    if (e.key === "Backspace" && !inp.value && i > 0) otpInputs[i - 1].focus();
  });
});

document.getElementById("otpCancelBtn").addEventListener("click", closeOtpModal);
document.getElementById("otpSubmitBtn").addEventListener("click", handleVerifyOTP);
document.getElementById("cancelCancelBtn").addEventListener("click", closeCancelModal);
document.getElementById("cancelSubmitBtn").addEventListener("click", handleCancelOrder);
refreshBtn.addEventListener("click", () => refresh(true));

generateSlotsBtn.addEventListener(
    "click",
    generatePickupSlots
);


// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(msg, type = "info") {
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span class="toast-icon">${icons[type]}</span><span class="toast-msg">${msg}</span>`;
  toastCont.appendChild(el);
  setTimeout(() => {
    el.classList.add("fade-out");
    setTimeout(() => el.remove(), 400);
  }, 3500);
}

// ── Refresh logic ─────────────────────────────────────────────────────────────
async function refresh(manual = false) {
  if (manual) {
    refreshBtn.classList.add("spinning");
  }

  try {
    // Fire auto-cancel cron silently
    API.autoCancelCron().catch(() => {});

    const pending = await API.getPendingOrders();

    // Merge into state — only add/update PENDING orders from server
    // We keep CONFIRMED/PREPARING/READY in memory (they were moved by our actions)
    (pending || []).forEach((o) => {
      if (!STATE.orders[o.id] || STATE.orders[o.id].status === "PENDING") {
        STATE.orders[o.id] = o;
      }
    });

    // Remove orders that are no longer pending on server and not in our local tracking
    const serverIds = new Set((pending || []).map((o) => o.id));
    Object.keys(STATE.orders).forEach((id) => {
      if (STATE.orders[id].status === "PENDING" && !serverIds.has(parseInt(id))) {
        delete STATE.orders[id];
      }
    });

    renderBoard();
    lastUpdEl.textContent = new Date().toLocaleTimeString("en-IN");
    if (manual) toast("Board refreshed!", "success");
  } catch (err) {
    if (manual) toast(err.message || "Failed to refresh", "error");
  } finally {
    refreshBtn.classList.remove("spinning");
  }
}

/* ────────────────────────────────────────────────────────────────
   Pickup Slot Generation
──────────────────────────────────────────────────────────────── */

async function generatePickupSlots() {

    const today =
        new Date().toISOString().split("T")[0];

    generateSlotsBtn.disabled = true;

    generateSlotsBtn.textContent =
        "Generating...";

    try {

        const result =
            await API.generatePickupSlots(today);

        toast(
            result.message ||
            "Pickup slots generated successfully!",
            "success"
        );

        await refresh();

    }
    catch (err) {

        toast(
            err.message,
            "error"
        );

    }
    finally {

        generateSlotsBtn.disabled = false;

        generateSlotsBtn.textContent =
            "⚡ Generate Today's Slots";

    }

}

// ── Render ────────────────────────────────────────────────────────────────────
function renderBoard() {
  const buckets = { PENDING: [], CONFIRMED: [], PREPARING: [], READY: [] };

  Object.values(STATE.orders).forEach((o) => {
    if (buckets[o.status] !== undefined) buckets[o.status].push(o);
  });

  Object.entries(buckets).forEach(([status, orders]) => {
    const col = cols[status];
    col.innerHTML = "";

    if (counts[status]) counts[status].textContent = orders.length;
    if (stats[status])  stats[status].textContent  = orders.length;

    if (orders.length === 0) {
      col.innerHTML = `
        <div class="col-empty">
          <span class="empty-icon">🍽️</span>
          <p>No orders here</p>
        </div>`;
      return;
    }

    // Sort newest first
    orders.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    orders.forEach((o) => col.appendChild(buildCard(o)));
  });
}

function buildCard(order) {
  const card = document.createElement("div");
  card.className = "order-card";
  card.id = `card-${order.id}`;

  const itemsHtml = (order.items || [])
    .map((it) => `${it.menu_item_name || it.name} × ${it.quantity}`)
    .join("<br>");

  const slot = order.pickup_slot
    ? `${order.pickup_slot.start_time?.slice(0, 5)} – ${order.pickup_slot.end_time?.slice(0, 5)}`
    : "";

  let actionsHtml = "";
  let extraHtml   = "";

  if (order.status === "PENDING") {
    actionsHtml = `
      <button class="btn-action btn-confirm"  onclick="handleConfirm(${order.id})">✅ Confirm</button>
      <button class="btn-action btn-cancel"   onclick="openCancelModal(${order.id})">✕ Cancel</button>`;
  } else if (order.status === "CONFIRMED") {
    actionsHtml = `
      <button class="btn-action btn-prepare"  onclick="handlePrepare(${order.id})">🔥 Prepare</button>
      <button class="btn-action btn-cancel"   onclick="openCancelModal(${order.id})">✕ Cancel</button>`;
  } else if (order.status === "PREPARING") {
    actionsHtml = `
      <button class="btn-action btn-ready"    onclick="handleReady(${order.id})">🔔 Mark Ready</button>
      <button class="btn-action btn-cancel"   onclick="openCancelModal(${order.id})">✕ Cancel</button>`;
  } else if (order.status === "READY") {
    const otp = STATE.otpMap[order.id];
    if (otp) {
      extraHtml = `<div class="otp-badge">🔐 ${otp}</div>`;
    }
    actionsHtml = `<button class="btn-action btn-otp" onclick="openOtpModal(${order.id})">🔑 Verify OTP</button>`;
  }

  card.innerHTML = `
    <div class="card-header">
      <span class="order-number">${order.order_number || `#${order.id}`}</span>
      <span class="order-time">${timeAgo(order.created_at)}</span>
    </div>
    <div class="customer-name">${order.user?.name || "Student"}</div>
    <div class="customer-reg">${order.user?.registration_number || ""}</div>
    ${slot ? `<div class="slot-badge">🕐 ${slot}</div>` : ""}
    <div class="order-items">${itemsHtml || "No items"}</div>
    ${extraHtml}
    <div class="card-footer">
      <span class="order-amount">${formatCurrency(order.total_amount)}</span>
      <div class="card-actions">${actionsHtml}</div>
    </div>`;

  return card;
}

// ── Action handlers ───────────────────────────────────────────────────────────
async function handleConfirm(id) {
  disableCardButtons(id);
  try {
    const updated = await API.confirmOrder(id);
    STATE.orders[id] = updated;
    renderBoard();
    toast(`Order ${updated.order_number} confirmed!`, "success");
  } catch (err) {
    toast(err.message, "error");
    enableCardButtons(id);
  }
}

async function handlePrepare(id) {
  disableCardButtons(id);
  try {
    const updated = await API.prepareOrder(id);
    STATE.orders[id] = updated;
    renderBoard();
    toast(`Order ${updated.order_number} is now being prepared 🔥`, "info");
  } catch (err) {
    toast(err.message, "error");
    enableCardButtons(id);
  }
}

async function handleReady(id) {
  disableCardButtons(id);
  try {
    const res = await API.readyOrder(id);
    // res = { order: {...}, otp: "123456" }
    STATE.orders[id] = res.order;
    STATE.otpMap[id] = res.otp;
    renderBoard();
    toast(`Order ready! OTP: ${res.otp} — send to student via WhatsApp 📲`, "success");
  } catch (err) {
    toast(err.message, "error");
    enableCardButtons(id);
  }
}

// ── OTP Modal ─────────────────────────────────────────────────────────────────
function openOtpModal(orderId) {
  STATE.pendingOtpModal = { orderId };
  document.getElementById("otpOrderNum").textContent =
    STATE.orders[orderId]?.order_number || `#${orderId}`;
  otpInputs.forEach((i) => (i.value = ""));
  otpModal.classList.remove("hidden");
  otpInputs[0].focus();
}

function closeOtpModal() {
  otpModal.classList.add("hidden");
  STATE.pendingOtpModal = null;
}

async function handleVerifyOTP() {
  if (!STATE.pendingOtpModal) return;
  const { orderId } = STATE.pendingOtpModal;
  const otp = Array.from(otpInputs).map((i) => i.value).join("");

  if (otp.length !== 6) {
    toast("Please enter the full 6-digit OTP", "error");
    return;
  }

  const btn = document.getElementById("otpSubmitBtn");
  btn.disabled = true; btn.textContent = "Verifying…";

  try {
    const updated = await API.verifyOTP(orderId, otp);
    delete STATE.orders[orderId];
    delete STATE.otpMap[orderId];
    closeOtpModal();
    renderBoard();
    toast(`Order ${updated.order_number} completed! 🎉`, "success");
  } catch (err) {
    toast(err.message || "Invalid OTP", "error");
  } finally {
    btn.disabled = false; btn.textContent = "Complete Order";
  }
}

// ── Cancel Modal ──────────────────────────────────────────────────────────────
function openCancelModal(orderId) {
  STATE.pendingCancelModal = { orderId };
  document.getElementById("cancelOrderNum").textContent =
    STATE.orders[orderId]?.order_number || `#${orderId}`;
  document.getElementById("cancelReason").value = "";
  cancelModal.classList.remove("hidden");
  document.getElementById("cancelReason").focus();
}

function closeCancelModal() {
  cancelModal.classList.add("hidden");
  STATE.pendingCancelModal = null;
}

async function handleCancelOrder() {
  if (!STATE.pendingCancelModal) return;
  const { orderId } = STATE.pendingCancelModal;
  const reason = document.getElementById("cancelReason").value.trim();

  if (!reason) {
    toast("Please provide a cancellation reason", "error");
    return;
  }

  const btn = document.getElementById("cancelSubmitBtn");
  btn.disabled = true; btn.textContent = "Cancelling…";

  try {
    await API.cancelOrder(orderId, reason);
    delete STATE.orders[orderId];
    closeCancelModal();
    renderBoard();
    toast("Order cancelled successfully", "info");
  } catch (err) {
    toast(err.message || "Cancellation failed", "error");
  } finally {
    btn.disabled = false; btn.textContent = "Cancel Order";
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function disableCardButtons(id) {
  const card = document.getElementById(`card-${id}`);
  if (!card) return;
  card.querySelectorAll(".btn-action").forEach((b) => (b.disabled = true));
}

function enableCardButtons(id) {
  const card = document.getElementById(`card-${id}`);
  if (!card) return;
  card.querySelectorAll(".btn-action").forEach((b) => (b.disabled = false));
}

// ── Reset Code Modal Handlers ─────────────────────────────────────────────
const resetCodeModal = document.getElementById("resetCodeModal");
const resetCodeCloseBtn = document.getElementById("resetCodeCloseBtn");
if (resetCodeCloseBtn) {
  resetCodeCloseBtn.addEventListener("click", () => {
    if (resetCodeModal) resetCodeModal.classList.add("hidden");
  });
}

async function handleResetAdminCode(userId, regNum, stallName) {
  if (!confirm(`Are you sure you want to generate a new login code for ${regNum} (${stallName || 'Unassigned'})?`)) {
    return;
  }
  try {
    const res = await API.resetAdminLoginCode(userId);
    document.getElementById("resetCodeRegNum").textContent = res.registration_number;
    document.getElementById("resetCodeStall").textContent = res.stall_name || "Unassigned";
    document.getElementById("resetCodeDisplay").textContent = res.new_login_code;
    resetCodeModal.classList.remove("hidden");
    toast(`Reset code generated for ${res.registration_number}`, "success");
    loadSuperAdminPanel();
  } catch (err) {
    toast(err.message || "Failed to reset code", "error");
  }
}

async function loadSuperAdminPanel() {
  const tableBody = document.getElementById("adminTableBody");
  if (!tableBody) return;
  tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem;">Loading admin list...</td></tr>`;

  try {
    const admins = await API.getAllAdmins();
    if (!admins || admins.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color: var(--text-secondary);">No registered stall admins found.</td></tr>`;
      return;
    }

    tableBody.innerHTML = admins
      .map(
        (a) => `
        <tr>
          <td><strong style="font-family: monospace; color: var(--accent-primary);">${a.registration_number}</strong></td>
          <td>${a.stall_name ? `🏪 <strong>${a.stall_name}</strong>` : '<span style="color: var(--text-muted);">Unassigned</span>'}</td>
          <td>
            <div><strong>${a.name || "Pending Setup"}</strong></div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">${a.phone_number || "-"}</div>
          </td>
          <td>
            <span class="badge-status ${a.profile_complete ? "complete" : "pending"}">
              ${a.profile_complete ? "Active" : "Setup Pending"}
            </span>
          </td>
          <td style="font-size: 0.85rem; color: var(--text-secondary);">${new Date(a.created_at).toLocaleDateString("en-IN")}</td>
          <td>
            <button class="btn-reset-code" onclick="handleResetAdminCode(${a.id}, '${a.registration_number}', '${a.stall_name || ""}')">
              🔑 Reset Login Code
            </button>
          </td>
        </tr>
      `
      )
      .join("");
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color: var(--status-cancelled);">Error: ${err.message}</td></tr>`;
  }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
(async () => {
  const isSuperAdmin = !Auth.getStallId();

  if (isSuperAdmin) {
    // Hide Stall Admin UI elements
    const opsPanel = document.querySelector(".operations-panel");
    const statsBar = document.querySelector(".stats-bar");
    const refreshBar = document.querySelector(".refresh-bar");
    const boardWrapper = document.getElementById("kanbanBoardWrapper");
    const superAdminPanel = document.getElementById("superAdminPanel");

    if (opsPanel) opsPanel.style.display = "none";
    if (statsBar) statsBar.style.display = "none";
    if (refreshBar) refreshBar.style.display = "none";
    if (boardWrapper) boardWrapper.style.display = "none";

    if (superAdminPanel) superAdminPanel.classList.remove("hidden");

    loadSuperAdminPanel();
  } else {
    // Stall Admin Mode
    todayDateEl.textContent = new Date().toLocaleDateString("en-IN", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });

    Object.values(cols).forEach((col) => {
      col.innerHTML = `
        <div class="skeleton skeleton-card"></div>
        <div class="skeleton skeleton-card"></div>`;
    });

    await refresh();

    // Auto-refresh every 30 seconds for Stall Admins
    STATE.pollingTimer = setInterval(() => refresh(), 30_000);
  }
})();

