/**
 * app.js — Punto de entrada de la interfaz de PayFast.
 *
 * Controla la vista de acceso (login y registro), el panel principal
 * (perfil y billetera, incluida la recarga de demostración) y delega
 * el módulo de financiación en financing.js.
 */

import { register, login, logout } from "./auth.js";
import {
  createWallet,
  getWallet,
  topUpWallet,
  setUnauthorizedHandler,
} from "./api.js";
import {
  initializeFinancing,
  loadFinancingForUser,
  resetFinancingView,
  setWalletState,
  loadTransactions,
} from "./financing.js";

/** Atajo para document.querySelector. */
const $ = (selector) => document.querySelector(selector);

// Referencias a los elementos principales de la interfaz.
const authView = $("#auth-view");
const dashboardView = $("#dashboard-view");
const loginForm = $("#login-form");
const registerForm = $("#register-form");

const showLoginButton = $("#show-login");
const showRegisterButton = $("#show-register");
const logoutButton = $("#logout-btn");

const notification = $("#notification");

/** Temporizador del aviso activo, para reiniciarlo si llega otro. */
let notificationTimeout = null;

/**
 * Muestra mensajes de éxito o error.
 */
function notify(message, type = "success") {
  notification.textContent = message;
  notification.classList.remove("hidden", "error");

  if (type === "error") {
    notification.classList.add("error");
  }

  if (notificationTimeout !== null) {
    clearTimeout(notificationTimeout);
  }

  notificationTimeout = setTimeout(() => {
    notification.classList.add("hidden");
  }, 6000);
}

/**
 * Impide enviar varias veces el mismo formulario
 * mientras se procesa la petición.
 */
