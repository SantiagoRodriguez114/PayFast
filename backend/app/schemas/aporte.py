from decimal import Decimal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class AporteCrear(BaseModel):
    monto: Decimal = Field(gt=Decimal("0.00"), description="El monto del aporte debe ser mayor a cero")

class AportePublico(BaseModel):
    id: UUID
    solicitud_id: UUID
    prestamista_id: UUID
    monto: Decimal
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)