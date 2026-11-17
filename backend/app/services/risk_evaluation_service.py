from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.states import EstadoSolicitud, validar_transicion
from app.models.credit_request import SolicitudCredito
from app.models.risk_evaluation import EvaluacionRiesgo
from app.services.credit_bureau_simulator import (
    ErrorConsultaBuro,
    calcular_puntaje,
    consultar_buro,
)


class SolicitudNoEvaluableError(Exception):
    """La solicitud no está en un estado que permita evaluarla."""


def evaluar_solicitud(
    db: Session,
    solicitud: SolicitudCredito,
) -> EvaluacionRiesgo:
    """
    Consulta el buró simulado, calcula el puntaje y registra el resultado.

    Los intentos fallidos se guardan sin modificar el estado de la solicitud.
    Las evaluaciones exitosas actualizan el estado en la misma transacción.
    """

    if solicitud.estado != EstadoSolicitud.PENDIENTE_EVALUACION.value:
        raise SolicitudNoEvaluableError(
            "La solicitud no está pendiente de evaluación."
        )

    try:
        datos_buro = consultar_buro(solicitud.id)

    except ErrorConsultaBuro as error:
        evaluacion = EvaluacionRiesgo(
            solicitud_id=solicitud.id,
            resultado="FALLIDA",
            puntaje=None,
            datos_buro=None,
            detalle_error=str(error),
        )

        try:
            db.add(evaluacion)
            db.commit()
            db.refresh(evaluacion)
        except SQLAlchemyError:
            db.rollback()
            raise

        return evaluacion

    puntaje = calcular_puntaje(datos_buro)

    nuevo_estado = (
        EstadoSolicitud.EVALUADA
        if puntaje >= 50
        else EstadoSolicitud.RECHAZADA
    )

    validar_transicion(
        EstadoSolicitud(solicitud.estado),
        nuevo_estado,
    )

    evaluacion = EvaluacionRiesgo(
        solicitud_id=solicitud.id,
        resultado="EXITOSA",
        puntaje=puntaje,
        datos_buro=datos_buro,
        detalle_error=None,
    )

    try:
        db.add(evaluacion)
        solicitud.estado = nuevo_estado.value

        db.commit()
        db.refresh(evaluacion)

    except SQLAlchemyError:
        db.rollback()
        raise

    return evaluacion


def listar_evaluaciones(
    db: Session,
    solicitud_id: UUID,
) -> list[EvaluacionRiesgo]:
    """Devuelve el historial de evaluaciones de una solicitud."""

    consulta = (
        select(EvaluacionRiesgo)
        .where(EvaluacionRiesgo.solicitud_id == solicitud_id)
        .order_by(EvaluacionRiesgo.evaluada_en.desc())
    )

    return list(db.scalars(consulta).all())