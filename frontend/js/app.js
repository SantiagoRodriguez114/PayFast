import { register, login, logout } from "./auth.js";
import { createWallet, getWallet } from "./api.js";

const $ = (selector) => document.querySelector(selector);

const authView = $("#auth-view");
const dashboardView = $("#dashboard-view");
const loginForm = $("#login-form");
const registerForm = $("#register-form");

const showLoginButton = $("#show-login");
const showRegisterButton = $("#show-register");
const logoutButton = $("#logout-btn");

const notification = $("#notification");

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
  } catch (error) {
    if (error.status === 404) {
      empty.classList.remove("hidden");
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

/**
 * Cierre de sesión.
 */
logoutButton.addEventListener("click", () => {
  logout();

  dashboardView.classList.add("hidden");
  authView.classList.remove("hidden");
  logoutButton.classList.add("hidden");

  showAuthTab("login");

  notify("Sesión cerrada.");
});

// Estado inicial de la aplicación.
showAuthTab("login");