import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models import Rol


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