from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvaluacionRiesgoPublica(BaseModel):
    id: UUID
    solicitud_id: UUID
    resultado: str
    puntaje: int | None = Field(default=None, ge=0, le=100)
    datos_buro: dict[str, Any] | None = None
    detalle_error: str | None = None
    evaluada_en: datetime

    model_config = ConfigDict(from_attributes=True)