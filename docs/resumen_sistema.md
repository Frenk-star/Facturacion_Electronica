# Resumen funcional y técnico del sistema

## Propósito y alcance

Nexo es un sistema académico de facturación electrónica peruana que conserva el proyecto `Facturacion_Electronica`, la aplicación `facturacion` y la configuración `FacturacionSunat`. Gestiona el ciclo de ventas y ajustes con datos persistentes, API protegida y una interfaz web responsive.

El XML se basa en una estructura académica inspirada en UBL 2.1. El OSE y la marca de firma son simulados; no existe comunicación real con SUNAT, firma criptográfica válida ni CDR tributario.

## Tecnologías

| Área | Implementación |
|---|---|
| Backend | Python, Django 5.2 y Django REST Framework |
| Interfaz | Django Templates, Bootstrap 5 local y JavaScript con Fetch |
| Autenticación | Sesiones Django para web y SimpleJWT para API |
| Base de datos | SQLite local y PostgreSQL para emisión concurrente |
| Importes | Decimal con redondeo comercial a dos decimales |
| XML | ElementTree con namespaces UBL |
| PDF | ReportLab |
| Excel | openpyxl |
| Documentación API | drf-spectacular, Swagger y OpenAPI |
| Calidad | Ruff, Black, pytest-django y Coverage |
| Navegador | Prueba optativa Playwright/Chromium |

## Pantallas y operaciones

- **Login:** autenticación, validación de acceso, sesión y cierre mediante POST.
- **Dashboard:** ventas netas mensuales, conteos de facturas/boletas/estados, pendientes, últimos documentos y gráfico diario.
- **Emisión:** factura/boleta, selección de serie, autocompletado de clientes/productos, líneas dinámicas, cantidades, precios, descuentos, vista previa, borrador y emisión.
- **Comprobantes:** listado paginado, filtros, badges por estado, detalle, historial, descargas y reenvío autorizado.
- **Voucher:** emisor/receptor históricos, líneas, importes, impresión y PDF.
- **Notas de crédito:** selección de original aceptado, motivo, monto, saldo disponible y documento 07 vinculado.
- **Clientes:** creación, búsqueda, edición, desactivación e historial de documentos.
- **Productos y servicios:** catálogo, precio con IGV, unidad, afectación, búsqueda y desactivación.
- **Libro de ventas:** mes/año, documentos aceptados, créditos negativos, totales netos y descargas CSV/Excel.
- **Configuración:** administración empresarial de datos, series, cuentas y roles locales.

## Entidades

Se conservan Empresa, SerieComprobante, Cliente, Producto, Comprobante, DetalleComprobante, LogEnvioSUNAT y NotaCredito. Se añaden Membresia e HistorialEstado para autorización empresarial y trazabilidad. Existen restricciones de unicidad, FK protegidas, precisión decimal, índices y snapshots históricos.

## Reglas tributarias académicas

Los precios **incluyen IGV**. El descuento es monetario por línea. Para productos gravados, `total = cantidad × precio − descuento`, `base = total / 1.18` e `IGV = total − base`; para no gravados, IGV cero. El backend recalcula y no acepta totales manipulados por el navegador.

Factura exige RUC numérico de 11 dígitos. Boleta admite DNI de 8 dígitos; el catálogo también contempla CE. Clientes permite consultar RUC mediante ConsultadeRUC.pe y DNI mediante Factiliza pulsando Buscar junto al número. Ambas integraciones se comprobaron en vivo; la selección de clientes en emisión sigue consultando el catálogo local. No hay consulta automática al escribir.

La numeración es automática por empresa/tipo/serie. En PostgreSQL se bloquean filas dentro de una transacción; un rollback revierte documento y contador. Los borradores no consumen números y los reenvíos conservan la identidad original. Las claves de idempotencia evitan duplicar solicitudes lógicas.

Flujo: `BORRADOR → EMITIDO → ENVIADO → ACEPTADO / RECHAZADO`; un rechazado puede volver a ENVIADO. Cada transición y cada intento quedan registrados. Los documentos emitidos conservan sus datos históricos y no se eliminan desde la aplicación.

Una nota de crédito exige original aceptado, motivo e importe positivo no superior al saldo acumulado. El original se bloquea para evitar que créditos simultáneos excedan su total. Las bases/impuestos se prorratean y se controlan diferencias de céntimos.

## Roles y aislamiento

| Rol | Alcance |
|---|---|
| ADMIN | Gestión de su empresa, usuarios, roles, series, emisión, consultas y reportes |
| EMISOR | Emisión, catálogos, consultas, impresión y reenvíos autorizados |
| CONTADOR | Lectura, historial, PDF/XML, reportes y exportaciones |

El rol pertenece a una membresía empresarial. Toda empresa seleccionada se valida contra permisos; un identificador enviado por el navegador no concede acceso. Los objetos ajenos no se exponen mediante sus IDs. El superusuario Django dispone de administración global separada.

## API

Rutas principales: `POST /api/facturas/`, `POST /api/boletas/`, `POST /api/notas-credito/`, `GET /api/comprobantes/`, `POST /api/comprobantes/{id}/reenviar/`, `GET /api/comprobantes/{id}/pdf/` y `GET /api/reportes/ventas-por-periodo/`.

También existen JWT/refresh, catálogos, empresas, series, usuarios, membresías, emisión de borradores, XML, logs, historial y dashboard. Los listados tienen paginación y filtros validados. Swagger está en `/api/docs/` y OpenAPI en `/api/schema/`.

## Reportes, documentos y datos iniciales

PDF, voucher y XML utilizan datos históricos para que cambios posteriores de catálogo no reescriban el documento original. El libro mensual suma facturas/boletas aceptadas y resta créditos aceptados una sola vez; los rechazados se informan y excluyen de importes. CSV y Excel comparten las filas del reporte.

`seed_demo` y la entrada compatible `seed.py` cargan datos ficticios de demostración sin duplicarlos al repetir la ejecución. Las cuentas nuevas reciben contraseñas generadas localmente; no se distribuyen claves de acceso permanentes en el código público.

## Calidad y documentación

La entrega funcional registró 64 pruebas aprobadas con PostgreSQL y Chromium, sin omisiones, y cobertura de aplicación del 95,35%. Se verificaron cálculos, concurrencia, permisos, multiempresa, XML, PDF, reportes y un recorrido de navegador con escritorio/móvil. También pasaron checks de Django, consistencia de migraciones, Ruff, Black y OpenAPI.

La documentación formal incluye arquitectura, datos, reglas, API, XML, seguridad, pruebas, manual, despliegue y matriz de trazabilidad. Las cifras anteriores corresponden al registro de esa ejecución; las comprobaciones posteriores se registran de forma independiente.

## Publicación y configuración privada

El código público incluye `.env.example` vacío de secretos. La configuración real, base de datos, credenciales locales, certificados, respaldos y entornos pertenecen a archivos ignorados. Una instalación nueva requiere dependencias, clave local, migraciones y creación de sus propias cuentas. La guía `ejecutar_otra_pc.md` detalla el procedimiento.
