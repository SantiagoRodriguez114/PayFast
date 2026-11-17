import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EvaluacionRiesgo(Base):
    """Almacena cada intento de evaluación de riesgo de una solicitud."""

    __tablename__ = "evaluacion_riesgo"

    __table_args__ = (
        CheckConstraint(
            "puntaje IS NULL OR (puntaje >= 0 AND puntaje <= 100)",
            name="ck_evaluacion_puntaje_rango",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    solicitud_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("solicitudes_credito.id"),
        nullable=False,
        index=True,
    )

    resultado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    puntaje: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    datos_buro: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    detalle_error: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    evaluada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    solicitud: Mapped["SolicitudCredito"] = relationship(
        back_populates="evaluaciones_riesgo",
    )