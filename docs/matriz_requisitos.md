# Matriz de trazabilidad académica

La matriz relaciona requisitos del enunciado con código y evidencias ejecutables. Los nombres `test_*` pertenecen a `facturacion/tests.py`, `test_administracion.py`, `test_concurrencia.py` o `test_browser.py`. La prueba de navegador se habilita con `RUN_BROWSER_TESTS=1`; las de bloqueo requieren PostgreSQL.

Estados autorizados: COMPLETADO Y VERIFICADO, IMPLEMENTADO SIN VERIFICAR, PARCIAL, PENDIENTE. Verificado significa implementado con evidencia específica; no implica homologación SUNAT ni cobertura absoluta de todos los entornos.

| ID | Requisito | Módulo | Archivo | Prueba | Estado |
|---|---|---|---|---|---|
| M01 | Empresa | Modelos | facturacion/models.py | test_empresa_edicion | COMPLETADO Y VERIFICADO |
| M02 | SerieComprobante | Modelos | facturacion/models.py | test_correlativos_sucesivos | COMPLETADO Y VERIFICADO |
| M03 | Cliente | Modelos | facturacion/models.py | test_validacion_modelo_documento | COMPLETADO Y VERIFICADO |
| M04 | Producto | Modelos | facturacion/models.py | test_unicidad_catalogo | COMPLETADO Y VERIFICADO |
| M05 | Comprobante | Modelos | facturacion/models.py | test_factura_historial_logs_xml | COMPLETADO Y VERIFICADO |
| M06 | DetalleComprobante | Modelos | facturacion/models.py | test_mixto_totales | COMPLETADO Y VERIFICADO |
| M07 | LogEnvioSUNAT | Modelos | facturacion/models.py | test_api_reenvio_logs_descargas | COMPLETADO Y VERIFICADO |
| M08 | NotaCredito | Modelos | facturacion/models.py | test_credito_vinculado_xml | COMPLETADO Y VERIFICADO |
| API01 | POST /api/facturas/ | API REST | facturacion/views.py; facturacion/urls.py | test_api_factura_backend_recalcula | COMPLETADO Y VERIFICADO |
| API02 | POST /api/boletas/ | API REST | facturacion/views.py; facturacion/urls.py | test_api_boleta_legacy | COMPLETADO Y VERIFICADO |
| API03 | POST /api/notas-credito/ | API REST | facturacion/views.py; facturacion/urls.py | test_api_nota_credito | COMPLETADO Y VERIFICADO |
| API04 | GET /api/comprobantes/ | API REST | facturacion/views.py; facturacion/urls.py | test_api_filtros | COMPLETADO Y VERIFICADO |
| API05 | POST /api/comprobantes/{id}/reenviar/ | API REST | facturacion/views.py; facturacion/urls.py | test_api_reenvio_logs_descargas | COMPLETADO Y VERIFICADO |
| API06 | GET /api/comprobantes/{id}/pdf/ | API REST | facturacion/views.py; facturacion/urls.py | test_api_reenvio_logs_descargas | COMPLETADO Y VERIFICADO |
| API07 | GET /api/reportes/ventas-por-periodo/ | API REST | facturacion/views.py; facturacion/urls.py | test_reportes_neto_sin_duplicacion | COMPLETADO Y VERIFICADO |
| WEB01 | Login | Frontend | facturacion/templates/facturacion/login.html | test_web_sesiones_roles_empresa | COMPLETADO Y VERIFICADO |
| WEB02 | Dashboard y gráficos | Frontend | facturacion/templates/facturacion/dashboard.html | test_flujo_completo | COMPLETADO Y VERIFICADO |
| WEB03 | Emisión y vista previa | Frontend | facturacion/templates/facturacion/emitir.html | test_flujo_completo | COMPLETADO Y VERIFICADO |
| WEB04 | Listado paginado con filtros | Frontend | facturacion/templates/facturacion/comprobantes.html | test_api_filtros; test_paginas_web_y_voucher | COMPLETADO Y VERIFICADO |
| WEB05 | Detalle e historial | Frontend | facturacion/templates/facturacion/comprobante_detalle.html | test_paginas_web_y_voucher | COMPLETADO Y VERIFICADO |
| WEB06 | Voucher e impresión | Frontend | facturacion/templates/facturacion/voucher.html | test_flujo_completo | COMPLETADO Y VERIFICADO |
| WEB07 | Notas de crédito | Frontend | facturacion/templates/facturacion/nota_credito.html | test_flujo_completo | COMPLETADO Y VERIFICADO |
| WEB08 | Clientes CRUD y desactivación | Frontend | facturacion/templates/facturacion/clientes.html | test_api_crud_catalogos; test_formularios_web_y_busquedas | COMPLETADO Y VERIFICADO |
| WEB09 | Formulario de cliente | Frontend | facturacion/templates/facturacion/cliente_form.html | test_formularios_web_y_busquedas | COMPLETADO Y VERIFICADO |
| WEB10 | Historial de cliente | Frontend | facturacion/templates/facturacion/cliente_detalle.html | test_paginas_web_y_voucher | COMPLETADO Y VERIFICADO |
| WEB11 | Productos/servicios CRUD | Frontend | facturacion/templates/facturacion/productos.html | test_formularios_web_y_busquedas | COMPLETADO Y VERIFICADO |
| WEB12 | Formulario de producto | Frontend | facturacion/templates/facturacion/producto_form.html | test_formularios_web_y_busquedas | COMPLETADO Y VERIFICADO |
| WEB13 | Libro mensual y descargas | Frontend | facturacion/templates/facturacion/reporte_ventas.html | test_flujo_completo; test_exportaciones | COMPLETADO Y VERIFICADO |
| WEB14 | Configuración ADMIN | Frontend | facturacion/templates/facturacion/configuracion.html | test_configuracion_web; test_usuarios_administracion_local | COMPLETADO Y VERIFICADO |
| R01 | Numeración única sin saltos ante rollback | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_rollback_no_consume_correlativo; test_numeracion_sin_duplicados_ni_saltos | COMPLETADO Y VERIFICADO |
| R02 | Factura requiere RUC de 11 dígitos | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_factura_requiere_ruc | COMPLETADO Y VERIFICADO |
| R03 | Boleta acepta DNI | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_boleta_acepta_dni | COMPLETADO Y VERIFICADO |
| R04 | IGV 18% incluido y no gravados | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_igv_incluido; test_igv_no_gravado | COMPLETADO Y VERIFICADO |
| R05 | Crédito no supera saldo acumulado | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_creditos_acumulados_y_cierre_impuestos; test_creditos_concurrentes_no_superan_saldo | COMPLETADO Y VERIFICADO |
| R06 | Aceptados no eliminables e importes inmutables | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_aceptado_no_eliminable_ni_editable | COMPLETADO Y VERIFICADO |
| R07 | Flujo BORRADOR a ACEPTADO/RECHAZADO | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_factura_historial_logs_xml; test_estado_invalido | COMPLETADO Y VERIFICADO |
| R08 | Logs de envío y reenvío | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_rechazo_reenvio_mismo_numero | COMPLETADO Y VERIFICADO |
| R09 | Filtrado por empresa | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_multiempresa_lectura_escritura | COMPLETADO Y VERIFICADO |
| R10 | Roles por membresía | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_contador_solo_lectura; test_series_solo_administrador | COMPLETADO Y VERIFICADO |
| R11 | API protegida | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_api_protegida; test_jwt_y_refresh | COMPLETADO Y VERIFICADO |
| R12 | Cálculo navegador y servidor | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_flujo_completo; test_api_factura_backend_recalcula | COMPLETADO Y VERIFICADO |
| R13 | XML académico 01/03/07 | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_factura_historial_logs_xml; test_boleta_acepta_dni; test_credito_vinculado_xml | COMPLETADO Y VERIFICADO |
| R14 | PDF e impresión | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_api_reenvio_logs_descargas; test_flujo_completo | COMPLETADO Y VERIFICADO |
| R15 | Reporte sin doble conteo | Reglas críticas | facturacion/services.py; views.py; permissions.py; reportes.py | test_reportes_neto_sin_duplicacion | COMPLETADO Y VERIFICADO |
| A21 | Emisión y cálculo correcto | Aceptación | facturacion/services.py | test_mixto_totales; test_api_factura_backend_recalcula | COMPLETADO Y VERIFICADO |
| A22 | Autocompletado real y totales dinámicos | Aceptación | facturacion/static/facturacion/js/emitir.js | test_flujo_completo | COMPLETADO Y VERIFICADO |
| A23 | Voucher e impresión | Aceptación | facturacion/templates/facturacion/voucher.html | test_flujo_completo | COMPLETADO Y VERIFICADO |
| A24 | Nota de crédito vinculada | Aceptación | facturacion/services.py; xml_utils.py | test_credito_vinculado_xml; test_flujo_completo | COMPLETADO Y VERIFICADO |
| A25 | Libro de ventas mensual | Aceptación | facturacion/reportes.py | test_reportes_neto_sin_duplicacion; test_exportaciones | COMPLETADO Y VERIFICADO |
| Q01 | Compatibilidad de estructura y migraciones originales | Calidad e integración | facturacion/migrations/ | manage.py migrate; makemigrations --check --dry-run | COMPLETADO Y VERIFICADO |
| Q02 | Borrador sin consumo y emisión posterior | Calidad e integración | facturacion/services.py | test_borrador_sin_numero_y_emision | COMPLETADO Y VERIFICADO |
| Q03 | Idempotencia ante solicitudes simultáneas | Calidad e integración | facturacion/services.py | test_idempotencia_concurrente; test_claves_no_reutilizables_con_otros_datos | COMPLETADO Y VERIFICADO |
| Q04 | Datos históricos del emisor/receptor/producto | Calidad e integración | facturacion/models.py; services.py | test_datos_historicos | COMPLETADO Y VERIFICADO |
| Q05 | Descuentos y redondeo comercial | Calidad e integración | facturacion/services.py | test_descuento; test_redondeo_comercial; test_decimales_sqlite_no_producen_falsos_rechazos | COMPLETADO Y VERIFICADO |
| Q06 | Exportación CSV/Excel sin fórmulas de usuario | Calidad e integración | facturacion/reportes.py | test_exportaciones; revisión de _texto_seguro | COMPLETADO Y VERIFICADO |
| Q07 | OpenAPI/Swagger y recursos locales | Calidad e integración | facturacion/urls.py; schema.yml | test_swagger_schema; spectacular --validate; collectstatic | COMPLETADO Y VERIFICADO |
| Q08 | Seed repetible sin claves permanentes | Calidad e integración | facturacion/management/commands/seed_demo.py; seed.py | test_seed_repetible; dos ejecuciones seed_demo | COMPLETADO Y VERIFICADO |
| Q09 | Sesión, logout y CSRF | Calidad e integración | facturacion/web_urls.py; static/facturacion/js/app.js | test_web_sesiones_roles_empresa; test_csrf_sesion_exigido_en_mutaciones | COMPLETADO Y VERIFICADO |
| Q10 | Gestión local de usuarios, empresas y series | Calidad e integración | facturacion/views.py; templates/facturacion/configuracion.html | test_usuarios_administracion_local; test_empresa_edicion; test_series_solo_administrador | COMPLETADO Y VERIFICADO |
| Q11 | Errores de negocio con códigos y logging | Calidad e integración | facturacion/exceptions.py | test_api_errores_validacion; test_empresa_invalida_no_genera_error_interno | COMPLETADO Y VERIFICADO |
| Q12 | Ruff, Black, pytest y cobertura mínima | Calidad e integración | pyproject.toml | ruff check; black --check; pytest --cov | COMPLETADO Y VERIFICADO |
| Q13 | Documentación formal de arquitectura/datos/reglas/API/XML/seguridad/pruebas/manual/despliegue/trazabilidad | Calidad e integración | docs/; README.md | Revisión de rutas, comandos y correspondencia con implementación | COMPLETADO Y VERIFICADO |
| Q14 | Interfaz responsive, mensajes, carga y protección de doble clic | Calidad e integración | facturacion/static/facturacion/ | test_flujo_completo; capturas escritorio y móvil | COMPLETADO Y VERIFICADO |
| E01 | Modelos y base de datos: 15% | Rúbrica | facturacion/models.py; migrations/ | M01–M08, R01, Q01, Q04 | COMPLETADO Y VERIFICADO |
| E02 | API REST: 15% | Rúbrica | facturacion/views.py; serializers.py; urls.py | API01–API07, Q07, Q11 | COMPLETADO Y VERIFICADO |
| E03 | Lógica tributaria: 15% | Rúbrica | facturacion/services.py; xml_utils.py; ose_mock.py | R01–R08, R13, A21, A24 | COMPLETADO Y VERIFICADO |
| E04 | Frontend web: 20% | Rúbrica | facturacion/templates/; static/; web_views.py | WEB01–WEB14, A22–A25, Q14 | COMPLETADO Y VERIFICADO |
| E05 | Integración API/frontend: 10% | Rúbrica | facturacion/static/facturacion/js/ | test_flujo_completo, Q03, Q09 | COMPLETADO Y VERIFICADO |
| E06 | Autenticación y permisos: 10% | Rúbrica | facturacion/permissions.py; views.py; settings.py | R09–R11, Q09–Q10 | COMPLETADO Y VERIFICADO |
| E07 | Testing: 10% | Rúbrica | facturacion/tests.py; test_*.py; pyproject.toml | Suite SQLite, PostgreSQL y Chromium; cobertura | COMPLETADO Y VERIFICADO |
| E08 | Documentación y calidad: 5% | Rúbrica | README.md; docs/; pyproject.toml | Q12–Q13, check, lint y formato | COMPLETADO Y VERIFICADO |

## Método de evaluación

Actualización de alcance: consulta externa RUC/DNI **PENDIENTE** y aplazada por el usuario. Las evidencias de autocompletado de esta matriz corresponden exclusivamente a búsquedas en clientes locales; no verifican consultas externas. Véase `pendientes.md`.

La guía proporciona ponderaciones por categoría, pero no descriptores numéricos detallados dentro de cada una. Esta entrega usa trazabilidad binaria por requisito como evidencia de cumplimiento y conserva separada la calificación académica, que corresponde al evaluador. La cobertura automatizada no se interpreta como porcentaje de la rúbrica.

Los porcentajes definitivos y los límites de verificación se registran en `docs/entrega.md`, después de ejecutar la verificación final. Una aceptación OSE mock no se cuenta como aceptación tributaria real.
