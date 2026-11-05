"""OSE académico determinista; no contiene conectividad con SUNAT."""

from xml.etree import ElementTree as ET

from django.core.exceptions import ValidationError


def procesar(xml: str, resultado: str = "ACEPTADO") -> dict:
    """Valida XML bien formado y devuelve una respuesta simulada."""
    if resultado not in {"ACEPTADO", "RECHAZADO"}:
        raise ValidationError("Resultado mock inválido.")
    try:
        ET.fromstring(xml)
    except ET.ParseError:
        resultado = "RECHAZADO"
    return {
        "estado_respuesta": resultado,
        "codigo_respuesta": "0" if resultado == "ACEPTADO" else "MOCK-400",
        "descripcion": f"SIMULACIÓN ACADÉMICA: documento {resultado.lower()}. Sin validez tributaria.",
    }
