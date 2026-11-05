"""Excepciones de negocio con códigos estables para clientes HTTP."""

import logging

from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ErrorNegocio(ValidationError):
    """Señala una operación incompatible con las reglas del sistema."""

    code = "regla_negocio"


class DocumentoClienteInvalido(ErrorNegocio):
    code = "documento_cliente_invalido"


class NumeracionNoDisponible(ErrorNegocio):
    code = "numeracion_no_disponible"


class MontoNotaCreditoExcedido(ErrorNegocio):
    code = "monto_nota_credito_excedido"


class TransicionEstadoInvalida(ErrorNegocio):
    code = "transicion_estado_invalida"


class ComprobanteNoModificable(ErrorNegocio):
    code = "comprobante_no_modificable"


class EmpresaNoAutorizada(ErrorNegocio):
    code = "empresa_no_autorizada"


class ProductoNoDisponible(ErrorNegocio):
    code = "producto_no_disponible"


def manejar_error_api(exc, context):
    """Normaliza errores de validación sin revelar trazas internas."""
    if isinstance(exc, ValidationError):
        logging.getLogger("facturacion").info(
            "Operación rechazada por validación: %s", type(exc).__name__
        )
        details = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        return Response(
            {
                "codigo": getattr(exc, "code", None) or "validacion",
                "mensaje": "Revise los datos de la operación.",
                "detalles": details,
            },
            status=400,
        )
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "codigo": "error_solicitud",
            "mensaje": "No se pudo completar la solicitud.",
            "detalles": response.data,
        }
    return response
