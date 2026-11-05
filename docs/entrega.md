# Informe de entrega y cumplimiento

Se modificó el proyecto abierto, conservando `facturacion`, `FacturacionSunat`, nombres de modelos, puntos de entrada de servicios y las migraciones iniciales. El README original se sustituyó por documentación que refleja la implementación real. No se generó otra aplicación principal ni un frontend React.

## Estado por módulo

| Módulo | Estado | Archivo | Prueba realizada |
|---|---|---|---|
| Modelos | COMPLETADO Y VERIFICADO | `facturacion/models.py`, `migrations/` | Migraciones SQLite/PostgreSQL, unicidad, validación e integridad histórica |
| Facturas | COMPLETADO Y VERIFICADO | `services.py`, `views.py` | RUC obligatorio, API y emisión real desde Chromium |
| Boletas | COMPLETADO Y VERIFICADO | `services.py`, `views.py` | DNI, serie B y compatibilidad de rutas |
| Notas de crédito | COMPLETADO Y VERIFICADO | `services.py`, `models.py` | Referencia, saldo acumulado, céntimos y competencia concurrente |
| IGV | COMPLETADO Y VERIFICADO | `services.py`, `static/facturacion/js/emitir.js` | Gravados/no gravados, descuentos y total dinámico S/ 91,00 validado en backend |
| Numeración | COMPLETADO Y VERIFICADO | `services.py` | Rollback, borradores, series independientes y cinco conexiones PostgreSQL |
| XML | COMPLETADO Y VERIFICADO | `xml_utils.py` | Análisis XML 01/03/07 y referencia al original; marca mock explícita |
| OSE Mock | COMPLETADO Y VERIFICADO | `ose_mock.py` | Aceptación, rechazo, XML malformado, logs y reenvíos |
| API REST | COMPLETADO Y VERIFICADO | `views.py`, `serializers.py`, `urls.py` | Siete endpoints, auxiliares, filtros, JWT y OpenAPI validado |
| Frontend | COMPLETADO Y VERIFICADO | `templates/`, `static/`, `web_views.py` | Todas las vistas, formularios y recorrido Chromium escritorio/móvil |
| PDF | COMPLETADO Y VERIFICADO | `pdf_utils.py`, `voucher.html` | Archivo PDF real, descarga y llamada de impresión; CSS print verificado |
| Reportes | COMPLETADO Y VERIFICADO | `reportes.py` | Créditos negativos, rechazados excluidos, CSV y XLSX abierto con openpyxl |
| JWT y roles | COMPLETADO Y VERIFICADO | `permissions.py`, `settings.py` | Login/refresh, sesiones, CSRF, ADMIN/EMISOR/CONTADOR y aislamiento empresarial |
| Testing | COMPLETADO Y VERIFICADO | `tests.py`, `test_*.py`, `pyproject.toml` | 64 aprobadas con PostgreSQL y Chromium; cobertura 95,35% |
| Documentación | COMPLETADO Y VERIFICADO | `README.md`, `docs/`, `schema.yml` | Manual, diez documentos formales, diagramas y matriz de 71 filas |

Los archivos sin prefijo en la tabla pertenecen a `facturacion/`, salvo `settings.py`, que corresponde a `FacturacionSunat/`.

## Cumplimiento de la rúbrica

La guía aporta ocho pesos y exige cobertura mínima de 60%; no ofrece una escala detallada de puntuación interna para cada categoría. Se calcula **cumplimiento técnico trazado**, no una calificación emitida por una institución. Cada categoría se considera cubierta cuando sus requisitos relacionados tienen implementación y evidencia de prueba o revisión identificada en la matriz.

| Categoría | Peso | Cobertura técnica de requisitos trazados | Aporte ponderado |
|---|---:|---:|---:|
| Modelos y base de datos | 15% | 100% | 15 |
| API REST | 15% | 100% | 15 |
| Lógica tributaria académica | 15% | 100% | 15 |
| Frontend web | 20% | 100% | 20 |
| Integración API/frontend | 10% | 100% | 10 |
| Autenticación y permisos | 10% | 100% | 10 |
| Testing | 10% | 100% del umbral y escenarios exigidos | 10 |
| Documentación y calidad | 5% | 100% | 5 |
| **Total técnico de la matriz** | **100%** | | **100/100** |

La fórmula es suma de `peso × fracción de requisitos trazados cumplidos` para las ocho categorías. Las 71 filas de trazabilidad, incluidas las ocho filas agregadas de rúbrica, tienen evidencia identificada. La cobertura de código **no es 100%**: se midió **95,35%**. El resultado técnico tampoco implica que un evaluador externo deba asignar la máxima nota de usabilidad, diseño o documentación.

## Alcance y límites

No quedan funcionalidades de la guía académica identificadas como pendientes en la matriz. La evidencia de navegador cubre Chromium en dos tamaños; no constituye una certificación universal de navegadores o accesibilidad. La numeración concurrente está verificada con PostgreSQL, no con SQLite. Los borradores se pueden guardar y emitir; la modificación posterior de sus líneas no se ofrece como una operación independiente.

El XML es una estructura académica basada en UBL 2.1 y **no está homologado contra XSD/Schematron SUNAT**. La marca de firma es textual y no criptográfica. No se emiten CDR reales ni se comunica con SUNAT/OSE real. Esas diferencias corresponden al mock solicitado y están documentadas, no se presentan como funcionalidades tributarias certificadas.

Las credenciales demo se generan aleatoriamente al crear usuarios; para ingresar después de la entrega puede establecer una contraseña propia con `python manage.py changepassword demo_admin`. Las pruebas usan bases temporales y no cambian las credenciales de la demostración local.
