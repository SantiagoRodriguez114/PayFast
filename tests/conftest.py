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


@pytest.fixture
def client():
    """Cliente HTTP de prueba con una base de datos propia, aislada y desechable.

    Cada prueba recibe una base SQLite en memoria recién creada con los roles
    ya sembrados, y la API usa esa base en lugar de PostgreSQL. Al terminar la
    prueba, todo se descarta, así que ninguna prueba contamina a otra ni a la
    base de desarrollo.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # una sola conexión compartida: la base vive en memoria
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    db.add_all([Rol(nombre="emprendedor"), Rol(nombre="prestamista")])
    db.commit()
    db.close()

    def override_get_db():
        database = TestingSessionLocal()
        try:
            yield database
        finally:
            database.close()

    # Le decimos a FastAPI: "cuando un endpoint pida get_db, entrega la sesión de prueba".
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()