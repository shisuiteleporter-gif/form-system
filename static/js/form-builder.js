(function () {
  'use strict';

  let fields = [];
  let selectedFieldId = null;

  const FIELD_TYPES = [
    { type: 'text',           label: 'Texto Curto',  icon: 'fa-font' },
    { type: 'textarea',       label: 'Texto Longo',   icon: 'fa-align-left' },
    { type: 'number',         label: 'Numero',        icon: 'fa-hashtag' },
    { type: 'date',           label: 'Data',          icon: 'fa-calendar' },
    { type: 'select',         label: 'Select',        icon: 'fa-caret-down' },
    { type: 'radio',          label: 'Radio',         icon: 'fa-circle-dot' },
    { type: 'checkbox',       label: 'Checkbox',      icon: 'fa-square-check' },
    { type: 'cpf',            label: 'CPF',           icon: 'fa-id-card' },
    { type: 'cnpj',           label: 'CNPJ',          icon: 'fa-building' },
    { type: 'email',          label: 'Email',         icon: 'fa-envelope' },
    { type: 'phone',          label: 'Telefone',      icon: 'fa-phone' },
    { type: 'currency',       label: 'Moeda',         icon: 'fa-dollar-sign' },
    { type: 'file',           label: 'Arquivo',       icon: 'fa-file' },
    { type: 'section_title', label: 'Titulo de Secao', icon: 'fa-heading' }
  ];

  const EDOCS_MAPPINGS = [
    { value: '',       label: '(nenhum)' },
    { value: 'resumo', label: 'Resumo' },
    { value: 'classe_documental', label: 'Classe Documental' },
    { value: 'interessado_nome',  label: 'Interessado - Nome' },
    { value: 'interessado_cpf',   label: 'Interessado - CPF' },
    { value: 'assunto',           label: 'Assunto' },
    { value: 'observacao',       label: 'Observacao' }
  ];

  const VALOR_LEGAL_OPTIONS = [
    { value: 'Original', label: 'Original' },
    { value: 'CopiaAutenticadaAdministrativamente', label: 'Copia Autenticada Administrativamente' },
    { value: 'CopiaSimples', label: 'Copia Simples' }
  ];

  const NATUREZA_OPTIONS = [
    { value: 'NatoDigital', label: 'Nato Digital' },
    { value: 'Digitalizado', label: 'Digitalizado' }
  ];

  function uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      const r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  function defaultField(type) {
    return {
      id: uuid(),
      type: type,
      label: '',
      placeholder: '',
      help_text: '',
      required: false,
      options: [],
      validation: { min: null, max: null, pattern: null },
      edocs_mapping: null,
      sort_order: 0,
      section: null
    };
  }

  function getFieldById(fieldId) {
    return fields.find(function (f) { return f.id === fieldId; });
  }

  function updateHiddenInput() {
    const el = document.getElementById('fields_json');
    if (el) {
      el.value = JSON.stringify(fields);
    }
  }

  function renderPreview() {
    const container = document.getElementById('form-preview');
    if (!container) return;
    container.innerHTML = '';

    if (fields.length === 0) {
      container.innerHTML =
        '<div class="text-muted text-center py-5"><i class="fas fa-inbox fa-3x mb-3 d-block"></i>Nenhum campo adicionado</div>';
      return;
    }

    fields.forEach(function (field) {
      const wrapper = document.createElement('div');
      wrapper.className = 'mb-3';

      if (field.type === 'section_title') {
        const hr = document.createElement('hr');
        const h5 = document.createElement('h5');
        h5.className = 'text-primary mt-3 mb-0';
        h5.textContent = field.label || 'Nova Secao';
        wrapper.appendChild(hr);
        wrapper.appendChild(h5);
        container.appendChild(wrapper);
        return;
      }

      const labelEl = document.createElement('label');
      labelEl.className = 'form-label';
      labelEl.textContent = field.label || 'Campo sem rotulo';
      if (field.required) {
        const req = document.createElement('span');
        req.className = 'text-danger ms-1';
        req.textContent = '*';
        labelEl.appendChild(req);
      }
      wrapper.appendChild(labelEl);

      if (field.help_text) {
        const help = document.createElement('div');
        help.className = 'form-text mb-1';
        help.textContent = field.help_text;
        wrapper.appendChild(help);
      }

      const type = field.type;
      let input;

      if (type === 'textarea') {
        input = document.createElement('textarea');
        input.className = 'form-control';
        input.rows = 3;
        input.placeholder = field.placeholder || '';
        if (field.required) input.required = true;
      } else if (type === 'select') {
        input = document.createElement('select');
        input.className = 'form-select';
        if (field.required) input.required = true;
        const defOpt = document.createElement('option');
        defOpt.value = '';
        defOpt.textContent = field.placeholder || 'Selecione...';
        input.appendChild(defOpt);
        (field.options || []).forEach(function (opt) {
          const o = document.createElement('option');
          o.value = opt.value;
          o.textContent = opt.label;
          input.appendChild(o);
        });
      } else if (type === 'radio' || type === 'checkbox') {
        (field.options || []).forEach(function (opt, idx) {
          const div = document.createElement('div');
          div.className = 'form-check';
          const inp = document.createElement('input');
          inp.className = 'form-check-input';
          inp.type = type;
          inp.name = 'preview_' + field.id;
          inp.id = 'preview_' + field.id + '_' + idx;
          inp.value = opt.value;
          if (field.required) inp.required = true;
          const lb = document.createElement('label');
          lb.className = 'form-check-label';
          lb.htmlFor = inp.id;
          lb.textContent = opt.label;
          div.appendChild(inp);
          div.appendChild(lb);
          wrapper.appendChild(div);
        });
        container.appendChild(wrapper);
        return;
      } else if (type === 'file') {
        input = document.createElement('input');
        input.className = 'form-control';
        input.type = 'file';
      } else if (type === 'cpf') {
        input = document.createElement('input');
        input.className = 'form-control cpf-mask';
        input.type = 'text';
        input.placeholder = field.placeholder || '000.000.000-00';
        input.value = '000.000.000-00';
        input.disabled = true;
        input.style.color = '#adb5bd';
      } else if (type === 'cnpj') {
        input = document.createElement('input');
        input.className = 'form-control cnpj-mask';
        input.type = 'text';
        input.placeholder = field.placeholder || '00.000.000/0000-00';
        input.value = '00.000.000/0000-00';
        input.disabled = true;
        input.style.color = '#adb5bd';
      } else if (type === 'phone') {
        input = document.createElement('input');
        input.className = 'form-control phone-mask';
        input.type = 'text';
        input.placeholder = field.placeholder || '(00) 00000-0000';
        input.value = '(00) 00000-0000';
        input.disabled = true;
        input.style.color = '#adb5bd';
      } else if (type === 'currency') {
        input = document.createElement('input');
        input.className = 'form-control currency-mask';
        input.type = 'text';
        input.placeholder = field.placeholder || 'R$ 0,00';
        input.value = 'R$ 1.234,56';
        input.disabled = true;
        input.style.color = '#adb5bd';
      } else {
        input = document.createElement('input');
        input.className = 'form-control';
        input.type = type === 'number' ? 'number' : 'text';
        input.placeholder = field.placeholder || '';
        if (field.required) input.required = true;
      }

      if (input) wrapper.appendChild(input);
      container.appendChild(wrapper);
    });
  }

  function removeField(fieldId) {
    fields = fields.filter(function (f) { return f.id !== fieldId; });
    if (selectedFieldId === fieldId) {
      selectedFieldId = null;
    }
    renderFields();
    updateHiddenInput();
    renderPreview();
  }

  function moveField(fromIndex, toIndex) {
    if (fromIndex < 0 || fromIndex >= fields.length || toIndex < 0 || toIndex >= fields.length) return;
    const item = fields.splice(fromIndex, 1)[0];
    fields.splice(toIndex, 0, item);
    renderFields();
    updateHiddenInput();
    renderPreview();
  }

  function updateFieldProperty(fieldId, prop, value) {
    const field = getFieldById(fieldId);
    if (!field) return;

    if (prop.indexOf('.') > -1) {
      const parts = prop.split('.');
      if (parts.length === 2) {
        field[parts[0]] = field[parts[0]] || {};
        field[parts[0]][parts[1]] = value;
      }
    } else {
      field[prop] = value;
    }
    renderPreview();
    updateHiddenInput();
  }

  function renderProperties() {
    const panel = document.getElementById('field-properties');
    if (!panel) return;

    if (!selectedFieldId) {
      panel.innerHTML =
        '<div class="text-muted text-center py-5"><i class="fas fa-arrow-left fa-2x mb-2 d-block"></i>Selecione um campo para editar suas propriedades</div>';
      return;
    }

    const field = getFieldById(selectedFieldId);
    if (!field) {
      panel.innerHTML = '<div class="text-muted">Campo nao encontrado</div>';
      return;
    }

    const isOptionType = field.type === 'select' || field.type === 'radio' || field.type === 'checkbox';
    const isSectionTitle = field.type === 'section_title';

    let html = '';
    html += '<div class="mb-3">';
    html += '  <label class="form-label fw-semibold"><i class="fas fa-tag me-1"></i>Rotulo</label>';
    html += '  <input type="text" class="form-control prop-label" value="' + escapeHtml(field.label) + '" placeholder="Rotulo do campo">';
    html += '</div>';

    if (!isSectionTitle) {
      html += '<div class="mb-3">';
      html += '  <label class="form-label fw-semibold"><i class="fas fa-text me-1"></i>Placeholder</label>';
      html += '  <input type="text" class="form-control prop-placeholder" value="' + escapeHtml(field.placeholder || '') + '" placeholder="Texto de exemplo">';
      html += '</div>';

      html += '<div class="mb-3">';
      html += '  <label class="form-label fw-semibold"><i class="fas fa-info-circle me-1"></i>Texto de Ajuda</label>';
      html += '  <input type="text" class="form-control prop-help-text" value="' + escapeHtml(field.help_text || '') + '" placeholder="Instrucao exibida abaixo do campo">';
      html += '</div>';

      html += '<div class="mb-3">';
      html += '  <div class="form-check form-switch">';
      html += '    <input class="form-check-input prop-required" type="checkbox" ' + (field.required ? 'checked' : '') + ' id="prop-required">';
      html += '    <label class="form-check-label" for="prop-required">Campo obrigatorio</label>';
      html += '  </div>';
      html += '</div>';
    }

    if (isOptionType) {
      html += '<hr><div class="mb-3">';
      html += '  <label class="form-label fw-semibold"><i class="fas fa-list me-1"></i>Opcoes</label>';
      html += '  <div id="options-list" class="mb-2">';
      (field.options || []).forEach(function (opt, idx) {
        html +=
          '<div class="input-group input-group-sm mb-1 option-row" data-index="' + idx + '">' +
          '  <span class="input-group-text handle-option"><i class="fas fa-grip-vertical"></i></span>' +
          '  <input type="text" class="form-control opt-value" placeholder="Valor" value="' + escapeHtml(opt.value) + '">' +
          '  <input type="text" class="form-control opt-label" placeholder="Rotulo" value="' + escapeHtml(opt.label) + '">' +
          '  <button class="btn btn-outline-danger btn-sm remove-option" type="button"><i class="fas fa-times"></i></button>' +
          '</div>';
      });
      html += '  </div>';
      html += '  <button class="btn btn-sm btn-outline-primary w-100" id="add-option-btn"><i class="fas fa-plus me-1"></i>Adicionar Opcao</button>';
      html += '</div>';
    }

    html += '<hr><div class="mb-3">';
    html += '  <label class="form-label fw-semibold"><i class="fas fa-check-double me-1"></i>Validacao</label>';
    html += '  <div class="row g-2 mb-2">';
    html += '    <div class="col-6"><input type="number" class="form-control form-control-sm prop-val-min" placeholder="Min" value="' + (field.validation.min !== null && field.validation.min !== undefined ? field.validation.min : '') + '"></div>';
    html += '    <div class="col-6"><input type="number" class="form-control form-control-sm prop-val-max" placeholder="Max" value="' + (field.validation.max !== null && field.validation.max !== undefined ? field.validation.max : '') + '"></div>';
    html += '  </div>';
    html += '  <input type="text" class="form-control form-control-sm prop-val-pattern" placeholder="Regex (opcional)" value="' + escapeHtml(field.validation.pattern || '') + '">';
    html += '</div>';

    html += '<hr><div class="mb-3">';
    html += '  <label class="form-label fw-semibold"><i class="fas fa-file-signature me-1"></i>Mapeamento E-Docs</label>';
    html += '  <select class="form-select prop-edocs-mapping">';
    EDOCS_MAPPINGS.forEach(function (m) {
      html += '    <option value="' + m.value + '"' + (field.edocs_mapping === m.value ? ' selected' : '') + '>' + m.label + '</option>';
    });
    html += '  </select>';
    html += '</div>';

    panel.innerHTML = html;
    bindPropertyEvents(field);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function bindPropertyEvents(field) {
    const panel = document.getElementById('field-properties');
    if (!panel) return;

    const labelInput = panel.querySelector('.prop-label');
    if (labelInput) {
      labelInput.addEventListener('input', function () {
        field.label = this.value;
        renderFields();
        renderPreview();
        updateHiddenInput();
      });
    }

    const placeholderInput = panel.querySelector('.prop-placeholder');
    if (placeholderInput) {
      placeholderInput.addEventListener('input', function () {
        updateFieldProperty(field.id, 'placeholder', this.value);
      });
    }

    const helpInput = panel.querySelector('.prop-help-text');
    if (helpInput) {
      helpInput.addEventListener('input', function () {
        updateFieldProperty(field.id, 'help_text', this.value);
      });
    }

    const requiredCheck = panel.querySelector('.prop-required');
    if (requiredCheck) {
      requiredCheck.addEventListener('change', function () {
        field.required = this.checked;
        renderFields();
        renderPreview();
        updateHiddenInput();
      });
    }

    const minInput = panel.querySelector('.prop-val-min');
    if (minInput) {
      minInput.addEventListener('input', function () {
        field.validation.min = this.value !== '' ? Number(this.value) : null;
        updateHiddenInput();
      });
    }

    const maxInput = panel.querySelector('.prop-val-max');
    if (maxInput) {
      maxInput.addEventListener('input', function () {
        field.validation.max = this.value !== '' ? Number(this.value) : null;
        updateHiddenInput();
      });
    }

    const patternInput = panel.querySelector('.prop-val-pattern');
    if (patternInput) {
      patternInput.addEventListener('input', function () {
        field.validation.pattern = this.value || null;
        updateHiddenInput();
      });
    }

    const mappingSelect = panel.querySelector('.prop-edocs-mapping');
    if (mappingSelect) {
      mappingSelect.addEventListener('change', function () {
        field.edocs_mapping = this.value || null;
        updateHiddenInput();
      });
    }

    const addOptionBtn = panel.querySelector('#add-option-btn');
    if (addOptionBtn) {
      addOptionBtn.addEventListener('click', function () {
        if (!field.options) field.options = [];
        field.options.push({ value: '', label: '' });
        renderProperties();
        renderFields();
        updateHiddenInput();
      });
    }

    const optionsList = panel.querySelector('#options-list');
    if (optionsList) {
      optionsList.addEventListener('click', function (e) {
        const btn = e.target.closest('.remove-option');
        if (btn) {
          const row = btn.closest('.option-row');
          const idx = parseInt(row.getAttribute('data-index'), 10);
          if (!isNaN(idx) && field.options) {
            field.options.splice(idx, 1);
            renderProperties();
            renderFields();
            updateHiddenInput();
          }
        }
      });

      optionsList.addEventListener('input', function (e) {
        const row = e.target.closest('.option-row');
        if (!row) return;
        const idx = parseInt(row.getAttribute('data-index'), 10);
        if (isNaN(idx) || !field.options || !field.options[idx]) return;
        const valInput = row.querySelector('.opt-value');
        const lblInput = row.querySelector('.opt-label');
        if (valInput) field.options[idx].value = valInput.value;
        if (lblInput) field.options[idx].label = lblInput.value;
        updateHiddenInput();
      });
    }
  }

  function selectField(fieldId) {
    selectedFieldId = fieldId;
    renderFields();
    renderProperties();
  }

  function renderFields() {
    const zone = document.getElementById('fields-drop-zone');
    if (!zone) return;

    if (fields.length === 0) {
      zone.innerHTML =
        '<div class="text-muted text-center py-5 border border-2 border-dashed rounded" id="empty-zone">' +
        '  <i class="fas fa-cloud-upload-alt fa-3x mb-3 d-block"></i>' +
        '  <p class="mb-0">Arraste campos para ca ou clique nos botoes ao lado</p>' +
        '</div>';
      return;
    }

    zone.innerHTML = '';
    fields.forEach(function (field, index) {
      const card = document.createElement('div');
      card.className = 'card mb-2 field-card' + (selectedFieldId === field.id ? ' border-primary shadow-sm' : '');
      card.setAttribute('data-field-id', field.id);
      card.setAttribute('draggable', 'true');

      const typeDef = FIELD_TYPES.find(function (t) { return t.type === field.type; });
      const icon = typeDef ? typeDef.icon : 'fa-cog';

      const labelText = field.label || 'Campo sem rotulo (' + field.type + ')';

      card.innerHTML =
        '<div class="card-body py-2 px-3 d-flex align-items-center gap-2">' +
        '  <span class="drag-handle text-muted" style="cursor:grab"><i class="fas fa-grip-vertical"></i></span>' +
        '  <span class="badge bg-light text-dark border me-1"><i class="fas ' + icon + ' me-1"></i>' + (typeDef ? typeDef.label : field.type) + '</span>' +
        '  <span class="flex-grow-1 text-truncate small">' + escapeHtml(labelText) + '</span>' +
        '  <span class="text-muted small">#' + (index + 1) + '</span>' +
        '  <button class="btn btn-sm text-danger remove-field-btn" type="button" title="Remover campo"><i class="fas fa-times"></i></button>' +
        '</div>';

      card.querySelector('.remove-field-btn').addEventListener('click', function (e) {
        e.stopPropagation();
        removeField(field.id);
      });

      card.addEventListener('click', function () {
        selectField(field.id);
      });

      card.addEventListener('dragstart', function (e) {
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', field.id);
        card.classList.add('opacity-50');
      });

      card.addEventListener('dragend', function () {
        card.classList.remove('opacity-50');
      });

      card.addEventListener('dragover', function (e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
      });

      card.addEventListener('drop', function (e) {
        e.preventDefault();
        e.stopPropagation();
        const draggedId = e.dataTransfer.getData('text/plain');
        const fromIndex = fields.findIndex(function (f) { return f.id === draggedId; });
        if (fromIndex === -1) {
          addField(draggedId);
          return;
        }
        const toIndex = fields.findIndex(function (f) { return f.id === field.id; });
        if (fromIndex !== -1 && toIndex !== -1 && fromIndex !== toIndex) {
          moveField(fromIndex, toIndex);
        }
      });

      zone.appendChild(card);
    });
  }

  function addField(type) {
    const field = defaultField(type);

    const typeDef = FIELD_TYPES.find(function (t) { return t.type === type; });
    field.label = typeDef ? 'Novo ' + typeDef.label : 'Novo Campo';

    if (type === 'cpf') {
      field.placeholder = '000.000.000-00';
    } else if (type === 'cnpj') {
      field.placeholder = '00.000.000/0000-00';
    } else if (type === 'phone') {
      field.placeholder = '(00) 00000-0000';
    } else if (type === 'currency') {
      field.placeholder = 'R$ 0,00';
    }

    fields.push(field);
    renderFields();
    updateHiddenInput();
    renderPreview();
    selectField(field.id);
  }

  function saveForm() {
    const btn = document.getElementById('save-form-btn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Salvando...';
    }

    updateHiddenInput();

    const form = document.getElementById('form-builder-form');
    const formData = new FormData(form);

    fetch('/forms/salvar', {
      method: 'POST',
      body: formData,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          if (data.redirect) {
            window.location.href = data.redirect;
          } else {
            showToast('success', 'Formulario salvo com sucesso!');
          }
        } else {
          showToast('danger', data.message || 'Erro ao salvar formulario.');
        }
      })
      .catch(function () {
        showToast('danger', 'Erro de conexao ao salvar formulario.');
      })
      .finally(function () {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i class="fas fa-save me-1"></i>Salvar Formulario';
        }
      });
  }

  function showToast(type, message) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-bg-' + type + ' border-0 show';
    toast.role = 'alert';
    toast.innerHTML =
      '<div class="d-flex">' +
      '  <div class="toast-body">' + escapeHtml(message) + '</div>' +
      '  <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>' +
      '</div>';
    container.appendChild(toast);
    setTimeout(function () { toast.remove(); }, 4000);
  }

  function initEdocsConfig() {
    const container = document.getElementById('edocs-config');
    if (!container) return;

    let html = '';

    html += '<div class="mb-4">';
    html += '  <div class="form-check form-switch">';
    html += '    <input class="form-check-input" type="checkbox" name="auto_submit" id="auto-submit">';
    html += '    <label class="form-check-label" for="auto-submit">Enviar automaticamente ao E-Docs apos preenchimento</label>';
    html += '  </div>';
    html += '</div>';

    html += '<h6 class="fw-bold border-bottom pb-2 mb-3"><i class="fas fa-file-alt me-1"></i>Documento</h6>';
    html += '<div class="row g-3 mb-4">';
    html += '  <div class="col-md-6">';
    html += '    <label class="form-label">Valor Legal</label>';
    html += '    <select class="form-select" name="valor_legal">';
    VALOR_LEGAL_OPTIONS.forEach(function (opt) {
      html += '      <option value="' + opt.value + '">' + opt.label + '</option>';
    });
    html += '    </select>';
    html += '  </div>';
    html += '  <div class="col-md-6">';
    html += '    <label class="form-label">Natureza</label>';
    html += '    <select class="form-select" name="natureza">';
    NATUREZA_OPTIONS.forEach(function (opt) {
      html += '      <option value="' + opt.value + '">' + opt.label + '</option>';
    });
    html += '    </select>';
    html += '  </div>';
    html += '</div>';

    html += '<h6 class="fw-bold border-bottom pb-2 mb-3"><i class="fas fa-cogs me-1"></i>Processo</h6>';
    html += '<div class="mb-3">';
    html += '  <div class="form-check form-switch">';
    html += '    <input class="form-check-input" type="checkbox" name="criar_processo" id="criar-processo">';
    html += '    <label class="form-check-label" for="criar-processo">Criar processo</label>';
    html += '  </div>';
    html += '</div>';
    html += '<div class="mb-3" id="assunto-template-wrapper">';
    html += '  <label class="form-label">Template de Assunto</label>';
    html += '  <input type="text" class="form-control" name="template_assunto" placeholder="{{form_name}} - {{protocolo}}">';
    html += '  <div class="form-text">Use <code>{{form_name}}</code> e <code>{{protocolo}}</code> como placeholders.</div>';
    html += '</div>';

    container.innerHTML = html;

    const criarProcesso = container.querySelector('#criar-processo');
    const assuntoWrapper = container.querySelector('#assunto-template-wrapper');
    if (criarProcesso && assuntoWrapper) {
      criarProcesso.addEventListener('change', function () {
        assuntoWrapper.style.display = this.checked ? 'block' : 'none';
      });
      assuntoWrapper.style.display = criarProcesso.checked ? 'block' : 'none';
    }
  }

  function initFormBuilder() {
    const zone = document.getElementById('fields-drop-zone');
    const panels = document.querySelectorAll('.field-type-btn');

    if (window.FORM_DATA && Array.isArray(window.FORM_DATA)) {
      fields = JSON.parse(JSON.stringify(window.FORM_DATA));
    } else if (window.FORM_DATA && window.FORM_DATA.fields) {
      fields = JSON.parse(JSON.stringify(window.FORM_DATA.fields));
    }

    panels.forEach(function (btn) {
      const type = btn.getAttribute('data-type');

      btn.addEventListener('click', function () {
        addField(type);
      });

      btn.addEventListener('dragstart', function (e) {
        e.dataTransfer.effectAllowed = 'copy';
        e.dataTransfer.setData('text/plain', type);
      });
    });

    if (zone) {
      zone.addEventListener('dragover', function (e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        zone.classList.add('bg-light');
      });

      zone.addEventListener('dragleave', function () {
        zone.classList.remove('bg-light');
      });

      zone.addEventListener('drop', function (e) {
        e.preventDefault();
        zone.classList.remove('bg-light');
        const type = e.dataTransfer.getData('text/plain');
        if (type && FIELD_TYPES.some(function (t) { return t.type === type; })) {
          addField(type);
        } else {
          const draggedId = type;
          const existingIndex = fields.findIndex(function (f) { return f.id === draggedId; });
          if (existingIndex === -1 && FIELD_TYPES.some(function (t) { return t.type === draggedId; })) {
            addField(draggedId);
          }
        }
      });
    }

    const saveBtn = document.getElementById('save-form-btn');
    if (saveBtn) {
      saveBtn.addEventListener('click', saveForm);
    }

    initEdocsConfig();
    renderFields();
    renderPreview();
    updateHiddenInput();

    if (fields.length > 0) {
      selectField(fields[0].id);
    } else {
      renderProperties();
    }

    const triggerEl = document.querySelector('button[data-bs-toggle="tab"][data-bs-target="#preview"]');
    if (triggerEl) {
      triggerEl.addEventListener('shown.bs.tab', function () {
        renderPreview();
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFormBuilder);
  } else {
    initFormBuilder();
  }

})();
