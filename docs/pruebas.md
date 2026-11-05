# Estrategia y ejecución de pruebas

## Alcance

### Actualización del 5 de noviembre de 2026

`python manage.py test facturacion.test_consulta_ruc facturacion.test_consulta_dni --noinput`:
**9 pruebas aprobadas en SQLite**, sin incidencias de system check. Ruff aprobó los
módulos revisados. Incluye contratos, formatos, ausencia de token, errores HTTP/red,
permisos, POST, CSRF y rechazo de emisión real sin integración. No se recalculó
cobertura ni se repitió la suite histórica completa de 64 pruebas.

Consultas en vivo correctas: DNI `27427864` con Factiliza y RUC `20536066528` con
ConsultadeRUC.pe. Inicialmente fallaban por `WinError 10013`: el entorno bloqueaba
sockets externos. Funcionaron con red autorizada; se reinició el servidor con ese acceso.
Estas llamadas usan los proveedores reales y pueden consumir cuota.

Verificación puntual con Playwright y Edge/Chromium, escritorio 1440 × 1000:
primer cliente visible, sin recorte, recibe clic y rellena `cliente-id` en `/emitir/`.
Se comprobó `overflow: visible` en la tarjeta. El arreglo también se aplicó a productos;
no se afirma selección de producto en esta comprobación puntual. No se reemplazaron
capturas anteriores. La consulta automática se retiró; se revisó que las llamadas
externas se ejecutan desde los clics de Buscar y no desde eventos de escritura.

Las pruebas usan una base temporal creada por Django; no modifican los comprobantes de demostración de la base local. `tests.py` se conserva y contiene los escenarios principales. Los módulos complementarios `test_administracion.py`, `test_concurrencia.py` y `test_browser.py` evitan el conflicto entre un archivo `tests.py` y un paquete `tests/` con el mismo nombre.

| Módulo | Escenarios principales |
|---|---|
| `tests.py` | IGV incluido, no gravados, descuentos, redondeo, RUC/DNI/CE, emisión, rollback, borradores, correlativos por empresa, idempotencia, estados, reenvíos y logs |
| `tests.py` | Créditos vinculados/acumulados, cierre de céntimos, XML bien formado, datos históricos e inmutabilidad |
| `tests.py` | API protegida, JWT/refresh, filtros, permisos de contador, aislamiento multiempresa, CRUD y descargas |
| `tests.py` | Libro neto sin duplicación, CSV/Excel reales, formularios, sesiones, todas las páginas, Swagger y seed repetible |
| `test_administracion.py` | Usuarios/roles locales, cuentas compartidas, configuración, restricciones globales, decimales SQLite y créditos pequeños |
| `test_concurrencia.py` | Cinco emisiones simultáneas, cinco reintentos idempotentes, dos créditos competidores sobre el mismo saldo |
| `test_browser.py` | Chromium: autocompletado, líneas gravadas/no gravadas, descuento, vista previa, emisión, voucher, PDF, crédito, Excel, reenvío y menú móvil |

La cobertura mide código de aplicación, excluyendo migraciones y tests. El mínimo configurado es 60%; se persigue al menos 80% en lógica crítica. Las comprobaciones no sustituyen una auditoría tributaria ni una revisión exhaustiva de accesibilidad.

## Comandos reproducibles

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --noinput
python -m pytest --cov=facturacion --cov-report=term-missing --cov-report=html --cov-report=xml
python -m ruff check .
python -m black --check . --workers 1
python manage.py spectacular --validate --file schema.yml
```

Para navegador instalar `requirements-browser.txt` y ejecutar `python -m playwright install chromium`; definir `RUN_BROWSER_TESTS=1`. En esta estación se utilizó `PLAYWRIGHT_BROWSERS_PATH` apuntando a `.runtime/browsers`, sin instalar navegadores globalmente. Los tests PostgreSQL se omiten en SQLite y se habilitan automáticamente si las variables `POSTGRES_*` seleccionan ese motor.

## Evidencia observada durante la implementación

La primera ejecución de 48 escenarios detectó dos expectativas incorrectas en los tests: borrado protegido por FK y duplicación de argumento en un helper. Corregidos, pasaron. La prueba Chromium descubrió que el menú móvil cubría el control de cierre; se añadió un botón interno y Escape, y el recorrido completo pasó al repetirlo.

Ejecución ampliada con SQLite: **56 pruebas aprobadas, 4 omitidas**, cobertura de aplicación **95,33%**; servicios **97%**. Las omisiones corresponden a una prueba de navegador optativa y tres pruebas PostgreSQL. La prueba optativa de Chromium se ejecutó por separado y **pasó**. Estos resultados son una medición intermedia; el registro final se encuentra al final de este documento y en la matriz.

Las capturas reales están en [dashboard escritorio](evidencias/dashboard-desktop.png), [emisión](evidencias/emision-desktop.png), [voucher](evidencias/voucher.png) y [dashboard móvil](evidencias/dashboard-mobile.png). Las imágenes provienen del recorrido con una base temporal y no de datos fabricados para un mockup.

## Límites de verificación

El navegador comprueba un tamaño de escritorio y otro móvil; no certifica todos los navegadores ni dispositivos. El PDF se verifica por descarga y estructura binaria; el botón de impresión usa `window.print()` y se puede revisar con el diálogo del navegador. No se solicita impresión física. El XML se analiza y se inspeccionan sus referencias, sin validación XSD oficial ni firma digital.

## Registro final ejecutado

Fecha: 5 de noviembre de 2026. Python 3.12.10, Django 5.2.19, PostgreSQL 17.11 y Chromium de Playwright. La instancia PostgreSQL fue temporal, local a 127.0.0.1:55432, autenticada con contraseña aleatoria fuera del repositorio versionado y detenida al terminar.

| Verificación | Resultado observado |
|---|---|
| `manage.py check` | Sin incidencias |
| `makemigrations --check --dry-run` | No changes detected |
| `manage.py migrate --noinput` | Migraciones 0001–0006 aplicadas; también sobre base temporal PostgreSQL |
| `manage.py test --noinput` con SQLite | 64 descubiertas; 60 aprobadas y 4 omitidas explícitamente por motor/opt-in |
| pytest con PostgreSQL y RUN_BROWSER_TESTS=1 | **64 aprobadas, 0 fallidas, 0 omitidas; 44,33 segundos** |
| Cobertura de aplicación | **95,35%: 1168 de 1225 sentencias** |
| Cobertura de servicios | 97% redondeado; XML, PDF y OSE mock 100% de sentencias |
| `ruff check .` | All checks passed |
| `black --check . --workers 1` | 32 archivos sin cambios necesarios |
| `spectacular --validate --file schema.yml` | Código de salida 0, sin errores ni advertencias |
| `collectstatic --noinput` | 185 recursos copiados |
| `seed_demo` dos veces | Sin duplicaciones; además comprobado en tests |

La comprobación final de impresión sustituye temporalmente `window.print` por un contador, pulsa el botón y comprueba una única invocación; emula media `print` y verifica voucher visible y sidebar oculto. No afirma impresión física.

Evidencias versionables: [JUnit PostgreSQL](evidencias/pytest-postgresql.xml), [cobertura JSON](evidencias/cobertura.json), [cobertura resumida](evidencias/cobertura.txt) y capturas. `coverage.xml`, `.coverage` y `htmlcov/` se generan localmente y están ignorados por Git. Las pruebas de navegador y concurrencia no se cuentan como omitidas en la ejecución PostgreSQL completa.
