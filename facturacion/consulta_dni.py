"""Consulta de nombres por DNI mediante Factiliza; no es acceso directo a RENIEC."""

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from .consulta_ruc import ErrorConsultaRuc


class ErrorConsultaDni(ErrorConsultaRuc):
    """Error controlado de la consulta externa de DNI."""


def consultar_dni(dni):
    if not re.fullmatch(r"[0-9]{8}", dni):
        raise ErrorConsultaDni("Ingrese un DNI de 8 dígitos.", 400)
    if not settings.DNI_API_TOKEN:
        raise ErrorConsultaDni(
            "La consulta DNI aún no está configurada. Contacte al administrador."
        )
    request = Request(
        f"https://api.factiliza.com/v1/dni/info/{dni}",
        headers={"Authorization": f"Bearer {settings.DNI_API_TOKEN}", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)
        data = payload.get("data")
        if payload.get("success") is not True:
            raise ErrorConsultaDni("El proveedor no pudo encontrar o consultar este DNI.", 502)
        if not isinstance(data, dict) or data.get("numero") != dni:
            raise ErrorConsultaDni("El proveedor devolvió una respuesta incompleta.", 502)
        nombre = data.get("nombre_completo")
        if not isinstance(nombre, str) or not nombre.strip():
            raise ErrorConsultaDni("El proveedor no devolvió un nombre válido.", 502)
        # Solo exponer los datos necesarios para identificar al cliente.
        return {"dni": dni, "razon_social": nombre.strip(), "fuente": "Factiliza · Consulta DNI"}
    except HTTPError as exc:
        mensajes = {
            400: "El proveedor no pudo consultar este DNI. Revise el número.",
            401: "Token de consulta DNI inválido. Contacte al administrador.",
            403: "El proveedor no autorizó la consulta DNI. Revise el plan y el token.",
            404: "DNI no encontrado en el proveedor.",
            422: "El proveedor indica que el DNI no es válido.",
            429: "Límite de consultas DNI alcanzado. Intente más tarde.",
        }
        raise ErrorConsultaDni(
            mensajes.get(exc.code, "El proveedor de consulta DNI no está disponible."),
            exc.code if exc.code in {400, 404, 422, 429} else 503,
        ) from exc
    except (URLError, TimeoutError, OSError, ValueError, TypeError, AttributeError) as exc:
        raise ErrorConsultaDni(
            "No se pudo obtener una respuesta válida del proveedor DNI.", 502
        ) from exc
