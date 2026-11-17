import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class SolicitudCredito(Base):
    """
    Representa una solicitud de microcrédito realizada por un emprendedor.
    """

    __tablename__ = "solicitudes_credito"

    __table_args__ = (
        CheckConstraint(
            "monto > 0",
            name="ck_solicitud_monto_positivo"
        ),
        CheckConstraint(
            "plazo_meses > 0",
            name="ck_solicitud_plazo_positivo"
        ),
        CheckConstraint(
            "monto_financiado >= 0",
            name="ck_solicitud_monto_financiado_no_negativo"
        ),
        CheckConstraint(
            "monto_financiado <= monto",
            name="ck_solicitud_monto_financiado_limite"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("usuario.id"),
        nullable=False,
        index=True
    )

    monto: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )

    monto_financiado: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00")
    )

    plazo_meses: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    proposito: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    estado: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="PENDIENTE_EVALUACION",
        server_default=text("'PENDIENTE_EVALUACION'")
    )

    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    @property
    def saldo_pendiente(self) -> Decimal:
        monto_f = self.monto_financiado or Decimal("0.00")
        return self.monto - monto_f

    usuario: Mapped["Usuario"] = relationship(
        back_populates="solicitudes_credito"
    )

    evaluaciones_riesgo: Mapped[list["EvaluacionRiesgo"]] = relationship(
        back_populates="solicitud",
        cascade="all, delete-orphan",
    )

    aportes = relationship("Aporte", back_populates="solicitud", cascade="all, delete-orphan")
