from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from decimal import Decimal
from app.domain.states import EstadoSolicitud

from app.models.credit_request import SolicitudCredito
from app.models.wallet import Billetera
from app.models.user import Usuario
from app.schemas.credit_request import SolicitudCreditoCrear


class BilleteraNoActivaError(Exception):
    """Se produce cuando el usuario no tiene una billetera activa."""


def crear_solicitud_credito(
    db: Session,
    usuario: Usuario,
    datos: SolicitudCreditoCrear,
) -> SolicitudCredito:
    """
    Registra una solicitud de crédito para un usuario autenticado.

    Antes de crearla, verifica que el usuario tenga una billetera activa.
    El propietario y el estado inicial se establecen en el backend.
    """

    # Verificar que el usuario tenga al menos una billetera activa.
    consulta_billetera = select(Billetera).where(
        Billetera.usuario_id == usuario.id,
        Billetera.activa.is_(True),
    )

    billetera = db.scalar(consulta_billetera)

    if billetera is None:
        raise BilleteraNoActivaError(
            "Necesitas una billetera activa para solicitar un crédito."
        )

    # Construir la solicitud usando la identidad del usuario autenticado.
    solicitud = SolicitudCredito(
        usuario_id=usuario.id,
        monto=datos.monto,
        plazo_meses=datos.plazo_meses,
        proposito=datos.proposito,
    )

    try:
        db.add(solicitud)
        db.commit()
        db.refresh(solicitud)

    except SQLAlchemyError:
        db.rollback()
        raise

    return solicitud


def listar_solicitudes_usuario(
    db: Session,
    usuario: Usuario,
) -> list[SolicitudCredito]:
    """Devuelve las solicitudes pertenecientes al usuario autenticado."""

    consulta = (
        select(SolicitudCredito)
        .where(SolicitudCredito.usuario_id == usuario.id)
        .order_by(SolicitudCredito.creada_en.desc())
    )

    return list(db.scalars(consulta).all())


def obtener_solicitud_usuario(
    db: Session,
    usuario: Usuario,
    solicitud_id,
) -> SolicitudCredito | None:
    """
    Busca una solicitud por su identificador y verifica que pertenezca
    al usuario autenticado.
    """

    consulta = select(SolicitudCredito).where(
        SolicitudCredito.id == solicitud_id,
        SolicitudCredito.usuario_id == usuario.id,
    )

    return db.scalar(consulta)

ESTADOS_ELEGIBLES_P2P = (
    EstadoSolicitud.EVALUADA.value,
    EstadoSolicitud.EN_FINANCIACION.value,
)


def listar_solicitudes_elegibles(
    db: Session,
    monto_min: Decimal | None = None,
    monto_max: Decimal | None = None,
    plazo_min: int | None = None,
    plazo_max: int | None = None,
    proposito_q: str | None = None,
) -> list[SolicitudCredito]:
    consulta = select(SolicitudCredito).where(
        SolicitudCredito.estado.in_([EstadoSolicitud.EVALUADA.value, EstadoSolicitud.EN_FINANCIACION.value]),
        (SolicitudCredito.monto - SolicitudCredito.monto_financiado) > 0,
    )

    if monto_min is not None:
        consulta = consulta.where(SolicitudCredito.monto >= monto_min)
    if monto_max is not None:
        consulta = consulta.where(SolicitudCredito.monto <= monto_max)
    if plazo_min is not None:
        consulta = consulta.where(SolicitudCredito.plazo_meses >= plazo_min)
    if plazo_max is not None:
        consulta = consulta.where(SolicitudCredito.plazo_meses <= plazo_max)
    if proposito_q:
        termino = f"%{proposito_q.strip()}%"
        consulta = consulta.where(SolicitudCredito.proposito.ilike(termino))

    consulta = consulta.order_by(SolicitudCredito.creada_en.desc())
    return list(db.scalars(consulta).all())