/**
 * api.js — Capa de acceso al backend de PayFast.
 *
 * Centraliza el manejo del token JWT y las llamadas HTTP. El resto de la
 * aplicación nunca usa fetch directamente: siempre pasa por apiRequest.
 */

/** URL base del backend. Se puede sobrescribir definiendo `window.PAYFAST_API_URL` antes de cargar app.js. */
const API_BASE_URL = window.PAYFAST_API_URL ?? "http://127.0.0.1:8000";

// Función a ejecutar cuando el backend responde 401 con una sesión activa.
let unauthorizedHandler = () => {};

/** Se invoca cuando una sesión activa recibe HTTP 401 (token vencido). */
export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
}

/** Token JWT de la sesión. Vive solo en memoria: recargar la página cierra la sesión. */
let accessToken = null;

/**
 * Guarda el token JWT que se enviará en cada petición.
 * @param {string} token Token devuelto por /auth/login.
 */
export function setAccessToken(token) {
  accessToken = token;
}

/** Elimina el token de memoria (cierre de sesión). */
export function clearAccessToken() {
  accessToken = null;
}

/** @returns {boolean} true si hay un token activo en memoria. */
export function hasSession() {
  return Boolean(accessToken);
}

/**
 * Envía una petición al backend y devuelve el JSON de la respuesta.
 * Agrega Content-Type y Authorization automáticamente.
 * Ante un error HTTP lanza un Error con el mensaje del backend (`detail`)
 * y el código en `error.status`; un 401 con sesión activa dispara el
 * manejador registrado con setUnauthorizedHandler.
 *
 * @param {string} path Ruta del endpoint, p. ej. "/wallets/me".
 * @param {RequestInit} [options] Opciones de fetch (method, body...).
 * @returns {Promise<any>} Cuerpo JSON de la respuesta.
 */
export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers);

  if (options.body !== undefined && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error(
      "No fue posible conectar con PayFast. Comprueba que el backend esté ejecutándose."
    );
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 && accessToken) {
      unauthorizedHandler();
    }

    let message = "No fue posible completar la operación.";

    if (typeof data?.detail === "string") {
      message = data.detail;
    } else if (Array.isArray(data?.detail)) {
      message = data.detail
        .map((item) => item.msg)
        .filter(Boolean)
        .join(". ");
    }

    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return data;
}

/**
 * POST /auth/register. No devuelve token: hay que iniciar sesión después.
 * @param {{nombre:string, correo:string, password:string, rol:string}} datos
 */
export function registerUser(datos) {
  return apiRequest("/auth/register", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

/**
 * POST /auth/login.
 * @param {{correo:string, password:string}} datos
 * @returns {Promise<{access_token:string, token_type:string}>}
 */
export function loginUser(datos) {
  return apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

/** GET /auth/me. Devuelve el perfil público del usuario autenticado. */
export function getCurrentUser() {
  return apiRequest("/auth/me");
}

/** POST /wallets/. Crea la billetera principal (saldo inicial 0). Responde 409 si ya existe. */
export function createWallet() {
  return apiRequest("/wallets/", {
    method: "POST",
  });
}

/** GET /wallets/me. Devuelve la billetera del usuario; 404 si todavía no tiene. */
export function getWallet() {
  return apiRequest("/wallets/me");
}

/**
 * POST /wallets/me/top-up. Acredita saldo ficticio (solo demostración).
 * El backend exige monto > 0, máximo 2 decimales y tope de 10.000.000;
 * responde 403 si ENABLE_DEMO_TOPUPS está desactivado.
 * @param {string} monto Monto en COP como texto (evita errores de punto flotante).
 * @returns {Promise<object>} Billetera actualizada.
 */
export function topUpWallet(monto) {
  return apiRequest("/wallets/me/top-up", {
    method: "POST",
    body: JSON.stringify({ monto }),
  });
}


/* Solicitudes del emprendedor */

/** GET /credit-requests/me. Solicitudes del emprendedor autenticado. */
export function getMyCreditRequests() {
  return apiRequest("/credit-requests/me");
}

/**
 * POST /credit-requests/. Crea una solicitud (estado PENDIENTE_EVALUACION).
 * @param {{monto:string, plazo_meses:number, proposito:string}} datos
 */
export function createCreditRequest(datos) {
  return apiRequest("/credit-requests/", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

/** GET /credit-requests/{id}/risk-evaluations. Historial de evaluaciones, la más reciente primero. */
export function getRiskEvaluations(requestId) {
  return apiRequest(
    `/credit-requests/${encodeURIComponent(requestId)}/risk-evaluations`
  );
}

/**
 * POST /credit-requests/{id}/risk-evaluations. Consulta el buró simulado.
 * Si el buró falla responde 201 con resultado "FALLIDA" y el estado no cambia.
 */
export function evaluateCreditRequest(requestId) {
  return apiRequest(
    `/credit-requests/${encodeURIComponent(requestId)}/risk-evaluations`,
    { method: "POST" }
  );
}

/** POST /credit-requests/{id}/disburse. Acredita el crédito FINANCIADO en la billetera del emprendedor. */
export function disburseCredit(requestId) {
  return apiRequest(
    `/credit-requests/${encodeURIComponent(requestId)}/disburse`,
    { method: "POST" }
  );
}

/* Catálogo y financiación del prestamista */

/**
 * GET /credit-requests/eligible. Catálogo para prestamistas.
 * @param {{q?:string, monto_min?:string, monto_max?:string, plazo_min?:string, plazo_max?:string}} filters
 *   Los filtros vacíos se omiten de la consulta.
 */
export function getEligibleRequests(filters = {}) {
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(filters)) {
    if (value !== "" && value !== null && value !== undefined) {
      params.set(key, value);
    }
  }

  const query = params.toString();

  return apiRequest(
    `/credit-requests/eligible${query ? `?${query}` : ""}`
  );
}

/**
 * POST /credit-requests/{id}/contributions. Aporta fondos desde la billetera del prestamista.
 * @param {string} requestId Identificador de la solicitud.
 * @param {string} monto Monto del aporte en COP.
 */
export function contributeToRequest(requestId, monto) {
  return apiRequest(
    `/credit-requests/${encodeURIComponent(requestId)}/contributions`,
    {
      method: "POST",
      body: JSON.stringify({ monto }),
    }
  );
}

/* Historial de movimientos */

/** GET /credit-requests/transactions/me. Transacciones (desembolsos) de las billeteras del usuario. */
export function getMyTransactions() {
  return apiRequest("/credit-requests/transactions/me");
}

/**
 * Consulta el historial unificado de la billetera:
 * recargas, aportes y desembolsos.
 */
export function getWalletMovements() {
  return apiRequest("/wallets/me/movements");
}