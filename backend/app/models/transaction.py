import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.states import EstadoTransaccion

from sqlalchemy import Index, text

class Transaccion(Base):
    __tablename__ = "transacciones"

    __table_args__ = (
        CheckConstraint(
            "monto > 0",
            name="ck_transacciones_monto_positivo",
        ),
        Index(
            "uq_transacciones_desembolso_exitoso",
            "solicitud_id",
            unique=True,
            postgresql_where=text("estado = 'EXITOSA'"),
            sqlite_where=text("estado = 'EXITOSA'"),
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

    estado: Mapped[EstadoTransaccion] = mapped_column(
        SQLEnum(
            EstadoTransaccion,
            name="estado_transaccion",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=EstadoTransaccion.PENDIENTE,
    )

    referencia_pasarela: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
    )

    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )