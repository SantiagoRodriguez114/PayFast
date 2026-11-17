"""Fixtures compartidas por todas las pruebas de integración de la API."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Rol


@pytest.fixture(autouse=True)
def client():
    """Cliente HTTP de prueba con una base de datos propia, aislada y desechable.

    Cada prueba recibe una base SQLite en memoria recién creada con los roles
    ya sembrados, y la API usa esa base en lugar de la base principal. Al terminar la
    prueba, todo se descarta, evitando contaminación entre pruebas.
    """
    # 1. Crear motor SQLite en memoria aislado para esta prueba específica
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # una sola conexión compartida en memoria
    )
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    # 2. Crear todas las tablas (incluyendo 'usuario', 'aportes', etc.)
    Base.metadata.create_all(bind=test_engine)

    # 3. Sembrar los roles iniciales necesarios para el registro
    db = TestingSessionLocal()
    try:
        db.add_all([Rol(nombre="emprendedor"), Rol(nombre="prestamista")])
        db.commit()
    finally:
        db.close()

    # 4. Sobrescribir la dependencia get_db para que la API use esta base en memoria
    def override_get_db():
        database = TestingSessionLocal()
        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_get_db

    # 5. Ejecutar la prueba con el cliente de test
    with TestClient(app) as test_client:
        yield test_client

    # 6. Limpieza posterior a la prueba
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()