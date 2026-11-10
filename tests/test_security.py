from datetime import timedelta

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_hash_password_no_guarda_password_original():
    password = "MiClaveSegura123"
    hashed = hash_password(password)

    assert hashed != password


def test_verify_password_acepta_password_correcta():
    password = "MiClaveSegura123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_rechaza_password_incorrecta():
    hashed = hash_password("MiClaveSegura123")

    assert verify_password("OtraClave123", hashed) is False


def test_create_access_token_genera_token_valido():
    token = create_access_token({"sub": "usuario-123"})

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "usuario-123"
    assert "exp" in payload


def test_decode_access_token_rechaza_token_invalido():
    payload = decode_access_token("token_invalido")

    assert payload is None


def test_decode_access_token_rechaza_token_expirado():
    token = create_access_token(
        {"sub": "usuario-123"},
        expires_delta=timedelta(seconds=-1)
    )

    payload = decode_access_token(token)

    assert payload is None