from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, StringConstraints
from typing import Annotated


# Restricciones para el nombre del usuario.
NombreUsuario = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=120
    )
]


class RegistroUsuario(BaseModel):
    """
    Datos necesarios para registrar una cuenta en PayFast.
    """

    nombre: NombreUsuario

    correo: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )

    rol: Literal["emprendedor", "prestamista"] # limita los roles a los que se pueden registrar los usuarios


class InicioSesion(BaseModel):
    """
    Credenciales necesarias para iniciar sesión.
    """

    correo: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128
    )


class UsuarioPublico(BaseModel):
    """
    Información pública que puede recibir el frontend.
    Nunca incluye el hash de la contraseña.
    """

    id: UUID
    nombre: str
    correo: EmailStr
    activo: bool
    creado_en: datetime
    roles: list[str]


class TokenRespuesta(BaseModel):
    """
    Respuesta que da el backend y que recibe el usuario al autenticarse.
    """

    access_token: str
    token_type: str = "bearer"
