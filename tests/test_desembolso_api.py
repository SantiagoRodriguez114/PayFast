from decimal import Decimal
from app.db.session import SessionLocal, get_db
from app.models.credit_request import SolicitudCredito
from app.models.wallet import Billetera
from app.models.user import Usuario

def _get_test_db(client):
    override_gen = client.app.dependency_overrides.get(get_db)
    if override_gen:
        return next(override_gen())
    return SessionLocal()

def _registrar_y_login(client, correo, rol="emprendedor"):
    client.post("/auth/register", json={"nombre": "Test", "correo": correo, "password": "password123", "rol": rol})
    res = client.post("/auth/login", json={"correo": correo, "password": "password123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_desembolso_exitoso(client):
    correo = "emp_desembolso@gmail.com"
    headers = _registrar_y_login(client, correo, "emprendedor")

    db = _get_test_db(client)
    try:
        user = db.query(Usuario).filter_by(correo=correo).first()
        billetera = Billetera(usuario_id=user.id, saldo=Decimal("0.00"), activa=True)
        solicitud = SolicitudCredito(usuario_id=user.id, monto=Decimal("1500000.00"), plazo_meses=12, proposito="Expansión", estado="FINANCIADA")
        db.add_all([billetera, solicitud])
        db.commit()
        s_id = str(solicitud.id)
    finally:
        db.close()

    # Ejecutar desembolso
    response = client.post(f"/credit-requests/{s_id}/disburse", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["monto_desembolsado"] == "1500000.00"
    assert "referencia_pasarela" in data

    # Validar idempotencia (segundo desembolso debe fallar con 409)
    response_segundo = client.post(f"/credit-requests/{s_id}/disburse", headers=headers)
    assert response_segundo.status_code == 409

def test_consultar_transacciones(client):
    correo = "emp_trx@gmail.com"
    headers = _registrar_y_login(client, correo, "emprendedor")

    response = client.get("/credit-requests/transactions/me", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)