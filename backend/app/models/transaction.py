from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.sqlite import CHAR
import uuid
from datetime import datetime, timezone
import enum
from app.db.base import Base

class EstadoTransaccion(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    EXITOSA = "EXITOSA"
    FALLIDA = "FALLIDA"

class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    solicitud_id = Column(CHAR(36), ForeignKey("solicitudes_credito.id"), nullable=False)
    billetera_id = Column(CHAR(36), ForeignKey("billetera.id"), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    estado = Column(SQLEnum(EstadoTransaccion), default=EstadoTransaccion.PENDIENTE, nullable=False)
    referencia_pasarela = Column(String(100), unique=True, nullable=True)
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)