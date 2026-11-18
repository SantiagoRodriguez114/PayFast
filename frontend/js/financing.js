/**
 * financing.js — Módulo de financiación P2P.
 *
 * Emprendedor: crear solicitudes, evaluarlas y desembolsar.
 * Prestamista: explorar el catálogo y aportar.
 * Todo el contenido dinámico se construye con createElement/textContent.
 */

import {
  getMyCreditRequests,
  createCreditRequest,
  getRiskEvaluations,
  evaluateCreditRequest,
  disburseCredit,
  getEligibleRequests,
  contributeToRequest,
  getMyTransactions,
  getWalletMovements,
} from "./api.js";

/** Atajo para document.querySelector. */
const $ = (selector) => document.querySelector(selector);

// Dependencias inyectadas por app.js en initializeFinancing().
// notifyUser: muestra avisos; refreshWallet: recarga el saldo de la billetera.
// walletReady: indica si el usuario tiene billetera (la actualiza setWalletState).
let notifyUser = () => {};
let refreshWallet = async () => {};
let walletReady = true;

/** Nombre legible de cada estado de solicitud, evaluación o transacción (claves del backend). */
const ESTADOS = {
  PENDIENTE_EVALUACION: "Pendiente de evaluación",
  EVALUADA: "Evaluada",
  RECHAZADA: "Rechazada",
  EN_FINANCIACION: "En financiación",
  FINANCIADA: "Financiada",
  DESEMBOLSADA: "Desembolsada",
  PENDIENTE: "Pendiente",
  EXITOSA: "Exitosa",
  FALLIDA: "Fallida",
};

/** Texto de ayuda que se muestra al emprendedor según el estado de su solicitud. */
const AYUDA_ESTADO = {
  PENDIENTE_EVALUACION: "Evalúa la solicitud para que pueda recibir financiación.",
  EVALUADA: "Aprobada. Ya es visible para los prestamistas.",
  EN_FINANCIACION: "Está recibiendo aportes de prestamistas.",
  FINANCIADA: "Financiada por completo. Ya puedes desembolsar.",
  RECHAZADA: "No superó la evaluación de riesgo.",
  DESEMBOLSADA: "El dinero ya fue acreditado en tu billetera.",
};

/** Devuelve el nombre legible de un estado; si no lo conoce, devuelve el valor original. */
const label = (estado) => ESTADOS[estado] ?? estado ?? "Sin estado";

/**
 * Formatea un valor como pesos colombianos con dos decimales.
 * @param {string|number} value
 * @returns {string} p. ej. "$1.500.000,00", o "No disponible" si no es numérico.
 */
function money(value) {
  const amount = Number(value);

  return Number.isFinite(amount)
    ? new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(amount)
    : "No disponible";
}

/** Convierte una fecha ISO en texto local (es-CO); devuelve "" si no es válida. */
function dateText(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("es-CO");
}

// Positivo y con máximo dos decimales (regla del backend).
/**
 * Valida un monto: mayor que cero y con máximo dos decimales (regla del backend).
 * @param {string|number} value
 * @returns {boolean}
 */
function isValidAmount(value) {
  return /^\d+(\.\d{1,2})?$/.test(String(value).trim()) && Number(value) > 0;
}

/**
 * Crea un elemento con texto seguro. Se usa textContent (nunca innerHTML)
 * para que los datos del servidor no se interpreten como HTML.
 */
function createElement(tag, className = "", content = "") {
  const element = document.createElement(tag);

  if (className) {
    element.className = className;
  }

  element.textContent = String(content ?? "");
  return element;
}

/** Crea un párrafo secundario (<p class="item-meta">). */
function paragraph(text) {
  return createElement("p", "item-meta", text);
}

/** Crea la etiqueta de color de un estado (la clase status-<estado> define el color). */
function statusPill(estado) {
  const key = String(estado ?? "").toLowerCase();
  return createElement("span", `status-pill status-${key}`, label(estado));
}

