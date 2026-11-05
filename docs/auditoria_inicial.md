# Auditoría del repositorio inicial

La revisión se efectuó antes de modificar modelos, serializadores, servicios, vistas, rutas, configuración, seed, dependencias y las migraciones `0001`/`0002`.

| Componente | Evidencia inicial | Acción adoptada |
|---|---|---|
| Ocho entidades | Presentes en `models.py` | Conservar nombres y relaciones; ampliar restricciones y auditoría |
| IGV | Servicio usaba precios finales con IGV | Conservar criterio; validar y centralizar redondeo |
| Numeración | Bloqueo de serie existente; unicidad global serie/número | Ampliar ámbito a empresa/tipo/serie; separar borradores |
| Nota de crédito | Registro independiente, sin descuento acumulado | Vincular documento 07 y controlar saldo bajo bloqueo |
| XML | Cadena con declaración XML inválida y sin UBL | Sustituir por serialización XML estructurada académica |
| OSE | Aceptaba siempre | Añadir rechazo determinista, historial e intentos |
| API | CRUD sin permisos y emisión con excepción genérica | JWT, sesiones, roles, entradas validadas y rutas compatibles |
| Interfaz | Sin templates ni estáticos | Implementar interfaz Bootstrap local y Fetch |
| Pruebas | `tests.py` únicamente contenía el stub generado | Mantener archivo e incorporar escenarios reales |
| Seed | Empresa, series y catálogo idempotentes | Conservar entrada `run_seeder`; ampliar mediante comando |
| README | Describía Docker, Redis y arquitectura inexistentes | Reescribir conforme al código entregado |
| Entorno | Alias Python inaccesible, Git fuera del PATH | Preparar Python local ignorado y localizar Git instalado |

No se creó un proyecto o aplicación principal adicional. No se eliminaron las migraciones preexistentes. La carga y las pruebas usan exclusivamente el OSE simulado.