async function withLoading(button, callback) {
  const originalText = button.textContent;

  button.disabled = true;
  button.textContent = "Procesando...";

  try {
    return await callback();
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

/**
 * Cambia entre los formularios de acceso.
 */
function showAuthTab(tab) {
  const isLogin = tab === "login";

  loginForm.classList.toggle("hidden", !isLogin);
  registerForm.classList.toggle("hidden", isLogin);

  showLoginButton.classList.toggle("active", isLogin);
  showRegisterButton.classList.toggle("active", !isLogin);

  showLoginButton.setAttribute("aria-selected", String(isLogin));
  showRegisterButton.setAttribute("aria-selected", String(!isLogin));
}

showLoginButton.addEventListener("click", () => {
  showAuthTab("login");
});

showRegisterButton.addEventListener("click", () => {
  showAuthTab("register");
});

/**
 * Muestra los datos públicos del usuario autenticado.
 * Se utiliza textContent para evitar interpretar
 * información del usuario como HTML.
 */
function renderProfile(user) {
  const role = user.roles?.[0] ?? "usuario";

  $("#welcome-title").textContent = `Hola, ${user.nombre}`;
  $("#profile-name").textContent = user.nombre;
  $("#profile-email").textContent = user.correo;
  $("#profile-role").textContent = user.roles.join(", ");
  $("#profile-status").textContent = user.activo ? "Activo" : "Inactivo";
  $("#role-badge").textContent = role;

  if (user.roles.includes("emprendedor")) {
    $("#role-description").textContent =
      "Como emprendedor podrás crear solicitudes de crédito, consultar " +
      "su evaluación y gestionar los desembolsos de tus proyectos.";
  } else if (user.roles.includes("prestamista")) {
    $("#role-description").textContent =
      "Como prestamista podrás consultar solicitudes elegibles " +
      "y participar en su financiación mediante aportes simulados.";
  } else {
    $("#role-description").textContent =
      "Consulta las funcionalidades disponibles para tu cuenta.";
  }
}

/**
 * Cambia a la vista principal después de iniciar sesión.
 */
async function openDashboard(user) {
  renderProfile(user);

  authView.classList.add("hidden");
  dashboardView.classList.remove("hidden");
  logoutButton.classList.remove("hidden");

  await loadWallet();

  try {
    await loadFinancingForUser(user);
  } catch (error) {
    notify(error.message, "error");
  }
}

/**
 * Formatea el saldo usando la moneda de la billetera.
 */
function formatMoney(amount, currency = "COP") {
  const numericAmount = Number(amount);

  if (!Number.isFinite(numericAmount)) {
    return "Saldo no disponible";
  }

  try {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(numericAmount);
  } catch {
    return `${numericAmount.toFixed(2)} ${currency}`;
  }
}

/**
 * Muestra una vista previa del monto sin modificar el valor
 * que posteriormente se envía a la API.
 */
function attachMoneyPreview(input) {
  if (!input || input.dataset.moneyPreviewAttached) return;

  input.dataset.moneyPreviewAttached = "true";

  const preview = document.createElement("small");
  preview.className = "money-preview";
  preview.setAttribute("aria-live", "polite");

  input.insertAdjacentElement("afterend", preview);

  function update() {
    const value = input.value.trim();

    if (!value) {
      preview.textContent = "Monto: $ 0,00 COP";
      preview.classList.remove("invalid");
      return;
    }

    if (!/^\d+(\.\d{1,2})?$/.test(value)) {
      preview.textContent = "Introduce un monto válido (máximo 2 decimales).";
      preview.classList.add("invalid");
      return;
    }

    preview.textContent = `Monto: ${formatMoney(value)}`;
    preview.classList.remove("invalid");
  }

  input.addEventListener("input", update);
  input.addEventListener("change", update);
  update();
}

attachMoneyPreview($("#topup-amount"));
attachMoneyPreview($("#credit-amount"));

/**
 * Consulta la billetera del usuario.
 *
 * Un HTTP 404 indica que todavía no tiene billetera.
 * Otros errores se muestran sin confundirlos con ese caso.
 */
async function loadWallet() {
  const loading = $("#wallet-loading");
  const empty = $("#wallet-empty");
  const content = $("#wallet-content");

  loading.classList.remove("hidden");
  empty.classList.add("hidden");
  content.classList.add("hidden");

  try {
    const wallet = await getWallet();

    $("#wallet-balance").textContent = formatMoney(
      wallet.saldo,
      wallet.moneda
    );

    $("#wallet-currency").textContent = wallet.moneda;
    $("#wallet-status").textContent = wallet.activa
      ? "Activa"
      : "Inactiva";

    content.classList.remove("hidden");
    // Una billetera existente no basta: debe estar activa para solicitar,
    // aportar o recargar (el backend rechaza esas operaciones si no lo está).
    setWalletState(true, wallet.activa);
    setTopupControls(
      wallet.activa,
      wallet.activa ? "" : "Tu billetera está inactiva: no puedes recargar saldo."
    );
  } catch (error) {
    if (error.status === 404) {
      empty.classList.remove("hidden");
      setWalletState(false);
    } else {
      notify(error.message, "error");
    }
  } finally {
    loading.classList.add("hidden");
  }
}

/**
 * Registro de usuario.
 *
 * Después del registro se muestra el formulario de login,
 * ya que /auth/register no devuelve un token JWT.
 */
registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const button = registerForm.querySelector('[type="submit"]');

  const datos = {
    nombre: $("#register-name").value,
    correo: $("#register-email").value,
    password: $("#register-password").value,
    rol: $("#register-role").value,
  };

  try {
    await withLoading(button, () => register(datos));

    const email = datos.correo.trim().toLowerCase();

    registerForm.reset();
    showAuthTab("login");

    $("#login-email").value = email;
    $("#login-password").value = "";

    notify("Cuenta creada correctamente. Ahora inicia sesión.");
  } catch (error) {
    notify(error.message, "error");
  }
});

/**
 * Inicio de sesión.
 */
loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const button = loginForm.querySelector('[type="submit"]');

  try {
    await withLoading(button, async () => {
      const user = await login({
        correo: $("#login-email").value,
        password: $("#login-password").value,
      });

      loginForm.reset();
      await openDashboard(user);
    });

    notify("Sesión iniciada correctamente.");
  } catch (error) {
    notify(error.message, "error");
  }
});

/**
 * Creación de la billetera principal.
 */
$("#create-wallet-btn").addEventListener("click", async (event) => {
  const button = event.currentTarget;

  try {
    await withLoading(button, async () => {
      await createWallet();
      await loadWallet();
    });

    notify("Tu billetera fue creada correctamente.");
  } catch (error) {
    if (error.status === 409) {
      await loadWallet();
    }

    notify(error.message, "error");
  }
});

/**
 * Actualización manual del saldo.
 */
