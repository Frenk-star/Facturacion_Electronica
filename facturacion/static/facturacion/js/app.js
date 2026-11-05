'use strict';
document.getElementById('modo-real')?.addEventListener('change', async event => {
  const control = event.currentTarget;
  control.disabled = true;
  try {
    await Nexo.api(control.dataset.url, {method: 'POST', body: '{}'});
  } catch (error) { Nexo.message(error.message); }
  finally { control.checked = false; control.disabled = false; }
});
window.Nexo = {
  csrf() { return document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''; },
  money(value) { return `S/ ${Number(value).toFixed(2)}`; },
  message(text, success = false) {
    const box = document.getElementById('global-message');
    box.textContent = text;
    box.className = `alert alert-${success ? 'success' : 'danger'}`;
    box.focus(); box.scrollIntoView({block: 'center', behavior: 'smooth'});
  },
  async api(url, options = {}) {
    const response = await fetch(url, {credentials: 'same-origin', ...options,
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': this.csrf(), ...options.headers}});
    const data = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) {
      const details = data?.detalles || data?.detail || data || 'Revise su conexión o vuelva a iniciar sesión.';
      throw new Error(typeof details === 'string' ? details : JSON.stringify(details));
    }
    return data;
  },
  debounce(fn, delay = 250) { let timeout; return (...args) => { clearTimeout(timeout); timeout = setTimeout(() => fn(...args), delay); }; },
  async all(url) {
    const rows = [];
    while (url) { const data = await this.api(url); rows.push(...(data.results || data)); url = data.next || null; }
    return rows;
  },
  autocomplete(input, results, endpoint, describe, choose) {
    let generation = 0;
    const search = this.debounce(async () => {
      const current = ++generation;
      try {
        const data = await this.api(`${endpoint}?activo=true&q=${encodeURIComponent(input.value)}`);
        if (current !== generation) return;
        results.replaceChildren();
        for (const row of data.results || data) {
          const button = document.createElement('button'); button.type = 'button'; button.className = 'search-result';
          button.setAttribute('role', 'option'); button.textContent = describe(row);
          button.addEventListener('click', () => { choose(row); results.replaceChildren(); input.setAttribute('aria-expanded', 'false'); });
          results.append(button);
        }
        if (!results.children.length) { const empty = document.createElement('div'); empty.className = 'search-result'; empty.textContent = 'No se encontraron resultados.'; results.append(empty); }
        input.setAttribute('aria-expanded', 'true');
      } catch (error) { this.message(error.message); }
    });
    input.addEventListener('input', search); input.addEventListener('focus', search);
    input.addEventListener('keydown', event => {
      if (event.key === 'ArrowDown') { event.preventDefault(); results.querySelector('button')?.focus(); }
      if (event.key === 'Escape') { results.replaceChildren(); input.setAttribute('aria-expanded', 'false'); }
    });
    results.addEventListener('keydown', event => {
      if (event.key === 'ArrowDown') { event.preventDefault(); event.target.nextElementSibling?.focus(); }
      if (event.key === 'ArrowUp') { event.preventDefault(); event.target.previousElementSibling?.focus(); }
      if (event.key === 'Escape') { results.replaceChildren(); input.focus(); }
    });
    document.addEventListener('click', event => { if (event.target !== input && !results.contains(event.target)) { results.replaceChildren(); input.setAttribute('aria-expanded', 'false'); } });
  }
};
document.getElementById('menu-toggle')?.addEventListener('click', event => {
  const open = document.getElementById('sidebar').classList.toggle('open'); event.currentTarget.setAttribute('aria-expanded', String(open));
});
function closeMenu() {
  document.getElementById('sidebar')?.classList.remove('open');
  document.getElementById('menu-toggle')?.setAttribute('aria-expanded', 'false');
}
document.getElementById('menu-close')?.addEventListener('click', closeMenu);
document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMenu(); });
document.querySelectorAll('[data-post],[data-delete]').forEach(button => button.addEventListener('click', async () => {
  if (button.dataset.confirm && !confirm(button.dataset.confirm)) return;
  const label = button.textContent; button.disabled = true; button.textContent = 'Procesando…';
  try { await Nexo.api(button.dataset.post || button.dataset.delete, {method: button.dataset.delete ? 'DELETE' : 'POST', body: '{}'}); location.reload(); }
  catch (error) { Nexo.message(error.message); button.disabled = false; button.textContent = label; }
}));
