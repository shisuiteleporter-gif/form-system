function validateCPF(cpf) {
  cpf = cpf.replace(/\D/g, '');
  if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;
  let sum = 0, rest;
  for (let i = 1; i <= 9; i++) sum += parseInt(cpf[i-1]) * (11 - i);
  rest = (sum * 10) % 11;
  if (rest === 10) rest = 0;
  if (rest !== parseInt(cpf[9])) return false;
  sum = 0;
  for (let i = 1; i <= 10; i++) sum += parseInt(cpf[i-1]) * (12 - i);
  rest = (sum * 10) % 11;
  if (rest === 10) rest = 0;
  if (rest !== parseInt(cpf[10])) return false;
  return true;
}

function validateCNPJ(cnpj) {
  cnpj = cnpj.replace(/\D/g, '');
  if (cnpj.length !== 14 || /^(\d)\1{13}$/.test(cnpj)) return false;
  let sum = 0, rest;
  let weights1 = [5,4,3,2,9,8,7,6,5,4,3,2];
  for (let i = 0; i < 12; i++) sum += parseInt(cnpj[i]) * weights1[i];
  rest = sum % 11;
  if (rest < 2) rest = 0; else rest = 11 - rest;
  if (rest !== parseInt(cnpj[12])) return false;
  sum = 0;
  let weights2 = [6,5,4,3,2,9,8,7,6,5,4,3,2];
  for (let i = 0; i < 13; i++) sum += parseInt(cnpj[i]) * weights2[i];
  rest = sum % 11;
  if (rest < 2) rest = 0; else rest = 11 - rest;
  if (rest !== parseInt(cnpj[13])) return false;
  return true;
}

function maskCPF(input) {
  let v = input.value.replace(/\D/g, '').slice(0, 11);
  if (v.length > 9) v = v.slice(0,3)+'.'+v.slice(3,6)+'.'+v.slice(6,9)+'-'+v.slice(9);
  else if (v.length > 6) v = v.slice(0,3)+'.'+v.slice(3,6)+'.'+v.slice(6);
  else if (v.length > 3) v = v.slice(0,3)+'.'+v.slice(3);
  input.value = v;
}

function maskCNPJ(input) {
  let v = input.value.replace(/\D/g, '').slice(0, 14);
  if (v.length > 12) v = v.slice(0,2)+'.'+v.slice(2,5)+'.'+v.slice(5,8)+'/'+v.slice(8,12)+'-'+v.slice(12);
  else if (v.length > 8) v = v.slice(0,2)+'.'+v.slice(2,5)+'.'+v.slice(5,8)+'/'+v.slice(8);
  else if (v.length > 5) v = v.slice(0,2)+'.'+v.slice(2,5)+'.'+v.slice(5);
  else if (v.length > 2) v = v.slice(0,2)+'.'+v.slice(2);
  input.value = v;
}

function maskPhone(input) {
  let v = input.value.replace(/\D/g, '').slice(0, 11);
  if (v.length > 6) v = '('+v.slice(0,2)+') '+v.slice(2,7)+'-'+v.slice(7);
  else if (v.length > 2) v = '('+v.slice(0,2)+') '+v.slice(2);
  else if (v.length > 0) v = '('+v;
  input.value = v;
}

function maskCurrency(input) {
  let v = input.value.replace(/\D/g, '').slice(0, 15);
  if (v.length === 0) { input.value = ''; return; }
  while (v.length < 3) v = '0' + v;
  let cents = v.slice(-2);
  let whole = v.slice(0, -2);
  whole = whole.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  input.value = 'R$ ' + whole + ',' + cents;
}

function maskDate(input) {
  let v = input.value.replace(/\D/g, '').slice(0, 8);
  if (v.length > 4) v = v.slice(0,2)+'/'+v.slice(2,4)+'/'+v.slice(4);
  else if (v.length > 2) v = v.slice(0,2)+'/'+v.slice(2);
  input.value = v;
}

function applyMask(input) {
  if (input.classList.contains('mask-cpf')) maskCPF(input);
  else if (input.classList.contains('mask-cnpj')) maskCNPJ(input);
  else if (input.classList.contains('mask-phone')) maskPhone(input);
  else if (input.classList.contains('mask-currency')) maskCurrency(input);
  else if (input.classList.contains('mask-date')) maskDate(input);
}

function showFieldError(field, message) {
  field.classList.add('is-invalid');
  let feedback = field.parentElement.querySelector('.invalid-feedback');
  if (!feedback) {
    feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    field.parentElement.appendChild(feedback);
  }
  feedback.textContent = message;
}

