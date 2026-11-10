from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app

client = TestClient(app)


def test_database_health_ok():
    response = client.get("/health/database")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}


def test_database_health_devuelve_503_si_la_base_falla():
    class SesionRota:
        def execute(self, *args, **kwargs):
            raise OperationalError("SELECT 1", {}, Exception("conexion rechazada"))

    def get_db_roto():
        yield SesionRota()

    app.dependency_overrides[get_db] = get_db_roto
    try:
        response = client.get("/health/database")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Database connection unavailable"}