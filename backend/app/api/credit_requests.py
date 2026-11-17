from decimal import Decimal
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.schemas.aporte import AporteCrear, AportePublico
from app.services.aporte_service import crear_aporte, AporteError
from app.services.desembolso_service import (
    desembolsar_credito, 
    listar_transacciones_usuario, 
    DesembolsoError
)

from app.api.dependencies import get_current_user, require_prestamista
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.credit_request import (
    SolicitudCreditoCrear,
    SolicitudCreditoPublica,
    SolicitudElegiblePublica,
)
from app.services.credit_request_service import (
    BilleteraNoActivaError,
    crear_solicitud_credito,
    listar_solicitudes_elegibles,
    listar_solicitudes_usuario,
    obtener_solicitud_usuario,
)

router = APIRouter(prefix="/credit-requests", tags=["credit-requests"])


@router.get(
    "/eligible",
    response_model=List[SolicitudElegiblePublica],
    summary="Consultar catálogo de solicitudes elegibles para financiación P2P (HU-06)",
)
def consultar_solicitudes_elegibles(
    monto_min: Decimal | None = Query(default=None),
    monto_max: Decimal | None = Query(default=None),
    plazo_min: int | None = Query(default=None),
    plazo_max: int | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    prestamista: Usuario = Depends(require_prestamista),
):
    if monto_min is not None and monto_max is not None and monto_min > monto_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="monto_min no puede ser mayor que monto_max.",
        )
    if plazo_min is not None and plazo_max is not None and plazo_min > plazo_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="plazo_min no puede ser mayor que plazo_max.",
        )

    return listar_solicitudes_elegibles(
        db=db,
        monto_min=monto_min,
        monto_max=monto_max,
        plazo_min=plazo_min,
        plazo_max=plazo_max,
        proposito_q=q,
    )


@router.get("/me", response_model=List[SolicitudCreditoPublica])
def listar_mis_solicitudes(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    return listar_solicitudes_usuario(db=db, usuario=usuario_actual)


@router.post("/", response_model=SolicitudCreditoPublica, status_code=status.HTTP_201_CREATED)
def solicitar_credito(
    datos: SolicitudCreditoCrear,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    try:
        return crear_solicitud_credito(db=db, usuario=usuario_actual, datos=datos)
    except BilleteraNoActivaError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("/{solicitud_id}", response_model=SolicitudCreditoPublica)
def obtener_solicitud(
    solicitud_id: UUID,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    solicitud = obtener_solicitud_usuario(db=db, solicitud_id=solicitud_id, usuario=usuario_actual)
    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud de crédito no encontrada.",
        )
    return solicitud

@router.post(
    "/{solicitud_id}/contributions",
    response_model=AportePublico,
    status_code=status.HTTP_201_CREATED,
    summary="Aportar fondos a una solicitud de microcrédito P2P (HU-07)"
)
def aportar_a_solicitud(
    solicitud_id: UUID,
    datos: AporteCrear,
    db: Session = Depends(get_db),
    prestamista: Usuario = Depends(require_prestamista),
):
    try:
        return crear_aporte(
            db=db,
            prestamista=prestamista,
            solicitud_id=solicitud_id,
            monto=datos.monto
        )
    except AporteError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post(
    "/{solicitud_id}/disburse",
    status_code=status.HTTP_200_OK,
    summary="Desembolsar microcrédito financiado a la billetera del emprendedor (HU-08)",
)
def desembolsar_credito_endpoint(
    solicitud_id: UUID,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    try:
        return desembolsar_credito(db=db, usuario_actual=usuario_actual, solicitud_id=solicitud_id)
    except DesembolsoError as e:
        mensaje = str(e).lower()
        if "ya cuenta" in mensaje or "exitosamente" in mensaje:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/transactions/me",
    summary="Consultar historial de transacciones del usuario autenticado (HU-08)",
)
def consultar_transacciones_usuario(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    try:
        return listar_transacciones_usuario(db=db, usuario_actual=usuario_actual)
    except DesembolsoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )