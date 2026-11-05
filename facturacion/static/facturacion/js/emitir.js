'use strict';
(() => {
  const form = document.getElementById('emision-form'); if (!form) return;
  const lines = []; let busy = false; let requestKey = crypto.randomUUID();
  const body = document.getElementById('lineas');
  const clientInput = document.getElementById('cliente-busqueda');
  const clientId = document.getElementById('cliente-id');
  clientInput.addEventListener('input', () => { clientId.value = ''; });
  Nexo.autocomplete(clientInput, document.getElementById('clientes-resultados'), '/api/clientes/',
    row => `${row.tipo_doc} ${row.num_doc} · ${row.razon_social}`,
    row => { clientId.value = row.id; clientInput.value = `${row.num_doc} · ${row.razon_social}`; });
  const productInput = document.getElementById('producto-busqueda');
  Nexo.autocomplete(productInput, document.getElementById('productos-resultados'), '/api/productos/',
    row => `${row.codigo} · ${row.descripcion} · ${Nexo.money(row.precio_unitario)}`,
    row => { lines.push({producto_id: row.id, descripcion: row.descripcion, afecto: row.afecto_igv, cantidad: '1.00', precio_unitario: row.precio_unitario, descuento: '0.00'}); productInput.value = ''; render(); });

  function round(value) { return Math.round((value + Number.EPSILON) * 100) / 100; }
  function amounts(line) {
    const total = round(Number(line.cantidad) * Number(line.precio_unitario) - Number(line.descuento));
    const base = line.afecto ? round(total / 1.18) : total;
    return {total, base, igv: round(total - base)};
  }
  function totals() {
    const result = {gravada: 0, noGravada: 0, igv: 0, total: 0};
    for (const line of lines) { const a = amounts(line); result[line.afecto ? 'gravada' : 'noGravada'] += a.base; result.igv += a.igv; result.total += a.total; }
    document.getElementById('base-gravada').textContent = Nexo.money(result.gravada);
    document.getElementById('base-no-gravada').textContent = Nexo.money(result.noGravada);
    document.getElementById('igv-total').textContent = Nexo.money(result.igv);
    document.getElementById('total-general').textContent = Nexo.money(result.total);
    return result;
  }
  function render() {
    body.replaceChildren(); document.getElementById('lineas-vacias').hidden = lines.length > 0;
    lines.forEach((line, index) => {
      const tr = document.createElement('tr'); const description = document.createElement('td');
      description.textContent = line.descripcion; const tax = document.createElement('small'); tax.className = 'd-block text-secondary'; tax.textContent = line.afecto ? 'Gravado · IGV 18%' : 'No gravado'; description.append(tax); tr.append(description);
      for (const field of ['cantidad', 'precio_unitario', 'descuento']) {
        const td = document.createElement('td'); const input = document.createElement('input');
        input.className = 'form-control'; input.type = 'number'; input.step = '.01'; input.min = field === 'cantidad' ? '.01' : '0'; input.value = line[field]; input.required = true;
        input.setAttribute('aria-label', `${field.replace('_', ' ')} de ${line.descripcion}`);
        input.addEventListener('input', () => { line[field] = input.value; const a = amounts(line); tr.querySelector('[data-igv]').textContent = Nexo.money(a.igv); tr.querySelector('[data-total]').textContent = Nexo.money(a.total); totals(); }); td.append(input); tr.append(td);
      }
      for (const field of ['igv', 'total']) { const td = document.createElement('td'); td.dataset[field] = ''; td.textContent = Nexo.money(amounts(line)[field]); tr.append(td); }
      const td = document.createElement('td'); const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'btn btn-sm btn-outline-danger'; remove.textContent = '×'; remove.setAttribute('aria-label', `Quitar ${line.descripcion}`); remove.addEventListener('click', () => { lines.splice(index, 1); render(); }); td.append(remove); tr.append(td); body.append(tr);
    }); totals();
  }
  function validate() {
    if (!form.reportValidity()) return false;
    if (!clientId.value) { Nexo.message('Selecciona un cliente del autocompletado.'); return false; }
    if (!lines.length) { Nexo.message('Agrega al menos un producto.'); return false; }
    if (lines.some(line => Number(line.descuento) > Number(line.cantidad) * Number(line.precio_unitario))) { Nexo.message('El descuento no puede superar el importe de la línea.'); return false; }
    return true;
  }
  async function save(draft) {
    if (busy || !validate()) return;
    if (!draft && !confirm('¿Emitir el documento y asignar su numeración definitiva?')) return;
    busy = true; form.querySelectorAll('button').forEach(button => { button.disabled = true; }); form.classList.add('loading'); form.setAttribute('aria-busy', 'true');
    const payload = {cliente_id: Number(clientId.value), serie: document.getElementById('serie-comp').value, borrador: draft,
      resultado_mock: document.getElementById('resultado-mock').value, clave_idempotencia: requestKey,
      items: lines.map(({producto_id, cantidad, precio_unitario, descuento}) => ({producto_id, cantidad, precio_unitario, descuento}))};
    try {
      const endpoint = document.getElementById('tipo-comp').value === '01' ? 'facturas' : 'boletas';
      const data = await Nexo.api(`/api/${endpoint}/`, {method: 'POST', body: JSON.stringify(payload)});
      location.assign(`/comprobantes/${data.id}/`);
    } catch (error) { Nexo.message(error.message); busy = false; form.querySelectorAll('button').forEach(button => { button.disabled = false; }); form.classList.remove('loading'); form.setAttribute('aria-busy', 'false'); }
  }
  form.addEventListener('submit', event => { event.preventDefault(); save(false); });
  document.getElementById('guardar-borrador').addEventListener('click', () => save(true));
  const dialog = document.getElementById('preview-dialog');
  document.getElementById('vista-previa').addEventListener('click', () => {
    if (!validate()) return;
    const preview = document.getElementById('preview-content'); preview.replaceChildren();
    const heading = document.createElement('p'); heading.textContent = clientInput.value; preview.append(heading);
    for (const line of lines) { const p = document.createElement('p'); p.textContent = `${line.cantidad} × ${line.descripcion}: ${Nexo.money(amounts(line).total)}`; preview.append(p); }
    const strong = document.createElement('strong'); strong.textContent = `Total: ${Nexo.money(totals().total)}`; preview.append(strong); dialog.showModal();
  });
  document.getElementById('cerrar-preview').addEventListener('click', () => dialog.close());
  function series() { const type = document.getElementById('tipo-comp').value === '01' ? 'F' : 'B'; const select = document.getElementById('serie-comp'); for (const option of select.options) { option.hidden = option.dataset.tipo !== type; option.disabled = option.hidden; } select.value = [...select.options].find(option => !option.disabled)?.value || ''; }
  document.getElementById('tipo-comp').addEventListener('change', series); series();
})();
