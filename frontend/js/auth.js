import {
  registerUser,
  loginUser,
  getCurrentUser,
  setAccessToken,
  clearAccessToken,
} from "./api.js";

/**
 * Registra una cuenta nueva.
 * El backend exige nombre, correo, contraseña y rol.
 */
export async function register(datos) {
  const nombre = datos.nombre.trim();
  const correo = datos.correo.trim().toLowerCase();

  if (nombre.length < 2 || nombre.length > 120) {
    throw new Error("El nombre debe tener entre 2 y 120 caracteres.");
  }

  if (datos.password.length < 8 || datos.password.length > 128) {
    throw new Error("La contraseña debe tener entre 8 y 128 caracteres.");
  }

  if (!["emprendedor", "prestamista"].includes(datos.rol)) {
    throw new Error("Selecciona un tipo de cuenta válido.");
  }

  return registerUser({
    nombre,
    correo,
    password: datos.password,
    rol: datos.rol,
  });
}

/**
 * Inicia sesión y obtiene el perfil autenticado.
 * Si la consulta del perfil falla, descarta el token.
 */
export async function login(datos) {
  const response = await loginUser({
    correo: datos.correo.trim().toLowerCase(),
    password: datos.password,
  });

  if (!response.access_token) {
    throw new Error("El servidor no devolvió un token de acceso.");
  }

  setAccessToken(response.access_token);

  try {
    return await getCurrentUser();
  } catch (error) {
    clearAccessToken();
    throw error;
  }
}

/**
 * Cierra la sesión del navegador.
 *
 * El backend actual no dispone de un endpoint para revocar JWT.
 * El token se elimina de la memoria del frontend.
 */
export function logout() {
  clearAccessToken();
}