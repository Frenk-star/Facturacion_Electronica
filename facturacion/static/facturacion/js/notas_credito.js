'use strict';
(() => {
  const form = document.getElementById('nota-form'); if (!form) return;
  const select = document.getElementById('original-id'); const search = document.getElementById('original-busqueda');
  const amount = document.getElementById('monto-nota'); const info = document.getElementById('original-datos');
  let documents = []; let busy = false; const requestKey = crypto.randomUUID();
  function display() {
    const document = documents.find(row => String(row.id) === select.value);
    if (!document) { info.classList.add('d-none'); return; }
    info.classList.remove('d-none'); info.textContent = `${document.cliente_nombre} · Total ${Nexo.money(document.total)} · Saldo disponible ${Nexo.money(document.saldo_disponible)}`;
    amount.max = document.saldo_disponible;
    amount.value = document.saldo_disponible;
  }
  function filter() {
    const selected = select.value || select.dataset.inicial; const term = search.value.toLocaleLowerCase();
    select.replaceChildren(new Option('Selecciona un comprobante', ''));
    for (const row of documents) {
      const label = `${row.serie}-${row.numero} · ${row.cliente_nombre} · Saldo ${Nexo.money(row.saldo_disponible)}`;
      if (label.toLocaleLowerCase().includes(term) || String(row.id) === selected) select.add(new Option(label, row.id));
    }
    select.value = selected; display();
  }
  Nexo.all('/api/comprobantes/?estado=ACEPTADO').then(rows => { documents = rows.filter(row => ['01', '03'].includes(row.tipo) && Number(row.saldo_disponible) > 0); filter(); }).catch(error => Nexo.message(error.message));
  search.addEventListener('input', Nexo.debounce(filter)); select.addEventListener('change', display);
  form.addEventListener('submit', async event => {
    event.preventDefault(); if (busy || !form.reportValidity()) return;
    if (!confirm('¿Emitir la nota de crédito y descontar el saldo del original?')) return;
    busy = true; const button = document.getElementById('emitir-nota'); button.disabled = true; button.textContent = 'Emitiendo…';
    try {
      const nota = await Nexo.api('/api/notas-credito/', {method: 'POST', body: JSON.stringify({comprobante_id: Number(select.value), motivo: document.getElementById('motivo-nota').value, tipo_nota: document.getElementById('tipo-nota').value, monto_afectado: amount.value, clave_idempotencia: requestKey})});
      location.assign(`/comprobantes/${nota.comprobante}/`);
    } catch (error) { Nexo.message(error.message); busy = false; button.disabled = false; button.textContent = 'Emitir nota de crédito →'; }
  });
})();
