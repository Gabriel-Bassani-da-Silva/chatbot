import json

wf_path = 'workflows/Agente RAG Fatec.json'
with open(wf_path, 'r', encoding='utf-8') as f:
    wf = json.load(f)

classificar_code = """const prev = $('Liberar conteúdo textual para o agente').item.json ?? {};
const text = String($json.contentText ?? prev.contentText ?? '').trim();
const conversationId = String($json.conversationId ?? prev.conversationId ?? '').trim();
const messageId = String($json.messageId ?? prev.messageId ?? Date.now());
const now = Date.now();

let stored = null;
try {
  const raw = $json.appMode;
  stored = typeof raw === 'string' ? JSON.parse(raw) : (raw && typeof raw === 'object' ? raw : null);
} catch { stored = null; }

// Sessão ativa no Redis por até 2 horas (120 minutos) iniciada por comando prévio
const validStored = stored && ['agenda', 'cardapio'].includes(stored.app) && typeof stored.sessionKey === 'string' && Number.isFinite(Number(stored.updatedAt)) && (now - Number(stored.updatedAt) >= 0) && (now - Number(stored.updatedAt) <= 120 * 60 * 1000);

const normText = text.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase().replace(/[^a-z0-9/]+/g, ' ').trim();

// Comandos explícitos de modo
const isCardapioCommand = /^\\/cardapio(?:\\s|$)/i.test(text) || /^\\/menu(?:\\s|$)/i.test(text) || /^(cardapio|menu)$/i.test(normText);
const isAgendaCommand = /^\\/agenda(?:\\s|$)/i.test(text) || /^(agenda|agendamento)$/i.test(normText);
const isCancelCommand = /^\\/cancelar(?:\\s|$)/i.test(text) || /^(cancelar|parar)$/i.test(normText);
const isFatecCommand = /^\\/fatec(?:\\s|$)/i.test(text) || /^(fatec|sair|voltar)$/i.test(normText);

let route = 'rag';
let appSessionKey = null;
let appModeValue = null;
let routedText = text;
const writeMode = (app, sessionKey) => JSON.stringify({ app, sessionKey, updatedAt: now });

if (isCancelCommand) {
  route = 'cancel';
} else if (isFatecCommand) {
  route = 'rag';
  routedText = text.replace(/^\\/fatec\\s*/i, '').trim() || 'Olá';
} else if (isCardapioCommand) {
  // Comando explícito: ZERA o contexto e inicia nova sessão de cardápio
  route = 'cardapio';
  appSessionKey = 'cardapio:' + conversationId + ':' + now;
  appModeValue = writeMode('cardapio', appSessionKey);
} else if (isAgendaCommand) {
  // Comando explícito: ZERA o contexto e inicia nova sessão de agenda
  route = 'agenda';
  appSessionKey = 'agenda:' + conversationId + ':' + now;
  appModeValue = writeMode('agenda', appSessionKey);
} else if (validStored) {
  // Continuidade no modo ativo já iniciado por comando
  route = stored.app;
  appSessionKey = stored.sessionKey;
  appModeValue = writeMode(stored.app, stored.sessionKey);
} else {
  // Sem comando digitado e sem modo ativo prévio: segue diretamente para o atendimento da Fatec (RAG)
  route = 'rag';
}

return {
  json: {
    ...prev,
    ...$json,
    contentText: routedText,
    route,
    appSessionKey,
    appModeValue
  }
};"""

for n in wf['nodes']:
    if n['name'] == 'Classificar comando':
        n['parameters']['jsCode'] = classificar_code
        print("Updated Classificar comando: default to Fatec when no command is typed.")

with open(wf_path, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

print("Saved Agente RAG Fatec.json successfully.")
