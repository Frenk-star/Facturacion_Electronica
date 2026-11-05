"""Casos de uso tributarios. Los precios y descuentos incluyen IGV."""

import json
from decimal import ROUND_HALF_UP, Decimal
from hashlib import sha256

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from .exceptions import (
    DocumentoClienteInvalido,
    EmpresaNoAutorizada,
    MontoNotaCreditoExcedido,
    NumeracionNoDisponible,
    ProductoNoDisponible,
    TransicionEstadoInvalida,
)
from .models import (
    Cliente,
    Comprobante,
    DetalleComprobante,
    Empresa,
    HistorialEstado,
    LogEnvioSUNAT,
    NotaCredito,
    Producto,
    SerieComprobante,
)

CENTIMO = Decimal("0.01")
TASA_IGV = Decimal("0.18")
CERO = Decimal("0.00")
TRANSICIONES = {
    "BORRADOR": {"EMITIDO"},
    "EMITIDO": {"ENVIADO"},
    "ENVIADO": {"ACEPTADO", "RECHAZADO"},
    "RECHAZADO": {"ENVIADO"},
    "ACEPTADO": set(),
}


def dinero(valor) -> Decimal:
    """Redondea importes a céntimos mediante redondeo comercial."""
    return Decimal(str(valor)).quantize(CENTIMO, rounding=ROUND_HALF_UP)


def calcular_linea(cantidad, precio_unitario, descuento=0, afecto_igv=True) -> dict[str, Decimal]:
    """Desglosa IGV incluido: base = total / 1.18; IGV = total - base.

    El descuento es un importe por línea, también con IGV incluido.
    La validación antecede cualquier consumo de correlativos.
    """
    cantidad, precio, descuento = map(
        lambda v: Decimal(str(v)), (cantidad, precio_unitario, descuento)
    )
    if not all(v.is_finite() for v in (cantidad, precio, descuento)):
        raise ValidationError("Los importes deben ser finitos.")
    if cantidad <= 0 or precio < 0 or descuento < 0 or descuento > cantidad * precio:
        raise ValidationError("Cantidad, precio o descuento inválido.")
    total = dinero(cantidad * precio - descuento)
    base = dinero(total / (1 + TASA_IGV)) if afecto_igv else total
    return {"subtotal": base, "igv_linea": total - base, "total": total}


def cambiar_estado(comprobante, estado, usuario=None):
    """Aplica una transición válida y conserva el registro anterior."""
    if estado not in TRANSICIONES[comprobante.estado]:
        raise TransicionEstadoInvalida(f"No se permite {comprobante.estado} → {estado}.")
    anterior = comprobante.estado
    comprobante.estado = estado
    comprobante.save(update_fields=["estado"])
    HistorialEstado.objects.create(
        comprobante=comprobante, anterior=anterior, estado=estado, usuario=usuario
    )


def saldo_credito(original: Comprobante) -> Decimal:
    """Reserva créditos emitidos, incluidos rechazados susceptibles de reenvío."""
    usado = (
        original.notas_credito.filter(
            Q(comprobante__isnull=True) | ~Q(comprobante__estado="BORRADOR")
        ).aggregate(total=Sum("monto_afectado"))["total"]
        or CERO
    )
    return original.total - usado


def _huella_emision(tipo, cliente_id, items, serie, borrador):
    """Identifica la petición lógica para rechazar claves reutilizadas con otros datos."""
    lineas = []
    for item in items:
        producto_id = item["producto"].pk if "producto" in item else item.get("producto_id")
        linea = {"producto_id": producto_id}
        for campo in ["cantidad", "precio_unitario", "descuento"]:
            valor = item.get(campo, 0 if campo == "descuento" else None)
            linea[campo] = str(Decimal(str(valor)).normalize()) if valor is not None else None
        lineas.append(linea)
    datos = {
        "tipo": tipo,
        "cliente": cliente_id,
        "items": lineas,
        "serie": serie,
        "borrador": borrador,
    }
    return sha256(json.dumps(datos, sort_keys=True).encode()).hexdigest()


def _numerar(comprobante, serie=None):
    """Bloquea la serie en la transacción que persiste el documento.

    PostgreSQL serializa solicitudes competidoras. El rollback revierte contador
    y documento. SQLite solo es apto para demostración local sin concurrencia.
    """
    tipo = {"01": "F", "03": "B", "07": "FC"}[comprobante.tipo]
    series = SerieComprobante.objects.select_for_update().filter(
        empresa=comprobante.empresa, tipo=tipo
    )
    objeto = series.filter(serie=serie).first() if serie else series.order_by("pk").first()
    if not objeto:
        raise NumeracionNoDisponible("No existe una serie autorizada para el tipo solicitado.")
    objeto.correlativo_actual += 1
    objeto.save(update_fields=["correlativo_actual"])
    comprobante.serie, comprobante.numero = objeto.serie, objeto.correlativo_actual
    comprobante.estado = "EMITIDO"
    comprobante.fecha = timezone.now()
    comprobante.save(update_fields=["serie", "numero", "estado", "fecha"])
    HistorialEstado.objects.create(
        comprobante=comprobante,
        anterior="BORRADOR",
        estado="EMITIDO",
        usuario=comprobante.creado_por,
    )


