from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.aporte import Aporte
from app.models.credit_request import SolicitudCredito
from app.models.user import Usuario
from app.models.wallet import Billetera

class AporteError(Exception):
    pass

def crear_aporte(db: Session, prestamista: Usuario, solicitud_id, monto: Decimal) -> Aporte:
    # 1. Buscar la solicitud de crédito
    solicitud = db.get(SolicitudCredito, solicitud_id)
    if not solicitud:
        raise AporteError("La solicitud de crédito no existe.")

    # 2. Validar que la solicitud esté habilitada para financiación (por estados en string)
    estados_permitidos = ["EVALUADA", "EN_FINANCIACION"]
    if solicitud.estado not in estados_permitidos:
        raise AporteError("La solicitud no se encuentra habilitada para recibir financiación.")

    # 3. Calcular saldo pendiente
    monto_fin = solicitud.monto_financiado or Decimal("0.00")
    saldo_pendiente = solicitud.monto - monto_fin

    if monto <= 0:
        raise AporteError("El monto del aporte debe ser mayor que cero.")
    if monto > saldo_pendiente:
        raise AporteError("El monto del aporte supera el saldo pendiente de financiación.")

    # 4. Verificar billetera del prestamista
    billetera = db.query(Billetera).filter(Billetera.usuario_id == prestamista.id).first()
    if not billetera or not billetera.activa:
        raise AporteError("El prestamista no cuenta con una billetera activa.")
    
    saldo_billetera = billetera.saldo or Decimal("0.00")
    if saldo_billetera < monto:
        raise AporteError("Fondos insuficientes en la billetera del prestamista.")

    # 5. Actualización atómica de saldos y registro del aporte
    billetera.saldo = saldo_billetera - monto
    solicitud.monto_financiado = monto_fin + monto

    # Actualizar estado según corresponda
    if solicitud.monto_financiado >= solicitud.monto:
        solicitud.estado = "FINANCIADA"
    else:
        solicitud.estado = "EN_FINANCIACION"

    nuevo_aporte = Aporte(
        solicitud_id=solicitud.id,
        prestamista_id=prestamista.id,
        monto=monto
    )
    
    db.add(nuevo_aporte)
    db.commit()
    db.refresh(nuevo_aporte)
    return nuevo_aporte