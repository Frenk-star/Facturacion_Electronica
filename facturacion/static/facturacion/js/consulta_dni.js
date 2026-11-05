'use strict';
document.getElementById('consultar-dni')?.addEventListener('click', async event => {
  const button = event.currentTarget;
  const status = document.getElementById('consulta-ruc-estado');
  const tipo = document.getElementById('id_tipo_doc');
  const numero = document.getElementById('id_num_doc');
  const nombre = document.getElementById('id_razon_social');
  if (tipo.value !== 'DNI') {
    status.textContent = 'Selecciona DNI como tipo de documento.'; return;
  }
  const dni = numero.value.trim();
  if (!/^[0-9]{8}$/.test(dni)) {
    status.textContent = 'Ingresa un DNI de 8 dígitos.'; return;
  }
  if (nombre.value && !confirm('¿Reemplazar el nombre con el resultado de la consulta DNI?')) return;
  const nombreAnterior = nombre.value;
  const otroBoton = document.getElementById('consultar-ruc');
  button.disabled = true; otroBoton.disabled = true; status.textContent = 'Consultando DNI…';
  try {
    const response = await fetch(button.dataset.url, {
      method: 'POST', credentials: 'same-origin',
      headers: {'X-CSRFToken': Nexo.csrf()}, body: new URLSearchParams({dni})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'No se pudo consultar el DNI.');
    if (numero.value.trim() !== dni || tipo.value !== 'DNI' || nombre.value !== nombreAnterior) {
      status.textContent = 'Los datos cambiaron durante la consulta. Vuelve a consultar.'; return;
    }
    nombre.value = data.razon_social;
    status.textContent = `${data.fuente}. Revisa el nombre antes de guardar. Completa la dirección manualmente.`;
  } catch (error) { status.textContent = error.message; }
  finally { button.disabled = false; otroBoton.disabled = false; }
});
