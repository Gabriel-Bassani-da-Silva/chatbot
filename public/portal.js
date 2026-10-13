// Portal do Assistente - Lógica de Alternância Local / Público

(function () {
  var rawDomain = document.body.getAttribute('data-domain') || '';
  var fallbackDomain = 'fatecn8nabc.dpdns.org';
  // Se não foi renderizado pelo Caddy (ex: aberto via file://), usa o fallback
  var domain = (rawDomain && rawDomain.indexOf('{{') === -1) ? rawDomain : fallbackDomain;

  window.setMode = function (mode) {
    var tabLocal = document.getElementById('tab-local');
    var tabPublic = document.getElementById('tab-public');
    var btnN8n = document.getElementById('btn-n8n');
    var btnChatwoot = document.getElementById('btn-chatwoot');
    var btnWaha = document.getElementById('btn-waha');
    var wahaNotice = document.getElementById('waha-notice');
    var envLabel = document.getElementById('env-label');
    var badge = document.getElementById('env-badge');

    if (mode === 'public') {
      if (tabLocal) tabLocal.classList.remove('active');
      if (tabPublic) tabPublic.classList.add('active');
      if (btnN8n) btnN8n.href = 'https://n8n.' + domain;
      if (btnChatwoot) btnChatwoot.href = 'https://chatwoot.' + domain;
      if (btnWaha) btnWaha.style.display = 'none';
      if (wahaNotice) wahaNotice.style.display = 'flex';
      if (envLabel) envLabel.textContent = 'Público: ' + domain;
      if (badge) badge.classList.add('public');
      try { localStorage.setItem('portal_mode', 'public'); } catch (e) {}
    } else {
      if (tabPublic) tabPublic.classList.remove('active');
      if (tabLocal) tabLocal.classList.add('active');
      if (btnN8n) btnN8n.href = 'http://localhost:5678';
      if (btnChatwoot) btnChatwoot.href = 'http://localhost:3001';
      if (btnWaha) btnWaha.style.display = 'flex';
      if (wahaNotice) wahaNotice.style.display = 'none';
      if (envLabel) envLabel.textContent = 'Portas Locais (Docker)';
      if (badge) badge.classList.remove('public');
      try { localStorage.setItem('portal_mode', 'local'); } catch (e) {}
    }
  };

  // Inicialização automática:
  var isDirectPublic = window.location.protocol === 'https:' &&
                       window.location.hostname.indexOf('localhost') === -1 &&
                       window.location.hostname.indexOf('127.0.0.1') === -1;

  var savedMode = null;
  try { savedMode = localStorage.getItem('portal_mode'); } catch (e) {}
  var initialMode = isDirectPublic ? 'public' : (savedMode || 'local');
  window.setMode(initialMode);
})();
