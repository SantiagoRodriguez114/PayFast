"""Protección de rutas: solo un token válido da acceso a /auth/me.

Cada prueba representa una forma distinta en que una petición puede intentar
entrar sin derecho (o con un token que dejó de valer). Todas deben terminar en 401.
"""
from datetime import timedelta
from uuid import uuid4

import jwt
from sqlalchemy import select

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models import Usuario

CORREO = "carlos@gmail.com"
PASSWORD = "MiClaveSegura123"


def _registrar_y_entrar(client):
    """Registra un usuario, inicia sesión y devuelve (datos del usuario, token)."""
    usuario = client.post(
        "/auth/register",
        json={"nombre": "Carlos Pérez", "correo": CORREO, "password": PASSWORD, "rol": "emprendedor"},
    ).json()
    token = client.post(
        "/auth/login", json={"correo": CORREO, "password": PASSWORD}
    ).json()["access_token"]
    return usuario, token


def _con_token(token):
    return {"Authorization": f"Bearer {token}"}


# Sin credenciales no hay acceso, y la respuesta indica que se espera un Bearer
def test_ruta_protegida_sin_token_responde_401(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


# Con un token válido se obtiene el usuario dueño del token, sin datos secretos
def test_ruta_protegida_con_token_valido_devuelve_el_usuario(client):
    usuario, token = _registrar_y_entrar(client)

    response = client.get("/auth/me", headers=_con_token(token))

    assert response.status_code == 200
    datos = response.json()
    assert datos["id"] == usuario["id"]
    assert datos["correo"] == CORREO
    assert datos["roles"] == ["emprendedor"]
    assert "password_hash" not in datos


# Un texto cualquiera que no es un JWT se rechaza
def test_token_malformado_responde_401(client):
    response = client.get("/auth/me", headers=_con_token("esto-no-es-un-jwt"))

    assert response.status_code == 401


# Solo se acepta el esquema Bearer; otros esquemas (por ejemplo Basic) se ignoran
def test_esquema_distinto_de_bearer_responde_401(client):
    response = client.get("/auth/me", headers={"Authorization": "Basic dXNlcjpwYXNz"})

    assert response.status_code == 401


# Un token vencido ya no da acceso
def test_token_expirado_responde_401(client):
    usuario, _ = _registrar_y_entrar(client)
    vencido = create_access_token({"sub": usuario["id"]}, timedelta(seconds=-5))

    response = client.get("/auth/me", headers=_con_token(vencido))

    assert response.status_code == 401


# Un token firmado con otra clave es una falsificación y se rechaza
def test_token_firmado_con_otra_clave_responde_401(client):
    usuario, _ = _registrar_y_entrar(client)
    falso = jwt.encode(
        {"sub": usuario["id"], "exp": 4102444800},  # expira en el año 2100
        "una-clave-que-no-es-la-del-servidor-0123456789",
        algorithm="HS256",
    )

    response = client.get("/auth/me", headers=_con_token(falso))

    assert response.status_code == 401


# Un token válido pero sin "sub" no identifica a nadie
def test_token_sin_sub_responde_401(client):
    _registrar_y_entrar(client)
    sin_sub = create_access_token({})

    response = client.get("/auth/me", headers=_con_token(sin_sub))

    assert response.status_code == 401


# Un "sub" que no tiene formato de UUID se rechaza en lugar de provocar un error 500
def test_token_con_sub_que_no_es_uuid_responde_401(client):
    sub_invalido = create_access_token({"sub": "no-es-un-uuid"})

    response = client.get("/auth/me", headers=_con_token(sub_invalido))

    assert response.status_code == 401


# Un token bien firmado de un usuario que no existe no da acceso
def test_token_de_usuario_inexistente_responde_401(client):
    huerfano = create_access_token({"sub": str(uuid4())})

    response = client.get("/auth/me", headers=_con_token(huerfano))

    assert response.status_code == 401


# Si la cuenta se desactiva, su token anterior deja de funcionar
def test_token_de_cuenta_desactivada_deja_de_funcionar(client):
    _, token = _registrar_y_entrar(client)

    db = next(app.dependency_overrides[get_db]())
    try:
        usuario = db.scalar(select(Usuario).where(Usuario.correo == CORREO))
        usuario.activo = False
        db.commit()
    finally:
        db.close()

    response = client.get("/auth/me", headers=_con_token(token))

    assert response.status_code == 401