$("#refresh-wallet-btn").addEventListener("click", async (event) => {
  const button = event.currentTarget;

  try {
    await withLoading(button, loadWallet);
  } catch (error) {
    notify(error.message, "error");
  }
});

/** Tope por recarga que acepta el backend (COP). */
const MAX_TOPUP = 10_000_000;

/** true cuando el servidor respondió 403: las recargas de demostración están apagadas. */
let topupDisabled = false;

/** Aviso que se muestra cuando el servidor tiene las recargas apagadas. */
const TOPUP_SERVER_OFF = "Las recargas de demostración están deshabilitadas en este servidor.";

/**
 * Activa o desactiva los controles de recarga y muestra un aviso opcional.
 * Si el servidor tiene las recargas apagadas (topupDisabled) nunca se
 * activan, aunque la billetera esté en buen estado.
 * @param {boolean} enabled Si la billetera permite recargar.
 * @param {string} [notice] Motivo a mostrar; vacío oculta el aviso.
 */
function setTopupControls(enabled, notice = "") {
  const active = enabled && !topupDisabled;

  $("#topup-amount").disabled = !active;
  $("#topup-btn").disabled = !active;
  document
    .querySelectorAll(".topup-preset")
    .forEach((button) => (button.disabled = !active));

  const text = topupDisabled ? TOPUP_SERVER_OFF : notice;
  const note = $("#topup-disabled");

  note.textContent = text;
  note.classList.toggle("hidden", !text);
}

/** Marca las recargas como apagadas por el servidor (HTTP 403) y bloquea el formulario. */
function disableTopup() {
  topupDisabled = true;
  setTopupControls(false);
}

/** Los botones de monto rápido solo rellenan el campo; no envían nada. */
document.querySelectorAll(".topup-preset").forEach((button) => {
  button.addEventListener("click", () => {
    $("#topup-amount").value = button.dataset.amount;
  });
});

/**
 * Recarga de saldo ficticio (POST /wallets/me/top-up).
 * Valida el monto en el cliente, acredita y vuelve a consultar la billetera.
 */
$("#topup-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  if (topupDisabled) {
    return;
  }

  // currentTarget vale null después de un await: se guarda antes.
  const form = event.currentTarget;
  const monto = $("#topup-amount").value.trim();

  if (!/^\d+(\.\d{1,2})?$/.test(monto) || Number(monto) <= 0) {
    notify("El monto debe ser mayor que cero y tener máximo dos decimales.", "error");
    return;
  }

  if (Number(monto) > MAX_TOPUP) {
    notify(`El máximo por recarga es ${formatMoney(MAX_TOPUP)}.`, "error");
    return;
  }

  try {
    await withLoading($("#topup-btn"), () => topUpWallet(monto));

    form.reset();

    // La recarga ya fue acreditada: se confirma primero y después se
    // refresca el saldo, para que un fallo de esa consulta no parezca
    // una recarga fallida.
    notify(`Recarga de ${formatMoney(monto)} acreditada.`);

    // La recarga ya fue confirmada por el backend.
    // Actualizamos el saldo y el historial por separado.
    await Promise.allSettled([
      loadWallet(),
      loadTransactions(),
    ]);
  } catch (error) {
    if (error.status === 403) {
      disableTopup();
    }

    notify(error.message, "error");
  }
});

/**
 * Cierra la sesión del navegador y vuelve a la pantalla de acceso.
 * Lo usan el botón "Cerrar sesión" y el manejador de token vencido (401).
 * @param {string} message Aviso a mostrar.
 * @param {"success"|"error"} [type]
 */
function closeSession(message, type = "success") {
  logout();
  resetFinancingView();

  dashboardView.classList.add("hidden");
  authView.classList.remove("hidden");
  logoutButton.classList.add("hidden");

  $("#wallet-balance").textContent = "$0,00";

  showAuthTab("login");
  notify(message, type);
}

logoutButton.addEventListener("click", () => {
  closeSession("Sesión cerrada.");
});

// El token vence a los 30 minutos: se vuelve al login con un aviso claro.
setUnauthorizedHandler(() => {
  closeSession("Tu sesión expiró. Inicia sesión de nuevo.", "error");
});

// Estado inicial de la aplicación.
showAuthTab("login");

initializeFinancing({
  notify,
  reloadWallet: loadWallet,
});