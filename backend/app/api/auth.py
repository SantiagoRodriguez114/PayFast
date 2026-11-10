from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import RegistroUsuario, UsuarioPublico
from app.services.auth_service import (
    EmailAlreadyRegistered,
    RoleNotFound,
    registrar_usuario,
)


router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/register",
    response_model=UsuarioPublico,
    status_code=status.HTTP_201_CREATED,
)
def register(
    datos: RegistroUsuario,
    db: Session = Depends(get_db),
):
    try:
        usuario = registrar_usuario(db, datos)

        return UsuarioPublico(
            id=usuario.id,
            nombre=usuario.nombre,
            correo=usuario.correo,
            activo=usuario.activo,
            creado_en=usuario.creado_en,
            roles=[rol.nombre for rol in usuario.roles],
        )

    except EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado.",
        )

    except RoleNotFound:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El rol solicitado no está configurado.",
        )