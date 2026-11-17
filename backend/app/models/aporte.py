import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.credit_request import SolicitudCredito
from app.models.user import Usuario

class Aporte(Base):
    __tablename__ = "aportes"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    solicitud_id = Column(Uuid, ForeignKey("solicitudes_credito.id"), nullable=False)
    prestamista_id = Column(Uuid, ForeignKey("usuario.id"), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    solicitud = relationship("SolicitudCredito", back_populates="aportes")
    prestamista = relationship("Usuario", back_populates="aportes")