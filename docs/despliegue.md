# Instalación, ejecución y despliegue

## Entorno local

Python 3.12+, dependencias de `requirements.txt` y SQLite incluido en Python. Crear entorno virtual, instalar dependencias, copiar `.env.example`, generar clave propia y ejecutar `migrate`, `seed_demo` y `runserver`. Las instrucciones exactas para PowerShell están en README. No es necesario Node, React, Redis ni Docker.

Bootstrap 5.3.3 se entrega localmente en `static/facturacion/vendor/bootstrap.min.css` y conserva su aviso de licencia. Swagger usa `drf-spectacular-sidecar`. Gráficos y estilos no descargan bibliotecas desde Internet al navegar.

## Variables

| Variable | Uso |
|---|---|
| DJANGO_SECRET_KEY | Firma estable de sesiones/JWT; obligatoria con DEBUG false |
| DJANGO_DEBUG | `true` solo en desarrollo; valor inicial de ejemplo |
| DJANGO_ALLOWED_HOSTS | Nombres autorizados separados por coma |
| POSTGRES_DB | Activa PostgreSQL si no está vacía |
| POSTGRES_USER / POSTGRES_PASSWORD | Credenciales del motor |
| POSTGRES_HOST / POSTGRES_PORT | Servidor y puerto, por defecto localhost:5432 |
| DEMO_PASSWORD | Opcional, solo al crear usuarios demo; preferir generación aleatoria |
| RUN_BROWSER_TESTS | `1` habilita pruebas optativas con Playwright |
| PLAYWRIGHT_BROWSERS_PATH | Ubicación opcional de navegadores instalados |

La clave efímera de desarrollo evita incorporar secretos al código, pero invalida sesiones al reiniciar; configurar `.env` para uso normal. El entorno de CI debe definir claves propias y un motor temporal; no debe apuntar a una base productiva.

## PostgreSQL y migraciones

Crear base y usuario con permisos limitados de aplicación; definir las variables y ejecutar `python manage.py migrate`. Para pruebas, habilitar creación de base de prueba en una instancia aislada. Los tests de `TransactionTestCase` verifican concurrencia con conexiones independientes. No trasladar las garantías de esas pruebas a SQLite.

Respaldar la base antes de actualizar un despliegue existente. La migración de datos antigua asigna catálogos según documentos o empresa única; duplica solo cuando los datos estaban compartidos entre distintas empresas. Los casos sin empresa deducible requieren asignación del superusuario. Los créditos históricos sin documento 07 siguen reservando saldo, pero no se fabrican documentos ni aceptaciones retroactivas para ellos.

## Servicio público

Usar PostgreSQL, clave estable, DEBUG false, hosts concretos y HTTPS. Ejecutar `collectstatic` y servir `STATIC_ROOT` desde el servidor web. Usar un servidor WSGI/ASGI compatible con el entorno en lugar de `runserver`. Configurar el proxy TLS de forma que Django interprete correctamente HTTPS según la infraestructura real; no se confía automáticamente en cabeceras proxy arbitrarias.

```text
python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

Revisar las advertencias de `check --deploy` y habilitar redirección HTTPS/HSTS en la configuración del despliegue cuando el dominio tenga TLS correcto. Estas opciones no se fuerzan en el entorno local para permitir HTTP de desarrollo y pruebas.

Realizar backups periódicos y comprobaciones de restauración. Restringir acceso directo al motor, `.env` y registros. No activar integración real con SUNAT sin sustituir el mock por un adaptador certificado, firma digital válida y verificación de esquemas y reglas vigentes.
