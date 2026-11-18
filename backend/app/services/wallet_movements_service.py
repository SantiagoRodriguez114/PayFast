"""Construcción del historial unificado de movimientos de billetera."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.aporte import Aporte
from app.models.transaction import Transaccion
from app.models.wallet import Billetera
from app.models.wallet_topup import RecargaBilletera


def listar_movimientos_billetera(db: Session, usuario_id):
    """
    Devuelve recargas, aportes y desembolsos del usuario autenticado.

    Los montos se serializan como texto para conservar los decimales
    y evitar errores de precisión en las respuestas JSON.
    """

    billetera = db.execute(
        select(Billetera).where(
            Billetera.usuario_id == usuario_id,
            Billetera.tipo == "principal",
        )
    ).scalar_one_or_none()

    if billetera is None:
        return []

    movimientos = []

    # 1. Recargas simuladas: aumentan el saldo.
    recargas = db.execute(
        select(RecargaBilletera).where(
            RecargaBilletera.billetera_id == billetera.id
        )
    ).scalars().all()

    for recarga in recargas:
        movimientos.append({
            "id": str(recarga.id),
            "tipo": "RECARGA",
            "direccion": "INGRESO",
            "monto": str(recarga.monto),
            "estado": "EXITOSA",
            "fecha": recarga.creada_en,
            "solicitud_id": None,
            "referencia": None,
        })

    # 2. Aportes: descuentan saldo al prestamista.
    aportes = db.execute(
        select(Aporte).where(
            Aporte.prestamista_id == usuario_id
        )
    ).scalars().all()

    for aporte in aportes:
        movimientos.append({
            "id": str(aporte.id),
            "tipo": "APORTE",
            "direccion": "EGRESO",
            "monto": str(aporte.monto),
            "estado": "EXITOSA",
            "fecha": aporte.creado_en,
            "solicitud_id": str(aporte.solicitud_id),
            "referencia": None,
        })

    # 3. Desembolsos: solo los exitosos son ingresos efectivos.
    transacciones = db.execute(
        select(Transaccion).where(
            Transaccion.billetera_id == billetera.id
        )
    ).scalars().all()

    for transaccion in transacciones:
        estado = transaccion.estado.value

        movimientos.append({
            "id": str(transaccion.id),
            "tipo": "DESEMBOLSO",
            "direccion": (
                "INGRESO" if estado == "EXITOSA" else "NINGUNA"
            ),
            "monto": str(transaccion.monto),
            "estado": estado,
            "fecha": transaccion.fecha,
            "solicitud_id": str(transaccion.solicitud_id),
            "referencia": transaccion.referencia_pasarela,
        })

    # Los registros más recientes aparecen primero.
    movimientos.sort(
        key=lambda movimiento: movimiento["fecha"],
        reverse=True,
    )

    return movimientos