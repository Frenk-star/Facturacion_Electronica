"""XML académico inspirado en UBL 2.1; sin firma criptográfica ni validación XSD."""

from xml.etree.ElementTree import Element, SubElement, register_namespace, tostring

CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"


def generar_xml(comprobante):
    """Construye factura, boleta o crédito con los datos históricos preservados."""
    credito = comprobante.tipo == "07"
    nombre = "CreditNote" if credito else "Invoice"
    namespace = f"urn:oasis:names:specification:ubl:schema:xsd:{nombre}-2"
    register_namespace("", namespace)
    register_namespace("cbc", CBC)
    register_namespace("cac", CAC)
    raiz = Element(f"{{{namespace}}}{nombre}")

    def basico(padre, etiqueta, valor, **atributos):
        nodo = SubElement(padre, f"{{{CBC}}}{etiqueta}", atributos)
        nodo.text = str(valor)
        return nodo

    basico(raiz, "UBLVersionID", "2.1")
    basico(raiz, "CustomizationID", "2.0")
    basico(raiz, "ID", f"{comprobante.serie}-{comprobante.numero:08d}")
    basico(raiz, "IssueDate", comprobante.fecha.date().isoformat())
    basico(raiz, "CreditNoteTypeCode" if credito else "InvoiceTypeCode", comprobante.tipo)
    basico(raiz, "DocumentCurrencyCode", "PEN")
    basico(raiz, "Note", "FIRMA MOCK: simulación académica sin firma digital válida.")
    for etiqueta, clave in [
        ("AccountingSupplierParty", "empresa"),
        ("AccountingCustomerParty", "cliente"),
    ]:
        datos = comprobante.datos_historicos.get(clave, {})
        parte = SubElement(SubElement(raiz, f"{{{CAC}}}{etiqueta}"), f"{{{CAC}}}Party")
        identificacion = SubElement(parte, f"{{{CAC}}}PartyIdentification")
        basico(identificacion, "ID", datos.get("ruc", datos.get("num_doc", "")))
        legal = SubElement(parte, f"{{{CAC}}}PartyLegalEntity")
        basico(legal, "RegistrationName", datos.get("razon_social", ""))
        direccion = SubElement(parte, f"{{{CAC}}}PostalAddress")
        basico(direccion, "StreetName", datos.get("direccion", ""))
    if credito:
        nota = comprobante.nota_credito
        discrepancia = SubElement(raiz, f"{{{CAC}}}DiscrepancyResponse")
        basico(discrepancia, "ResponseCode", nota.tipo_nota)
        basico(discrepancia, "Description", nota.motivo)
        referencia = SubElement(
            SubElement(raiz, f"{{{CAC}}}BillingReference"), f"{{{CAC}}}InvoiceDocumentReference"
        )
        original = nota.comprobante_referencia
        basico(referencia, "ID", f"{original.serie}-{original.numero:08d}")
        basico(referencia, "DocumentTypeCode", original.tipo)
    impuesto = SubElement(raiz, f"{{{CAC}}}TaxTotal")
    basico(impuesto, "TaxAmount", comprobante.igv, currencyID="PEN")
    totales = SubElement(raiz, f"{{{CAC}}}LegalMonetaryTotal")
    basico(totales, "LineExtensionAmount", comprobante.subtotal, currencyID="PEN")
    basico(totales, "PayableAmount", comprobante.total, currencyID="PEN")
    detalles = list(comprobante.detalles.all())
    if credito:
        detalles = [
            {
                "descripcion": comprobante.nota_credito.motivo,
                "base": comprobante.subtotal,
                "igv": comprobante.igv,
            }
        ]
    for indice, detalle in enumerate(detalles, 1):
        linea = SubElement(raiz, f'{{{CAC}}}{"CreditNoteLine" if credito else "InvoiceLine"}')
        basico(linea, "ID", indice)
        basico(
            linea,
            "CreditedQuantity" if credito else "InvoicedQuantity",
            1 if credito else detalle.cantidad,
            unitCode="ZZ" if credito else detalle.unidad_historica,
        )
        basico(
            linea,
            "LineExtensionAmount",
            detalle["base"] if credito else detalle.subtotal,
            currencyID="PEN",
        )
        tributo = SubElement(linea, f"{{{CAC}}}TaxTotal")
        basico(
            tributo, "TaxAmount", detalle["igv"] if credito else detalle.igv_linea, currencyID="PEN"
        )
        item = SubElement(linea, f"{{{CAC}}}Item")
        basico(
            item,
            "Description",
            detalle["descripcion"] if credito else detalle.descripcion_historica,
        )
    return tostring(raiz, encoding="utf-8", xml_declaration=True).decode("utf-8")
