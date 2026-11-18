import pytest

from app.domain.states import (
    ESTADO_INICIAL,
    EstadoSolicitud,
    TransicionInvalida,
    validar_transicion,
)

E = EstadoSolicitud


def test_estado_inicial_es_pendiente_de_evaluacion():
    assert ESTADO_INICIAL == "PENDIENTE_EVALUACION"


@pytest.mark.parametrize("origen,destino", [
    (E.PENDIENTE_EVALUACION, E.EVALUADA),
    (E.PENDIENTE_EVALUACION, E.RECHAZADA),
    (E.EVALUADA, E.EN_FINANCIACION),
    (E.EVALUADA, E.FINANCIADA),
    (E.EN_FINANCIACION, E.FINANCIADA),
    (E.FINANCIADA, E.DESEMBOLSADA),
])
def test_transiciones_permitidas(origen, destino):
    validar_transicion(origen, destino)


@pytest.mark.parametrize("origen,destino", [
    (E.PENDIENTE_EVALUACION, E.EN_FINANCIACION),
    (E.PENDIENTE_EVALUACION, E.DESEMBOLSADA),
    (E.EVALUADA, E.DESEMBOLSADA),
    (E.RECHAZADA, E.EVALUADA),
    (E.DESEMBOLSADA, E.FINANCIADA),
])
def test_transiciones_no_permitidas(origen, destino):
    with pytest.raises(TransicionInvalida):
        validar_transicion(origen, destino)