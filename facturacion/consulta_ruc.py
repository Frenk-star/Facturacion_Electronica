"""Consulta explícita a ConsultadeRUC.pe, independiente de la emisión simulada."""

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class ErrorConsultaRuc(Exception):
    def __init__(self, mensaje, status=503):
        super().__init__(mensaje)
        self.status = status


def consultar_ruc(ruc):
    if not re.fullmatch(r"[0-9]{11}", ruc):
        raise ErrorConsultaRuc("Ingrese un RUC de 11 dígitos.", 400)
    if not settings.RUC_API_TOKEN:
        raise ErrorConsultaRuc(
            "Configure RUC_API_TOKEN en el entorno privado y reinicie el servidor."
        )
    request = Request(
        f"https://consultaderuc.pe/api/v1/ruc/{ruc}",
        headers={"Authorization": f"Bearer {settings.RUC_API_TOKEN}", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)
            data = payload.get("data")
            if (
                payload.get("success") is not True
                or not isinstance(data, dict)
                or data.get("ruc") != ruc
                or not isinstance(data.get("razon_social"), str)
                or not data["razon_social"].strip()
            ):
                raise ErrorConsultaRuc("El proveedor devolvió una respuesta incompleta.", 502)
            return {
                "ruc": ruc,
                "razon_social": data["razon_social"],
                "direccion": data.get("direccion") or "",
                "estado": data.get("estado"),
                "condicion": data.get("condicion_domicilio"),
                "fuente": "ConsultadeRUC.pe · Datos publicados por SUNAT",
            }
    except HTTPError as exc:
        mensajes = {
            401: "Token de consulta inválido.",
            403: "Verifique el token y la activación del plan gratuito.",
            404: "RUC no encontrado en el padrón del proveedor.",
            422: "El proveedor indica que el RUC no es válido.",
            429: "Cuota o límite de consultas alcanzado. Intente más tarde.",
        }
        raise ErrorConsultaRuc(
            mensajes.get(exc.code, "El proveedor de consulta no está disponible."),
            exc.code if exc.code in {404, 422, 429} else 503,
        ) from exc
    except (URLError, TimeoutError, OSError, ValueError, TypeError, AttributeError) as exc:
        raise ErrorConsultaRuc(
            "No se pudo obtener una respuesta válida del proveedor.", 502
        ) from exc
