from enum import StrEnum


class TransicionInvalida(Exception):
    """Se intentó pasar de un estado a otro que el negocio no permite."""


def _validar(transiciones, origen, destino):
    permitidos = transiciones.get(origen, set())
    if destino not in permitidos:
        raise TransicionInvalida(f"No se permite pasar de {origen} a {destino}")


class EstadoSolicitud(StrEnum):
    PENDIENTE_EVALUACION = "PENDIENTE_EVALUACION"
    EVALUADA = "EVALUADA"
    RECHAZADA = "RECHAZADA"
    EN_FINANCIACION = "EN_FINANCIACION"
    FINANCIADA = "FINANCIADA"
    DESEMBOLSADA = "DESEMBOLSADA"


ESTADO_INICIAL = EstadoSolicitud.PENDIENTE_EVALUACION

TRANSICIONES_SOLICITUD = {
    EstadoSolicitud.PENDIENTE_EVALUACION: {
        EstadoSolicitud.EVALUADA,
        EstadoSolicitud.RECHAZADA,
    },
    EstadoSolicitud.EVALUADA: {
        EstadoSolicitud.EN_FINANCIACION,
        EstadoSolicitud.FINANCIADA,
    },
    EstadoSolicitud.EN_FINANCIACION: {
        EstadoSolicitud.FINANCIADA,
    },
    EstadoSolicitud.FINANCIADA: {
        EstadoSolicitud.DESEMBOLSADA,
    },
}


def validar_transicion(origen, destino):
    _validar(TRANSICIONES_SOLICITUD, origen, destino)


class EstadoTransaccion(StrEnum):
    PENDIENTE = "PENDIENTE"
    EXITOSA = "EXITOSA"
    FALLIDA = "FALLIDA"


ESTADO_INICIAL_TRANSACCION = EstadoTransaccion.PENDIENTE

TRANSICIONES_TRANSACCION = {
    EstadoTransaccion.PENDIENTE: {EstadoTransaccion.EXITOSA, EstadoTransaccion.FALLIDA},
    EstadoTransaccion.FALLIDA: {EstadoTransaccion.PENDIENTE},
}


def validar_transicion_transaccion(origen, destino):
    _validar(TRANSICIONES_TRANSACCION, origen, destino)