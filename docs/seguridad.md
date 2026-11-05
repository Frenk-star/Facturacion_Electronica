# Seguridad y autorización multiempresa

## Identidad y ámbito

SimpleJWT autentica integradores; Django Authentication y sesiones autentican pantallas. Las contraseñas se almacenan con los hashers de Django. La creación de cuentas locales aplica los validadores de contraseña configurados. Los JWT no se guardan en localStorage en el frontend: este utiliza cookies de sesión y CSRF.

`empresa_autorizada` valida la empresa indicada en `X-Empresa-ID` o sesión contra las membresías activas del usuario. No acepta un `empresa_id` arbitrario del cuerpo. Si no hay selección, elige la primera empresa autorizada; sin membresías devuelve denegación. El selector web comprueba nuevamente la membresía antes de guardar la sesión.

| Capacidad | ADMIN local | EMISOR | CONTADOR |
|---|---|---|---|
| Consultar documentos, logs, PDF/XML y reportes | Sí | Sí | Sí |
| Emitir facturas/boletas/créditos y reenviar | Sí | Sí | No |
| Crear/editar/desactivar clientes/productos | Sí | Sí | No |
| Crear series y modificar empresa activa | Sí | No | No |
| Administrar usuarios y roles del ámbito | Sí | No | No |
| Administración global Django | Solo superusuario | No | No |

Los grupos ADMIN/EMISOR/CONTADOR se crean para identificar roles demo, pero la autoridad efectiva es `Membresia.rol`, local a cada empresa. Una persona puede tener distintos roles en empresas diferentes. Revocar una membresía restringe inmediatamente el acceso aunque conserve un JWT aún vigente.

Las cuentas compartidas con otras empresas no pueden modificar su perfil/contraseña desde un administrador local: se requiere intervención global o edición de la membresía local. Ningún serializer concede `is_superuser`, `is_staff`, permisos globales o una empresa ajena. Los documentos y catálogos se filtran antes de resolver IDs; los objetos ajenos responden 404. La administración global de la aplicación está reservada a superusuarios, incluso si un usuario posee permisos staff accidentales.

## Protección HTTP y datos

- Middleware CSRF activo; Fetch envía `X-CSRFToken` y credenciales del mismo origen. Logout requiere POST.
- Templates con autoescape y JavaScript que construye nodos con `textContent`, evitando insertar descripciones como HTML.
- PDF escapa textos antes de entregarlos a ReportLab. CSV/Excel neutralizan prefijos de fórmula en datos textuales.
- Errores de negocio normalizados sin trazas internas; logging registra la clase del error sin contraseñas ni tokens.
- Entradas numéricas y fechas validadas por serializers; cálculos del servidor con Decimal. El precio de una línea puede ajustarse explícitamente por un emisor autorizado; totales y estados no son editables por HTTP.
- Cookies HttpOnly/SameSite, cookies seguras con DEBUG desactivado, validación de hosts, cabecera contra sniffing y límites a solicitudes anónimas de API.
- Claves y credenciales leídas del entorno. `.env`, bases locales, intérpretes y artefactos de cobertura quedan ignorados por Git.

## Límites explícitos

La aplicación académica no incluye MFA, recuperación de contraseña por correo, auditoría de infraestructura, bloqueo específico del formulario de login, revocación individual de refresh tokens ni un servidor HTTPS incorporado. Estos controles adicionales no forman parte del flujo tributario simulado. El despliegue público requiere HTTPS, clave estable, DEBUG desactivado, respaldos y revisión de `check --deploy`.

La inmutabilidad ORM y los roles no sustituyen los permisos del administrador de la base de datos. Se deben restringir conexiones y cuentas de mantenimiento. No se ofrece aislamiento concurrente de emisión con SQLite.