/**
 * Crea un botón que ejecuta `action` desactivándose mientras corre.
 * Los errores se muestran como aviso en lugar de romper la interfaz.
 * @param {string} text Texto del botón.
 * @param {() => Promise<void>} action Acción asíncrona a ejecutar.
 * @param {string} [style] Clase de estilo (btn-outline o btn-primary).
 */
function makeButton(text, action, style = "btn-outline") {
  const button = createElement("button", `btn ${style}`, text);
  button.type = "button";

  button.addEventListener("click", async () => {
    button.disabled = true;

    try {
      await action();
    } catch (error) {
      notifyUser(error.message, "error");
    } finally {
      button.disabled = false;
    }
  });

  return button;
}

/** Reemplaza el contenido de una lista por un mensaje (cargando, vacío o error). */
function showListMessage(selector, message) {
  $(selector).replaceChildren(paragraph(message));
}

/** Aviso cuando la billetera existe pero está inactiva. */
const WALLET_INACTIVE_TEXT =
  "Tu billetera está inactiva: no puedes solicitar créditos ni aportar.";

/**
 * Registra el estado de la billetera. Sin una billetera activa el usuario
 * no puede solicitar créditos ni aportar, así que se avisa y se bloquea el envío.
 * @param {boolean} hasWallet Si el usuario ya tiene billetera.
 * @param {boolean} [isActive] Si esa billetera está activa (por defecto sí).
 */
export function setWalletState(hasWallet, isActive = true) {
  walletReady = hasWallet && isActive;

  document.querySelectorAll(".wallet-hint").forEach((hint) => {
    // Se guarda el texto original para restaurarlo cuando falte la billetera.
    hint.dataset.defaultText ??= hint.textContent;
    hint.textContent = hasWallet ? WALLET_INACTIVE_TEXT : hint.dataset.defaultText;
    hint.classList.toggle("hidden", walletReady);
  });

  $("#credit-submit-btn").disabled = !walletReady;
}

/* ---------- Emprendedor ---------- */

/**
 * Carga y dibuja las solicitudes del emprendedor (más recientes primero).
 * Según el estado ofrece: ver evaluaciones, evaluar (PENDIENTE_EVALUACION)
 * o desembolsar (FINANCIADA).
 */
export async function loadMyRequests() {
  showListMessage("#my-requests-list", "Cargando solicitudes...");

  try {
    const requests = await getMyCreditRequests();
    const container = $("#my-requests-list");

    container.replaceChildren();

    if (!requests.length) {
      container.append(
        paragraph("Todavía no tienes solicitudes. Crea la primera con el formulario.")
      );
      return;
    }

    const sorted = [...requests].sort(
      (a, b) => new Date(b.creada_en) - new Date(a.creada_en)
    );

    for (const request of sorted) {
      const card = createElement("article", "request-item");
      const heading = createElement("div", "item-heading");

      heading.append(
        createElement("strong", "", money(request.monto)),
        statusPill(request.estado)
      );

      card.append(
        heading,
        paragraph(request.proposito),
        paragraph(`Plazo: ${request.plazo_meses} meses`),
        paragraph(`Creada: ${dateText(request.creada_en)}`)
      );

      if (AYUDA_ESTADO[request.estado]) {
        card.append(createElement("p", "state-hint", AYUDA_ESTADO[request.estado]));
      }

      const actions = createElement("div", "item-actions");

      actions.append(
        makeButton("Ver evaluaciones", () => toggleEvaluations(request.id, card))
      );

      if (request.estado === "PENDIENTE_EVALUACION") {
        actions.append(
          makeButton(
            "Evaluar solicitud",
            async () => {
              const evaluation = await evaluateCreditRequest(request.id);

              if (evaluation.resultado === "EXITOSA") {
                notifyUser(`Evaluación completada. Puntaje: ${evaluation.puntaje}/100.`);
              } else {
                const detalle = evaluation.detalle_error
                  ? `: ${evaluation.detalle_error}`
                  : ".";
                notifyUser(
                  `La consulta al buró falló${detalle} Puedes reintentar.`,
                  "error"
                );
              }

              await loadMyRequests();
            },
            "btn-primary"
          )
        );
      }

      if (request.estado === "FINANCIADA") {
        actions.append(
          makeButton(
            "Desembolsar",
            async () => {
              const result = await disburseCredit(request.id);

              notifyUser(
                `Desembolso realizado. Nuevo saldo: ${money(result.nuevo_saldo_billetera)}.`
              );

              await Promise.all([
                loadMyRequests(),
                loadTransactions(),
                refreshWallet(),
              ]);
            },
            "btn-primary"
          )
        );
      }

      card.append(actions);
      container.append(card);
    }
  } catch (error) {
    showListMessage("#my-requests-list", error.message);
    notifyUser(error.message, "error");
  }
}

