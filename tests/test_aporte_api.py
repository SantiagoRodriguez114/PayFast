from decimal import Decimal
import uuid
from app.models.wallet import Billetera
from app.db.session import SessionLocal
from app.models.credit_request import SolicitudCredito
from app.models.user import Usuario
from app.db.session import get_db

def _get_test_db(client):
    override_gen = client.app.dependency_overrides.get(get_db)
    if override_gen:
        return next(override_gen())
    return SessionLocal()

def _registrar_y_login(client, correo, rol="prestamista"):
    client.post(
        "/auth/register",
        json={"nombre": "Usuario Test", "correo": correo, "password": "password123", "rol": rol},
    )
    res = client.post(
        "/auth/login",
        json={"correo": correo, "password": "password123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _crear_billetera_para_usuario(client, correo, saldo_inicial="0.00"):
    db = _get_test_db(client)
    try:
        user = db.query(Usuario).filter_by(correo=correo).first()
        if user:
            billetera = db.query(Billetera).filter_by(usuario_id=user.id).first()
            if not billetera:
                billetera = Billetera(usuario_id=user.id, saldo=Decimal(saldo_inicial), activa=True)
                db.add(billetera)
            else:
                billetera.saldo = Decimal(saldo_inicial)
                billetera.activa = True
            db.commit()
    finally:
        db.close()

def _crear_solicitud_emprendedor(client, headers, monto, plazo, proposito):
    res = client.post(
        "/credit-requests/",
        headers=headers,
        json={"monto": str(monto), "plazo_meses": plazo, "proposito": proposito},
    )
    data = res.json()
    if isinstance(data, dict):
        return data.get("id") or data.get("solicitud_id") or data.get("uuid")
    return None

def test_aportar_a_solicitud_exitoso(client):
    correo_emp = "emp_aporte@gmail.com"
    headers_emp = _registrar_y_login(client, correo_emp, "emprendedor")
    
    _crear_billetera_para_usuario(client, correo_emp)

    solicitud_id = _crear_solicitud_emprendedor(client, headers_emp, 2000000, 12, "Compra de inventario")
    assert solicitud_id is not None, "La API no devolvió el ID de la solicitud"

    # Convertir el ID a uuid.UUID para evitar conflictos de tipo con SQLite
    db = _get_test_db(client)
    try:
        uuid_obj = uuid.UUID(solicitud_id) if isinstance(solicitud_id, str) else solicitud_id
        s_db = db.get(SolicitudCredito, uuid_obj)
        s_db.estado = "EVALUADA"
        db.commit()
    finally:
        db.close()

    correo_prest = "prest_aporte@gmail.com"
    headers_prest = _registrar_y_login(client, correo_prest, "prestamista")
    _crear_billetera_para_usuario(client, correo_prest, "5000000.00")

    response = client.post(
        f"/credit-requests/{solicitud_id}/contributions",
        headers=headers_prest,
        json={"monto": "1000000.00"},
    )

    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["monto"]) == Decimal("1000000.00")
    assert data["solicitud_id"] == solicitud_id


def test_aportar_monto_superior_al_saldo_pendiente_falla(client):
    correo_emp = "emp_exceso@gmail.com"
    headers_emp = _registrar_y_login(client, correo_emp, "emprendedor")
    
    _crear_billetera_para_usuario(client, correo_emp)

    solicitud_id = _crear_solicitud_emprendedor(client, headers_emp, 1000000, 6, "Capital de trabajo")
    assert solicitud_id is not None, "La API no devolvió el ID de la solicitud"

    db = _get_test_db(client)
    try:
        uuid_obj = uuid.UUID(solicitud_id) if isinstance(solicitud_id, str) else solicitud_id
        s_db = db.get(SolicitudCredito, uuid_obj)
        s_db.estado = "EVALUADA"
        db.commit()
    finally:
        db.close()

    correo_prest = "prest_exceso@gmail.com"
    headers_prest = _registrar_y_login(client, correo_prest, "prestamista")
    
    response = client.post(
        f"/credit-requests/{solicitud_id}/contributions",
        headers=headers_prest,
        json={"monto": "2000000.00"},
    )

    assert response.status_code == 400
    assert "supera el saldo pendiente" in response.json()["detail"]

def test_aporte_completo_financia_solicitud_y_descuenta_saldo(client):
    # Registrar emprendedor y preparar su billetera.
    correo_emp = "emp_completo@gmail.com"
    headers_emp = _registrar_y_login(
        client, correo_emp, "emprendedor"
    )
    _crear_billetera_para_usuario(client, correo_emp)

    solicitud_id = _crear_solicitud_emprendedor(
        client,
        headers_emp,
        1000000,
        12,
        "Compra de maquinaria",
    )
    assert solicitud_id is not None

    # Preparar una solicitud elegible para financiación.
    db = _get_test_db(client)
    try:
        solicitud = db.get(
            SolicitudCredito,
            uuid.UUID(str(solicitud_id)),
        )
        assert solicitud is not None
        solicitud.estado = "EVALUADA"
        db.commit()
    finally:
        db.close()

    # Registrar prestamista con fondos suficientes.
    correo_prest = "prest_completo@gmail.com"
    headers_prest = _registrar_y_login(
        client, correo_prest, "prestamista"
    )
    _crear_billetera_para_usuario(
        client, correo_prest, "1500000.00"
    )

    # Financiar el monto completo.
    response = client.post(
        f"/credit-requests/{solicitud_id}/contributions",
        headers=headers_prest,
        json={"monto": "1000000.00"},
    )

    assert response.status_code == 201

    # Verificar los efectos persistidos en la base de datos.
    db = _get_test_db(client)
    try:
        solicitud = db.get(
            SolicitudCredito,
            uuid.UUID(str(solicitud_id)),
        )
        prestamista = db.query(Usuario).filter_by(
            correo=correo_prest
        ).one()
        billetera = db.query(Billetera).filter_by(
            usuario_id=prestamista.id,
            tipo="principal",
        ).one()

        assert solicitud.estado == "FINANCIADA"
        assert solicitud.monto_financiado == Decimal("1000000.00")
        assert billetera.saldo == Decimal("500000.00")
    finally:
        db.close()