# XML académico basado en UBL 2.1

`facturacion/xml_utils.py` utiliza `xml.etree.ElementTree`; no concatena valores de usuarios como etiquetas. La declaración es XML UTF-8 válida y los textos se escapan automáticamente. El mock analiza el documento para comprobar que está bien formado; no valida esquemas XSD SUNAT.

| Elemento | Contenido |
|---|---|
| Raíz `Invoice` | Facturas 01 y boletas 03 |
| Raíz `CreditNote` | Créditos 07 |
| `UBLVersionID`, `CustomizationID` | 2.1 y 2.0 académicos |
| `ID`, `IssueDate`, tipo y moneda | Serie/número, fecha, 01/03/07 y PEN |
| `AccountingSupplierParty` | RUC, nombre y dirección históricos del emisor |
| `AccountingCustomerParty` | Documento, nombre y dirección históricos del receptor |
| `InvoiceLine` / `CreditNoteLine` | Cantidad, unidad, descripción, base e IGV |
| `TaxTotal` | IGV del documento y líneas |
| `LegalMonetaryTotal` | Suma de bases y total pagadero |
| `DiscrepancyResponse` | Código y motivo de crédito |
| `BillingReference` | Identificador y tipo del original |
| `Note` | Texto explícito de firma mock sin validez criptográfica |

Namespaces CBC y CAC de UBL identifican componentes básicos y agregados. Las notas monetarias se representan con una línea de ajuste: el monto y el impuesto se prorratean según el original, conservando su referencia.

No se implementan certificados, digest, XMLDSig, catálogos completos SUNAT, comprobación XSD/Schematron, ZIP tributario, SOAP, credenciales SOL, CDR ni transporte real. `xml_firmado` conserva su nombre original por compatibilidad, pero contiene exclusivamente XML con una **marca textual mock**, no una firma digital.

`ose_mock.procesar` acepta un resultado determinista `ACEPTADO` o `RECHAZADO`. Un XML malformado fuerza rechazo. Devuelve código `0` o `MOCK-400`, descripción explícita de simulación y estado. `FacturacionService` registra cada intento y transición. Reenviar conserva identidad y numeración, vuelve a generar el XML a partir de datos históricos y añade un nuevo log.

Una futura integración real debe diseñar el manejo de certificados y transporte por separado y validar las especificaciones vigentes antes de enviar documentos. La estructura presente es un ejercicio funcional y verificable, no una certificación de conformidad tributaria.
