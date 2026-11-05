'use strict';
(() => {
  const chart = document.getElementById('sales-chart'); if (!chart) return;
  const rows = JSON.parse(document.getElementById('chart-data').textContent);
  if (!rows.length) { chart.textContent = 'Tus ventas del mes aparecerán aquí.'; chart.classList.add('empty-state'); return; }
  const days = new Map();
  for (const row of rows) { const day = Number(row.fecha.slice(-2)); days.set(day, (days.get(day) || 0) + Number(row.total)); }
  const max = Math.max(1, ...[...days.values()].map(Math.abs));
  const now = new Date(); const count = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  for (let day = 1; day <= count; day++) {
    const value = days.get(day) || 0; const bar = document.createElement('div');
    bar.className = `chart-bar${value < 0 ? ' negative' : ''}`; bar.style.height = `${Math.max(2, Math.abs(value) / max * 175)}px`;
    bar.title = `Día ${day}: ${Nexo.money(value)}`; bar.tabIndex = 0; bar.setAttribute('aria-label', bar.title);
    if (day === 1 || day % 5 === 0) { const label = document.createElement('span'); label.textContent = day; bar.append(label); }
    chart.append(bar);
  }
})();
