from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.states import EstadoSolicitud
from app.models.aporte import Aporte
from app.models.credit_request import SolicitudCredito
from app.models.user import Usuario
from app.models.wallet import Billetera


class AporteError(Exception):
    """Error de validación durante una operación de financiación."""


def crear_aporte(
    db: Session,
    prestamista: Usuario,
    solicitud_id: UUID,
    monto: Decimal,
) -> Aporte:
    """
    Registra un aporte y actualiza los saldos en una transacción.

    PostgreSQL bloquea las filas involucradas hasta que termina
    la transacción, evitando modificaciones concurrentes.
    """

    if not monto.is_finite():
        raise AporteError("El monto del aporte debe ser finito.")

    if monto <= 0:
        raise AporteError("El monto del aporte debe ser mayor que cero.")

    if monto != monto.quantize(Decimal("0.01")):
        raise AporteError(
        "El monto del aporte no puede tener más de dos decimales."
        )

    try:
        # Bloquear la solicitud antes de calcular su saldo pendiente.
        solicitud = db.execute(
            select(SolicitudCredito)
            .where(SolicitudCredito.id == solicitud_id)
            .with_for_update()
        ).scalar_one_or_none()

        if solicitud is None:
            raise AporteError("La solicitud de crédito no existe.")

        estados_permitidos = {
            EstadoSolicitud.EVALUADA,
            EstadoSolicitud.EN_FINANCIACION,
        }

        if solicitud.estado not in estados_permitidos:
            raise AporteError(
                "La solicitud no se encuentra habilitada para recibir financiación."
            )

        monto_financiado = solicitud.monto_financiado or Decimal("0.00")
        saldo_pendiente = solicitud.monto - monto_financiado

        if monto > saldo_pendiente:
            raise AporteError(
                "El monto del aporte supera el saldo pendiente de financiación."
            )

        # Bloquear la billetera para impedir descuentos concurrentes.
        billetera = db.execute(
            select(Billetera)
            .where(
                Billetera.usuario_id == prestamista.id,
                Billetera.tipo == "principal",
            )
            .with_for_update()
        ).scalar_one_or_none()

        if billetera is None or not billetera.activa:
            raise AporteError(
                "El prestamista no cuenta con una billetera activa."
            )

        saldo_billetera = billetera.saldo or Decimal("0.00")

        if saldo_billetera < monto:
            raise AporteError(
                "Fondos insuficientes en la billetera del prestamista."
            )

        # Ambas actualizaciones forman parte de la misma transacción.
        billetera.saldo = saldo_billetera - monto
        solicitud.monto_financiado = monto_financiado + monto

        if solicitud.monto_financiado == solicitud.monto:
            solicitud.estado = EstadoSolicitud.FINANCIADA
        else:
            solicitud.estado = EstadoSolicitud.EN_FINANCIACION

        nuevo_aporte = Aporte(
            solicitud_id=solicitud.id,
            prestamista_id=prestamista.id,
            monto=monto,
        )

        db.add(nuevo_aporte)
        db.commit()
        db.refresh(nuevo_aporte)

        return nuevo_aporte

    except Exception:
        db.rollback()
        raise