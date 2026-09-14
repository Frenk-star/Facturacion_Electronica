# Facturacion_Electronica

# Sistema de Facturación Electrónica SUNAT (Peru)

Sistema web de gestión de ventas y emisión de comprobantes electrónicos (Facturas, Boletas y Notas de Crédito) adaptado a las normativas de la SUNAT, estructurado bajo **Arquitectura Hexagonal (Nivel 3)** y patrones de diseño avanzadas de software.

---

## Descripción del Sistema
Gestiona el ciclo de vida completo de la facturación electrónica:
* Emisión con cálculo automático de IGV (18%) y validaciones tributarias.
* Generación de XML y simulación de respuesta CDR de OSE/SUNAT.
* Flujo de estados: `BORRADOR` ➔ `EMITIDO` ➔ `ENVIADO` ➔ `ACEPTADO` / `RECHAZADO`.
* Emisión de Notas de Crédito referenciadas a comprobantes originales.
* Exportación de Libro de Ventas en formato Excel.

---

## Exigencias Académicas Implementadas

### NIVEL 1 — Obligatorio (25% de la nota)
* **Service Layer:** Capa de servicios decoupled que encapsula las reglas de negocio. Las vistas solo procesan peticiones HTTP.
* **Excepciones de Dominio:** Jerarquía propia de excepciones en `exceptions.py` (`ComprobanteAceptadoNoEliminableException`, `MontoExcedidoException`, etc.).
* **Soft Delete + Auditoría:** Modelo base abstracto `AuditoriaModel` con `creado_en`, `actualizado_en`, `creado_por`, `activo` y método `eliminar()` de borrado lógico.
* **Docker Compose:** Orquestación completa con Django + PostgreSQL + Redis y `.env.example`.

### NIVEL 2 — Patrón de Diseño
* **Strategy Pattern & Repository Pattern:** 
  * *Strategy Pattern:* Reglas de cálculo de tributos y estrategias de validación de comprobantes según tipo (Factura vs Boleta).
  * *Repository Pattern:* Abstracción total del ORM de Django mediante interfaces.

### NIVEL 3 — Arquitectura Hexagonal (Bonus +10 Puntos)
* Estructura de carpetas estrictamente separada:
  * `dominio/`: Dataclasses de Python puro y contratos (`typing.Protocol`). **Cero dependencias de Django.**
  * `infraestructura/`: Adaptadores ORM, repositorios Django y servicios de terceros.
  * `interfaces/`: Vistas de Django, adaptadores REST y controladores web.

---

## Entidades del Modelo de Datos
* **Empresa:** RUC, Razón Social, Nombre Comercial, Dirección, Régimen Tributario.
* **SerieComprobante:** Tipo (F/B/FC), Serie, Correlativo Actual, Empresa.
* **Cliente:** Tipo Documento (RUC/DNI/CE), Número Documento, Razón Social, Dirección, Email.
* **Producto:** Código, Descripción, Unidad Medida, Precio Unitario, Afecto IGV.
* **Comprobante:** Serie, Número, Fecha, Cliente, Tipo, Subtotal, IGV, Total, Estado, XML Firmado.
* **DetalleComprobante:** Comprobante, Producto, Cantidad, Precio Unitario, Descuento, IGV Línea, Subtotal.
* **LogEnvioSUNAT:** Comprobante, Fecha Envío, Estado Respuesta, Código Respuesta, Descripción.
* **NotaCredito:** Comprobante Referencia, Motivo, Tipo Nota, Monto Afectado.

---

## Endpoints API REST Minimos
* `POST /api/facturas/` — Emitir factura con cálculo de IGV y simulación XML.
* `POST /api/boletas/` — Emitir boleta de venta.
* `POST /api/notas-credito/` — Emitir nota de crédito referenciada.
* `GET /api/comprobantes/?tipo=&fecha_desde=&ruc_cliente=` — Listado filtrado.
* `POST /api/comprobantes/{id}/reenviar/` — Reintentar envío de rechazados.
* `GET /api/comprobantes/{id}/pdf/` — Vista imprimible / Voucher.
* `GET /api/reportes/ventas-por-periodo/?mes=&anio=` — Libro de ventas simplificado.

---

## Pantallas Web (Bootstrap 5)
1. **Dashboard:** Métricas del mes, comprobantes emitidos, alertas de rechazados.
2. **Emitir Comprobante:** Formulario interactivo con tabla dinámica y cálculo en tiempo real.
3. **Lista de Comprobantes:** Listado paginado con insignias de estado SUNAT (Verde, Rojo, Amarillo).
4. **Vista Previa / Voucher:** Formato ticket para impresión o exportación a PDF.
5. **Emitir Nota de Crédito:** Búsqueda del comprobante original y validación de saldos.
6. **Mantenimientos CRUD:** Gestión de Clientes y Productos.
7. **Reporte Libro de Ventas:** Tabla mensual con exportación a Excel (.xlsx).

---

## Instrucciones para Ejecución Local

### Opción 1: Con Docker Compose (Recomendado)
```bash
docker compose up --build