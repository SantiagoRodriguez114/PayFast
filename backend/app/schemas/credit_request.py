from decimal import Decimal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


# Datos que el emprendedor debe enviar para solicitar un crédito.
class SolicitudCreditoCrear(BaseModel):
    monto: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=2,
    )

    plazo_meses: int = Field(gt=0)

    proposito: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=500,
        ),
    ]

    model_config = ConfigDict(extra="forbid") # API rechaza campos adicionales que no estén definidos en el modelo.

# Información que la API devuelve al cliente.
class SolicitudCreditoPublica(BaseModel):
    id: UUID
    monto: Decimal
    plazo_meses: int
    proposito: str
    estado: str
    creada_en: datetime

    model_config = ConfigDict(from_attributes=True)

class SolicitudElegiblePublica(BaseModel):
    id: UUID
    monto: Decimal
    monto_financiado: Decimal
    saldo_pendiente: Decimal
    plazo_meses: int
    proposito: str
    estado: str
    creada_en: datetime

    model_config = ConfigDict(from_attributes=True)