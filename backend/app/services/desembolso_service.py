import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.states import EstadoSolicitud, EstadoTransaccion
from app.models.credit_request import SolicitudCredito
from app.models.transaction import Transaccion
from app.models.wallet import Billetera
from app.services.pasarela_service import PasarelaBancariaService


class DesembolsoError(Exception):
    """Error de validación durante un desembolso."""


def desembolsar_credito(
    db: Session,
    usuario_actual,
    solicitud_id: uuid.UUID,
):
    """
    Procesa un desembolso simulado.

    En PostgreSQL, bloquea la solicitud y la billetera
    para evitar acreditaciones concurrentes.
    """
    try:
        # Bloquear la solicitud durante la operación.
        solicitud = db.execute(
            select(SolicitudCredito)
            .where(SolicitudCredito.id == solicitud_id)
            .with_for_update()
        ).scalar_one_or_none()

        if solicitud is None:
            raise DesembolsoError(
                "Solicitud de crédito no encontrada."
            )

        if solicitud.usuario_id != usuario_actual.id:
            raise DesembolsoError(
                "No tienes permisos para desembolsar esta solicitud."
            )

        # Comprobar si ya existe un desembolso exitoso.
        transaccion_existente = db.execute(
            select(Transaccion).where(
                Transaccion.solicitud_id == solicitud.id,
                Transaccion.estado == EstadoTransaccion.EXITOSA,
            )
        ).scalar_one_or_none()

        if transaccion_existente is not None:
            raise DesembolsoError(
                "Esta solicitud ya cuenta con un desembolso confirmado exitosamente."
            )

        if solicitud.estado != EstadoSolicitud.FINANCIADA:
            raise DesembolsoError(
                "La solicitud no cumple condiciones de desembolso. "
                f"Estado actual: {solicitud.estado}"
            )

        # Bloquear la billetera del emprendedor.
        billetera = db.execute(
            select(Billetera)
            .where(
                Billetera.usuario_id == solicitud.usuario_id,
                Billetera.tipo == "principal",
            )
            .with_for_update()
        ).scalar_one_or_none()

        if billetera is None or not billetera.activa:
            raise DesembolsoError(
                "El emprendedor no posee una billetera activa."
            )

        # Ejecutar la operación simulada.
        resultado = PasarelaBancariaService.procesar_desembolso(
            monto=solicitud.monto,
            cuenta_destino=str(billetera.id),
        )

        if not resultado["exito"]:
            transaccion_fallida = Transaccion(
                solicitud_id=solicitud.id,
                billetera_id=billetera.id,
                monto=solicitud.monto,
                estado=EstadoTransaccion.FALLIDA,
                referencia_pasarela=None,
            )

            db.add(transaccion_fallida)
            db.commit()

            raise DesembolsoError(
                "La pasarela bancaria rechazó el desembolso."
            )

        # Registrar la transacción exitosa.
        transaccion = Transaccion(
            solicitud_id=solicitud.id,
            billetera_id=billetera.id,
            monto=solicitud.monto,
            estado=EstadoTransaccion.EXITOSA,
            referencia_pasarela=resultado["referencia_pasarela"],
        )

        db.add(transaccion)

        # Acreditar el saldo y actualizar el estado.
        billetera.saldo = (
            (billetera.saldo or Decimal("0.00"))
            + solicitud.monto
        )

        solicitud.estado = EstadoSolicitud.DESEMBOLSADA

        db.commit()
        db.refresh(transaccion)

        return {
            "mensaje": "Desembolso realizado con éxito.",
            "transaccion_id": str(transaccion.id),
            "referencia_pasarela": transaccion.referencia_pasarela,
            "monto_desembolsado": str(solicitud.monto),
            "nuevo_saldo_billetera": str(billetera.saldo),
        }

    except Exception:
        db.rollback()
        raise


def listar_transacciones_usuario(
    db: Session,
    usuario_actual,
):
    """Consulta las transacciones de las billeteras del usuario."""

    billeteras = db.execute(
        select(Billetera).where(
            Billetera.usuario_id == usuario_actual.id
        )
    ).scalars().all()

    billetera_ids = [billetera.id for billetera in billeteras]

    if not billetera_ids:
        return []

    return db.execute(
        select(Transaccion).where(
            Transaccion.billetera_id.in_(billetera_ids)
        )
    ).scalars().all()
