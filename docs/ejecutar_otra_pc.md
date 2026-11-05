# Ejecutar el sistema en otra PC Windows

Esta guía permite instalar una copia del código público con una base nueva. No incluye credenciales locales, claves ni bases de datos. Las cuentas se crean en la PC de destino durante la carga de demostración.

## 1. Obtener el código

Copiar el ZIP público preparado o descargar/clonar el repositorio que contenga todos los cambios actuales. Extraerlo en una carpeta y comprobar que dentro existen `manage.py`, `requirements.txt`, `facturacion/` y `FacturacionSunat/`.

La carpeta `.runtime` pertenece al entorno de trabajo original y no es necesaria. No copiar `.venv` desde otra PC: se crea un entorno nuevo en destino.

## 2. Instalar Python

Utilizar Python 3.12, versión con la que se verificó esta entrega. En Windows, habilitar el acceso a Python desde la terminal durante la instalación. Comprobar en una terminal nueva:

```powershell
python --version
```

Si el comando abre Microsoft Store, revisar la instalación o utilizar `py -3.12` en lugar de `python` para crear el entorno del paso siguiente.

## 3. Abrir la carpeta del proyecto

En el Explorador de archivos, abrir la carpeta que contiene `manage.py`, hacer clic en la barra de dirección, escribir `powershell` y pulsar Enter. Así la terminal se abre en la carpeta correcta sin depender de una ruta particular de la PC original.

## 4. Crear el entorno e instalar dependencias

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

La instalación requiere conexión a Internet. Los comandos utilizan directamente el intérprete del entorno, por lo que no es necesario cambiar la política de ejecución de PowerShell ni activar scripts.

## 5. Configurar el entorno local

```powershell
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(64))"
notepad .env
```

Pegar el valor generado en `DJANGO_SECRET_KEY`, sin espacios alrededor del signo igual. Mantener `DJANGO_DEBUG=true` para demostración local y `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`. Dejar `POSTGRES_DB` vacío para usar SQLite.

El archivo `.env` permanece exclusivamente en la PC local y está excluido de Git. No reemplazar un `.env` existente sin revisar sus valores.

## 6. Crear la base y los datos de demostración

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
```

`seed_demo` crea empresa, roles, cuentas demo, series, clientes, productos y documentos de ejemplo. Las contraseñas iniciales se generan aleatoriamente y el comando las muestra solo al crear cada cuenta. Conservar esos datos de acceso en un archivo privado dentro de `.private/` o en un gestor de contraseñas; nunca agregarlos a documentación pública.

**Las credenciales de la PC original no viajan con el código.** Los cambios locales de usuario/contraseña están en la base privada, no en Git. No se crea automáticamente la cuenta personalizada de la instalación original.

## 7. Comprobar la instalación

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

El primer comando debe finalizar sin incidencias y el segundo debe indicar que no hay cambios de modelos pendientes.

## 8. Arrancar

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Mantener abierta la terminal y visitar `http://127.0.0.1:8000/`. Para arranques posteriores también se puede hacer doble clic en `iniciar.bat`, que detecta `.venv`.

Entrar con la cuenta administrativa local generada en el paso 6. La configuración empresarial está en `/configuracion/`; Swagger está en `/api/docs/`. Un administrador empresarial y un superusuario global Django tienen alcances diferentes. Para crear un superusuario global, si se necesita:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

## 9. Ejecutar pruebas opcionalmente

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe -m pytest --cov=facturacion --cov-report=term-missing
```

SQLite omite las tres pruebas de bloqueo PostgreSQL y la prueba de navegador optativa. Para reproducir el recorrido de interfaz:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-browser.txt
.\.venv\Scripts\python.exe -m playwright install chromium
$env:RUN_BROWSER_TESTS='1'
.\.venv\Scripts\python.exe manage.py test facturacion.test_browser
```

Para concurrencia, configurar una instancia PostgreSQL y las variables `POSTGRES_*` antes de ejecutar las pruebas. No es necesario instalar PostgreSQL para una demostración local de un usuario.

## 10. Conservar datos de una instalación anterior

La base `db.sqlite3` contiene usuarios, hashes de contraseñas y documentos: **no debe subirse a Git**. Si se requiere trasladar los mismos datos, detener el servidor original y transferir una copia de esa base por un medio privado. Colocarla junto a `manage.py` antes de ejecutar `migrate`. No sobrescribir una base de destino que contenga datos que deban conservarse. No ejecutar `seed_demo` si solo se desea trabajar con la base trasladada sin crear cuentas demo adicionales.

En PostgreSQL, utilizar backup/restauración propios de ese motor; copiar `db.sqlite3` no traslada una base PostgreSQL.

## Solución de problemas comunes

| Problema | Acción |
|---|---|
| `ERR_CONNECTION_REFUSED` | Iniciar el servidor y mantener abierta su terminal; comprobar dirección y puerto |
| `No module named django` | Instalar requirements usando el mismo `.venv\Scripts\python.exe` que ejecuta el proyecto |
| No se encuentra `manage.py` | Abrir PowerShell dentro de la carpeta correcta |
| Usuario local anterior no existe | Usar las cuentas generadas en esta instalación o trasladar la base por un medio privado |
| Puerto ocupado | Usar `runserver 127.0.0.1:8001` y abrir ese puerto |
| Se cierra la sesión al reiniciar | Definir una `DJANGO_SECRET_KEY` estable en `.env` |

El servidor de desarrollo y esta guía son para ejecución local. Para acceso público, consultar `despliegue.md`. El XML y el OSE continúan siendo simulaciones académicas.
