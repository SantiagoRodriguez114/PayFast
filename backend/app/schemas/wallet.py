from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BilleteraPublica(BaseModel):
    """
    Datos de una billetera que pueden exponerse mediante la API.

    No incluye información interna del propietario ni permite
    modificar directamente el saldo.
    """

    id: UUID
    tipo: str
    moneda: str
    saldo: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    activa: bool
    creada_en: datetime

    model_config = ConfigDict(from_attributes=True)

class RecargaSimuladaCrear(BaseModel):
    """Datos para acreditar fondos ficticios en una billetera."""

    monto: Decimal = Field(
        gt=Decimal("0.00"),
        le=Decimal("10000000.00"),
        max_digits=18,
        decimal_places=2,
    )

    model_config = ConfigDict(extra="forbid")