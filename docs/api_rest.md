# API REST

## Rutas web adicionales (5 de noviembre de 2026)

Estas rutas de `web_urls.py` usan sesión y CSRF, no JWT ni ViewSets DRF. Enviar
formulario URL-encoded con `X-CSRFToken`; no se incluyen en el OpenAPI de DRF.

| Método y ruta | Entrada | Rol | Resultado |
|---|---|---|---|
| `POST /clientes/consultar-ruc/` | `ruc`, 11 dígitos ASCII | ADMIN/EMISOR | `ruc`, `razon_social`, `direccion`, `estado`, `condicion`, `fuente` |
| `POST /clientes/consultar-dni/` | `dni`, 8 dígitos ASCII | ADMIN/EMISOR | `dni`, `razon_social` (nombre completo), `fuente` |
| `POST /configuracion/modo-emision/` | Sin parámetros necesarios | ADMIN | HTTP 409, `detail` con requisitos pendientes y `modo: PRUEBAS` |

Las consultas no guardan clientes. Falta de sesión: redirección a login; rol no
permitido: 403; GET: 405. Validación/errores de proveedor: 400/404/422/429 según
el caso, 503 por configuración/autorización del proveedor o indisponibilidad,
502 por respuesta inválida o red. Errores controlados contienen `detail`.

Base `/api/`. Respuestas JSON, salvo PDF/XML/CSV/Excel. Paginación: 25 registros, `count`, `next`, `previous`, `results`; parámetro `page`. La empresa se obtiene de sesión o cabecera `X-Empresa-ID` después de comprobar acceso; sin selección se utiliza la primera empresa autorizada por ID.

## Autenticación

`POST token/` recibe `username`, `password` y devuelve `access`, `refresh`; `POST token/refresh/` recibe `refresh`. Access dura 20 minutos; refresh, un día. Enviar `Authorization: Bearer <access>`. La web usa sesión Django, con cookie HttpOnly y cabecera `X-CSRFToken` para Fetch. Detalles de SimpleJWT: [documentación oficial](https://django-rest-framework-simplejwt.readthedocs.io/en/stable/getting_started.html).

## Emisión

| Método y ruta | Entrada / resultado |
|---|---|
| POST `facturas/` | `cliente_id`, `items`, `serie` opcional, `borrador` opcional, `resultado_mock` opcional, `clave_idempotencia` opcional → 201 comprobante |
| POST `boletas/` | Misma estructura; receptor admite DNI → 201 |
| POST `notas-credito/` | `comprobante_id`, `motivo`, `tipo_nota`, `monto_afectado`, clave y resultado opcionales → 201 nota con ID de documento 07 |
| GET `comprobantes/` | Lista paginada de la empresa activa |
| POST `comprobantes/{id}/reenviar/` | `resultado_mock` opcional; solo RECHAZADO → 200 documento actualizado |
| GET `comprobantes/{id}/pdf/` | PDF descargable generado con ReportLab |
| GET `reportes/ventas-por-periodo/` | `mes` 1–12, `anio` 2000–9999; por defecto mes/año actual |

`items`: lista no vacía de `{producto_id, cantidad, precio_unitario?, descuento?}`. Cantidad/importe admiten dos decimales. Precio omitido utiliza el catálogo. `resultado_mock`: ACEPTADO o RECHAZADO; valor por defecto ACEPTADO. Es un mecanismo académico, no un canal tributario. `empresa_id` es compatible con clientes antiguos, pero debe coincidir con el ámbito autorizado.

Ejemplo crédito:

```json
{"comprobante_id": 1, "motivo": "Devolución parcial", "tipo_nota": "07", "monto_afectado": "11.80", "clave_idempotencia": "devolucion-1"}
```

## Consulta, mantenimiento y auxiliares

| Ruta | Operaciones |
|---|---|
| `comprobantes/{id}/` | GET con líneas históricas y saldo disponible; PATCH/DELETE no admitidos |
| `comprobantes/{id}/emitir/` | POST para emitir borrador sin crear otro documento |
| `comprobantes/{id}/xml/` | GET XML; 400 si aún es borrador |
| `comprobantes/{id}/logs/` | GET intentos OSE ordenados por fecha |
| `comprobantes/{id}/historial/` | GET transiciones con actor |
| `comprobantes/emitir-factura/`, `emitir-boleta/` | Alias POST conservados |
| `clientes/`, `productos/` | GET/POST; GET/PUT/PATCH/DELETE por ID; DELETE desactiva |
| `clientes/{id}/historial/` | GET paginado de comprobantes del cliente |
| `series/` | GET/POST solo; creación restringida a ADMIN, contador de solo lectura |
| `empresas/` | GET y PUT/PATCH de la empresa activa; nuevas empresas en administración global |
| `usuarios/` | ADMIN: listar, crear, editar y revocar membresía con DELETE; no concede privilegios globales |
| `membresias/` | ADMIN: asignar/modificar/revocar roles locales |
| `reportes/dashboard/` | GET conteos de estado/tipo y libro del mes |
| `docs/`, `schema/` | Swagger con recursos locales y OpenAPI |

Filtros de comprobantes: `tipo`, `estado`, `fecha_desde`, `fecha_hasta`, `ruc_cliente`, `cliente`. Fechas ISO `YYYY-MM-DD`, inclusivas en zona America/Lima; fecha inicial no puede superar la final. `ruc_cliente` funciona con el documento del receptor (también DNI). Búsquedas de catálogo: `q` sobre documento/nombre o código/descripción, y `activo=true`.

Libro: `formato=csv` o `formato=xlsx` descarga; sin formato devuelve `{mes, anio, resumen, comprobantes}`. `resumen` contiene `total_subtotal`, `total_igv`, `total_ventas`, `notas_credito`, `cantidad_comprobantes` y `rechazados`. Las notas tienen importes negativos en las filas.

## Errores

400: validación o regla de negocio. 401: JWT ausente/incorrecto. 403: rol o empresa no autorizados, o CSRF inválido con sesión. 404: objeto inexistente o ajeno. 405: método no permitido. 429: límite anónimo excedido. No se devuelven trazas en respuestas de negocio.

```json
{
  "codigo": "monto_nota_credito_excedido",
  "mensaje": "Revise los datos de la operación.",
  "detalles": ["El monto debe ser positivo y no superar el saldo 106.20."]
}
```

Errores de DRF usan `codigo=error_solicitud` y conservan los detalles por campo. Un contador tiene acceso a lectura y descargas; las mutaciones exigen EMISOR/ADMIN. Usuarios ajenos no son enumerables mediante IDs de documentos.
