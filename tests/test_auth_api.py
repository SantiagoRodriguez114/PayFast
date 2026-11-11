import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import decode_access_token
from app.models import Rol, Usuario


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    db.add_all([
        Rol(nombre="emprendedor"),
        Rol(nombre="prestamista"),
    ])
    db.commit()
    db.close()

    def override_get_db():
        database = TestingSessionLocal()
        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

# El usuario se registra correctamente con un rol válido
def test_registro_usuario_exitoso(client):
    response = client.post(
        "/auth/register",
        json={
            "nombre": "Carlos Pérez",
            "correo": "carlos@gmail.com",
            "password": "MiClaveSegura123",
            "rol": "emprendedor",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["nombre"] == "Carlos Pérez"
    assert data["correo"] == "carlos@gmail.com"
    assert data["activo"] is True
    assert data["roles"] == ["emprendedor"]

    assert "password" not in data
    assert "password_hash" not in data


# sistema rechaza el registro de un usuario con un correo duplicado
def test_registro_rechaza_correo_duplicado(client):
    datos = {
        "nombre": "Carlos Pérez",
        "correo": "carlos@gmail.com",
        "password": "MiClaveSegura123",
        "rol": "emprendedor",
    }

    primera_respuesta = client.post(
        "/auth/register",
        json=datos,
    )

    segunda_respuesta = client.post(
        "/auth/register",
        json=datos,
    )

    assert primera_respuesta.status_code == 201
    assert segunda_respuesta.status_code == 409


# el sistema no crea un rol no configurado
def test_registro_rechaza_rol_no_configurado(client):
    db_override = app.dependency_overrides[get_db]
    db = next(db_override())

    try:
        rol = db.query(Rol).filter(
            Rol.nombre == "prestamista"
        ).first()

        db.delete(rol)
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/auth/register",
        json={
            "nombre": "Ana Pérez",
            "correo": "ana@gmail.com",
            "password": "MiClaveSegura123",
            "rol": "prestamista",
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "El rol solicitado no está configurado."
    )

# ------------ Inicio de sesión
CORREO = "carlos@gmail.com"
PASSWORD = "MiClaveSegura123"


def _registrar(client):
    """Crea el usuario de prueba y devuelve la respuesta del registro."""
    return client.post(
        "/auth/register",
        json={
            "nombre": "Carlos Pérez",
            "correo": CORREO,
            "password": PASSWORD,
            "rol": "emprendedor",
        },
    )


def _login(client, correo=CORREO, password=PASSWORD):
    return client.post("/auth/login", json={"correo": correo, "password": password})


# Con credenciales correctas se entrega un token que identifica al usuario
def test_login_exitoso_devuelve_token_del_usuario(client):
    usuario = _registrar(client).json()

    response = _login(client)

    assert response.status_code == 200
    datos = response.json()
    assert datos["token_type"] == "bearer"
    # El claim "sub" del token debe ser el id del usuario registrado.
    assert decode_access_token(datos["access_token"])["sub"] == usuario["id"]


# Una contraseña incorrecta se rechaza con 401 y el encabezado que exige Bearer
def test_login_rechaza_contrasena_incorrecta(client):
    _registrar(client)

    response = _login(client, password="ClaveEquivocada999")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


# El mensaje de error no debe revelar si el correo existe o no
def test_login_no_revela_si_el_correo_existe(client):
    _registrar(client)

    clave_mala = _login(client, password="ClaveEquivocada999")
    sin_cuenta = _login(client, correo="nadie@gmail.com")

    assert clave_mala.status_code == sin_cuenta.status_code == 401
    assert clave_mala.json() == sin_cuenta.json()


# El correo se normaliza: espacios y mayúsculas no impiden iniciar sesión
def test_login_normaliza_el_correo(client):
    _registrar(client)

    response = _login(client, correo="  CARLOS@Gmail.com ")

    assert response.status_code == 200


# Una cuenta desactivada no puede iniciar sesión aunque la contraseña sea correcta
def test_login_rechaza_cuenta_desactivada(client):
    _registrar(client)

    # Desactivamos la cuenta directamente en la base de pruebas.
    db = next(app.dependency_overrides[get_db]())
    try:
        usuario = db.scalar(select(Usuario).where(Usuario.correo == CORREO))
        usuario.activo = False
        db.commit()
    finally:
        db.close()

    assert _login(client).status_code == 401