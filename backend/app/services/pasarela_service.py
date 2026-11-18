import uuid
from decimal import Decimal


class PasarelaBancariaService:
    """Simula el procesamiento de desembolsos sin mover dinero real."""

    @staticmethod
    def procesar_desembolso(
        monto: Decimal,
        cuenta_destino: str,
    ) -> dict:
        if monto <= Decimal("0.00"):
            return {
                "exito": False,
                "error": "Monto inválido para pasarela",
            }

        return {
            "exito": True,
            "referencia_pasarela": (
                f"TRX-SIM-{uuid.uuid4().hex.upper()}"
            ),
        }
