from uuid import UUID


class ErrorConsultaBuro(Exception):
    """Error controlado durante la consulta al buró simulado."""


def consultar_buro(solicitud_id: UUID) -> dict:
    """
    Genera un perfil crediticio ficticio y determinista.

    Los datos no representan información financiera real.
    El mismo identificador produce siempre el mismo perfil.
    """

    semilla = solicitud_id.int

    # Simulación de indisponibilidad del servicio externo.
    if semilla % 10 == 0:
        raise ErrorConsultaBuro(
            "El buró de crédito simulado no está disponible."
        )

    return {
        "historial_pagos": semilla % 101,
        "nivel_endeudamiento": (semilla >> 8) % 101,
        "moras_ultimos_12_meses": (semilla >> 16) % 5,
        "antiguedad_crediticia_meses": (semilla >> 24) % 121,
    }


def calcular_puntaje(datos_buro: dict) -> int:
    """
    Calcula un puntaje ficticio de 0 a 100.

    Pesos provisionales:
    - Historial de pagos: 50 %.
    - Nivel de endeudamiento: 30 %.
    - Historial de moras: 20 %.

    La antigüedad crediticia se conserva como dato informativo.
    """

    historial = datos_buro["historial_pagos"]
    endeudamiento = datos_buro["nivel_endeudamiento"]
    moras = datos_buro["moras_ultimos_12_meses"]

    puntuacion_endeudamiento = 100 - endeudamiento
    puntuacion_moras = max(0, 100 - (moras * 25))

    puntaje = (
        historial * 0.50
        + puntuacion_endeudamiento * 0.30
        + puntuacion_moras * 0.20
    )

    return round(puntaje)