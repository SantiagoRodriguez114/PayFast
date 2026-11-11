from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Rol, Usuario
from app.schemas.auth import RegistroUsuario
from app.core.security import verify_password


class EmailAlreadyRegistered(Exception):
    """Se produce cuando el correo ya está registrado."""


class RoleNotFound(Exception):
    """Se produce cuando el rol solicitado no existe."""


def registrar_usuario(db: Session, datos: RegistroUsuario) -> Usuario:
    correo = str(datos.correo).strip().lower()

    # Comprobar si el correo ya está registrado.
    consulta_usuario = select(Usuario).where(
        Usuario.correo == correo
    )
    usuario_existente = db.scalar(consulta_usuario)

    if usuario_existente:
        raise EmailAlreadyRegistered

    # Buscar el rol solicitado.
    consulta_rol = select(Rol).where(
        Rol.nombre == datos.rol
    )
    rol = db.scalar(consulta_rol)

    if rol is None:
        raise RoleNotFound

    # Crear el usuario y generar el hash de su contraseña.
    usuario = Usuario(
        nombre=datos.nombre,
        correo=correo,
        password_hash=hash_password(datos.password),
        activo=True
    )

    usuario.roles.append(rol)

    try:
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    except IntegrityError as error:
        db.rollback()
        raise EmailAlreadyRegistered from error

    return usuario


class InvalidCredentials(Exception):
    """Se produce cuando las credenciales no son válidas."""


def autenticar_usuario(
    db: Session,
    correo: str,
    password: str
) -> Usuario:
    """
    Verifica las credenciales de un usuario.

    Devuelve el usuario si las credenciales son correctas
    y la cuenta está activa. No revela si falló el correo,
    la contraseña o el estado de la cuenta.
    """

    # Normalizamos el correo para mantener consistencia.
    correo = correo.strip().lower()

    # Buscamos el usuario por su correo.
    consulta = select(Usuario).where(
        Usuario.correo == correo
    )
    usuario = db.scalar(consulta)

    # Se utiliza el mismo error para evitar revelar información.
    if usuario is None:
        raise InvalidCredentials

    if not usuario.activo:
        raise InvalidCredentials

    # Comprobamos la contraseña contra el hash Argon2 almacenado.
    if not verify_password(password, usuario.password_hash):
        raise InvalidCredentials

    return usuario