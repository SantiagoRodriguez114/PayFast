from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.wallet import BilleteraPublica
from app.services.wallet_service import (
    crear_billetera,
    obtener_billetera,
    WalletAlreadyExists,
)

from app.core.config import settings
from app.schemas.wallet import RecargaSimuladaCrear
from app.services.wallet_service import (
    recargar_billetera_simulada,
    RecargaSimuladaError,
)

from app.services.wallet_movements_service import listar_movimientos_billetera

router = APIRouter(
    prefix="/wallets",
    tags=["Billeteras"]
)


@router.post(
    "/",
    response_model=BilleteraPublica,
    status_code=status.HTTP_201_CREATED
)
def abrir_billetera(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    """Abre la billetera principal del usuario autenticado."""

    try:
        return crear_billetera(db, usuario)

    except WalletAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya tiene una billetera principal."
        )


@router.get(
    "/me",
    response_model=BilleteraPublica,
    status_code=status.HTTP_200_OK
)
def consultar_billetera(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    """Consulta la billetera del usuario autenticado."""

    billetera = obtener_billetera(db, usuario.id)

    if billetera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes una billetera registrada."
        )

    return billetera

@router.post(
    "/me/top-up",
    response_model=BilleteraPublica,
    summary="Recargar saldo ficticio para demostración",
)
def recargar_saldo_simulado(
    datos: RecargaSimuladaCrear,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    if not settings.enable_demo_topups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Las recargas simuladas están deshabilitadas.",
        )

    try:
        return recargar_billetera_simulada(
            db=db,
            usuario=usuario_actual,
            monto=datos.monto,
        )

    except RecargaSimuladaError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "/me/movements",
    summary="Consultar movimientos de la billetera autenticada",
)
def consultar_movimientos_billetera(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """
    Consulta el historial unificado de la billetera.

    La identidad proviene del JWT; no se acepta un ID de usuario
    suministrado por el cliente.
    """
    return listar_movimientos_billetera(
        db=db,
        usuario_id=usuario.id,
    )