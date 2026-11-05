# Consulta de RUC y futura emisión real

Actualizado el 5 de noviembre de 2026. Las consultas RUC y DNI se verificaron en
vivo con los tokens privados configurados. La emisión tributaria real sigue pendiente.
El interruptor **Pruebas / Real** ahora permite solicitar el cambio: el backend
valida el rol ADMIN y responde HTTP 409 con los requisitos faltantes. El control
vuelve a Pruebas; no cambia la emisión ni declara habilitado un transporte inexistente.
Consultar RUC o DNI no cambia el modo de emisión.

Se preparó el adaptador de ConsultadeRUC.pe y el botón en Clientes > Nuevo/Editar.
Es un proveedor independiente, no una API oficial de SUNAT. Requiere registrar
una cuenta, verificar el correo, activar el plan Gratis y generar el token.
Configurar `RUC_API_TOKEN` en `.env` y reiniciar el servidor. No subir el token a Git.
Sin token no se hace ninguna llamada externa. Los datos se revisan antes de guardar.
La consulta real se comprobó con el RUC de ejemplo `20536066528`.

## Consulta DNI

El formulario de clientes también incluye consulta DNI mediante Factiliza,
un proveedor independiente, no una API oficial de RENIEC. Su plan gratuito anuncia
100 consultas mensuales de API Consulta. Crear una cuenta en https://app.factiliza.com,
obtener un token y configurar `DNI_API_TOKEN` en `.env`; reiniciar el servidor.
Documentación: https://docs.factiliza.com/api-consulta/endpoint/dni
Plan: https://factiliza.com/

Seleccionar DNI, ingresar los ocho dígitos y pulsar el botón. Solo se completa el
nombre del cliente; la dirección se mantiene y se completa manualmente. No se
exponen fecha de nacimiento, sexo ni otros datos del proveedor. El token nunca
se entrega al navegador. Se manejan falta de token, respuesta inválida, timeout,
documento no encontrado y cuota agotada. La consulta real se comprobó con el DNI
de ejemplo de la documentación `27427864`; las pruebas automáticas usan respuestas
controladas sin consumir cuota.

## Consulta manual y conectividad

En Clientes > Nuevo/Editar, seleccionar RUC o DNI y completar el número. Pulsar
**Buscar**, situado junto a la etiqueta Número de documento. Escribir, pegar,
corregir el número o cambiar el tipo no consulta APIs. La consulta automática se
retiró para evitar consumo accidental de cuota. Se valida la longitud antes del
envío y se permite revisar el resultado antes de Guardar cambios.

La etiqueta de identificación cambia a Razón social para RUC y Nombres y apellidos
para DNI/CE. RUC completa razón social y dirección cuando está disponible; DNI
solo completa el nombre. Correo, dirección faltante y estado se gestionan manualmente.

Se detectó `WinError 10013`: el entorno restringido impedía abrir sockets hacia
ambos proveedores. Las mismas consultas funcionaron al autorizar acceso a internet.
Se reinició el servidor con ese acceso. Verificar red, firewall y permisos del
proceso ante este error antes de atribuirlo al token. No desactivar validación TLS.

El acceso oficial de RENIEC requiere convenio; no se presenta esta integración
como conexión directa ni verificación oficial de identidad:
https://identidad.reniec.gob.pe/servicios-en-linea1

Según la documentación consultada el 5 de noviembre de 2026:
- Plan gratis: 100 consultas mensuales, reinicio el día 1 a las 00:00 de Lima.
- Ráfaga: 60 consultas/minuto por token; exceso devuelve 429.
- Un RUC inexistente consume cuota; uno mal formado no.
- Datos importados del padrón; no garantiza actualización en tiempo real.
- No publica domicilio de personas naturales.

Fuentes: https://consultaderuc.pe/precios y https://consultaderuc.pe/api-docs

Para implementar emisión directa desde el sistema se necesitan RUC, razón social,
dirección fiscal completa y ubigeo, régimen, correo, establecimiento, series y
correlativos vigentes, y confirmar la habilitación y sistema de emisión aplicable.
Credenciales: usuario SOL secundario con perfil de envío y su contraseña.
Certificado: archivo .p12/.pfx, contraseña, titular y vigencia, registrado según
el procedimiento SUNAT. Guardar los secretos localmente fuera del repositorio.
La emisión exige además implementar UBL válido, firma, envío, CDR, resúmenes y bajas.

Servicios oficiales y beta:
https://orientacion.sunat.gob.pe/guias-manuales-y-servicios-web
https://cpe.sunat.gob.pe/sistema_emision/see_contribuyente
https://cpe.sunat.gob.pe/certificado-digital

## Ruta propuesta para emisión real (no implementada)

1. Confirmar con la empresa su habilitación como emisor, régimen y si debe usar
   SEE-OSE o puede enviar por el sistema del contribuyente. Tener RUC, razón social,
   dirección fiscal con ubigeo, establecimiento, moneda, series y correlativos vigentes.
2. Elegir transporte: servicio oficial SUNAT cuando corresponda, o integración con
   OSE/PSE según la modalidad aplicable. Obtener credenciales de pruebas del proveedor
   si se elige uno. El token de consulta RUC/DNI no sirve para emitir.
3. Implementar XML UBL conforme a los documentos y catálogos oficiales, validación,
   firma digital, empaquetado y cliente de envío. Para la vía directa preparar usuario
   SOL secundario con permiso de envío y certificado .p12/.pfx válido con contraseña.
4. Probar estructuras y respuestas en beta cuando corresponda. Beta no es producción
   ni concede validez tributaria. Implementar lectura de CDR, rechazos, tickets,
   resúmenes de boletas, notas y bajas según el servicio aplicable.
5. Separar comprobantes, series y credenciales de pruebas y producción; conservar
   XML/CDR, implementar reintentos seguros y respaldos, y validar aceptación real
   del servicio antes de presentar un comprobante como aceptado tributariamente.
6. Habilitar el interruptor por empresa con validación del backend y registro del
   cambio solo después de completar y verificar la integración. Hoy devuelve 409.

El proyecto es una base reutilizable para esta ampliación; no se puede asegurar
emisión real cambiando únicamente una opción o añadiendo los tokens de consulta.
