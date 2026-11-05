"""Consultas y exportaciones del libro de ventas con créditos negativos."""

import csv
from decimal import Decimal
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from rest_framework import serializers


class PeriodoSerializer(serializers.Serializer):
    mes = serializers.IntegerField(min_value=1, max_value=12, required=False)
    anio = serializers.IntegerField(min_value=2000, max_value=9999, required=False)


def libro_ventas(queryset, parametros):
    """Incluye solo aceptados y resta cada nota una vez por fecha de emisión."""
    periodo = PeriodoSerializer(data=parametros)
    periodo.is_valid(raise_exception=True)
    hoy = timezone.localdate()
    mes = periodo.validated_data.get("mes", hoy.month)
    anio = periodo.validated_data.get("anio", hoy.year)
    documentos = queryset.filter(fecha__month=mes, fecha__year=anio)
    filas = []
    resumen = {
        campo: Decimal("0.00")
        for campo in ["total_subtotal", "total_igv", "total_ventas", "notas_credito"]
    }
    for documento in (
        documentos.filter(estado="ACEPTADO").select_related("cliente").order_by("fecha", "pk")
    ):
        signo = -1 if documento.tipo == "07" else 1
        fila = {
            "id": documento.pk,
            "fecha": timezone.localtime(documento.fecha).date().isoformat(),
            "tipo": documento.tipo,
            "documento": f"{documento.serie}-{documento.numero:08d}",
            "cliente": documento.datos_historicos.get("cliente", {}).get(
                "razon_social", documento.cliente.razon_social
            ),
            "subtotal": signo * documento.subtotal,
            "igv": signo * documento.igv,
            "total": signo * documento.total,
        }
        filas.append(fila)
        for campo, origen in [
            ("total_subtotal", "subtotal"),
            ("total_igv", "igv"),
            ("total_ventas", "total"),
        ]:
            resumen[campo] += fila[origen]
        if signo == -1:
            resumen["notas_credito"] += documento.total
    resumen.update(
        cantidad_comprobantes=len(filas), rechazados=documentos.filter(estado="RECHAZADO").count()
    )
    return {"mes": mes, "anio": anio, "resumen": resumen, "comprobantes": filas}


def _texto_seguro(valor):
    """Evita fórmulas ejecutables al abrir celdas proporcionadas por usuarios."""
    if isinstance(valor, str) and valor.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + valor
    return valor


def exportar_libro(libro, formato):
    """Exporta las mismas filas del reporte a CSV o Excel."""
    campos = ["fecha", "tipo", "documento", "cliente", "subtotal", "igv", "total"]
    filas = [[_texto_seguro(fila[campo]) for campo in campos] for fila in libro["comprobantes"]]
    filas.append(
        [
            "",
            "",
            "VENTAS NETAS",
            "",
            libro["resumen"]["total_subtotal"],
            libro["resumen"]["total_igv"],
            libro["resumen"]["total_ventas"],
        ]
    )
    if formato == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response.write("\ufeff")
        escritor = csv.writer(response)
        escritor.writerow(campos)
        escritor.writerows(filas)
    else:
        archivo = BytesIO()
        workbook = Workbook()
        hoja = workbook.active
        hoja.title = "Libro de ventas"
        hoja.append(campos)
        for fila in filas:
            hoja.append(fila)
        hoja.freeze_panes = "A2"
        hoja.auto_filter.ref = hoja.dimensions
        for columna in ["A", "B", "C", "D", "E", "F", "G"]:
            hoja.column_dimensions[columna].width = 24 if columna != "D" else 45
        workbook.save(archivo)
        response = HttpResponse(
            archivo.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    response["Content-Disposition"] = (
        f'attachment; filename="ventas-{libro["anio"]}-{libro["mes"]:02d}.{formato}"'
    )
    return response
