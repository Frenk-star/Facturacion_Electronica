'use strict';
document.getElementById('consultar-ruc')?.addEventListener('click', async event => {
  const button = event.currentTarget;
  const status = document.getElementById('consulta-ruc-estado');
  if (document.getElementById('id_tipo_doc').value !== 'RUC') {
    status.textContent = 'Selecciona RUC como tipo de documento.'; return;
  }
  const ruc = document.getElementById('id_num_doc').value.trim();
  if (!/^[0-9]{11}$/.test(ruc)) {
    status.textContent = 'Ingresa un RUC de 11 dígitos.'; return;
  }
  if ((document.getElementById('id_razon_social').value || document.getElementById('id_direccion').value) &&
      !confirm('¿Reemplazar la razón social y la dirección con los datos de la consulta?')) return;
  button.disabled = true; status.textContent = 'Consultando…';
  try {
    const response = await fetch(button.dataset.url, {
      method: 'POST', credentials: 'same-origin',
      headers: {'X-CSRFToken': Nexo.csrf()}, body: new URLSearchParams({ruc})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'No se pudo consultar el RUC.');
    if (document.getElementById('id_num_doc').value.trim() !== ruc ||
        document.getElementById('id_tipo_doc').value !== 'RUC') {
      status.textContent = 'El documento cambió. Vuelve a consultar.'; return;
    }
    document.getElementById('id_razon_social').value = data.razon_social;
    document.getElementById('id_direccion').value = data.direccion;
    status.textContent = `${data.fuente}. Estado: ${data.estado || 'No disponible'}. Condición: ${data.condicion || 'No disponible'}. Revisa y guarda los datos.`;
  } catch (error) { status.textContent = error.message; }
  finally { button.disabled = false; }
});
