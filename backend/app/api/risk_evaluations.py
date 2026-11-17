from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.risk_evaluation import EvaluacionRiesgoPublica
from app.services.credit_request_service import obtener_solicitud_usuario
from app.services.risk_evaluation_service import (
    SolicitudNoEvaluableError,
    evaluar_solicitud,
    listar_evaluaciones,
)


router = APIRouter(
    prefix="/credit-requests",
    tags=["Evaluación de riesgo"],
)


@router.post(
    "/{solicitud_id}/risk-evaluations",
    response_model=EvaluacionRiesgoPublica,
    status_code=status.HTTP_201_CREATED,
)
def evaluar_credito(
    solicitud_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    solicitud = obtener_solicitud_usuario(
        db=db,
        usuario=usuario,
        solicitud_id=solicitud_id,
    )

    if solicitud is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud de crédito no encontrada.",
        )

    try:
        return evaluar_solicitud(db, solicitud)

    except SolicitudNoEvaluableError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "/{solicitud_id}/risk-evaluations",
    response_model=list[EvaluacionRiesgoPublica],
)
def consultar_evaluaciones(
    solicitud_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    solicitud = obtener_solicitud_usuario(
        db=db,
        usuario=usuario,
        solicitud_id=solicitud_id,
    )

    if solicitud is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud de crédito no encontrada.",
        )

    return listar_evaluaciones(db, solicitud.id)