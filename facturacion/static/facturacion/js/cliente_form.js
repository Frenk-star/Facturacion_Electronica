'use strict';
(() => {
  const tipo = document.getElementById('id_tipo_doc');
  const numero = document.getElementById('id_num_doc');
  function adaptar() {
    const ruc = tipo.value === 'RUC';
    const dni = tipo.value === 'DNI';
    document.querySelector('label[for="id_razon_social"]').textContent =
      ruc ? 'Razón social *' : 'Nombres y apellidos *';
    numero.placeholder = ruc ? 'RUC de 11 dígitos' : dni ? 'DNI de 8 dígitos' : 'Número de carné';
    numero.maxLength = ruc ? 11 : dni ? 8 : 15;
    numero.inputMode = ruc || dni ? 'numeric' : 'text';
    document.getElementById('consultar-ruc').hidden = !ruc;
    document.getElementById('consultar-dni').hidden = !dni;
  }
  tipo.addEventListener('change', adaptar);
  adaptar();
})();
