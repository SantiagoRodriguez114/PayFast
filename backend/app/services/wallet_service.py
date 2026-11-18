from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import Usuario
from app.models.wallet import Billetera
from app.models.wallet_topup import RecargaBilletera


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


class RecargaSimuladaError(Exception):
    """Error de negocio durante una recarga simulada."""


def recargar_billetera_simulada(
    db: Session,
    usuario: Usuario,
    monto: Decimal,
) -> Billetera:
    """
    Acredita saldo ficticio a la billetera principal del usuario.

    Utiliza un bloqueo de fila para proteger las actualizaciones
    concurrentes cuando se ejecuta sobre PostgreSQL.
    """
    try:
        billetera = db.execute(
            select(Billetera)
            .where(
                Billetera.usuario_id == usuario.id,
                Billetera.tipo == "principal",
            )
            .with_for_update()
        ).scalar_one_or_none()

        if billetera is None:
            raise RecargaSimuladaError(
                "Debes crear una billetera antes de recargar saldo."
            )

        if not billetera.activa:
            raise RecargaSimuladaError(
                "La billetera se encuentra inactiva."
            )

        # Actualizamos el saldo de la billetera.
        billetera.saldo = (
            (billetera.saldo or Decimal("0.00")) + monto
        )

        # Guardamos el movimiento en la misma transacción.
        # Si falla el registro, tampoco se confirma el nuevo saldo.
        recarga = RecargaBilletera(
            billetera_id=billetera.id,
            monto=monto,
        )

        db.add(recarga)

        # Una única confirmación para ambas operaciones.
        db.commit()
        db.refresh(billetera)

        return billetera

    except Exception:
        db.rollback()
        raise