function clearFieldError(field) {
  field.classList.remove('is-invalid');
  let feedback = field.parentElement.querySelector('.invalid-feedback');
  if (feedback) feedback.textContent = '';
}

function clearAllErrors(form) {
  form.querySelectorAll('.is-invalid').forEach(function(el) {
    el.classList.remove('is-invalid');
  });
  form.querySelectorAll('.invalid-feedback').forEach(function(el) {
    el.textContent = '';
  });
}

function validateForm(formElement) {
  clearAllErrors(formElement);
  let valid = true;
  let firstInvalid = null;

  let requiredFields = formElement.querySelectorAll('[data-required="true"]');
  requiredFields.forEach(function(field) {
    let value = field.value.trim();
    if (field.type === 'file') return;
    if (value === '') {
      showFieldError(field, 'Este campo é obrigatório.');
      valid = false;
      if (!firstInvalid) firstInvalid = field;
    }
  });

  let emailFields = formElement.querySelectorAll('[data-type="email"]');
  emailFields.forEach(function(field) {
    if (!field.value.trim()) return;
    let re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!re.test(field.value.trim())) {
      showFieldError(field, 'Informe um e-mail válido.');
      valid = false;
      if (!firstInvalid) firstInvalid = field;
    }
  });

  let cpfFields = formElement.querySelectorAll('[data-type="cpf"]');
  cpfFields.forEach(function(field) {
    if (!field.value.trim()) return;
    if (!validateCPF(field.value)) {
      showFieldError(field, 'CPF inválido.');
      valid = false;
      if (!firstInvalid) firstInvalid = field;
    }
  });

  let cnpjFields = formElement.querySelectorAll('[data-type="cnpj"]');
  cnpjFields.forEach(function(field) {
    if (!field.value.trim()) return;
    if (!validateCNPJ(field.value)) {
      showFieldError(field, 'CNPJ inválido.');
      valid = false;
      if (!firstInvalid) firstInvalid = field;
    }
  });

  let phoneFields = formElement.querySelectorAll('[data-type="phone"]');
  phoneFields.forEach(function(field) {
    if (!field.value.trim()) return;
    let digits = field.value.replace(/\D/g, '');
    if (digits.length < 10 || digits.length > 11) {
      showFieldError(field, 'Informe um telefone com 10 ou 11 dígitos.');
      valid = false;
      if (!firstInvalid) firstInvalid = field;
    }
  });

  let patternFields = formElement.querySelectorAll('[data-validation-pattern]');
  patternFields.forEach(function(field) {
    if (!field.value.trim()) return;
    let pattern = field.getAttribute('data-validation-pattern');
    let re = new RegExp(pattern);
    if (!re.test(field.value.trim())) {
      let msg = field.getAttribute('data-validation-message') || 'Valor inválido para este campo.';
      showFieldError(field, msg);
      valid = false;
      if (!firstInvalid) firstInvalid = field;
    }
  });

  if (firstInvalid) firstInvalid.focus();
  return valid;
}

function initConditionalFields(formElement) {
  formElement.querySelectorAll('.conditional').forEach(function(el) {
    let conditionFieldId = el.getAttribute('data-condition-field');
    let conditionValue = el.getAttribute('data-condition-value');
    if (!conditionFieldId) return;
    let source = formElement.querySelector('[data-field-id="' + conditionFieldId + '"]');
    if (!source) return;
    function toggle() {
      if (source.type === 'checkbox') {
        if (conditionValue !== null) {
          el.style.display = source.checked ? '' : 'none';
        } else {
          el.style.display = source.checked ? '' : 'none';
        }
      } else if (source.type === 'radio') {
        let checked = formElement.querySelector('[name="' + source.name + '"]:checked');
        let show = checked && (!conditionValue || checked.value === conditionValue);
        el.style.display = show ? '' : 'none';
      } else {
        let show = !conditionValue || source.value === conditionValue;
        el.style.display = show ? '' : 'none';
      }
    }
    source.addEventListener('change', toggle);
    source.addEventListener('input', toggle);
    toggle();
  });
}

