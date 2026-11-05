# Nexo · Facturación electrónica académica

Aplicación Django existente `facturacion`, configurada en `FacturacionSunat`, ampliada con API REST y frontend de Django Templates, Bootstrap 5 local y JavaScript. Permite emitir facturas, boletas y notas de crédito con cálculo decimal, numeración transaccional, historial, XML académico, OSE simulado, PDF y libro de ventas.

**No envía documentos a SUNAT. No proporciona una firma digital válida, CDR real ni homologación UBL.** El término «SUNAT-ready académico» describe la separación de reglas y transporte para un ejercicio educativo; no autoriza uso tributario real.

## Instalación

Requiere Python 3.12 o superior. Se utiliza Django 5.2 LTS para disponer de una base compatible y verificable con Python 3.12, DRF y SimpleJWT; se conservan el proyecto y las migraciones originales.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Copiar el valor generado a DJANGO_SECRET_KEY en .env.
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

En Linux/macOS: activar con `source .venv/bin/activate` y copiar con `cp .env.example .env`. En el entorno de trabajo donde se desarrolló esta entrega existe además un intérprete local ignorado por Git: `.runtime/python.exe`; puede sustituir a `python` en los comandos. Este directorio es una herramienta de verificación, no un componente distribuible del proyecto.

Abrir `http://127.0.0.1:8000/`. `seed.py` sigue disponible y delega al comando `seed_demo`. La carga es idempotente: crea empresa, series F001/B001/FC01, clientes RUC/DNI, productos gravados/no gravados, usuarios `demo_admin`, `demo_emisor`, `demo_contador`, documentos aceptados/rechazados y un borrador. Las contraseñas iniciales se generan aleatoriamente y aparecen **solo al crear cada usuario**; alternativamente se lee `DEMO_PASSWORD` del entorno. No se guardan contraseñas permanentes en el repositorio. Para restablecer una contraseña: `python manage.py changepassword demo_emisor`.

Un superusuario se crea con `python manage.py createsuperuser`. Puede administrar empresas y membresías globales en `/admin/`. Un ADMIN local gestiona datos de su empresa, series, usuarios y roles en `/configuracion/`. Ningún rol local recibe automáticamente `is_staff` o `is_superuser`.

## Configuración y base de datos

Consultar [.env.example](.env.example). `DJANGO_SECRET_KEY` debe ser estable entre procesos; si se omite en desarrollo se genera una clave efímera y las sesiones/JWT dejan de ser válidos al reiniciar. En producción se exige una clave explícita y cookies seguras.

Sin `POSTGRES_DB`, utiliza SQLite para demostración local sin concurrencia. Para verificar o utilizar emisión concurrente, configurar `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` y `POSTGRES_PORT`, y ejecutar las migraciones sobre PostgreSQL. El usuario de pruebas requiere permiso para crear bases de datos de prueba. **SQLite no implementa el bloqueo `select_for_update()`**; no se ofrece la garantía concurrente con ese motor. Véase [documentación oficial de Django](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).

Las migraciones `0001` y `0002` se conservan. Las nuevas migraciones añaden ámbito empresarial, snapshots, membresías, historial y restricciones. El catálogo antiguo se asigna según su uso y se clona cuando estaba compartido entre empresas. Los registros ambiguos sin empresa permanecen fuera de las consultas de usuarios hasta que el superusuario los clasifique; no se asignan arbitrariamente. Los números históricos se preservan.

## Organización

```text
facturacion/
  models.py, serializers.py, services.py, views.py, urls.py
  permissions.py, exceptions.py, signals.py, forms.py
  web_views.py, web_urls.py, xml_utils.py, pdf_utils.py, reportes.py, ose_mock.py
  management/commands/seed_demo.py
  templates/facturacion/, static/facturacion/
  tests.py, test_administracion.py, test_concurrencia.py, test_browser.py
FacturacionSunat/
docs/
```

No se incorpora una arquitectura hexagonal, otra aplicación principal ni un frontend separado. Las vistas delegan reglas tributarias en servicios; los cálculos monetarios del backend se centralizan en `services.py`.

## API y autenticación

Swagger: `/api/docs/`. OpenAPI: `/api/schema/`. Esquema exportado: `schema.yml`.

```text
POST /api/token/                         Usuario y contraseña → access + refresh
POST /api/token/refresh/                 Refresh → access
POST /api/facturas/                      Emitir o guardar borrador
POST /api/boletas/                       Emitir o guardar borrador
POST /api/notas-credito/                 Emitir crédito vinculado
GET  /api/comprobantes/                  Listado paginado
POST /api/comprobantes/{id}/emitir/      Emitir borrador existente
POST /api/comprobantes/{id}/reenviar/    Reintentar rechazado
GET  /api/comprobantes/{id}/pdf/         Voucher PDF
GET  /api/comprobantes/{id}/xml/         XML académico
GET  /api/comprobantes/{id}/logs/        Intentos OSE
GET  /api/comprobantes/{id}/historial/   Transiciones
GET  /api/reportes/ventas-por-periodo/   Libro mensual, JSON/CSV/XLSX
GET  /api/reportes/dashboard/            Estadísticas
```

