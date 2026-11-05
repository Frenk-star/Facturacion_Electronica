# Pendientes acordados

## Consulta externa de RUC y DNI

Estado: **PENDIENTE**, aplazado por indicación del usuario.

El autocompletado actual consulta los clientes registrados en la empresa activa. Falta integrar un proveedor externo para recuperar los datos disponibles de un documento aún no registrado.

La integración deberá consultar desde Django, guardar el token exclusivamente en el entorno privado, manejar documentos no encontrados y errores del proveedor, y permitir revisar los datos antes de guardar el cliente. No deberá inventar información ni presentar datos demo como resultados reales.

No se ha seleccionado proveedor ni configurado un token. La consulta externa no debe marcarse como implementada o verificada.

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
