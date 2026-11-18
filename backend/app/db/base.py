from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Registrar todos los modelos en los metadatos de SQLAlchemy.
from app.models.user import Usuario
from app.models.role import Rol
from app.models.wallet import Billetera
from app.models.credit_request import SolicitudCredito
from app.models.risk_evaluation import EvaluacionRiesgo
from app.models.aporte import Aporte
from app.models.transaction import Transaccion