Catálogos CRUD `/api/clientes/`, `/api/productos/`; DELETE desactiva. `/api/series/` lista y crea; no permite editar contadores. `/api/empresas/` consulta/actualiza la empresa activa. `/api/usuarios/` y `/api/membresias/` administran accesos locales. Se conservan `/api/comprobantes/emitir-factura/` y `emitir-boleta/`. Detalles completos, filtros y errores: [API REST](docs/api_rest.md).

La API acepta `Authorization: Bearer <access>` y sesiones Django con CSRF para el frontend. La empresa activa se selecciona por sesión o cabecera `X-Empresa-ID`, **siempre validando la membresía**. Un `empresa_id` del cuerpo no amplía permisos.

Ejemplo de emisión:

```json
{
  "cliente_id": 1,
  "serie": "F001",
  "clave_idempotencia": "venta-externa-0001",
  "resultado_mock": "ACEPTADO",
  "items": [
    {"producto_id": 1, "cantidad": "2.00", "precio_unitario": "118.00", "descuento": "11.80"}
  ]
}
```

Agregar `"borrador": true` guarda sin consumir correlativo. Los identificadores corresponden a los datos de la empresa autorizada. Los totales enviados por el navegador se ignoran.

## Reglas y reportes

- **Precios con IGV incluido**, conservando el criterio original. Descuento monetario por línea, también con IGV. `total_línea = cantidad × precio − descuento`; `base_gravada = total_línea / 1.18`; `IGV = total_línea − base`. Redondeo comercial por línea con `Decimal` a dos decimales. No gravado: base igual al total e IGV cero. `subtotal` suma bases gravadas y no gravadas.
- Factura exige RUC numérico de 11 dígitos; boleta acepta DNI de 8 dígitos y otros documentos válidos del catálogo. El ejercicio no consulta RENIEC/SUNAT ni valida existencia del contribuyente.
- La numeración usa `atomic()` y bloqueo de empresa/serie en PostgreSQL. Un fallo antes del commit revierte documento y contador; borradores sin número; reenvíos con el número original. El navegador genera claves de idempotencia y bloquea doble envío.
- Estados: `BORRADOR → EMITIDO → ENVIADO → ACEPTADO / RECHAZADO`; `RECHAZADO → ENVIADO` para reintentar. Se registra cada transición y actor. Los documentos emitidos son inmutables y no se eliminan.
- Crédito sobre original aceptado 01/03, con motivo, tipo e importe positivo. El original se bloquea para restar créditos previos. Créditos rechazados reservan saldo para su eventual reenvío. La distribución de IGV es proporcional y el cierre absorbe céntimos sin exceder impuestos originales.
- OSE determinista: `resultado_mock` elige aceptación o rechazo, sin llamadas externas. XML bien formado inspirado en UBL 2.1 para 01/03/07, con indicación expresa de firma mock.
- Libro mensual: solo aceptados, por **fecha del documento**. Facturas/boletas suman, créditos restan una sola vez. Los rechazados se informan y excluyen. CSV y Excel usan exactamente las filas del reporte y neutralizan fórmulas en textos de usuario.

## Verificación y calidad

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python -m pytest --cov=facturacion --cov-report=term-missing --cov-report=html --cov-report=xml
python -m ruff check .
python -m black --check . --workers 1
python manage.py spectacular --validate --file schema.yml
```

Configuración común en `pyproject.toml`: Ruff, Black (100 columnas), pytest-django y Coverage con mínimo 60%. Las pruebas de concurrencia se omiten en SQLite y se ejecutan con PostgreSQL. El navegador es optativo:

```powershell
python -m pip install -r requirements-browser.txt
python -m playwright install chromium
$env:RUN_BROWSER_TESTS='1'
python manage.py test facturacion.test_browser
```

En Linux/macOS usar `RUN_BROWSER_TESTS=1 python manage.py test facturacion.test_browser`. Las capturas se escriben en `docs/evidencias/`. Resultados ejecutados, cobertura y limitaciones: [pruebas](docs/pruebas.md) y [matriz](docs/matriz_requisitos.md).

## Documentación formal

[Arquitectura](docs/arquitectura.md) · [Modelo de datos](docs/modelo_datos.md) · [Reglas de negocio](docs/reglas_negocio.md) · [API](docs/api_rest.md) · [XML](docs/xml_sunat.md) · [Seguridad](docs/seguridad.md) · [Pruebas](docs/pruebas.md) · [Manual](docs/manual_usuario.md) · [Despliegue](docs/despliegue.md) · [Trazabilidad](docs/matriz_requisitos.md) · [Auditoría inicial](docs/auditoria_inicial.md).

## Resultado de la entrega

Verificación final: **64 pruebas aprobadas con PostgreSQL y Chromium**, sin omisiones; cobertura de aplicación **95,35%**. Check, migraciones consistentes, Ruff, Black, OpenAPI y recursos estáticos verificados. Consultar el [informe por módulo y rúbrica](docs/entrega.md) y la [evidencia de pruebas](docs/pruebas.md).

## Traslado y publicación

Consultar [ejecución paso a paso en otra PC](docs/ejecutar_otra_pc.md), [resumen completo del sistema](docs/resumen_sistema.md) y [publicación sin información privada](docs/publicacion_git.md). Las credenciales concretas, configuración real y bases de datos se mantienen fuera del código público; cada instalación crea su propia configuración y cuentas.
