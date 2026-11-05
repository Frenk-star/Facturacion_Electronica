# Pendientes acordados

## Consulta externa de RUC y DNI

Estado: **RUC y DNI implementados y comprobados en vivo el 5 de noviembre de 2026**.

El autocompletado de emisión consulta clientes locales. El formulario de clientes incluye consultas externas explícitas de RUC mediante ConsultadeRUC.pe (`RUC_API_TOKEN`) y DNI mediante Factiliza (`DNI_API_TOKEN`). Véase [integración real](integracion_real.md).

La integración consulta desde Django, guarda los tokens en el entorno privado, maneja errores y permite revisar los datos antes de guardar. La consulta solo se ejecuta al pulsar Buscar junto al número del documento; no se consulta al escribir.

Proveedores: ConsultadeRUC.pe para RUC y Factiliza para DNI, ambos independientes de las entidades oficiales. Tokens configurados localmente y consultas en vivo correctas. Las pruebas automatizadas usan respuestas controladas. La emisión real sigue pendiente: el interruptor responde, valida ADMIN y explica mediante HTTP 409 que faltan transporte, certificado y credenciales SOL; permanece en Pruebas.

## Correcciones de interfaz completadas

- Buscar junto a Número de documento; retirada la consulta automática.
- Etiquetas adaptadas a razón social o nombres y apellidos.
- Listas de clientes y productos sin recorte en Emitir comprobante; cliente seleccionable verificado en navegador.
- Retirados los rótulos de entorno académico y simulación de las plantillas, conservando la identificación de documentos de prueba sin validez tributaria.

## Pantallas existentes

| Pantalla | Ruta | Alcance actual |
|---|---|---|
| Dashboard | `/` | Resumen mensual, importes netos, conteos, gráfico y alertas de rechazados |
| Emitir comprobante | `/emitir/` | Factura/boleta, autocompletado local, productos, IGV, totales, borrador y emisión |
| Lista de comprobantes | `/comprobantes/` | Paginación, filtros de tipo/fechas/documento del cliente/estado y badges |
| Voucher | `/comprobantes/{id}/voucher/` | Datos históricos, líneas, importes, impresión y descarga PDF |
| Nota de crédito | `/notas-credito/` | Búsqueda por serie/número/cliente, referencia, motivo, monto y saldo |
| Clientes | `/clientes/` | CRUD con desactivación, búsqueda documental e historial |
| Productos/servicios | `/productos/` | CRUD con desactivación, precio, unidad y afectación IGV |
| Libro de ventas | `/reportes/ventas/` | Periodo mensual, bases/IGV/ventas netas, CSV y Excel |

El libro actual muestra documentos aceptados y resta créditos aceptados; informa la cantidad de rechazados excluidos. La consulta de todos los estados se encuentra en la lista de comprobantes. Una tabla del libro que incluya también filas rechazadas, borradores o en proceso no está implementada; esos estados no deben sumarse a las ventas netas.