/**
 * Muestra u oculta el historial de evaluaciones de riesgo de una solicitud.
 * @param {string} requestId
 * @param {HTMLElement} card Tarjeta donde se inserta el detalle.
 */
async function toggleEvaluations(requestId, card) {
  const existing = card.querySelector(".evaluation-details");

  if (existing) {
    existing.remove();
    return;
  }

  const evaluations = await getRiskEvaluations(requestId);
  const details = createElement("div", "evaluation-details");

  if (!evaluations.length) {
    details.textContent = "Esta solicitud todavía no tiene evaluaciones.";
  } else {
    for (const evaluation of evaluations) {
      const entry = createElement("div", "evaluation-entry");

      entry.append(
        paragraph(`Fecha: ${dateText(evaluation.evaluada_en)}`),
        paragraph(`Resultado: ${label(evaluation.resultado)}`),
        paragraph(`Puntaje: ${evaluation.puntaje ?? "No disponible"}`)
      );

      if (evaluation.detalle_error) {
        entry.append(paragraph(`Error: ${evaluation.detalle_error}`));
      }

      details.append(entry);
    }
  }

  card.append(details);
}

/* ---------- Prestamista ---------- */

/** Lee los filtros del catálogo desde el formulario. Los campos vacíos quedan como "". */
function readCatalogFilters() {
  return {
    q: $("#filter-query").value.trim(),
    monto_min: $("#filter-min").value,
    monto_max: $("#filter-max").value,
    plazo_min: $("#filter-term-min").value,
    plazo_max: $("#filter-term-max").value,
  };
}

/** Comprueba que los mínimos no superen a los máximos; si no, avisa y devuelve false. */
function filtersAreConsistent(filters) {
  const { monto_min, monto_max, plazo_min, plazo_max } = filters;

  if (monto_min !== "" && monto_max !== "" && Number(monto_min) > Number(monto_max)) {
    notifyUser("El monto mínimo no puede ser mayor que el máximo.", "error");
    return false;
  }

  if (plazo_min !== "" && plazo_max !== "" && Number(plazo_min) > Number(plazo_max)) {
    notifyUser("El plazo mínimo no puede ser mayor que el máximo.", "error");
    return false;
  }

  return true;
}

/**
 * Carga y dibuja el catálogo de solicitudes elegibles para el prestamista.
 * Cada tarjeta incluye progreso de financiación y un formulario de aporte
 * validado en el cliente (monto positivo, máx. 2 decimales, sin superar el saldo pendiente).
 * @param {object} [filters] Filtros del catálogo; por defecto se leen del formulario.
 */
