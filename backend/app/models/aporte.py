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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Aporte(Base):
    __tablename__ = "aportes"

    __table_args__ = (
        CheckConstraint(
            "monto > 0",
            name="ck_aportes_monto_positivo",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    solicitud_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("solicitud_credito.id"),
        nullable=False,
        index=True,
    )

    prestamista_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("usuario.id"),
        nullable=False,
        index=True,
    )

    monto: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    solicitud: Mapped["SolicitudCredito"] = relationship(
        back_populates="aportes",
    )

    prestamista: Mapped["Usuario"] = relationship(
        back_populates="aportes",
    )