import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecargaBilletera(Base):
    """
    Registra las recargas simuladas realizadas sobre una billetera.

    Cada recarga queda almacenada para que pueda consultarse
    posteriormente en el historial de movimientos.
    """

    __tablename__ = "recargas_billetera"

    __table_args__ = (
        CheckConstraint(
            "monto > 0",
            name="ck_recargas_billetera_monto_positivo",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    billetera_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("billetera.id"),
        nullable=False,
        index=True,
    )

    monto: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )