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