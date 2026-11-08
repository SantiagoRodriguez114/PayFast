import pytest

from app.domain.states import (
    ESTADO_INICIAL_TRANSACCION,
    EstadoTransaccion,
    TransicionInvalida,
    validar_transicion_transaccion,
)

T = EstadoTransaccion


def test_estado_inicial_de_transaccion_es_pendiente():
    assert ESTADO_INICIAL_TRANSACCION == "PENDIENTE"


@pytest.mark.parametrize("origen,destino", [
    (T.PENDIENTE, T.EXITOSA),
    (T.PENDIENTE, T.FALLIDA),
    (T.FALLIDA, T.PENDIENTE),
])
def test_transiciones_permitidas(origen, destino):
    validar_transicion_transaccion(origen, destino)


@pytest.mark.parametrize("origen,destino", [
    (T.PENDIENTE, T.PENDIENTE),
    (T.FALLIDA, T.EXITOSA),
    (T.EXITOSA, T.PENDIENTE),
    (T.EXITOSA, T.FALLIDA),
    (T.EXITOSA, T.EXITOSA),
])
def test_transiciones_no_permitidas(origen, destino):
    with pytest.raises(TransicionInvalida):
        validar_transicion_transaccion(origen, destino)