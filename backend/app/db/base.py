from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Importante: Importar todos los modelos aquí para que SQLAlchemy registre las tablas en memoria
from app.models.user import Usuario
from app.models.wallet import Billetera
from app.models.credit_request import SolicitudCredito
from app.models.aporte import Aporte