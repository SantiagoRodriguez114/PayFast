import pytest

from app.services.credit_bureau_simulator import ErrorConsultaBuro


def obtener_autenticacion(client, correo="risk_test@gmail.com"):
    """Registra un emprendedor y obtiene su token."""

    datos_usuario = {
        "nombre": "Emprendedor de Prueba",
        "correo": correo,
        "password": "ClaveSegura123",
        "rol": "emprendedor",
    }

    registro = client.post("/auth/register", json=datos_usuario)
    assert registro.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "correo": correo,
            "password": "ClaveSegura123",
        },
    )
    assert login.status_code == 200

    return {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }


def crear_solicitud_prueba(client, headers):
    """Crea una billetera y registra una solicitud pendiente."""

    billetera = client.post("/wallets/", headers=headers)
    assert billetera.status_code == 201

    respuesta = client.post(
        "/credit-requests/",
        headers=headers,
        json={
            "monto": 800000,
            "plazo_meses": 12,
            "proposito": "Compra de maquinaria para mi emprendimiento",
        },
    )

    assert respuesta.status_code == 201
    return respuesta.json()


def datos_buro_prueba():
    return {
        "historial_pagos": 90,
        "nivel_endeudamiento": 20,
        "moras_ultimos_12_meses": 0,
        "antiguedad_crediticia_meses": 48,
    }


def test_evaluacion_exitosa_actualiza_estado(client, monkeypatch):
    headers = obtener_autenticacion(client)
    solicitud = crear_solicitud_prueba(client, headers)

    monkeypatch.setattr(
        "app.services.risk_evaluation_service.consultar_buro",
        lambda solicitud_id: datos_buro_prueba(),
    )
    monkeypatch.setattr(
        "app.services.risk_evaluation_service.calcular_puntaje",
        lambda datos: 75,
    )

    respuesta = client.post(
        f"/credit-requests/{solicitud['id']}/risk-evaluations",
        headers=headers,
    )

    assert respuesta.status_code == 201

    evaluacion = respuesta.json()
    assert evaluacion["solicitud_id"] == solicitud["id"]
    assert evaluacion["resultado"] == "EXITOSA"
    assert evaluacion["puntaje"] == 75
    assert evaluacion["datos_buro"] == datos_buro_prueba()
    assert evaluacion["detalle_error"] is None
    assert evaluacion["evaluada_en"] is not None

    consulta = client.get(
        f"/credit-requests/{solicitud['id']}",
        headers=headers,
    )

    assert consulta.status_code == 200
    assert consulta.json()["estado"] == "EVALUADA"


