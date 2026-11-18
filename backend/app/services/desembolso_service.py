from decimal import Decimal
import uuid
from sqlalchemy.orm import Session

from app.models.credit_request import SolicitudCredito
from app.models.wallet import Billetera
from app.models.transaction import Transaccion, EstadoTransaccion

class DesembolsoError(Exception):
    pass

class PasarelaBancariaService:
    @staticmethod
    def procesar_desembolso(monto: Decimal, cuenta_destino: str) -> dict:
        if monto <= 0:
            return {"exito": False, "error": "Monto inválido para pasarela"}
        return {
            "exito": True,
            "referencia_pasarela": f"TRX-SIM-{uuid.uuid4().hex[:10].upper()}"
        }

def desembolsar_credito(db: Session, usuario_actual, solicitud_id: uuid.UUID):
    solicitud = db.get(SolicitudCredito, solicitud_id)
    if not solicitud:
        raise DesembolsoError("Solicitud de crédito no encontrada.")

    if solicitud.usuario_id != usuario_actual.id:
        raise DesembolsoError("No tienes permisos para desembolsar esta solicitud.")

    # 1. VALIDAR IDEMPOTENCIA PRIMERO (evitar doble desembolso antes de chequear estado)
    transaccion_existente = db.query(Transaccion).filter_by(
        solicitud_id=solicitud_id,
        estado=EstadoTransaccion.EXITOSA
    ).first()
    
    if transaccion_existente:
        raise DesembolsoError("Esta solicitud ya cuenta con un desembolso confirmado exitosamente.")

    # 2. VALIDAR ELEGIBILIDAD
    if solicitud.estado != "FINANCIADA":
        raise DesembolsoError(f"La solicitud no cumple condiciones de desembolso. Estado actual: {solicitud.estado}")

    billetera = db.query(Billetera).filter_by(usuario_id=solicitud.usuario_id).first()
    if not billetera or not billetera.activa:
        raise DesembolsoError("El emprendedor no posee una billetera activa.")

    resultado_pasarela = PasarelaBancariaService.procesar_desembolso(
        solicitud.monto, 
        str(billetera.id)
    )

    if not resultado_pasarela["exito"]:
        trx_fallida = Transaccion(
            solicitud_id=solicitud.id,
            billetera_id=billetera.id,
            monto=solicitud.monto,
            estado=EstadoTransaccion.FALLIDA,
            referencia_pasarela=None,
        )
        db.add(trx_fallida)
        db.commit()
        raise DesembolsoError("La pasarela bancaria rechazó el desembolso.")

    trx_exitosa = Transaccion(
        solicitud_id=solicitud.id,
        billetera_id=billetera.id,
        monto=solicitud.monto,
        estado=EstadoTransaccion.EXITOSA,
        referencia_pasarela=resultado_pasarela["referencia_pasarela"],
    )
    db.add(trx_exitosa)

    billetera.saldo += solicitud.monto
    solicitud.estado = "DESEMBOLSADA"

    db.commit()
    db.refresh(trx_exitosa)

    return {
        "mensaje": "Desembolso realizado con éxito.",
        "transaccion_id": str(trx_exitosa.id),
        "referencia_pasarela": trx_exitosa.referencia_pasarela,
        "monto_desembolsado": str(solicitud.monto),
        "nuevo_saldo_billetera": str(billetera.saldo)
    }

def listar_transacciones_usuario(db: Session, usuario_actual):
    billeteras = db.query(Billetera).filter_by(usuario_id=usuario_actual.id).all()
    billetera_ids = [b.id for b in billeteras]

    if not billetera_ids:
        return []

    return db.query(Transaccion).filter(Transaccion.billetera_id.in_(billetera_ids)).all()