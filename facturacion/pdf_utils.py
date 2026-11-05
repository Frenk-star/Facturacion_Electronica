"""Representación PDF de comprobantes basada en sus datos históricos."""

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generar_pdf(comprobante):
    """Produce un voucher paginado sin ejecutar HTML proporcionado por usuarios."""
    archivo = BytesIO()
    documento = SimpleDocTemplate(
        archivo, pagesize=A4, title=str(comprobante), rightMargin=36, leftMargin=36
    )
    estilos = getSampleStyleSheet()
    estilos["Title"].alignment = TA_CENTER
    elementos = []

    def parrafo(texto, estilo="Normal"):
        return Paragraph(escape(str(texto)), estilos[estilo])

    empresa = comprobante.datos_historicos.get("empresa", {})
    cliente = comprobante.datos_historicos.get("cliente", {})
    elementos.extend(
        [
            parrafo(empresa.get("razon_social", ""), "Title"),
            parrafo(f'RUC: {empresa.get("ruc", "")} | {empresa.get("direccion", "")}'),
            Spacer(1, 18),
            parrafo(
                f'{comprobante.get_tipo_display()} · {comprobante.serie}-{comprobante.numero or "BORRADOR"}',
                "Heading2",
            ),
            parrafo(
                f"Fecha: {comprobante.fecha:%d/%m/%Y %H:%M} | Estado OSE mock: {comprobante.estado}"
            ),
            parrafo(f'Cliente: {cliente.get("razon_social", "")} · {cliente.get("num_doc", "")}'),
            parrafo(cliente.get("direccion", "")),
            Spacer(1, 18),
        ]
    )
    filas = [["Descripción", "Cant.", "Precio incl. IGV", "Desc.", "Base", "IGV"]]
    for detalle in comprobante.detalles.all():
        filas.append(
            [
                parrafo(detalle.descripcion_historica),
                str(detalle.cantidad),
                str(detalle.precio_unitario),
                str(detalle.descuento),
                str(detalle.subtotal),
                str(detalle.igv_linea),
            ]
        )
    if comprobante.tipo == "07":
        nota = comprobante.nota_credito
        elementos.append(
            parrafo(f"Referencia: {nota.comprobante_referencia} | Motivo: {nota.motivo}")
        )
        filas.append(
            [
                parrafo(nota.motivo),
                "1",
                str(comprobante.total),
                "0.00",
                str(comprobante.subtotal),
                str(comprobante.igv),
            ]
        )
    tabla = Table(filas, colWidths=[190, 42, 92, 55, 70, 70], repeatRows=1)
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12313b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elementos.extend(
        [
            tabla,
            Spacer(1, 18),
            parrafo(f"Base total: S/ {comprobante.subtotal}"),
            parrafo(f"IGV: S/ {comprobante.igv}"),
            parrafo(f"TOTAL: S/ {comprobante.total}", "Heading2"),
            parrafo("SIMULACIÓN ACADÉMICA. Sin validez tributaria ni firma digital válida."),
        ]
    )
    documento.build(elementos)
    return archivo.getvalue()
