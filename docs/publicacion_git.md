# Publicación del código sin información privada

## Archivos públicos

Se pueden publicar código de `facturacion/` y `FacturacionSunat/`, migraciones, templates, recursos estáticos, tests, dependencias, configuración de calidad, documentación, `iniciar.bat`, `manage.py`, `seed.py` y `.env.example` sin valores secretos.

Los nombres y documentos incluidos en seed/tests son datos de demostración. Las contraseñas de prueba se generan durante la ejecución y no corresponden a cuentas persistentes de la instalación local.

## Archivos privados

`.gitignore` excluye `.env` y variantes, `.private/`, bases SQLite, certificados/claves privadas, dumps SQL, logs, `.aws/`, `.ssh/`, `.runtime/`, entornos virtuales y artefactos locales de cobertura. Las credenciales de acceso locales están separadas en `.private/`, no en este documento.

`.gitignore` no elimina archivos que ya estuvieran versionados ni limpia commits anteriores. Antes de publicar, revisar los archivos incluidos y comprobar que ningún secreto real esté agregado al índice.

## Historial anterior

La auditoría detectó una clave de desarrollo de Django incrustada en commits anteriores del repositorio original. Esa clave ya no se utiliza en la configuración actual: se genera una clave local y se lee desde `.env`. El ZIP público preparado contiene únicamente los archivos actuales permitidos por Git, sin `.git`, historial, base ni configuración privada.

Para iniciar una publicación sin esos commits, extraer el ZIP en una carpeta nueva, revisar su contenido y utilizar un repositorio Git nuevo/vacío. Los comandos siguientes se ejecutan **en esa carpeta extraída**, no sobre el repositorio original:

```powershell
git init
git add .
git status --short
git commit -m "Sistema académico de facturación electrónica"
git branch -M main
git remote add origin URL_DEL_REPOSITORIO_VACIO
git push -u origin main
```

Sustituir `URL_DEL_REPOSITORIO_VACIO` por la dirección del repositorio de destino. No ejecutar un force push sobre un repositorio compartido para seguir esta guía. Publicar los commits originales conservaría su contenido histórico aunque los archivos actuales ya estén corregidos.

Las credenciales concretas no forman parte del ZIP ni del resumen del sistema. Tras clonar en otra PC, seguir `ejecutar_otra_pc.md` para generar configuración y cuentas propias.
