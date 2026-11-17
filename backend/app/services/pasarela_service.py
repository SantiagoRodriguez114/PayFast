import uuid

class PasarelaBancariaService:
    @staticmethod
    def procesar_desembolso(monto: float, cuenta_destino: str) -> dict:
        """
        Simula la pasarela bancaria. 
        Retorna éxito con referencia única o simula un fallo controlado si el monto excede reglas de prueba.
        """
        if monto <= 0:
            return {"exito": False, "error": "Monto inválido para pasarela"}
        
        # Simulación exitosa estándar
        return {
            "exito": True,
            "referencia_pasarela": f"TRX-SIM-{uuid.uuid4().hex[:10].upper()}"
        }