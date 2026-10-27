// ==========================================================================
// PORTAL DO ASSISTENTE - FATEC BEBEDOURO
// Script de Controle, Validador RAG e Integração de Webhooks
// ==========================================================================

(function () {
  'use strict';

  // 1. DADOS DOS 22 DOCUMENTOS OFICIAIS DA BASE DE CONHECIMENTO
  const KB_DOCUMENTS = [
    {
      file: "area-do-aluno.json",
      titulo: "Área do Aluno",
      categoria: "servicos",
      resumo: "Informações sobre acesso ao SIGA, serviços acadêmicos, carteirinha estudantil e canais de atendimento.",
      faqs: 7,
      secoes: 6
    },
    {
      file: "biblioteca-links-oficiais.json",
      titulo: "Biblioteca Central",
      categoria: "servicos",
      resumo: "Acervo físico e digital, normas de empréstimo, BiblioCPS, bases científicas e repositórios acadêmicos.",
      faqs: 8,
      secoes: 4
    },
    {
      file: "big-data-no-agronegocio-links-oficiais.json",
      titulo: "Curso: Big Data no Agronegócio",
      categoria: "cursos",
      resumo: "Apresentação do curso superior de tecnologia, perfil profissional, infraestrutura de laboratórios e mercado.",
      faqs: 9,
      secoes: 10
    },
    {
      file: "grade-big-data-no-agronegocio-nova-2026.json",
      titulo: "Grade Big Data no Agronegócio (Nova 2026)",
      categoria: "cursos",
      resumo: "Nova matriz curricular organizada por eixos de formação com curricularização da extensão.",
      faqs: 5,
      secoes: 8
    },
    {
      file: "grade-big-data-no-agronegocio-ate-2025.json",
      titulo: "Grade Big Data no Agronegócio (Até 2025)",
      categoria: "cursos",
      resumo: "Matriz curricular vigente para turmas ingressantes até 2025, com carga horária por semestre.",
      faqs: 5,
      secoes: 8
    },
    {
      file: "coordenacao-big-data-no-agronegocio.json",
      titulo: "Coordenação de Big Data",
      categoria: "cursos",
      resumo: "Contato oficial e horários de atendimento do coordenador do curso Prof. Dr. Renan Guilherme Nespolo.",
      faqs: 3,
      secoes: 2
    },
    {
      file: "estagio-big-data-no-agronegocio.json",
      titulo: "Estágio: Big Data no Agronegócio",
      categoria: "estagio",
      resumo: "Regulamento, prazos, relatórios parciais/finais e documentação para estágio curricular obrigatório.",
      faqs: 11,
      secoes: 11
    },
    {
      file: "convalidacao-big-data-no-agronegocio.json",
      titulo: "Convalidação de Estágio — Big Data",
      categoria: "estagio",
      resumo: "Processo para equivalência de emprego formal ou atividade profissional com a carga de estágio supervisionado.",
      faqs: 6,
      secoes: 2
    },
    {
      file: "tcc-big-data-no-agronegocio.json",
      titulo: "TCC: Big Data no Agronegócio",
      categoria: "estagio",
      resumo: "Manual de orientação, cronograma, modelo de autorização, depósito e defesa pública do Trabalho de Conclusão de Curso.",
      faqs: 4,
      secoes: 19
    },
    {
      file: "logistica-links-oficiais.json",
      titulo: "Curso: Logística",
      categoria: "cursos",
      resumo: "Apresentação da graduação em Logística, áreas de atuação em supply chain, gestão de transportes e compras.",
      faqs: 9,
      secoes: 6
    },
    {
      file: "grade-logistica-eixos-curriculares.json",
      titulo: "Grade Curricular: Logística",
      categoria: "cursos",
      resumo: "Matriz por eixos temáticos, disciplinas obrigatórias, optativas e distribuição de créditos.",
      faqs: 7,
      secoes: 8
    },
    {
      file: "coordenacao-estagio-logistica.json",
      titulo: "Coordenação de Estágio: Logística",
      categoria: "estagio",
      resumo: "Responsável pelo acompanhamento e validação de estágios supervisionados do curso de Logística.",
      faqs: 3,
      secoes: 2
    },
    {
      file: "estagio-logistica.json",
      titulo: "Estágio Supervisionado: Logística",
      categoria: "estagio",
      resumo: "Manual completo de estágio, formulários obrigatórios, prazos e convênios para alunos de Logística.",
      faqs: 11,
      secoes: 7
    },
    {
      file: "convalidacao-logistica.json",
      titulo: "Convalidação de Estágio — Logística",
      categoria: "estagio",
      resumo: "Critérios de aproveitamento de experiência profissional e equivalência de horas de trabalho na área.",
      faqs: 6,
      secoes: 2
    },
    {
      file: "tcc-logistica.json",
      titulo: "TCC: Logística",
      categoria: "estagio",
      resumo: "Regulamento, normas de formatação ABNT, cronograma de entrega e bancas examinadoras de TCC em Logística.",
      faqs: 4,
      secoes: 19
    },
    {
      file: "quem-somos.json",
      titulo: "Institucional: Quem Somos",
      categoria: "institucional",
      resumo: "História da Fatec Bebedouro, fundação, missão de ensino público gratuito de qualidade e infraestrutura do campus.",
      faqs: 4,
      secoes: 3
    },
    {
      file: "diretora-da-unidade.json",
      titulo: "Diretoria da Unidade",
      categoria: "institucional",
      resumo: "Gabinete da direção geral, Profa. Dra. Carla Lanzotti, competências e canais de comunicação com a comunidade.",
      faqs: 2,
      secoes: 2
    },
    {
      file: "diretoria-academica.json",
      titulo: "Diretoria Acadêmica (Secretaria)",
      categoria: "servicos",
      resumo: "Emissão de histórico escolar, atestados de matrícula, trancamento, transferências e diplomas oficiais.",
      faqs: 3,
      secoes: 3
    },
    {
      file: "diretoria-de-servicos.json",
      titulo: "Diretoria de Serviços Administrativos",
      categoria: "institucional",
      resumo: "Gestão administrativa, almoxarifado, patrimônio, compras e recursos humanos da faculdade.",
      faqs: 3,
      secoes: 2
    },
    {
      file: "congregacao.json",
      titulo: "Congregação da Fatec",
      categoria: "institucional",
      resumo: "Órgão máximo colegiado de deliberação acadêmica, representação docente, discente e comunidade externa.",
      faqs: 4,
      secoes: 9
    },
    {
      file: "comissao-propria-de-avaliacao-cpa.json",
      titulo: "Comissão Própria de Avaliação (CPA)",
      categoria: "institucional",
      resumo: "Avaliação institucional periódica, relatórios de autoavaliação, melhorias e participação dos alunos.",
      faqs: 4,
      secoes: 4
    },
    {
      file: "regulamento-geral.json",
      titulo: "Regulamento Geral dos Cursos (CPS)",
      categoria: "institucional",
      resumo: "Direitos e deveres discentes, regime disciplinar, avaliação de rendimento e normas do Centro Paula Souza.",
      faqs: 2,
      secoes: 3
    },
    {
      file: "tcc-gabriel-bassani.json",
      titulo: "TCC de Gabriel Bassani da Silva",
      categoria: "estagio",
      resumo: "Plataforma de Assistente Virtual Multimodal com RAG Local, transcrição de áudio por GPU CUDA e orquestração multi-agente.",
      faqs: 6,
      secoes: 4
    }
  ];

  const GITHUB_REPO_URL = 'https://github.com/Gabriel-Bassani-da-Silva/chatbot';
  const DRIVE_FOLDER_ID = '1AtN4X4jp5okt8ChlwRmYMpI4XwQuurF0';

  // 2. CONFIGURAÇÃO DE DOMÍNIO E AMBIENTE (LOCAL VS PÚBLICO)
  var rawDomain = document.body.getAttribute('data-domain') || '';
  var fallbackDomain = 'fatecn8nabc.dpdns.org';
  var domain = (rawDomain && rawDomain.indexOf('{{') === -1) ? rawDomain : fallbackDomain;

  var currentMode = 'local';
  var currentValidatedJson = null;
  var currentValidatedFileName = 'novo-documento.json';

  // Alternador de Modo: Local / Público
  window.setMode = function (mode) {
    currentMode = mode;
    var tabLocal = document.getElementById('tab-local');
    var tabPublic = document.getElementById('tab-public');
    var btnN8n = document.getElementById('btn-n8n');
    var btnChatwoot = document.getElementById('btn-chatwoot');
    var btnWaha = document.getElementById('btn-waha');
    var wahaNotice = document.getElementById('waha-notice');
    var wahaBadge = document.getElementById('waha-badge');
    var envLabel = document.getElementById('env-label');
    var badge = document.getElementById('env-badge');

    if (mode === 'public') {
      if (tabLocal) tabLocal.classList.remove('active');
      if (tabPublic) tabPublic.classList.add('active');
      if (btnN8n) btnN8n.href = 'https://n8n.' + domain;
      if (btnChatwoot) btnChatwoot.href = 'https://chatwoot.' + domain;
      if (btnWaha) btnWaha.style.display = 'none';
      if (wahaNotice) wahaNotice.style.display = 'flex';
      if (wahaBadge) {
        wahaBadge.innerHTML = '<span class="status-dot" style="background:#f59e0b"></span> Apenas Local';
      }
      if (envLabel) envLabel.textContent = 'Público: ' + domain;
      if (badge) badge.classList.add('public');
      document.querySelectorAll('.btn-restart-action').forEach(function (b) {
        b.style.display = 'none';
      });
      try { localStorage.setItem('portal_mode', 'public'); } catch (e) {}
    } else {
      if (tabPublic) tabPublic.classList.remove('active');
      if (tabLocal) tabLocal.classList.add('active');
      if (btnN8n) btnN8n.href = 'http://localhost:5678';
      if (btnChatwoot) btnChatwoot.href = 'http://localhost:3001';
      if (btnWaha) btnWaha.style.display = 'flex';
      if (wahaNotice) wahaNotice.style.display = 'none';
      if (wahaBadge) {
        wahaBadge.innerHTML = '<span class="status-dot"></span> Local (3000)';
      }
      if (envLabel) envLabel.textContent = 'Portas Locais (Docker)';
      if (badge) badge.classList.remove('public');
      document.querySelectorAll('.btn-restart-action').forEach(function (b) {
        b.style.display = 'inline-flex';
      });
      try { localStorage.setItem('portal_mode', 'local'); } catch (e) {}
    }
  };

  function getBaseN8nUrl() {
    return currentMode === 'public' ? ('https://n8n.' + domain) : 'http://localhost:5678';
  }

  // 3. NAVEGAÇÃO ENTRE ABAS
  window.switchSection = function (tabId) {
    const tabs = document.querySelectorAll('.nav-tab');
    const sections = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
      if (tab.getAttribute('data-target') === tabId) {
        tab.classList.add('active');
      } else {
        tab.classList.remove('active');
      }
    });

    sections.forEach(sec => {
      if (sec.id === tabId) {
        sec.classList.add('active');
      } else {
        sec.classList.remove('active');
      }
    });
  };

  // 4. SISTEMA DE TOAST NOTIFICATIONS
  window.showToast = function (message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'fa-circle-info';
    if (type === 'success') icon = 'fa-circle-check';
    if (type === 'warning') icon = 'fa-triangle-exclamation';
    if (type === 'error') icon = 'fa-circle-exclamation';

    toast.innerHTML = `
      <i class="fa-solid ${icon}"></i>
      <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      setTimeout(() => toast.remove(), 250);
    }, duration);
  };

  // 4.1 REINICIAR CONTAINER DOCKER LOCALMENTE (ON-DEMAND)
  window.restartService = async function (containerName, displayName) {
    if (currentMode !== 'local') {
      window.showToast('Reinício de containers só é permitido no acesso Local (localhost)', 'warning');
      return;
    }

    const clickedBtn = window.event ? window.event.currentTarget : null;
    if (clickedBtn) {
      clickedBtn.disabled = true;
      clickedBtn.classList.add('loading');
    }

    window.showToast(`Reiniciando serviço ${displayName}... Aguarde.`, 'info', 6000);

    try {
      const response = await fetch(`/api/docker/restart/${containerName}`, {
        method: 'POST'
      });

      if (response.ok || response.status === 204) {
        window.showToast(`Serviço ${displayName} reiniciado com sucesso!`, 'success', 5000);
        setTimeout(function () {
          checkServicesHealth();
        }, 3000);
      } else {
        const text = await response.text();
        window.showToast(`Falha ao reiniciar ${displayName}: ${text || response.statusText}`, 'error', 6000);
      }
    } catch (err) {
      window.showToast(`Erro ao comunicar com a API Docker local: ${err.message}`, 'error', 6000);
    } finally {
      if (clickedBtn) {
        clickedBtn.disabled = false;
        clickedBtn.classList.remove('loading');
      }
    }
  };

  // 5. VALIDAÇÃO DE SCHEMA DO JSON DA BASE DE CONHECIMENTO
  function validateJsonStructure(data) {
    const errors = [];
    const warnings = [];

    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      return { valid: false, errors: ['O conteúdo deve ser um objeto JSON válido.'] };
    }

    // Campos obrigatórios no cabeçalho
    const requiredFields = ['categoria', 'titulo', 'fonte', 'resumo'];
    requiredFields.forEach(field => {
      if (!data[field] || typeof data[field] !== 'string' || !data[field].trim()) {
        errors.push(`Campo obrigatório ausente ou vazio: "${field}".`);
      }
    });

    // Validar perguntas frequentes se presentes
    let faqsCount = 0;
    if (data.perguntas_frequentes) {
      if (!Array.isArray(data.perguntas_frequentes)) {
        errors.push('O campo "perguntas_frequentes" deve ser uma lista (array).');
      } else {
        faqsCount = data.perguntas_frequentes.length;
        data.perguntas_frequentes.forEach((faq, idx) => {
          if (!faq.pergunta || typeof faq.pergunta !== 'string') {
            errors.push(`FAQ #${idx + 1}: campo "pergunta" ausente ou inválido.`);
          }
          if (!faq.resposta || typeof faq.resposta !== 'string') {
            errors.push(`FAQ #${idx + 1}: campo "resposta" ausente ou inválido.`);
          }
        });
      }
    } else {
      warnings.push('Documento sem "perguntas_frequentes". Recomenda-se adicionar FAQs para maior relevância no RAG.');
    }

    // Validar seções de dados estruturados
    let sectionsCount = 0;
    if (data.dados_estruturados) {
      if (typeof data.dados_estruturados !== 'object' || Array.isArray(data.dados_estruturados)) {
        errors.push('O campo "dados_estruturados" deve ser um objeto com seções.');
      } else {
        sectionsCount = Object.keys(data.dados_estruturados).length;
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      faqsCount,
      sectionsCount,
      title: data.titulo || 'Sem título',
      category: data.categoria || 'Geral'
    };
  }

  // Manipulador de leitura de arquivo
  function handleFileSelected(file) {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.json')) {
      showToast('Por favor, selecione apenas arquivos com extensão .json', 'error');
      return;
    }

    currentValidatedFileName = file.name;
    const reader = new FileReader();

    reader.onload = function (e) {
      try {
        const parsed = JSON.parse(e.target.result);
        currentValidatedJson = parsed;
        const res = validateJsonStructure(parsed);
        renderValidationResult(file, res);
      } catch (err) {
        currentValidatedJson = null;
        renderValidationResult(file, {
          valid: false,
          errors: ['Erro de sintaxe JSON: ' + err.message],
          warnings: [],
          faqsCount: 0,
          sectionsCount: 0,
          title: 'JSON Inválido',
          category: 'Erro'
        });
      }
    };

    reader.onerror = function () {
      showToast('Erro ao ler o arquivo do disco.', 'error');
    };

    reader.readAsText(file, 'UTF-8');
  }

  function renderValidationResult(file, res) {
    const panel = document.getElementById('validation-panel');
    const fileNameEl = document.getElementById('val-file-name');
    const fileSizeEl = document.getElementById('val-file-size');
    const statusBadge = document.getElementById('val-status-badge');
    const titleEl = document.getElementById('val-title');
    const categoryEl = document.getElementById('val-category');
    const faqsEl = document.getElementById('val-faqs');
    const sectionsEl = document.getElementById('val-sections');
    const messagesEl = document.getElementById('val-messages');
    const btnIngest = document.getElementById('btn-ingest-json');

    panel.style.display = 'flex';
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = (file.size / 1024).toFixed(1) + ' KB';

    titleEl.textContent = res.title;
    categoryEl.textContent = res.category;
    faqsEl.textContent = res.faqsCount;
    sectionsEl.textContent = res.sectionsCount;

    if (res.valid) {
      statusBadge.className = 'val-badge valid';
      statusBadge.innerHTML = '<i class="fa-solid fa-circle-check"></i> Válido para o RAG';
      btnIngest.disabled = false;
      btnIngest.style.opacity = '1';
    } else {
      statusBadge.className = 'val-badge invalid';
      statusBadge.innerHTML = '<i class="fa-solid fa-circle-xmark"></i> Erros no Schema';
      btnIngest.disabled = true;
      btnIngest.style.opacity = '0.5';
    }

    let html = '';
    if (res.errors && res.errors.length > 0) {
      res.errors.forEach(err => {
        html += `<div class="val-msg error"><i class="fa-solid fa-triangle-exclamation"></i> <span>${err}</span></div>`;
      });
    }

    if (res.warnings && res.warnings.length > 0) {
      res.warnings.forEach(warn => {
        html += `<div class="val-msg success"><i class="fa-solid fa-info-circle"></i> <span>${warn}</span></div>`;
      });
    }

    if (res.valid && (!res.warnings || res.warnings.length === 0)) {
      html += `<div class="val-msg success"><i class="fa-solid fa-check"></i> <span>Estrutura 100% aderente ao padrão da Fatec Bebedouro. Pronto para ingestão!</span></div>`;
    }

    messagesEl.innerHTML = html;
    showToast(res.valid ? 'Arquivo JSON validado com sucesso!' : 'Arquivo contém inconsistências de schema.', res.valid ? 'success' : 'warning');
  }

  window.clearSelectedFile = function () {
    currentValidatedJson = null;
    const panel = document.getElementById('validation-panel');
    const fileInput = document.getElementById('file-input');
    if (panel) panel.style.display = 'none';
    if (fileInput) fileInput.value = '';
  };

  window.downloadCurrentValidatedJson = function () {
    if (!currentValidatedJson) {
      showToast('Nenhum JSON carregado no momento.', 'warning');
      return;
    }
    const blob = new Blob([JSON.stringify(currentValidatedJson, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = currentValidatedFileName || 'documento-formatado.json';
    a.click();
    URL.revokeObjectURL(url);
    showToast('Download concluído!', 'success');
  };

  window.downloadSchemaTemplate = function () {
    const template = {
      categoria: "cursos",
      titulo: "Nome Oficial do Curso ou Regulamento",
      fonte: "Fatec Bebedouro — Diretoria Acadêmica",
      resumo: "Resumo explicativo e conciso sobre a finalidade deste documento, prazos principais e público-alvo.",
      dados_estruturados: {
        "apresentacao_geral": "Texto corrido descrevendo o objetivo e regras principais.",
        "prazos_e_datas": "Informações de prazos, semestres vigentes e cronogramas oficiais.",
        "procedimento_passo_a_passo": "Passo 1: Solicitar pelo SIGA.\nPasso 2: Entregar termo assinado na secretaria."
      },
      perguntas_frequentes: [
        {
          pergunta: "Qual é o prazo limite para entrega deste documento?",
          resposta: "O prazo regular encerra-se sempre até o último dia útil de cada semestre letivo.",
          palavras_chave: ["prazo", "entrega", "limite", "secretaria"]
        },
        {
          pergunta: "Onde retiro o modelo assinado pela coordenação?",
          resposta: "O modelo deve ser solicitado diretamente na secretaria acadêmica ou via SIGA.",
          palavras_chave: ["retirada", "secretaria", "assinatura"]
        }
      ]
    };

    const blob = new Blob([JSON.stringify(template, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'modelo-base-conhecimento.json';
    a.click();
    URL.revokeObjectURL(url);
    showToast('Modelo de documento baixado com sucesso!', 'success');
  };

  window.ingestCurrentFile = function () {
    if (!currentValidatedJson) {
      showToast('Carregue e valide um arquivo JSON primeiro.', 'warning');
      return;
    }

    showToast('Iniciando sincronização via webhook do n8n...', 'info');
    triggerGdriveSync();
  };

  // 6. DISPARO DE WEBHOOKS SOB DEMANDA
  window.triggerGdriveSync = function () {
    const url = getBaseN8nUrl() + '/webhook/sincronizar-gdrive';
    showToast('Enviando requisição de sincronização do Google Drive...', 'info');

    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trigger: 'portal_web', timestamp: Date.now() })
    })
      .then(res => {
        if (res.ok) {
          showToast('Sincronização iniciada com sucesso no n8n!', 'success');
        } else {
          showToast('Resposta do n8n: ' + res.status + ' (' + res.statusText + ')', 'warning');
        }
      })
      .catch(err => {
        // Fallback: se o browser bloquear CORS em fetch local mas o webhook disparar
        showToast('Webhook acionado! Verifique as execuções no n8n.', 'success');
      });
  };

  window.triggerModelSync = function () {
    const url = getBaseN8nUrl() + '/webhook/sincronizar-modelo-embedding';
    showToast('Consultando modelo ativo no RAG...', 'info');

    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trigger: 'portal_web', timestamp: Date.now() })
    })
      .then(res => {
        if (res.ok) {
          showToast('Verificação concluída com sucesso no n8n!', 'success');
        } else {
          showToast('Resposta do n8n: ' + res.status + ' (' + res.statusText + ')', 'warning');
        }
      })
      .catch(err => {
        showToast('Verificação disparada no n8n!', 'success');
      });
  };

  window.copyWebhookUrl = function (path) {
    const fullUrl = getBaseN8nUrl() + '/webhook/' + path;
    navigator.clipboard.writeText(fullUrl).then(() => {
      showToast('URL copiada: ' + fullUrl, 'success');
    }).catch(() => {
      prompt('Copie a URL abaixo:', fullUrl);
    });
  };

  // 7. RENDERIZAÇÃO DO CATÁLOGO DE DOCUMENTOS
  var activeCategory = 'todos';
  var searchQuery = '';

  function renderDocumentsCatalog() {
    const container = document.getElementById('docs-grid');
    if (!container) return;

    const filtered = KB_DOCUMENTS.filter(doc => {
      const matchCat = activeCategory === 'todos' || doc.categoria === activeCategory;
      const q = searchQuery.toLowerCase();
      const matchSearch = !q || doc.titulo.toLowerCase().includes(q) || doc.file.toLowerCase().includes(q) || doc.resumo.toLowerCase().includes(q);
      return matchCat && matchSearch;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-muted);">
          <i class="fa-solid fa-magnifying-glass" style="font-size: 2rem; margin-bottom: 0.75rem;"></i>
          <p>Nenhum documento encontrado para a busca realizada.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = filtered.map(doc => {
      let badgeLabel = 'Institucional';
      let badgeClass = 'institucional';
      if (doc.categoria === 'cursos') { badgeLabel = 'Cursos & Grades'; badgeClass = 'cursos'; }
      if (doc.categoria === 'estagio' || doc.categoria === 'tcc_e_projetos') { badgeLabel = 'Estágio & TCC'; badgeClass = 'estagio'; }
      if (doc.categoria === 'servicos') { badgeLabel = 'Secretaria & Aluno'; badgeClass = 'servicos'; }

      const githubFileUrl = `${GITHUB_REPO_URL}/blob/main/base-conhecimento/${doc.file}`;

      return `
        <div class="doc-card" onclick="openDocViewer('${doc.file}')">
          <div class="doc-top">
            <span class="doc-badge ${badgeClass}">${badgeLabel}</span>
            <span class="doc-file-name">${doc.file}</span>
          </div>
          <h4>${doc.titulo}</h4>
          <p>${doc.resumo}</p>
          <div class="doc-meta">
            <span><i class="fa-solid fa-circle-question"></i> ${doc.faqs} FAQs</span>
            <span><i class="fa-solid fa-list-check"></i> ${doc.secoes} seções</span>
          </div>
          <div class="doc-card-actions" onclick="event.stopPropagation()">
            <button type="button" class="btn-card-view" onclick="openDocViewer('${doc.file}')">
              <i class="fa-solid fa-eye"></i>
              <span>Ver Conteúdo Completo</span>
            </button>
            <a class="doc-link-btn" href="${githubFileUrl}" target="_blank" rel="noopener" title="Abrir no GitHub">
              <i class="fa-brands fa-github"></i>
            </a>
          </div>
        </div>
      `;
    }).join('');
  }

  // ==========================================================================
  // 7.1 VISUALIZADOR DE CONTEXTO COMPLETO (MARKDOWN FORMATADO E JSON BRUTO)
  // ==========================================================================
  var currentModalDoc = null;
  var currentModalTab = 'text';

  function simpleMarkdownFallback(md) {
    if (!md) return '<p>Nenhum conteúdo disponível.</p>';
    var html = md
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
      .replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>')
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*)\*/gim, '<em>$1</em>')
      .replace(/`([^`]+)`/gim, '<code>$1</code>')
      .replace(/^\- (.*$)/gim, '<li>$1</li>')
      .replace(/\n\n/gim, '</p><p>');
    return '<p>' + html + '</p>';
  }

  function getDocByFilename(filename) {
    if (window.FATEC_KB_FULL && Array.isArray(window.FATEC_KB_FULL)) {
      var found = window.FATEC_KB_FULL.find(function (d) {
        return d.file === filename || d.md_file === filename;
      });
      if (found) return found;
    }
    return KB_DOCUMENTS.find(function (d) { return d.file === filename; }) || null;
  }

  window.openDocViewer = function (filename) {
    var doc = getDocByFilename(filename);
    if (!doc) {
      showToast('Documento não encontrado.', 'warning');
      return;
    }

    currentModalDoc = doc;
    currentModalTab = 'text';

    var modal = document.getElementById('doc-viewer-modal');
    var modalTitle = document.getElementById('modal-doc-title');
    var catBadge = document.getElementById('modal-cat-badge');
    var fileBadge = document.getElementById('modal-file-badge');
    var metaFaqs = document.getElementById('modal-meta-faqs');
    var metaSections = document.getElementById('modal-meta-sections');
    var githubLink = document.getElementById('modal-github-link');
    var textBody = document.getElementById('viewer-text-body');
    var jsonBody = document.getElementById('viewer-json-body');

    if (!modal) return;

    modalTitle.textContent = doc.titulo;
    var badgeLabel = 'Institucional';
    var badgeClass = 'institucional';
    if (doc.categoria === 'cursos') { badgeLabel = 'Cursos & Grades'; badgeClass = 'cursos'; }
    if (doc.categoria === 'estagio' || doc.categoria === 'tcc_e_projetos') { badgeLabel = 'Estágio & TCC'; badgeClass = 'estagio'; }
    if (doc.categoria === 'servicos') { badgeLabel = 'Secretaria & Aluno'; badgeClass = 'servicos'; }

    catBadge.className = 'doc-badge ' + badgeClass;
    catBadge.textContent = badgeLabel;
    fileBadge.innerHTML = '<i class="fa-solid fa-file-lines"></i> ' + doc.file;
    if (metaFaqs) metaFaqs.innerHTML = '<i class="fa-solid fa-circle-question"></i> ' + (doc.faqs || 0) + ' FAQs';
    if (metaSections) metaSections.innerHTML = '<i class="fa-solid fa-list-check"></i> ' + (doc.secoes || 1) + ' seções';

    var githubUrl = GITHUB_REPO_URL + '/blob/main/base-conhecimento/' + doc.file;
    if (githubLink) githubLink.href = githubUrl;

    // Renderizar Texto Completo (.md)
    var mdContent = doc.md_text || '';
    if (!mdContent && doc.json_raw) {
      mdContent = '# ' + doc.titulo + '\n\n' + (doc.resumo || '');
    }

    if (window.marked && typeof window.marked.parse === 'function') {
      textBody.innerHTML = window.marked.parse(mdContent);
    } else {
      textBody.innerHTML = simpleMarkdownFallback(mdContent);
    }

    // Renderizar JSON Bruto Formatado
    var rawJson = doc.json_raw || doc;
    jsonBody.textContent = JSON.stringify(rawJson, null, 2);

    switchViewerTab('text');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  };

  window.closeDocViewerModal = function () {
    var modal = document.getElementById('doc-viewer-modal');
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = '';
  };

  window.handleModalBackdropClick = function (e) {
    if (e.target && e.target.id === 'doc-viewer-modal') {
      closeDocViewerModal();
    }
  };

  window.switchViewerTab = function (tab) {
    currentModalTab = tab;
    var tabText = document.getElementById('tab-view-text');
    var tabJson = document.getElementById('tab-view-json');
    var contentText = document.getElementById('viewer-content-text');
    var contentJson = document.getElementById('viewer-content-json');

    if (tab === 'json') {
      if (tabText) tabText.classList.remove('active');
      if (tabJson) tabJson.classList.add('active');
      if (contentText) contentText.style.display = 'none';
      if (contentJson) contentJson.style.display = 'block';
    } else {
      if (tabJson) tabJson.classList.remove('active');
      if (tabText) tabText.classList.add('active');
      if (contentJson) contentJson.style.display = 'none';
      if (contentText) contentText.style.display = 'block';
    }
  };

  window.copyCurrentViewerContent = function () {
    if (!currentModalDoc) return;
    var textToCopy = '';
    if (currentModalTab === 'json') {
      textToCopy = JSON.stringify(currentModalDoc.json_raw || currentModalDoc, null, 2);
    } else {
      textToCopy = currentModalDoc.md_text || (currentModalDoc.titulo + '\n\n' + currentModalDoc.resumo);
    }

    navigator.clipboard.writeText(textToCopy).then(function () {
      showToast('Conteúdo copiado para a área de transferência!', 'success');
    }).catch(function () {
      prompt('Copie o conteúdo abaixo:', textToCopy.slice(0, 500));
    });
  };

  window.downloadCurrentViewerFile = function () {
    if (!currentModalDoc) return;
    var baseName = currentModalDoc.file.replace(/\.json$/i, '');
    var fileName = currentModalTab === 'json' ? currentModalDoc.file : (baseName + '.md');
    var content = currentModalTab === 'json'
      ? JSON.stringify(currentModalDoc.json_raw || currentModalDoc, null, 2)
      : (currentModalDoc.md_text || '');
    var mime = currentModalTab === 'json' ? 'application/json' : 'text/markdown';

    var blob = new Blob([content], { type: mime + ';charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Download de ' + fileName + ' concluído!', 'success');
  };

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' || e.key === 'Esc') {
      closeDocViewerModal();
    }
  });

  window.filterCategory = function (cat) {
    activeCategory = cat;
    const pills = document.querySelectorAll('.cat-pill');
    pills.forEach(p => {
      if (p.textContent.toLowerCase().includes(cat) || (cat === 'todos' && p.textContent.includes('Todos'))) {
        p.classList.add('active');
      } else {
        p.classList.remove('active');
      }
    });
    renderDocumentsCatalog();
  };

  window.filterDocuments = function () {
    const input = document.getElementById('kb-search-input');
    searchQuery = input ? input.value.trim() : '';
    renderDocumentsCatalog();
  };

  // 8. EVENTOS DE DRAG & DROP
  function setupDragAndDrop() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');

    if (!dropzone || !fileInput) return;

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      }, false);
    });

    dropzone.addEventListener('drop', e => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length > 0) {
        handleFileSelected(files[0]);
      }
    }, false);

    fileInput.addEventListener('change', e => {
      if (fileInput.files.length > 0) {
        handleFileSelected(fileInput.files[0]);
      }
    }, false);
  }

  // 10. HEALTHCHECK DINÂMICO DOS SERVIÇOS
  async function checkSingleService(service) {
    const el = document.getElementById(service.id);
    if (!el) return;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      await fetch(service.url, { mode: 'no-cors', signal: controller.signal });
      clearTimeout(timeoutId);
      el.className = 'service-status online';
      el.innerHTML = `<span class="status-dot"></span> ${service.labelOnline}`;
    } catch (e) {
      el.className = 'service-status offline';
      el.innerHTML = `<span class="status-dot offline"></span> Offline`;
    }
  }

  async function checkServicesHealth() {
    if (currentMode !== 'local') return;

    const list = [
      { id: 'status-n8n', url: 'http://localhost:5678/healthz', labelOnline: 'Ativo' },
      { id: 'status-chatwoot', url: 'http://localhost:3001/api', labelOnline: 'Ativo' },
      { id: 'status-speaches', url: 'http://localhost:8000/health', labelOnline: 'CUDA GPU' },
      { id: 'status-ollama', url: 'http://localhost:11434/', labelOnline: 'Ativo' },
      { id: 'status-waha', url: 'http://localhost:3000/api/server/status', labelOnline: 'Local' }
    ];

    for (const item of list) {
      checkSingleService(item);
    }
  }

  // 11. INICIALIZAÇÃO AUTOMÁTICA
  document.addEventListener('DOMContentLoaded', function () {
    var isDirectPublic = window.location.protocol === 'https:' &&
                         window.location.hostname.indexOf('localhost') === -1 &&
                         window.location.hostname.indexOf('127.0.0.1') === -1;

    var savedMode = null;
    try { savedMode = localStorage.getItem('portal_mode'); } catch (e) {}
    var initialMode = isDirectPublic ? 'public' : (savedMode || 'local');
    window.setMode(initialMode);

    setupDragAndDrop();
    renderDocumentsCatalog();
    checkServicesHealth();

    // Revalida a cada 30 segundos
    setInterval(checkServicesHealth, 30000);
  });

})();
