from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import RegistroUsuario, UsuarioPublico
from app.services.auth_service import (
    EmailAlreadyRegistered,
    RoleNotFound,
    registrar_usuario,
)

from app.core.security import create_access_token
from app.schemas.auth import InicioSesion, TokenRespuesta
from app.services.auth_service import (
    InvalidCredentials,
    autenticar_usuario,
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


@router.post(
    "/login",
    response_model=TokenRespuesta,
    status_code=status.HTTP_200_OK,
)
def login(
    datos: InicioSesion,
    db: Session = Depends(get_db),
):
    """
    Autentica al usuario y devuelve un token JWT.

    El token identifica al usuario mediante su UUID.
    """

    try:
        # Verificamos las credenciales contra PostgreSQL.
        usuario = autenticar_usuario(
            db,
            datos.correo,
            datos.password
        )

        # El UUID del usuario se utiliza como identificador del token.
        token = create_access_token(
            data={"sub": str(usuario.id)}
        )

        return TokenRespuesta(
            access_token=token,
            token_type="bearer"
        )

    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
