"""Dependencias compartidas para la autenticación y autorización de la API."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Usuario


# Permite recibir el encabezado Authorization sin generar automáticamente
# un error; así controlamos que todas las fallas respondan de forma uniforme.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Obtiene el usuario autenticado a partir de un token Bearer válido.

    Verifica la firma y expiración del JWT, identifica al usuario mediante
    el claim 'sub' y comprueba que la cuenta exista y permanezca activa.
    """

    # Todas las fallas de autenticación usan la misma respuesta.
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la autenticación",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    payload = decode_access_token(credentials.credentials)

    if payload is None:
        raise unauthorized

    subject = payload.get("sub")

    # El claim sub debe contener el UUID del usuario.
    if not isinstance(subject, str):
        raise unauthorized

    try:
        user_id = UUID(subject)
    except ValueError:
        raise unauthorized

    # El token no basta: verificamos que el usuario siga existiendo y activo.
    usuario = db.scalar(
        select(Usuario).where(Usuario.id == user_id)
    )

    if usuario is None or not usuario.activo:
        raise unauthorized

    return usuario

def require_role(required_role: str):
    """Verifica que el usuario autenticado posea el rol requerido."""
    def _role_checker(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        roles_usuario = {rol.nombre for rol in usuario.roles}
        if required_role not in roles_usuario:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: se requiere el rol '{required_role}'.",
            )
        return usuario

    return _role_checker


require_prestamista = require_role("prestamista")