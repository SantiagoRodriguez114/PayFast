from decimal import Decimal


def obtener_autenticacion(client, correo="wallet_test@gmail.com"):
    """Registra un usuario y obtiene su token de acceso."""

    datos_usuario = {
        "nombre": "Usuario de Prueba",
        "correo": correo,
        "password": "ClaveSegura123",
        "rol": "emprendedor"
    }

    respuesta_registro = client.post(
        "/auth/register",
        json=datos_usuario
    )
    assert respuesta_registro.status_code == 201

    respuesta_login = client.post(
        "/auth/login",
        json={
            "correo": correo,
            "password": "ClaveSegura123"
        }
    )
    assert respuesta_login.status_code == 200

    token = respuesta_login.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_abrir_billetera_requiere_autenticacion(client):
    respuesta = client.post("/wallets/")

    assert respuesta.status_code == 401


def test_consultar_billetera_requiere_autenticacion(client):
    respuesta = client.get("/wallets/me")

    assert respuesta.status_code == 401


def test_abrir_billetera_correctamente(client):
    headers = obtener_autenticacion(client)

    # Intentamos enviar un saldo desde el cliente.
    # El backend debe ignorarlo y establecer el saldo en cero.
    respuesta = client.post(
        "/wallets/",
        headers=headers,
        json={"saldo": 1000000}
    )

    assert respuesta.status_code == 201

    datos = respuesta.json()

    assert datos["tipo"] == "principal"
    assert datos["moneda"] == "COP"
    assert Decimal(str(datos["saldo"])) == Decimal("0.00")
    assert datos["activa"] is True

    # La respuesta no debe exponer el identificador interno del propietario.
    assert "usuario_id" not in datos


def test_no_permitir_dos_billeteras_principales(client):
    headers = obtener_autenticacion(client)

    primera_respuesta = client.post(
        "/wallets/",
        headers=headers
    )
    segunda_respuesta = client.post(
        "/wallets/",
        headers=headers
    )

    assert primera_respuesta.status_code == 201
    assert segunda_respuesta.status_code == 409


def test_consultar_billetera_del_usuario(client):
    headers = obtener_autenticacion(client)

    client.post("/wallets/", headers=headers)

    respuesta = client.get(
        "/wallets/me",
        headers=headers
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["tipo"] == "principal"
    assert datos["moneda"] == "COP"
    assert Decimal(str(datos["saldo"])) == Decimal("0.00")


def test_consultar_billetera_inexistente(client):
    headers = obtener_autenticacion(client)

    respuesta = client.get(
        "/wallets/me",
        headers=headers
    )

    assert respuesta.status_code == 404