function initFileUploads(formElement) {
  formElement.querySelectorAll('input[type="file"]').forEach(function(input) {
    let maxSize = parseInt(input.getAttribute('data-max-size')) || 10485760;
    let accept = input.getAttribute('data-accept') || '.pdf,.jpg,.jpeg,.png,.gif,.bmp,.doc,.docx,.xls,.xlsx,.odt,.ods';
    input.setAttribute('accept', accept);

    let wrapper = input.parentElement;
    let fileNameDisplay = wrapper.querySelector('.file-name');
    if (!fileNameDisplay) {
      fileNameDisplay = document.createElement('span');
      fileNameDisplay.className = 'file-name ms-2 text-muted small';
      wrapper.appendChild(fileNameDisplay);
    }

    input.addEventListener('change', function() {
      if (input.files.length > 0) {
        let file = input.files[0];
        fileNameDisplay.textContent = file.name;
        if (file.size > maxSize) {
          showFieldError(input, 'O arquivo excede o tamanho máximo de 10MB.');
          input.value = '';
          fileNameDisplay.textContent = '';
        } else {
          clearFieldError(input);
        }
      } else {
        fileNameDisplay.textContent = '';
      }
    });
  });
}

function initAutoResize() {
  document.querySelectorAll('textarea.auto-resize').forEach(function(ta) {
    ta.style.overflow = 'hidden';
    function resize() {
      ta.style.height = 'auto';
      ta.style.height = ta.scrollHeight + 'px';
    }
    ta.addEventListener('input', resize);
    resize();
  });
}

function submitForm(formId, event) {
  if (event) event.preventDefault();
  let form = document.getElementById(formId);
  if (!form) return;

  if (!validateForm(form)) return;

  let formData = new FormData(form);
  let submitBtn = form.querySelector('button[type="submit"]');
  if (submitBtn) { submitBtn.disabled = true; submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Enviando...'; }

  let overlay = document.createElement('div');
  overlay.className = 'form-loading-overlay';
  overlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div>';
  document.body.appendChild(overlay);

  let hasFiles = Array.from(form.querySelectorAll('input[type="file"]')).some(function(i) { return i.files.length > 0; });

  let action = form.getAttribute('action');

  function onError(msg) {
    if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
    if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = 'Enviar'; }
    let container = form.querySelector('.form-error-container') || form;
    let alert = document.createElement('div');
    alert.className = 'alert alert-danger mt-3';
    alert.textContent = msg || 'Ocorreu um erro ao enviar o formulário. Tente novamente.';
    container.prepend(alert);
    setTimeout(function() { if (alert.parentNode) alert.parentNode.removeChild(alert); }, 8000);
  }

  if (hasFiles) {
    fetch(action, { method: 'POST', body: formData, headers: { 'Accept': 'application/json' } })
      .then(function(r) { return r.json().then(function(d) { return { ok: r.ok, data: d }; }); })
      .then(function(res) {
        if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
        if (res.ok && res.data && res.data.redirect) { window.location.href = res.data.redirect; return; }
        if (res.ok && res.data && res.data.id) { window.location.href = '/submissions/' + res.data.id; return; }
        if (res.ok) { window.location.href = '/submissions/success'; return; }
        onError(res.data && res.data.message ? res.data.message : null);
      })
      .catch(function() { onError(); });
    return;
  }

  let jsonData = {};
  formData.forEach(function(value, key) { jsonData[key] = value; });

  fetch(action, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(jsonData) })
    .then(function(r) {
      if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
      if (r.redirected) { window.location.href = r.url; return; }
      return r.json().then(function(d) { return { ok: r.ok, data: d }; });
    })
    .then(function(res) {
      if (!res) return;
      if (res.ok && res.data && res.data.redirect) { window.location.href = res.data.redirect; return; }
      if (res.ok && res.data && res.data.id) { window.location.href = '/submissions/' + res.data.id; return; }
      if (res.ok) { window.location.href = '/submissions/success'; return; }
      onError(res.data && res.data.message ? res.data.message : null);
    })
    .catch(function() { onError(); });
}

function initFormRenderer() {
  document.querySelectorAll('.mask-cpf, .mask-cnpj, .mask-phone, .mask-currency, .mask-date').forEach(function(input) {
    input.addEventListener('input', function() { applyMask(input); });
  });

  document.querySelectorAll('form[data-form-renderer]').forEach(function(form) {
    form.addEventListener('submit', function(e) { submitForm(form.id, e); });
    initConditionalFields(form);
    initFileUploads(form);
  });

  var textareas = document.querySelectorAll('textarea');
  if (textareas.length > 0) initAutoResize();

  var firstMasked = document.querySelector('.mask-cpf, .mask-cnpj, .mask-phone, .mask-currency, .mask-date');
  if (firstMasked) applyMask(firstMasked);
}

document.addEventListener('DOMContentLoaded', initFormRenderer);
