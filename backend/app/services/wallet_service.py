from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import Usuario
from app.models.wallet import Billetera


class WalletAlreadyExists(Exception):
    """Se produce cuando el usuario ya tiene una billetera principal."""
    pass


def crear_billetera(db: Session, usuario: Usuario) -> Billetera:
    """
    Crea la billetera principal de un usuario autenticado.

    El propietario se obtiene del usuario autenticado y el saldo
    inicial se establece siempre en cero.
    """

    billetera_existente = (
        db.query(Billetera)
        .filter(
            Billetera.usuario_id == usuario.id,
            Billetera.tipo == "principal"
        )
        .first()
    )

    if billetera_existente:
        raise WalletAlreadyExists

    nueva_billetera = Billetera(
        usuario_id=usuario.id,
        tipo="principal",
        moneda="COP",
        saldo=Decimal("0.00"),
        activa=True
    )

    db.add(nueva_billetera)

    try:
        db.commit()
        db.refresh(nueva_billetera)
        return nueva_billetera

    except IntegrityError:
        db.rollback()

        # Comprueba si otra petición creó la billetera simultáneamente.
        billetera_existente = (
            db.query(Billetera)
            .filter(
                Billetera.usuario_id == usuario.id,
                Billetera.tipo == "principal"
            )
            .first()
        )

        if billetera_existente:
            raise WalletAlreadyExists

        raise


def obtener_billetera(db: Session, usuario_id: UUID) -> Billetera | None:
    """
    Consulta la billetera principal perteneciente a un usuario.
    Devuelve None si todavía no existe.
    """

    return (
        db.query(Billetera)
        .filter(
            Billetera.usuario_id == usuario_id,
            Billetera.tipo == "principal"
        )
        .first()
    )