from unittest.mock import patch

from app.domain.states import EstadoTransaccion
from app.models.transaction import Transaccion

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


def test_desembolso_no_duplica_saldo_tras_20_reintentos(client):
    correo = "emp_reintentos@gmail.com"
    headers = _registrar_y_login(client, correo)

    db = _get_test_db(client)
    try:
        usuario = db.query(Usuario).filter_by(correo=correo).first()

        billetera = Billetera(
            usuario_id=usuario.id,
            saldo=Decimal("0.00"),
            activa=True,
        )

        solicitud = SolicitudCredito(
            usuario_id=usuario.id,
            monto=Decimal("1500000.00"),
            plazo_meses=12,
            proposito="Capital de trabajo",
            estado="FINANCIADA",
        )

        db.add_all([billetera, solicitud])
        db.commit()
        solicitud_id = solicitud.id
        billetera_id = billetera.id
    finally:
        db.close()

    primera_respuesta = client.post(
        f"/credit-requests/{solicitud_id}/disburse",
        headers=headers,
    )
    assert primera_respuesta.status_code == 200

    for _ in range(20):
        respuesta = client.post(
            f"/credit-requests/{solicitud_id}/disburse",
            headers=headers,
        )
        assert respuesta.status_code == 409

    db = _get_test_db(client)
    try:
        billetera = db.get(Billetera, billetera_id)

        assert billetera.saldo == Decimal("1500000.00")

        transacciones_exitosas = db.query(Transaccion).filter_by(
            solicitud_id=solicitud_id,
            estado=EstadoTransaccion.EXITOSA,
        ).all()

        assert len(transacciones_exitosas) == 1
    finally:
        db.close()


def test_20_fallos_pasarela_no_acreditan_saldo(client):
    correo = "emp_fallos_pasarela@gmail.com"
    headers = _registrar_y_login(client, correo)

    db = _get_test_db(client)
    try:
        usuario = db.query(Usuario).filter_by(correo=correo).first()

        billetera = Billetera(
            usuario_id=usuario.id,
            saldo=Decimal("0.00"),
            activa=True,
        )

        solicitud = SolicitudCredito(
            usuario_id=usuario.id,
            monto=Decimal("900000.00"),
            plazo_meses=6,
            proposito="Compra de herramientas",
            estado="FINANCIADA",
        )

        db.add_all([billetera, solicitud])
        db.commit()
        solicitud_id = solicitud.id
        billetera_id = billetera.id
    finally:
        db.close()

    with patch(
        "app.services.desembolso_service."
        "PasarelaBancariaService.procesar_desembolso",
        return_value={
            "exito": False,
            "error": "Fallo simulado de pasarela",
        },
    ):
        for _ in range(20):
            respuesta = client.post(
                f"/credit-requests/{solicitud_id}/disburse",
                headers=headers,
            )
            assert respuesta.status_code == 400

    db = _get_test_db(client)
    try:
        billetera = db.get(Billetera, billetera_id)
        solicitud = db.get(SolicitudCredito, solicitud_id)

        assert billetera.saldo == Decimal("0.00")
        assert solicitud.estado == "FINANCIADA"

        transacciones_exitosas = db.query(Transaccion).filter_by(
            solicitud_id=solicitud_id,
            estado=EstadoTransaccion.EXITOSA,
        ).count()

        transacciones_fallidas = db.query(Transaccion).filter_by(
            solicitud_id=solicitud_id,
            estado=EstadoTransaccion.FALLIDA,
        ).count()

        assert transacciones_exitosas == 0
        assert transacciones_fallidas == 20
    finally:
        db.close()
