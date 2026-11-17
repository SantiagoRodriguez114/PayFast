from decimal import Decimal

import pytest


def obtener_autenticacion(client, correo="credit_test@gmail.com"):
    """Registra un emprendedor y obtiene su token de acceso."""

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

    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def abrir_billetera(client, headers):
    """Crea la billetera principal necesaria para solicitar un crédito."""

    respuesta = client.post("/wallets/", headers=headers)
    assert respuesta.status_code == 201
    return respuesta


def datos_solicitud():
    return {
        "monto": 800000,
        "plazo_meses": 12,
        "proposito": "Compra de maquinaria para mi emprendimiento",
    }


def test_crear_solicitud_requiere_autenticacion(client):
    respuesta = client.post(
        "/credit-requests/",
        json=datos_solicitud(),
    )

    assert respuesta.status_code == 401


def test_crear_solicitud_requiere_billetera_activa(client):
    headers = obtener_autenticacion(client)

    respuesta = client.post(
        "/credit-requests/",
        headers=headers,
        json=datos_solicitud(),
    )

    assert respuesta.status_code == 409


def test_crear_solicitud_correctamente(client):
    headers = obtener_autenticacion(client)
    abrir_billetera(client, headers)

    respuesta = client.post(
        "/credit-requests/",
        headers=headers,
        json=datos_solicitud(),
    )

    assert respuesta.status_code == 201

    datos = respuesta.json()

    assert datos["monto"] == "800000.00"
    assert datos["plazo_meses"] == 12
    assert datos["estado"] == "PENDIENTE_EVALUACION"
    assert datos["proposito"] == datos_solicitud()["proposito"]
    assert datos["id"] is not None
    assert datos["creada_en"] is not None

    # La respuesta no debe exponer el identificador interno del propietario.
    assert "usuario_id" not in datos


def test_solicitar_credito_no_modifica_saldo(client):
    headers = obtener_autenticacion(client)
    abrir_billetera(client, headers)

    billetera_antes = client.get("/wallets/me", headers=headers)
    saldo_antes = Decimal(billetera_antes.json()["saldo"])

    respuesta = client.post(
        "/credit-requests/",
        headers=headers,
        json=datos_solicitud(),
    )

    assert respuesta.status_code == 201

    billetera_despues = client.get("/wallets/me", headers=headers)
    saldo_despues = Decimal(billetera_despues.json()["saldo"])

    assert saldo_antes == saldo_despues


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("monto", 0),
        ("monto", -100),
        ("plazo_meses", 0),
        ("plazo_meses", -5),
        ("proposito", "   "),
    ],
)
def test_rechazar_datos_invalidos(client, campo, valor):
    headers = obtener_autenticacion(client)
    abrir_billetera(client, headers)

    datos = datos_solicitud()
    datos[campo] = valor

    respuesta = client.post(
        "/credit-requests/",
        headers=headers,
        json=datos,
    )

    assert respuesta.status_code == 422


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("usuario_id", "00000000-0000-0000-0000-000000000001"),
        ("estado", "aprobado"),
    ],
)
def test_rechazar_campos_controlados_por_el_backend(client, campo, valor):
    headers = obtener_autenticacion(client)
    abrir_billetera(client, headers)

    datos = datos_solicitud()
    datos[campo] = valor

    respuesta = client.post(
        "/credit-requests/",
        headers=headers,
        json=datos,
    )

    assert respuesta.status_code == 422


def crear_solicitud_prueba(client, headers):
    """Prepara una billetera y registra una solicitud."""

    billetera = client.post("/wallets/", headers=headers)
    assert billetera.status_code == 201

    respuesta = client.post(
        "/credit-requests/",
        headers=headers,
        json=datos_solicitud(),
    )
    assert respuesta.status_code == 201

    return respuesta.json()


def test_consultar_solicitudes_requiere_autenticacion(client):
    respuesta = client.get("/credit-requests/me")

    assert respuesta.status_code == 401


def test_consultar_mis_solicitudes(client):
    headers = obtener_autenticacion(client)
    solicitud = crear_solicitud_prueba(client, headers)

    respuesta = client.get(
        "/credit-requests/me",
        headers=headers,
    )

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1
    assert respuesta.json()[0]["id"] == solicitud["id"]


def test_consultar_solicitud_especifica(client):
    headers = obtener_autenticacion(client)
    solicitud = crear_solicitud_prueba(client, headers)

    respuesta = client.get(
        f"/credit-requests/{solicitud['id']}",
        headers=headers,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == solicitud["id"]


def test_no_consultar_solicitud_de_otro_usuario(client):
    headers_usuario_1 = obtener_autenticacion(
        client,
        "usuario1@gmail.com",
    )
    solicitud = crear_solicitud_prueba(client, headers_usuario_1)

    headers_usuario_2 = obtener_autenticacion(
        client,
        "usuario2@gmail.com",
    )

    respuesta = client.get(
        f"/credit-requests/{solicitud['id']}",
        headers=headers_usuario_2,
    )

    assert respuesta.status_code == 404


def test_consultar_solicitudes_sin_registros(client):
    headers = obtener_autenticacion(client)

    respuesta = client.get(
        "/credit-requests/me",
        headers=headers,
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == []