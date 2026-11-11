import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Billetera(Base):
    """
    Representa la billetera simulada de un usuario dentro de PayFast.

    El saldo se almacena como Numeric para evitar errores de precisión
    propios de los números de punto flotante.
    """

    __tablename__ = "billetera"

    __table_args__ = (
        # Un usuario no puede tener dos billeteras del mismo tipo.
        UniqueConstraint(
            "usuario_id",
            "tipo",
            name="uq_billetera_usuario_tipo"
        ),
        # El saldo de una billetera no puede ser negativo.
        CheckConstraint(
            "saldo >= 0",
            name="ck_billetera_saldo_no_negativo"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    tipo: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="principal",
        server_default=text("'principal'")
    )

    moneda: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="COP",
        server_default=text("'COP'")
    )

    saldo: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00")
    )

    activa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true")
    )

    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    usuario: Mapped["Usuario"] = relationship(
        back_populates="billeteras"
    )