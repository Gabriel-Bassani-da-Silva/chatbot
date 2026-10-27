import json

path = 'workflows/Agente RAG Fatec.json'
with open(path, 'r', encoding='utf-8') as f:
    wf = json.load(f)

for node in wf['nodes']:
    # 1. Remove contact restriction in 'Validar evento, mensagem e atendimento humano'
    if node['name'] == 'Validar evento, mensagem e atendimento humano':
        val_code = r"""/** Validação de produção do RAG: aceita mensagens diretas de qualquer contato. */
const acceptedItems = [];
for (const item of $input.all()) {
  const root = item.json ?? {};
  const payload = root.body ?? root;
  const message = payload.message && typeof payload.message === 'object' ? payload.message : payload;
  const conversation = payload.conversation ?? message.conversation ?? {};
  const event = String(payload.event ?? '');
  const rawType = message.message_type ?? payload.message_type;
  const isIncoming = rawType === 'incoming' || rawType === 0 || rawType === '0';
  const privateValue = message.private ?? payload.private;
  const isPublic = privateValue === false || privateValue === 0 || String(privateValue).trim().toLowerCase() === 'false';
  const senderAttributes = conversation.meta?.sender?.custom_attributes ?? payload.sender?.custom_attributes ?? {};
  const chatId = String(senderAttributes.waha_whatsapp_chat_id ?? '').trim().toLowerCase();
  const isGroupChat = chatId.endsWith('@g.us');
  const conversationId = String(conversation.id ?? payload.conversation_id ?? '');
  const messageId = String(message.id ?? payload.id ?? '');
  const hasMessageIdentity = Boolean(conversationId && messageId);

  // Sem restrição de contato: aceita qualquer conversa/contato (apenas ignora grupos de WhatsApp se houver @g.us)
  const channelAllowed = !isGroupChat;

  if (event === 'message_created' && isIncoming && isPublic && channelAllowed && hasMessageIdentity) {
    acceptedItems.push(item);
  }
}
return acceptedItems;"""
        node['parameters']['jsCode'] = val_code
        print('Updated Validar evento, mensagem e atendimento humano: REMOVED ALL CONTACT RESTRICTIONS!')

    # 2. Fix Classificar comando code
    elif node['name'] == 'Classificar comando':
        classif_code = r"""const prev = $('Liberar conteúdo textual para o agente').item.json ?? {};
const text = String($json.contentText ?? prev.contentText ?? '').trim();
const conversationId = String($json.conversationId ?? prev.conversationId ?? '').trim();
const messageId = String($json.messageId ?? prev.messageId ?? Date.now());
const now = Date.now();

let stored = null;
try {
  const raw = $json.appMode;
  stored = typeof raw === 'string' ? JSON.parse(raw) : (raw && typeof raw === 'object' ? raw : null);
} catch { stored = null; }

// Sessão ativa no Redis por até 15 minutos iniciada por comando prévio
const validStored = stored && ['agenda', 'cardapio'].includes(stored.app) && typeof stored.sessionKey === 'string' && Number.isFinite(Number(stored.updatedAt)) && (now - Number(stored.updatedAt) >= 0) && (now - Number(stored.updatedAt) <= 15 * 60 * 1000);

const normText = text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9/]+/g, ' ').trim();

// Comandos explícitos de modo
const isCardapioCommand = /^\/cardapio(?:\s|$)/i.test(text) || /^\/menu(?:\s|$)/i.test(text) || /^(cardapio|menu)$/i.test(normText);
const isAgendaCommand = /^\/agenda(?:\s|$)/i.test(text) || /^(agenda|agendamento)$/i.test(normText);
const isCancelCommand = /^\/cancelar(?:\s|$)/i.test(text) || /^(cancelar|parar)$/i.test(normText);
const isFatecCommand = /^\/fatec(?:\s|$)/i.test(text) || /^(fatec|sair|voltar)$/i.test(normText) || /\b(?:atendimento fatec|voltar pra fatec|voltar para fatec|falar com a fatec|secretaria|vestibular|matricula|fatec bebedouro)\b/i.test(normText);

let route = 'rag';
let appSessionKey = null;
let appModeValue = null;
let routedText = text;
const writeMode = (app, sessionKey) => JSON.stringify({ app, sessionKey, updatedAt: now });

if (isCancelCommand) {
  route = 'cancel';
} else if (isFatecCommand) {
  route = 'rag';
  routedText = text.replace(/^\/fatec\s*/i, '').trim() || 'Olá';
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
        node['parameters']['jsCode'] = classif_code
        print('Updated Classificar comando: Restored clean syntax!')

with open(path, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write('\n')

print('Agente RAG Fatec.json successfully updated!')