export async function loadEligibleRequests(filters = readCatalogFilters()) {
  showListMessage("#eligible-requests-list", "Cargando oportunidades...");

  try {
    const requests = await getEligibleRequests(filters);
    const container = $("#eligible-requests-list");

    container.replaceChildren();

    if (!requests.length) {
      container.append(
        paragraph("No hay solicitudes disponibles con esos filtros.")
      );
      return;
    }

    for (const request of requests) {
      const card = createElement("article", "catalog-card");

      const funded = Number(request.monto_financiado);
      const total = Number(request.monto);
      const progress =
        total > 0 ? Math.max(0, Math.min(100, (funded / total) * 100)) : 0;

      const track = createElement("div", "progress-track");
      track.setAttribute("role", "progressbar");
      track.setAttribute("aria-valuemin", "0");
      track.setAttribute("aria-valuemax", "100");
      track.setAttribute("aria-valuenow", String(Math.round(progress)));

      const fill = createElement("div", "progress-fill");
      fill.style.width = `${progress}%`;
      track.append(fill);

      card.append(
        createElement("h3", "", request.proposito),
        createElement("div", "amount", money(request.monto)),
        paragraph(`Plazo: ${request.plazo_meses} meses`),
        statusPill(request.estado),
        track,
        paragraph(`Financiado: ${money(request.monto_financiado)} (${Math.round(progress)}%)`),
        paragraph(`Pendiente: ${money(request.saldo_pendiente)}`)
      );

      const form = createElement("form", "contribution-form");
      const input = document.createElement("input");

      input.type = "number";
      input.min = "0.01";
      input.max = String(request.saldo_pendiente);
      input.step = "0.01";
      input.required = true;
      input.placeholder = "Monto del aporte";
      input.setAttribute("aria-label", `Aporte para ${request.proposito}`);

      const button = createElement("button", "btn btn-primary", "Aportar");
      button.type = "submit";

      form.append(input, button);

      form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const value = input.value.trim();

        if (!walletReady) {
          notifyUser("Necesitas una billetera activa para aportar.", "error");
          return;
        }

        if (!isValidAmount(value)) {
          notifyUser(
            "El aporte debe ser mayor que cero y tener máximo dos decimales.",
            "error"
          );
          return;
        }

        if (Number(value) > Number(request.saldo_pendiente)) {
          notifyUser("El aporte no puede superar el saldo pendiente.", "error");
          return;
        }

        button.disabled = true;

        try {
          await contributeToRequest(request.id, value);

          notifyUser(`Aporte de ${money(value)} registrado correctamente.`);

          await Promise.all([
            loadEligibleRequests(readCatalogFilters()),
            refreshWallet(),
            loadTransactions(),
          ]);
        } catch (error) {
          notifyUser(error.message, "error");
        } finally {
          button.disabled = false;
        }
      });

      card.append(form);
      container.append(card);
    }
  } catch (error) {
    showListMessage("#eligible-requests-list", error.message);
    notifyUser(error.message, "error");
  }
}

/* ---------- Movimientos ---------- */

/** Carga y dibuja los movimientos (desembolsos) del usuario, más recientes primero. */

/**
 * Muestra los movimientos de la billetera del usuario:
 * recargas, aportes y desembolsos.
 */
export async function loadTransactions() {
  showListMessage("#transactions-list", "Cargando movimientos...");

  try {
    const movements = await getWalletMovements();
    const container = $("#transactions-list");

    container.replaceChildren();

    if (!movements.length) {
      container.append(
        paragraph("Todavía no tienes movimientos registrados.")
      );
      return;
    }

    const sorted = [...movements].sort(
      (a, b) => new Date(b.fecha) - new Date(a.fecha)
    );

    const labels = {
      RECARGA: "Recarga de billetera",
      APORTE: "Aporte a crédito",
      DESEMBOLSO: "Desembolso de crédito",
    };

    for (const movement of sorted) {
      const card = createElement("article", "transaction-item");

      const isIncome = movement.direccion === "INGRESO";
      const isExpense = movement.direccion === "EGRESO";

      const sign = isIncome ? "+" : isExpense ? "−" : "";

      const amount = createElement(
        "strong",
        isIncome
          ? "movement-income"
          : isExpense
            ? "movement-expense"
            : "movement-neutral",
        `${sign}${money(movement.monto)}`
      );

      const heading = createElement("div", "item-heading");

      const title = createElement(
        "strong",
        "",
        labels[movement.tipo] ?? "Movimiento"
      );

      heading.append(title, amount);

      card.append(
        heading,
        statusPill(movement.estado)
      );

      if (movement.solicitud_id) {
        card.append(
          paragraph(
            `Solicitud: ${String(movement.solicitud_id).slice(0, 8)}`
          )
        );
      }

      if (movement.referencia) {
        card.append(
          paragraph(`Referencia: ${movement.referencia}`)
        );
      }

      if (movement.fecha) {
        card.append(
          paragraph(`Fecha: ${dateText(movement.fecha)}`)
        );
      }

      container.append(card);
    }
  } catch (error) {
    showListMessage("#transactions-list", error.message);
    notifyUser(error.message, "error");
  }
}


