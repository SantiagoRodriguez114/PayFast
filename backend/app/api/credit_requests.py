from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.credit_request import (
    SolicitudCreditoCrear,
    SolicitudCreditoPublica,
)
from app.services.credit_request_service import (
    BilleteraNoActivaError,
    crear_solicitud_credito,
    listar_solicitudes_usuario,
    obtener_solicitud_usuario,
)


router = APIRouter(
    prefix="/credit-requests",
    tags=["Solicitudes de crédito"],
)


@router.post(
    "/",
    response_model=SolicitudCreditoPublica,
    status_code=status.HTTP_201_CREATED,
)
def crear_solicitud(
    datos: SolicitudCreditoCrear,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Registra una solicitud de crédito para el usuario autenticado.
    """

    try:
        solicitud = crear_solicitud_credito(
            db=db,
            usuario=usuario,
            datos=datos,
        )

    except BilleteraNoActivaError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return solicitud

# Consulta todas las solicitudes del usuario autenticado.
@router.get(
    "/me",
    response_model=list[SolicitudCreditoPublica],
)
def consultar_mis_solicitudes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return listar_solicitudes_usuario(db, usuario)


# Consulta una solicitud específica del usuario autenticado.
@router.get(
    "/{solicitud_id}",
    response_model=SolicitudCreditoPublica,
)
def consultar_solicitud(
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

    return solicitud