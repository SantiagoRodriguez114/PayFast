from enum import StrEnum


class TransicionInvalida(Exception):
    """Se intentó pasar de un estado a otro que el negocio no permite."""


class EstadoSolicitud(StrEnum):
    PENDIENTE_EVALUACION = "PENDIENTE_EVALUACION"
    EVALUADA = "EVALUADA"
    RECHAZADA = "RECHAZADA"
    EN_FINANCIACION = "EN_FINANCIACION"
    FINANCIADA = "FINANCIADA"
    DESEMBOLSADA = "DESEMBOLSADA"


ESTADO_INICIAL = EstadoSolicitud.PENDIENTE_EVALUACION

TRANSICIONES_SOLICITUD = {
    EstadoSolicitud.PENDIENTE_EVALUACION: {EstadoSolicitud.EVALUADA, EstadoSolicitud.RECHAZADA},
    EstadoSolicitud.EVALUADA: {EstadoSolicitud.EN_FINANCIACION},
    EstadoSolicitud.EN_FINANCIACION: {EstadoSolicitud.FINANCIADA},
    EstadoSolicitud.FINANCIADA: {EstadoSolicitud.DESEMBOLSADA},
}


def validar_transicion(origen, destino):
    permitidos = TRANSICIONES_SOLICITUD.get(origen, set())
    if destino not in permitidos:
        raise TransicionInvalida(f"No se permite pasar de {origen} a {destino}")