/* ---------- Inicialización ---------- */

/**
 * Registra los eventos del módulo y recibe las dependencias de app.js.
 * Debe llamarse una sola vez, después de que el DOM esté cargado.
 * @param {{notify: Function, reloadWallet: Function}} deps
 */
export function initializeFinancing({ notify, reloadWallet }) {
  notifyUser = notify;
  refreshWallet = reloadWallet;

  $("#credit-request-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    // event.currentTarget vale null después de un await: se guarda antes.
    const form = event.currentTarget;
    const button = $("#credit-submit-btn");

    const monto = $("#credit-amount").value.trim();
    const plazo = Number($("#credit-term").value);
    const proposito = $("#credit-purpose").value.trim();

    if (!isValidAmount(monto)) {
      notifyUser("El monto debe ser mayor que cero y tener máximo dos decimales.", "error");
      return;
    }

    if (!Number.isInteger(plazo) || plazo <= 0) {
      notifyUser("El plazo debe ser un número entero de meses.", "error");
      return;
    }

    if (!proposito) {
      notifyUser("Describe el propósito de la solicitud.", "error");
      return;
    }

    button.disabled = true;

    try {
      await createCreditRequest({ monto, plazo_meses: plazo, proposito });

      form.reset();
      notifyUser("Solicitud creada correctamente.");
      await loadMyRequests();
    } catch (error) {
      notifyUser(error.message, "error");
    } finally {
      button.disabled = !walletReady;
    }
  });

  $("#catalog-filters").addEventListener("submit", async (event) => {
    event.preventDefault();

    const filters = readCatalogFilters();

    if (filtersAreConsistent(filters)) {
      await loadEligibleRequests(filters);
    }
  });

  $("#clear-filters-btn").addEventListener("click", async () => {
    $("#catalog-filters").reset();
    await loadEligibleRequests({});
  });

  $("#refresh-requests-btn").addEventListener("click", () => loadMyRequests());
  $("#refresh-transactions-btn").addEventListener("click", () => loadTransactions());
}

/**
 * Muestra las secciones que corresponden al rol del usuario y carga sus datos.
 * Emprendedor: solicitudes y movimientos. Prestamista: catálogo de oportunidades.
 * @param {{roles?: string[]}} user Usuario autenticado.
 */
export async function loadFinancingForUser(user) {
  const roles = user.roles ?? [];

  const isEntrepreneur = roles.includes("emprendedor");
  const isLender = roles.includes("prestamista");

  $("#entrepreneur-section").classList.toggle("hidden", !isEntrepreneur);
  $("#lender-section").classList.toggle("hidden", !isLender);

  // Solo se registran desembolsos como transacciones; los aportes del
  // prestamista no aparecen en este historial.
  $("#transactions-section").classList.toggle(
    "hidden",
    !(isEntrepreneur || isLender)
  );

  const tasks = [];

  if (isEntrepreneur) {
    tasks.push(loadMyRequests());
  }

  if (isLender) {
    tasks.push(loadEligibleRequests({}));
  }

  if (isEntrepreneur || isLender) {
    tasks.push(loadTransactions());
  }

  await Promise.all(tasks);
}

/** Limpia listas, formularios y avisos al cerrar sesión. */
export function resetFinancingView() {
  walletReady = true;

  for (const id of ["entrepreneur-section", "lender-section", "transactions-section"]) {
    $(`#${id}`).classList.add("hidden");
  }

  $("#my-requests-list").replaceChildren();
  $("#eligible-requests-list").replaceChildren();
  $("#transactions-list").replaceChildren();

  $("#credit-request-form").reset();
  $("#catalog-filters").reset();

  document
    .querySelectorAll(".wallet-hint")
    .forEach((hint) => hint.classList.add("hidden"));

  $("#credit-submit-btn").disabled = false;
}