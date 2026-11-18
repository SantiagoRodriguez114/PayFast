const API_BASE_URL = "http://127.0.0.1:8000";

let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function clearAccessToken() {
  accessToken = null;
}

export function hasSession() {
  return Boolean(accessToken);
}

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

export function registerUser(datos) {
  return apiRequest("/auth/register", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function loginUser(datos) {
  return apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function getCurrentUser() {
  return apiRequest("/auth/me");
}

export function createWallet() {
  return apiRequest("/wallets/", {
    method: "POST",
  });
}

export function getWallet() {
  return apiRequest("/wallets/me");
}