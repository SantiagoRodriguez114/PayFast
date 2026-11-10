
import pytest
from pydantic import ValidationError

from app.schemas.auth import RegistroUsuario, InicioSesion


def test_registro_acepta_datos_validos():
    usuario = RegistroUsuario(
        nombre="Carlos Pérez",
        correo="carlos@gmail.com",
        password="MiClave123",
        rol="emprendedor"
    )

    assert usuario.nombre == "Carlos Pérez"
    assert usuario.correo == "carlos@gmail.com"
    assert usuario.rol == "emprendedor"


def test_registro_rechaza_correo_invalido():
    with pytest.raises(ValidationError):
        RegistroUsuario(
            nombre="Carlos Pérez",
            correo="correo_invalido",
            password="MiClave123",
            rol="emprendedor"
        )


def test_registro_rechaza_password_corta():
    with pytest.raises(ValidationError):
        RegistroUsuario(
            nombre="Carlos Pérez",
            correo="carlos@gmail.com",
            password="123",
            rol="emprendedor"
        )


def test_registro_rechaza_rol_no_permitido():
    with pytest.raises(ValidationError):
        RegistroUsuario(
            nombre="Carlos Pérez",
            correo="carlos@gmail.com",
            password="MiClave123",
            rol="administrador"
        )


def test_inicio_sesion_acepta_credenciales_validas():
    credenciales = InicioSesion(
        correo="carlos@gmail.com",
        password="MiClave123"
    )

    assert credenciales.correo == "carlos@gmail.com"
