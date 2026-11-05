# Manual de usuario

## Acceso y navegación

1. El administrador ejecuta migraciones y `seed_demo`, o crea usuarios propios y membresías.
2. Abrir `/login/`, escribir usuario y contraseña y pulsar **Ingresar**. Si falla, corregir los datos; no se muestran errores internos.
3. Seleccionar la empresa en la barra superior si se dispone de varias membresías. Todas las pantallas y acciones utilizan esa empresa.
4. En móviles, abrir la navegación con **☰** y cerrarla con **×** dentro del panel o Escape.
5. **Salir** cierra la sesión mediante POST.

## Dashboard

`/` muestra ventas netas del mes, facturas, boletas, aceptados, rechazados y pendientes. El gráfico agrega importes diarios de documentos aceptados; las notas de crédito restan. El historial reciente enlaza al detalle de cada documento. Los enlaces del centro de control llevan a rechazados y libro mensual.

## Emitir factura o boleta

1. Entrar a **Emitir comprobante**, disponible para ADMIN y EMISOR.
2. Seleccionar Factura/Boleta y serie. La lista muestra series del tipo y empresa activos.
3. Escribir documento o nombre del cliente y **seleccionar un resultado**. La búsqueda consulta la base local, no SUNAT ni RENIEC. Si no existe, usar **Registrar cliente**.
4. Buscar productos por código o descripción y seleccionarlos. Cada selección agrega una línea.
5. Ajustar cantidad, precio final con IGV y descuento monetario por línea. El resumen se recalcula al escribir. Quitar líneas con **×**.
6. **Vista previa** permite revisar receptor, líneas y total sin persistir ni consumir número.
7. **Guardar borrador** guarda sin número ni XML; luego puede abrirse y emitirse desde el detalle. El formulario no implementa edición posterior de líneas de borradores: para una venta diferente, crear otro borrador.
8. **Emitir comprobante** solicita confirmación, valida en Django, asigna número y procesa el OSE simulado. Se redirige al detalle. Ante errores, el formulario conserva las entradas y muestra detalles; los botones vuelven a habilitarse.

El selector de respuesta permite ensayar aceptación o rechazo académico de forma determinista. No representa una decisión real de SUNAT.

## Documentos, voucher y reenvío

**Comprobantes** ofrece filtros de tipo, estado, fechas y documento del cliente; **Limpiar** restablece el listado. La paginación conserva filtros. Estados: aceptado verde, rechazado rojo, enviado amarillo, emitido azul y borrador gris.

**Ver** abre importes y datos históricos, historial de estados e intentos OSE. **Ver voucher / Imprimir** abre la representación imprimible; **Imprimir** llama al diálogo de impresión del navegador. PDF se descarga desde listado, detalle o voucher. XML solo está disponible después de emitir. Un rechazo permite **Reenviar** sin cambiar número. Los aceptados 01/03 permiten generar una nota de crédito, mostrando el saldo.

## Notas de crédito

Entrar desde el original o desde **Notas de crédito**. Buscar por serie/número/cliente y seleccionar un original aceptado con saldo. La pantalla informa receptor, total y remanente. Seleccionar motivo, escribir monto con IGV y descripción, y emitir tras confirmar. Django comprueba nuevamente el saldo bloqueando el original; otra solicitud concurrente no puede sobrepasarlo. La nota resultante tiene su propio comprobante 07, XML, PDF e historial.

## Clientes y productos

En Nuevo/Editar cliente, selecciona RUC, DNI o CE. Para RUC o DNI aparece **Buscar**
junto a Número de documento. Escribe el número completo, revísalo y pulsa Buscar:
escribir o corregir números no consume consultas. Se exige RUC de 11 dígitos o
DNI de 8. RUC completa razón social y dirección disponible; DNI completa nombres
y apellidos y conserva la dirección. Revisa los datos antes de Guardar cambios.
El correo se ingresa manualmente. Si falta configurar la API se muestra un aviso
y puedes completar el registro manualmente. CE se registra sin consulta externa.

Las listas de selección de clientes y productos en Emitir comprobante ya no se
recortan al sobrepasar la tarjeta. La búsqueda de esa pantalla sigue siendo local.

El interruptor **Pruebas / Real** solicita habilitar emisión real. Solo ADMIN puede
solicitarlo; actualmente informa los requisitos faltantes y vuelve a Pruebas.
No envía comprobantes a SUNAT. Las consultas reales de documentos son independientes.

Los listados consultan la base y permiten buscar, crear y editar. En clientes se valida longitud y tipo de documento y existe historial de comprobantes. En productos se registran código, descripción, unidad, precio final, afectación y estado. **Desactivar** requiere confirmación, conserva el historial y excluye el registro del autocompletado activo. Puede reactivarse editando **Activo**. El contador solo consulta.

## Libro de ventas

Seleccionar mes/año y **Consultar periodo**. Se muestran base neta, IGV neto y ventas netas, filas aceptadas y cantidad de rechazados excluidos. Las notas se identifican como crédito y aparecen negativas. **CSV** y **Excel** descargan el mismo periodo; ambos incluyen totales netos. Un documento de otro mes no altera retroactivamente el libro de un periodo anterior.

## Configuración administrativa

Solo ADMIN: editar datos de la empresa activa; crear una serie; crear cuentas con contraseña inicial y rol; guardar cambios de rol; revocar/restaurar acceso local. Los contadores existentes son de solo lectura. El superusuario utiliza `/admin/` para crear empresas y asignar las membresías iniciales; documentos, logs y estados se inspeccionan sin edición manual.