class FacturacionService:
    """Coordina emisión, borradores, créditos y transporte OSE simulado."""

    @staticmethod
    @transaction.atomic
    def emitir_comprobante(
        tipo_comp,
        empresa_id,
        cliente_id,
        items_data,
        usuario=None,
        borrador=False,
        serie=None,
        resultado_mock="ACEPTADO",
        clave_idempotencia=None,
    ):
        """Valida el ámbito y recalcula todos los importes antes de numerar."""
        if tipo_comp not in {"01", "03"}:
            raise ValidationError("Tipo de comprobante inválido.")
        huella = _huella_emision(tipo_comp, cliente_id, items_data, serie, borrador)
        empresa = Empresa.objects.select_for_update().get(pk=empresa_id)
        if usuario:
            from .permissions import rol_usuario

            if rol_usuario(usuario, empresa) not in {"ADMIN", "EMISOR"}:
                raise EmpresaNoAutorizada("No tiene permiso de emisión en esta empresa.")
        if clave_idempotencia:
            existente = Comprobante.objects.filter(
                empresa=empresa, clave_idempotencia=clave_idempotencia
            ).first()
            if existente:
                huella_anterior = existente.datos_historicos.get("huella_solicitud")
                if (
                    existente.tipo != tipo_comp
                    or existente.cliente_id != cliente_id
                    or (huella_anterior and huella_anterior != huella)
                ):
                    raise ValidationError(
                        "La clave de idempotencia ya fue utilizada con otros datos."
                    )
                return existente
        cliente = Cliente.objects.filter(pk=cliente_id, empresa=empresa, activo=True).first()
        if not cliente:
            raise DocumentoClienteInvalido("El cliente no está activo en esta empresa.")
        cliente.full_clean()
        if tipo_comp == "01" and cliente.tipo_doc != "RUC":
            raise DocumentoClienteInvalido("Las facturas requieren RUC de 11 dígitos.")
        if not items_data:
            raise ValidationError("Agregue al menos una línea.")
        comprobante = Comprobante.objects.create(
            empresa=empresa,
            cliente=cliente,
            tipo=tipo_comp,
            serie="",
            numero=None,
            subtotal=0,
            igv=0,
            total=0,
            creado_por=usuario,
            clave_idempotencia=clave_idempotencia,
            datos_historicos={
                "huella_solicitud": huella,
                "empresa": {
                    "ruc": empresa.ruc,
                    "razon_social": empresa.razon_social,
                    "direccion": empresa.direccion,
                },
                "cliente": {
                    "num_doc": cliente.num_doc,
                    "tipo_doc": cliente.tipo_doc,
                    "razon_social": cliente.razon_social,
                    "direccion": cliente.direccion,
                },
            },
        )
        HistorialEstado.objects.create(
            comprobante=comprobante, anterior="", estado="BORRADOR", usuario=usuario
        )
        for item in items_data:
            producto_id = item["producto"].pk if "producto" in item else item["producto_id"]
            producto = Producto.objects.filter(pk=producto_id, empresa=empresa, activo=True).first()
            if not producto:
                raise ProductoNoDisponible("Producto no disponible en esta empresa.")
            precio = item.get("precio_unitario", producto.precio_unitario)
            calculo = calcular_linea(
                item["cantidad"], precio, item.get("descuento", 0), producto.afecto_igv
            )
            detalle = DetalleComprobante(
                comprobante=comprobante,
                producto=producto,
                cantidad=item["cantidad"],
                precio_unitario=precio,
                descuento=item.get("descuento", 0),
                subtotal=calculo["subtotal"],
                igv_linea=calculo["igv_linea"],
                descripcion_historica=producto.descripcion,
                unidad_historica=producto.unidad_medida,
                afecto_igv_historico=producto.afecto_igv,
            )
            detalle.full_clean()
            detalle.save()
            comprobante.subtotal += calculo["subtotal"]
            comprobante.igv += calculo["igv_linea"]
        comprobante.total = comprobante.subtotal + comprobante.igv
        if comprobante.total > Decimal("9999999999.99"):
            raise ValidationError("El importe excede la capacidad monetaria del documento.")
        comprobante.save(update_fields=["subtotal", "igv", "total"])
        if not borrador:
            _numerar(comprobante, serie)
            FacturacionService.enviar_a_sunat(comprobante, resultado_mock, usuario)
        return comprobante

    @staticmethod
    @transaction.atomic
    def emitir_borrador(comprobante, usuario=None, serie=None):
        """Emite exactamente una vez un borrador existente sin alterar sus líneas."""
        comprobante = Comprobante.objects.select_for_update().get(pk=comprobante.pk)
        if comprobante.estado != "BORRADOR":
            raise TransicionEstadoInvalida("Solo se pueden emitir borradores.")
        _numerar(comprobante, serie)
        FacturacionService.enviar_a_sunat(comprobante, usuario=usuario)
        return comprobante

    @staticmethod
    @transaction.atomic
    def enviar_a_sunat(comprobante, resultado_mock="ACEPTADO", usuario=None):
        """Registra un intento determinista sin realizar comunicaciones externas."""
        from .ose_mock import procesar
        from .xml_utils import generar_xml

        bloqueado = Comprobante.objects.select_for_update().get(pk=comprobante.pk)
        cambiar_estado(bloqueado, "ENVIADO", usuario)
        bloqueado.xml_firmado = generar_xml(bloqueado)
        bloqueado.save(update_fields=["xml_firmado"])
        resultado = procesar(bloqueado.xml_firmado, resultado_mock)
        LogEnvioSUNAT.objects.create(comprobante=bloqueado, **resultado)
        cambiar_estado(bloqueado, resultado["estado_respuesta"], usuario)
        comprobante.refresh_from_db()
        return comprobante

    @staticmethod
    @transaction.atomic
    def emitir_nota_credito(
        comprobante_original_id,
        motivo,
        tipo_nota,
        monto_afectado,
        usuario=None,
        resultado_mock="ACEPTADO",
        clave_idempotencia=None,
    ):
        """Bloquea el original y valida el saldo acumulado antes de emitir un 07.

        Prorratea base e impuesto según el original; la última nota absorbe los
        céntimos para que la suma de créditos no exceda sus impuestos.
        """
        original = Comprobante.objects.select_for_update().get(pk=comprobante_original_id)
        if usuario:
            from .permissions import rol_usuario

            if rol_usuario(usuario, original.empresa) not in {"ADMIN", "EMISOR"}:
                raise EmpresaNoAutorizada("No tiene permiso sobre el original.")
        if clave_idempotencia:
            existente = NotaCredito.objects.filter(
                comprobante__empresa=original.empresa,
                comprobante__clave_idempotencia=clave_idempotencia,
            ).first()
            if existente:
                if (
                    existente.comprobante_referencia_id != original.pk
                    or existente.motivo != motivo
                    or existente.tipo_nota != tipo_nota
                    or existente.monto_afectado != dinero(monto_afectado)
                ):
                    raise ValidationError(
                        "La clave de idempotencia ya corresponde a otra nota de crédito."
                    )
                return existente
        monto = dinero(monto_afectado)
        if original.estado != "ACEPTADO" or original.tipo not in {"01", "03"}:
            raise ValidationError("El original debe ser una factura o boleta aceptada.")
        saldo = saldo_credito(original)
        if monto <= 0 or monto > saldo:
            raise MontoNotaCreditoExcedido(
                f"El monto debe ser positivo y no superar el saldo {saldo}."
            )
        if not motivo or not str(motivo).strip() or tipo_nota not in {"01", "02", "03", "06", "07"}:
            raise ValidationError("Indique un motivo y un tipo de nota válido.")
        usados = original.notas_credito.filter(comprobante__isnull=False).aggregate(
            igv=Sum("comprobante__igv")
        )
        igv = (
            original.igv - (usados["igv"] or CERO)
            if monto == saldo
            else dinero(monto * original.igv / original.total)
        )
        base_usada = (
            original.notas_credito.filter(comprobante__isnull=False).aggregate(
                base=Sum("comprobante__subtotal")
            )["base"]
            or CERO
        )
        igv = max(CERO, min(igv, original.igv - (usados["igv"] or CERO), monto))
        if monto - igv > original.subtotal - base_usada:
            igv = monto - (original.subtotal - base_usada)
        documento = Comprobante.objects.create(
            empresa=original.empresa,
            cliente=original.cliente,
            tipo="07",
            serie="",
            numero=None,
            subtotal=monto - igv,
            igv=igv,
            total=monto,
            creado_por=usuario,
            datos_historicos=original.datos_historicos,
            clave_idempotencia=clave_idempotencia,
        )
        HistorialEstado.objects.create(
            comprobante=documento, anterior="", estado="BORRADOR", usuario=usuario
        )
        nc = NotaCredito.objects.create(
            comprobante=documento,
            comprobante_referencia=original,
            motivo=motivo,
            tipo_nota=tipo_nota,
            monto_afectado=monto,
        )
        _numerar(documento)
        FacturacionService.enviar_a_sunat(documento, resultado_mock, usuario)
        return nc