@pytest.mark.parametrize(
    "puntaje,estado_esperado",
    [
        (50, "EVALUADA"),
        (49, "RECHAZADA"),
    ],
)
def test_estado_segun_puntaje(
    client,
    monkeypatch,
    puntaje,
    estado_esperado,
):
    headers = obtener_autenticacion(client)
    solicitud = crear_solicitud_prueba(client, headers)

    monkeypatch.setattr(
        "app.services.risk_evaluation_service.consultar_buro",
        lambda solicitud_id: datos_buro_prueba(),
    )
    monkeypatch.setattr(
        "app.services.risk_evaluation_service.calcular_puntaje",
        lambda datos: puntaje,
    )

    respuesta = client.post(
        f"/credit-requests/{solicitud['id']}/risk-evaluations",
        headers=headers,
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["puntaje"] == puntaje

    consulta = client.get(
        f"/credit-requests/{solicitud['id']}",
        headers=headers,
    )

    assert consulta.json()["estado"] == estado_esperado


def test_fallo_del_buro_no_modifica_estado(client, monkeypatch):
    headers = obtener_autenticacion(client)
    solicitud = crear_solicitud_prueba(client, headers)

    def simular_fallo(solicitud_id):
        raise ErrorConsultaBuro("Servicio de buró no disponible.")

    monkeypatch.setattr(
        "app.services.risk_evaluation_service.consultar_buro",
        simular_fallo,
    )

    respuesta = client.post(
        f"/credit-requests/{solicitud['id']}/risk-evaluations",
        headers=headers,
    )

    assert respuesta.status_code == 201

    evaluacion = respuesta.json()
    assert evaluacion["resultado"] == "FALLIDA"
    assert evaluacion["puntaje"] is None
    assert evaluacion["datos_buro"] is None
    assert evaluacion["detalle_error"] == (
        "Servicio de buró no disponible."
    )

    consulta = client.get(
        f"/credit-requests/{solicitud['id']}",
        headers=headers,
    )

    assert consulta.json()["estado"] == "PENDIENTE_EVALUACION"


def test_reintento_despues_de_fallo_del_buro(client, monkeypatch):
    headers = obtener_autenticacion(client)
    solicitud = crear_solicitud_prueba(client, headers)

    def simular_fallo(solicitud_id):
        raise ErrorConsultaBuro("Buró temporalmente no disponible.")

    monkeypatch.setattr(
        "app.services.risk_evaluation_service.consultar_buro",
        simular_fallo,
    )

    primer_intento = client.post(
        f"/credit-requests/{solicitud['id']}/risk-evaluations",
        headers=headers,
    )

    assert primer_intento.status_code == 201
    assert primer_intento.json()["resultado"] == "FALLIDA"

    monkeypatch.setattr(
        "app.services.risk_evaluation_service.consultar_buro",
        lambda solicitud_id: datos_buro_prueba(),
    )
    monkeypatch.setattr(
        "app.services.risk_evaluation_service.calcular_puntaje",
        lambda datos: 80,
    )

    segundo_intento = client.post(
        f"/credit-requests/{solicitud['id']}/risk-evaluations",
        headers=headers,
    )

    assert segundo_intento.status_code == 201
    assert segundo_intento.json()["resultado"] == "EXITOSA"

    historial = client.get(
        f"/credit-requests/{solicitud['id']}/risk-evaluations",
        headers=headers,
    )

    assert historial.status_code == 200
    assert len(historial.json()) == 2
    assert {item["resultado"] for item in historial.json()} == {
        "FALLIDA",
        "EXITOSA",
    }


def test_no_permite_evaluar_solicitud_ya_evaluada(client, monkeypatch):
    headers = obtener_autenticacion(client)
    solicitud = crear_solicitud_prueba(client, headers)

    monkeypatch.setattr(
        "app.services.risk_evaluation_service.consultar_buro",
        lambda solicitud_id: datos_buro_prueba(),
    )
    monkeypatch.setattr(
        "app.services.risk_evaluation_service.calcular_puntaje",
        lambda datos: 80,
    )

    primera = client.post(
        f"/credit-requests/{solicitud['id']}/risk-evaluations",
        headers=headers,
    )
    assert primera.status_code == 201

    segunda = client.post(
        f"/credit-requests/{solicitud['id']}/risk-evaluations",
        headers=headers,
    )

    assert segunda.status_code == 409


def test_consultar_historial_sin_evaluaciones(client):
    headers = obtener_autenticacion(client)
    solicitud = crear_solicitud_prueba(client, headers)

    respuesta = client.get(
        f"/credit-requests/{solicitud['id']}/risk-evaluations",
        headers=headers,
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_evaluacion_y_consulta_requieren_autenticacion(client):
    solicitud = client.post(
        "/credit-requests/",
        json={
            "monto": 800000,
            "plazo_meses": 12,
            "proposito": "Compra de maquinaria",
        },
    )

    assert solicitud.status_code == 401


def test_usuario_no_puede_evaluar_ni_consultar_solicitud_ajena(
    client,
    monkeypatch,
):
    headers_usuario_1 = obtener_autenticacion(
        client,
        "usuario1_risk@gmail.com",
    )
    solicitud = crear_solicitud_prueba(client, headers_usuario_1)

    headers_usuario_2 = obtener_autenticacion(
        client,
        "usuario2_risk@gmail.com",
    )

    evaluar = client.post(
        f"/credit-requests/{solicitud['id']}/risk-evaluations",
        headers=headers_usuario_2,
    )

    consultar = client.get(
        f"/credit-requests/{solicitud['id']}/risk-evaluations",
        headers=headers_usuario_2,
    )

    assert evaluar.status_code == 404
    assert consultar.status_code == 404