from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings


# Configuración del algoritmo de hash de contraseñas.
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Genera un hash seguro de una contraseña."""
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Comprueba si una contraseña coincide con su hash."""
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
) -> str:
    """Genera un token JWT con fecha de expiración."""
    payload = data.copy()

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.access_token_expire_minutes
        )

    expiration = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expiration})

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return token


def decode_access_token(token: str) -> dict | None:
    """Verifica un JWT y devuelve su contenido si es válido."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except InvalidTokenError:
        return None