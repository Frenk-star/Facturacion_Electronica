'use strict';
document.querySelectorAll('[data-api-form]').forEach(form => form.addEventListener('submit', async event => {
  event.preventDefault(); if (!form.reportValidity()) return;
  const button = form.querySelector('button'); button.disabled = true;
  try { await Nexo.api(form.dataset.apiForm, {method: form.dataset.method || 'POST', body: JSON.stringify(Object.fromEntries(new FormData(form)))}); location.reload(); }
  catch (error) { Nexo.message(error.message); button.disabled = false; }
}));
document.querySelectorAll('[data-reactivar]').forEach(button => button.addEventListener('click', async () => {
  button.disabled = true;
  try { await Nexo.api(`/api/membresias/${button.dataset.reactivar}/`, {method: 'PATCH', body: JSON.stringify({activo: true})}); location.reload(); }
  catch (error) { Nexo.message(error.message); button.disabled = false; }
}));
