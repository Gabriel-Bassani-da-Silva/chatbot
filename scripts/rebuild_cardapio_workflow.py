import json
import os

wf_path = 'workflows/subworkflows/Comando _cardapio — Google Sheets.json'
with open(wf_path, 'r', encoding='utf-8') as f:
    wf = json.load(f)

# Keep the non-AI nodes
kept_node_names = [
    'Entrada do workflow principal',
    'Redis — ler confirmação',
    'Interpretar /cardapio',
    'Precisa confirmar?',
    'Redis — salvar confirmação',
    'Responder resumo do pedido',
    'Pedido confirmado?',
    'Sheets — registrar pedido',
    'Redis — limpar após pedido',
    'Resposta de pedido registrado',
    'Redis — limpar após falha',
    'Resposta de falha de gravação',
    'Redis — limpar solicitação inválida',
    'Responder instrução do cardápio',
    'Redis — encerrar modo Cardápio'
]

nodes_dict = {n['name']: n for n in wf['nodes'] if n['name'] in kept_node_names}

# 1. New "Preparar contexto /cardapio"
prep_node = {
    "parameters": {
        "mode": "runOnceForEachItem",
        "jsCode": """const original = $('Entrada do workflow principal').item.json ?? {};
const text = String(original.contentText ?? '').trim();
const sessionKey = String(original.appSessionKey ?? '');

let oldState = null;
try {
  let val = $('Redis — ler confirmação').item.json.pendingState;
  if (typeof val === 'string') { try { val = JSON.parse(val); } catch {} }
  if (typeof val === 'string') { try { val = JSON.parse(val); } catch {} }
  oldState = (val && typeof val === 'object') ? val : null;
} catch {}

const norm = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
const normText = norm(text);
const asksMenu = /^\\/cardapio(?:\\s|$)/i.test(text) || /\\b(?:mostra|mostrar|ver|quero ver|me envie|envie)\\b.{0,24}\\b(?:cardapio|menu)\\b/i.test(normText) || /^(menu|cardapio)$/i.test(normText) || /\\b(preco|precos|quanto custa|valor)\\b/i.test(normText);
const isCancel = /^\\/cancelar$/i.test(text);
const affirmative = /^(sim|confirmo|isso mesmo|pode fechar|pode confirmar|esta certo|tudo certo|correto|confirmado)$/.test(normText);
const sameSession = Boolean(oldState && oldState.sessionKey === sessionKey);
const stateAge = oldState ? Date.now() - Number(oldState.summaryAt ?? 0) : Number.POSITIVE_INFINITY;
const isConfirm = affirmative && sameSession && oldState?.summaryAt > 0 && stateAge >= 0 && stateAge <= 15 * 60 * 1000;

const skipLLM = asksMenu || isCancel || isConfirm;

const systemPrompt = `Você atende somente o aplicativo independente Cardápio demonstrativo de uma lanchonete fictícia para um projeto de TCC da Fatec Bebedouro. Responda em português brasileiro.

MENU E PREÇOS FIXOS:
Hambúrgueres avulsos: B1 Clássico R$ 19,90; B2 Cheeseburger R$ 22,90; B3 Duplo R$ 29,90; B4 Frango Crocante R$ 24,90.
Combos (1 sanduíche + 1 batata pequena + 1 bebida): C1 Combo Clássico R$ 31,90; C2 Combo Cheeseburger R$ 34,90; C3 Combo Duplo R$ 41,90; C4 Combo Frango R$ 36,90. Cada combo exige escolher uma bebida: D1 Cola, D2 Cola Zero, D3 Guaraná, D4 Água, D5 Suco de laranja, sem custo adicional. Trocar batata pequena por grande custa +R$ 5,00 por combo.
Acompanhamentos: A1 batata pequena R$ 9,90; A2 batata grande R$ 14,90; A3 anéis de cebola R$ 12,90.
Bebidas avulsas: D1 Cola R$ 6,00; D2 Cola Zero R$ 6,00; D3 Guaraná R$ 6,00; D4 Água R$ 4,00; D5 Suco de laranja R$ 8,00.
Ingredientes removíveis: B1: carne, alface, tomate, cebola, picles, molho da casa. B2 e B3: carne, queijo, alface, tomate, cebola, picles, molho da casa. B4: frango, queijo, alface, tomate, maionese. Remoções como sem cebola e sem picles são gratuitas. Extras somente em hambúrgueres e combos: queijo +R$ 3,00, bacon +R$ 4,00, carne +R$ 7,00, por unidade.

COLETA DE DADOS DO PEDIDO:
1. Monte o carrinho com os códigos, quantidades, bebidas de combos e adicionais/remoções solicitados.
2. NOME DO CLIENTE: Peça o nome da pessoa se ela ainda não informou. NUNCA invente um nome, NUNCA use palavras como "nenhuma", "sim", "não" ou números como nome. Se não foi informado um nome real de pessoa, retorne null no campo nome.
3. FORMA DE PAGAMENTO: Peça a forma de pagamento (Pix, Cartão de Crédito, Cartão de Débito ou Dinheiro). Se não foi informada, retorne null.
4. OBSERVAÇÕES: Pergunte se há alguma observação para a cozinha (ou se é "nenhuma").

IMPORTANTE: Retorne EXCLUSIVAMENTE um objeto JSON no seguinte formato:
{
  "cliente": {
    "nome": string ou null,
    "forma_pagamento": string ou null,
    "observacoes": string ou null
  },
  "itens_carrinho": [
    {
      "codigo": "B1" | "B2" | "B3" | "B4" | "C1" | "C2" | "C3" | "C4" | "A1" | "A2" | "A3" | "D1" | "D2" | "D3" | "D4" | "D5",
      "quantidade": integer entre 1 e 20,
      "bebida_combo": string ou null,
      "troca_batata_grande": boolean,
      "adicionais": ["queijo", "bacon", "carne"],
      "remocoes": [string]
    }
  ],
  "resposta_bot": string
}`;

return {
  json: {
    ...original,
    skipLLM,
    systemPrompt,
    userText: text
  }
};"""
    },
    "id": "c1f7a012-9b24-4e2b-8a10-7e12f00a0001",
    "name": "Preparar contexto /cardapio",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [608, 0]
}

# 2. New "Precisa chamar IA?"
if_node = {
    "parameters": {
        "conditions": {
            "options": {
                "caseSensitive": True,
                "leftValue": "",
                "typeValidation": "strict",
                "version": 1
            },
            "conditions": [
                {
                    "leftValue": "={{ $json.skipLLM }}",
                    "operator": {
                        "type": "boolean",
                        "operation": "true"
                    }
                }
            ],
            "combinator": "and"
        },
        "options": {}
    },
    "id": "c1f7a012-9b24-4e2b-8a10-7e12f00a0002",
    "name": "Comando direto?",
    "type": "n8n-nodes-base.if",
    "typeVersion": 2.3,
    "position": [840, 0]
}

# 3. New "Ollama — Interpretar Pedido"
ollama_http_node = {
    "parameters": {
        "method": "POST",
        "url": "http://host.docker.internal:11434/api/chat",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={\n  \"model\": \"qwen3:4b\",\n  \"format\": \"json\",\n  \"stream\": false,\n  \"messages\": [\n    {\n      \"role\": \"system\",\n      \"content\": {{ JSON.stringify($json.systemPrompt) }}\n    },\n    {\n      \"role\": \"user\",\n      \"content\": {{ JSON.stringify($json.userText) }}\n    }\n  ],\n  \"options\": {\n    \"temperature\": 0.1,\n    \"num_ctx\": 4096\n  }\n}",
        "options": {
            "timeout": 45000
        }
    },
    "id": "c1f7a012-9b24-4e2b-8a10-7e12f00a0003",
    "name": "Ollama — Interpretar Pedido",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.2,
    "position": [1060, 160]
}

# 4. Updated "Interpretar /cardapio"
interpret_code = r"""const original = $('Entrada do workflow principal').item.json ?? {};
const text = String(original.contentText ?? '').trim();
let raw = $json.message ? $json.message.content : ($json.output ?? $json);
if (typeof raw === 'string') { try { raw = JSON.parse(raw); } catch { raw = {}; } }
if (raw && raw.output && typeof raw.output === 'object') { raw = raw.output; }
const parsed = raw && typeof raw === 'object' ? raw : {};
const customer = parsed.cliente && typeof parsed.cliente === 'object' ? parsed.cliente : {};

const sessionKey = String(original.appSessionKey ?? '');
let oldState = null;
try {
  let value = $('Redis — ler confirmação').item.json.pendingState;
  if (typeof value === 'string') { try { value = JSON.parse(value); } catch {} }
  if (typeof value === 'string') { try { value = JSON.parse(value); } catch {} }
  oldState = (value && typeof value === 'object') ? value : null;
} catch { oldState = null; }

const stateAge = oldState ? Date.now() - Number(oldState.summaryAt ?? 0) : Number.POSITIVE_INFINITY;
const sameSession = Boolean(oldState && oldState.sessionKey === sessionKey);
const norm = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
const affirmative = /^(sim|confirmo|isso mesmo|pode fechar|pode confirmar|esta certo|tudo certo|correto|confirmado)$/.test(norm(text));
const money = cents => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100);

function result(action, output, extra = {}) {
  return { json: { ...original, action, output, ...extra } };
}

function pending(output, summaryAt = 0, stateData = {}) {
  const mergedState = {
    ...(oldState && sameSession ? oldState : {}),
    sessionKey,
    summaryAt,
    ...stateData
  };
  return result('pending', output, { pendingState: JSON.stringify(mergedState) });
}

// 1. Contato: extraído automaticamente do número de WhatsApp do remetente
let contato = null;
const rawPhone = original.phone_number ||
  original.sender?.phone_number ||
  original.conversation?.meta?.sender?.phone_number ||
  original.conversation?.meta?.sender?.custom_attributes?.waha_whatsapp_jid ||
  original.sender?.custom_attributes?.waha_whatsapp_jid ||
  original.senderAttributes?.waha_whatsapp_chat_id ||
  original.chatId ||
  '';

const digits = String(rawPhone).replace(/\D/g, '');
if (digits.length >= 10) {
  if (digits.startsWith('55') && digits.length >= 12) {
    const ddd = digits.slice(2, 4);
    const num = digits.slice(4);
    contato = `+55 (${ddd}) ${num.length === 9 ? num.slice(0, 5) + '-' + num.slice(5) : num.slice(0, 4) + '-' + num.slice(4)}`;
  } else {
    contato = '+' + digits;
  }
} else if (original.conversationId) {
  contato = 'WhatsApp #' + original.conversationId;
} else {
  contato = 'WhatsApp do remetente';
}

// 2. Validação estrita do Nome do Cliente
function isValidCustomerName(val) {
  if (!val || typeof val !== 'string') return false;
  const s = val.trim();
  if (s.length < 2 || s.length > 80) return false;
  const lower = s.toLowerCase();
  if (['nenhuma', 'nenhum', 'nao', 'não', 'null', 'undefined', 'sim', 'ok', 'nada', 'cliente', 'teste'].includes(lower)) return false;
  if (/^[\d\s+\-().]+$/.test(s)) return false;
  if (/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u.test(s)) return false;
  if (!/[a-zA-ZÀ-ÿ]{2,}/.test(s)) return false;
  const badWords = ['porra', 'caralho', 'puta', 'merda', 'viado', 'fdp', 'cu'];
  for (const bw of badWords) {
    if (new RegExp('\\b' + bw + '\\b', 'i').test(s)) return false;
  }
  return true;
}

let nome = null;
if (isValidCustomerName(customer.nome)) {
  nome = customer.nome.trim();
} else if (sameSession && isValidCustomerName(oldState?.nome)) {
  nome = oldState.nome;
}

// 3. Validação e Normalização da Forma de Pagamento
function parsePaymentMethod(val) {
  if (!val || typeof val !== 'string') return null;
  const normVal = norm(val);
  if (/pix/.test(normVal)) return 'Pix';
  if (/credito/.test(normVal)) return 'Cartão de Crédito';
  if (/debito/.test(normVal)) return 'Cartão de Débito';
  if (/cartao/.test(normVal)) return 'Cartão';
  if (/dinheiro/.test(normVal)) return 'Dinheiro';
  return null;
}

let forma_pagamento = parsePaymentMethod(customer.forma_pagamento) ||
  parsePaymentMethod(text) ||
  (sameSession ? oldState?.forma_pagamento : null) ||
  null;

// 4. Observações (padrão 'Nenhuma' se não informado para agilizar o fluxo)
let observacoes = 'Nenhuma';
if (customer.observacoes !== undefined && customer.observacoes !== null) {
  const obsClean = String(customer.observacoes).trim();
  observacoes = (norm(obsClean) === 'nenhuma' || norm(obsClean) === 'nenhum' || norm(obsClean) === 'nao') ? 'Nenhuma' : obsClean;
} else if (sameSession && oldState?.observacoes !== undefined) {
  observacoes = oldState.observacoes;
}

// Texto do Menu com Introdução do TCC
const menuText = [
  '🎓 *Demonstração Acadêmica — TCC Fatec Bebedouro*',
  '_Assistente Conversacional com IA Generativa e Automação n8n_',
  '',
  '🍔 *CARDÁPIO DEMONSTRATIVO — Lanchonete Exemplo* 🍟',
  '',
  '🥪 *HAMBÚRGUERES AVULSOS*',
  '• *B1* Clássico — R$ 19,90',
  '• *B2* Cheeseburger — R$ 22,90',
  '• *B3* Duplo — R$ 29,90',
  '• *B4* Frango Crocante — R$ 24,90',
  '',
  '🍟 *COMBOS* _(sanduíche + batata pequena + bebida)_',
  '• *C1* Combo Clássico — R$ 31,90',
  '• *C2* Combo Cheeseburger — R$ 34,90',
  '• *C3* Combo Duplo — R$ 41,90',
  '• *C4* Combo Frango — R$ 36,90',
  '_Opções de bebida do combo:_ D1 Cola, D2 Cola Zero, D3 Guaraná, D4 Água ou D5 Suco de laranja.',
  '_Troca para batata grande:_ +R$ 5,00',
  '',
  '🍟 *ACOMPANHAMENTOS*',
  '• *A1* Batata pequena — R$ 9,90',
  '• *A2* Batata grande — R$ 14,90',
  '• *A3* Anéis de cebola — R$ 12,90',
  '',
  '🥤 *BEBIDAS AVULSAS*',
  '• *D1* Cola — R$ 6,00',
  '• *D2* Cola Zero — R$ 6,00',
  '• *D3* Guaraná — R$ 6,00',
  '• *D4* Água Mineral — R$ 4,00',
  '• *D5* Suco de Laranja — R$ 8,00',
  '',
  '⚙️ *PERSONALIZAÇÕES*',
  '• *Remoções gratuitas:* sem cebola, sem picles, etc.',
  '• *Extras (hambúrgueres/combos):*',
  '  - Queijo extra: +R$ 3,00',
  '  - Bacon extra: +R$ 4,00',
  '  - Carne extra: +R$ 7,00',
  '',
  '💡 *Como pedir:*',
  'Basta enviar o que deseja pedir (ex: _"Quero 1 C1 com Cola Zero e batata grande"_).',
  '_Nota: Ambiente de demonstração acadêmica (Fatec Bebedouro). Preços fictícios, sem cobrança real._'
].join('\n');

const asksMenu = /^\/cardapio(?:\s|$)/i.test(text) || /\b(?:mostra|mostrar|ver|quero ver|me envie|envie)\b.{0,24}\b(?:cardapio|menu)\b/i.test(norm(text)) || /^(menu|cardapio)$/i.test(norm(text));
if (/^\/cancelar$/i.test(text)) return pending('Carrinho demonstrativo cancelado. Nenhum pedido foi registrado.', 0);
if (asksMenu) return pending(menuText, 0);
if (/\b(preco|precos|quanto custa|valor)\b/i.test(norm(text))) return pending(menuText, 0);

// Se já temos um resumo pendente no estado anterior e o usuário confirmou com "sim":
if (affirmative && sameSession && oldState?.summaryAt > 0 && stateAge >= 0 && stateAge <= 15 * 60 * 1000) {
  const digits = value => String(value).replace(/\D/g, '');
  const finalNome = oldState.nome || nome || 'Cliente';
  const finalContato = oldState.contato || contato;
  const finalPagamento = oldState.forma_pagamento || forma_pagamento || 'Demonstrativo';
  return result('sheet', '', {
    nome: finalNome,
    contato: finalContato,
    forma_pagamento: finalPagamento,
    observacoes: `Pagamento: ${finalPagamento} | Obs: ${oldState.observacoes || observacoes || 'Nenhuma'}`,
    itens: oldState.summaryItems || 'Itens demonstrativos',
    pedido_id: 'cw-' + digits(original.conversationId) + '-' + digits(original.messageId),
    criado_em: new Date().toISOString(),
    status: 'novo',
    total: oldState.totalCents ? oldState.totalCents / 100 : 0
  });
}

// Processa itens do carrinho (preserva itens da sessão anterior se a mensagem atual não enviou itens)
const rawItems = (Array.isArray(parsed.itens_carrinho) && parsed.itens_carrinho.length > 0)
  ? parsed.itens_carrinho
  : (sameSession && Array.isArray(oldState?.rawItems) ? oldState.rawItems : []);

const MENU = {
  B1: { name: 'Clássico', cents: 1990, ingredients: ['carne','alface','tomate','cebola','picles','molho da casa'], kind: 'burger' },
  B2: { name: 'Cheeseburger', cents: 2290, ingredients: ['carne','queijo','alface','tomate','cebola','picles','molho da casa'], kind: 'burger' },
  B3: { name: 'Duplo', cents: 2990, ingredients: ['carne','queijo','alface','tomate','cebola','picles','molho da casa'], kind: 'burger' },
  B4: { name: 'Frango Crocante', cents: 2490, ingredients: ['frango','queijo','alface','tomate','maionese'], kind: 'burger' },
  C1: { name: 'Combo Clássico', cents: 3190, base: 'B1', kind: 'combo' },
  C2: { name: 'Combo Cheeseburger', cents: 3490, base: 'B2', kind: 'combo' },
  C3: { name: 'Combo Duplo', cents: 4190, base: 'B3', kind: 'combo' },
  C4: { name: 'Combo Frango', cents: 3690, base: 'B4', kind: 'combo' },
  A1: { name: 'Batata pequena', cents: 990, kind: 'side' },
  A2: { name: 'Batata grande', cents: 1490, kind: 'side' },
  A3: { name: 'Anéis de cebola', cents: 1290, kind: 'side' },
  D1: { name: 'Cola', cents: 600, kind: 'drink' },
  D2: { name: 'Cola Zero', cents: 600, kind: 'drink' },
  D3: { name: 'Guaraná', cents: 600, kind: 'drink' },
  D4: { name: 'Água Mineral', cents: 400, kind: 'drink' },
  D5: { name: 'Suco de Laranja', cents: 800, kind: 'drink' }
};
const EXTRA_CENTS = { queijo: 300, bacon: 400, carne: 700 };
const drinkAliases = { d1:'D1', cola:'D1', 'refrigerante cola':'D1', d2:'D2', 'cola zero':'D2', 'refrigerante cola zero':'D2', d3:'D3', guarana:'D3', d4:'D4', agua:'D4', 'agua mineral':'D4', d5:'D5', suco:'D5', 'suco de laranja':'D5' };
const aliasIngredient = { 'cebola roxa':'cebola', 'pepino em conserva':'picles', 'molho especial':'molho da casa', 'molho':'molho da casa' };
const errors = [];
const lines = [];
let totalCents = 0;

if (rawItems.length > 30) errors.push('O carrinho pode ter no máximo 30 linhas de itens.');
for (const item of rawItems.slice(0, 30)) {
  const sku = String(item?.codigo ?? '').trim().toUpperCase();
  const product = MENU[sku];
  if (!product) { errors.push('Há um produto não reconhecido no carrinho. Consulte /cardapio e escolha um item do menu.'); continue; }
  const quantity = Number(item.quantidade);
  if (!Number.isInteger(quantity) || quantity < 1 || quantity > 20) { errors.push('A quantidade de cada item deve ser um número inteiro entre 1 e 20.'); continue; }
  const base = product.base ? MENU[product.base] : product;
  const extraRaw = Array.isArray(item.adicionais) ? item.adicionais : [];
  const extras = [...new Set(extraRaw.map(value => norm(value)).filter(Boolean))];
  let bad = false;
  for (const extra of extras) {
    if (!Object.prototype.hasOwnProperty.call(EXTRA_CENTS, extra)) { errors.push('Extra não permitido. Escolha queijo, bacon ou carne.'); bad = true; }
    if (!['burger','combo'].includes(product.kind)) { errors.push('Extras só podem ser adicionados a hambúrgueres ou combos.'); bad = true; }
  }
  const removedRaw = Array.isArray(item.remocoes) ? item.remocoes : [];
  const removed = [...new Set(removedRaw.map(value => norm(value).replace(/^sem /, '')).map(value => aliasIngredient[value] || value).filter(Boolean))];
  for (const ingredient of removed) {
    if (!base.ingredients || !base.ingredients.includes(ingredient)) { errors.push('Uma remoção não corresponde a ingrediente do produto selecionado.'); bad = true; }
  }
  const large = item.troca_batata_grande === true;
  if (large && product.kind !== 'combo') { errors.push('A troca para batata grande só se aplica a combos.'); bad = true; }
  let drinkSku = null;
  if (product.kind === 'combo') {
    const drink = norm(item.bebida_combo);
    drinkSku = drinkAliases[drink] || null;
    if (!drinkSku) { errors.push('Escolha a bebida obrigatória para cada combo: D1 Cola, D2 Cola Zero, D3 Guaraná, D4 Água ou D5 Suco de laranja.'); bad = true; }
  } else if (item.bebida_combo) {
    errors.push('A bebida escolhida para um combo foi associada a um item que não é combo.'); bad = true;
  }
  if (bad) continue;
  let unitCents = product.cents + extras.reduce((sum, key) => sum + EXTRA_CENTS[key], 0) + (large ? 500 : 0);
  const lineCents = unitCents * quantity;
  totalCents += lineCents;
  const details = [];
  if (drinkSku) details.push('bebida: ' + MENU[drinkSku].name);
  if (large) details.push('batata grande (+R$ 5,00)');
  if (extras.length) details.push('extras: ' + extras.join(', '));
  if (removed.length) details.push('sem ' + removed.join(', '));
  lines.push('• ' + quantity + 'x *' + sku + '* ' + product.name + (details.length ? ' _(' + details.join('; ') + ')_' : '') + ' — ' + money(lineCents));
}

if (errors.length) {
  return pending('⚠️ *Atenção aos itens do carrinho:*\n• ' + [...new Set(errors)].join('\n• ') + '\n\nO pedido ainda não foi registrado. Corrija o carrinho ou consulte */cardapio* para rever o menu.', 0, { nome, contato, forma_pagamento, observacoes, rawItems });
}

if (!lines.length) {
  const answer = typeof parsed.resposta_bot === 'string' ? parsed.resposta_bot.trim() : '';
  return pending(answer || 'O que você gostaria de pedir? Envie */cardapio* para ver os produtos e preços demonstrativos.', 0, { nome, contato, forma_pagamento, observacoes });
}

// Validação dos dados obrigatórios: Nome e Forma de Pagamento
if (!nome || !forma_pagamento) {
  const missing = [];
  if (!nome) missing.push('o *seu nome*');
  if (!forma_pagamento) missing.push('a *forma de pagamento* (Pix, Cartão de Crédito, Cartão de Débito ou Dinheiro)');
  return pending('🛒 *Itens no seu carrinho:*\n' + lines.join('\n') + '\n\nPara continuar o pedido demonstrativo, por favor informe ' + missing.join(' e ') + '.', 0, { nome, contato, forma_pagamento, observacoes, rawItems, totalCents });
}

const summaryItems = lines.join('\n');
const totalText = money(totalCents);
const fullSummary = '📋 *Resumo do Pedido Demonstrativo*\n\n' +
  '👤 *Cliente:* ' + nome + '\n' +
  '📞 *Contato:* ' + contato + '\n' +
  '💳 *Pagamento:* ' + forma_pagamento + '\n\n' +
  '🛒 *Itens:*\n' + summaryItems + '\n\n' +
  '📝 *Observações:* ' + (observacoes || 'Nenhuma') + '\n' +
  '💰 *TOTAL:* *' + totalText + '*\n\n' +
  'Está tudo certo para registrar na planilha? Responda *“sim”* para confirmar ou *“não”* para alterar/cancelar.\n' +
  '_Demonstração acadêmica de TCC — nenhum pagamento real será cobrado._';

return pending(fullSummary, Date.now(), {
  nome,
  contato,
  forma_pagamento,
  observacoes: observacoes || 'Nenhuma',
  summaryItems,
  totalCents,
  totalText,
  rawItems
});"""

nodes_dict['Interpretar /cardapio']['parameters']['jsCode'] = interpret_code
nodes_dict['Interpretar /cardapio']['position'] = [1300, 0]

all_nodes = [
    nodes_dict['Entrada do workflow principal'],
    nodes_dict['Redis — ler confirmação'],
    prep_node,
    if_node,
    ollama_http_node,
    nodes_dict['Interpretar /cardapio'],
    nodes_dict['Precisa confirmar?'],
    nodes_dict['Redis — salvar confirmação'],
    nodes_dict['Responder resumo do pedido'],
    nodes_dict['Pedido confirmado?'],
    nodes_dict['Sheets — registrar pedido'],
    nodes_dict['Redis — limpar após pedido'],
    nodes_dict['Redis — encerrar modo Cardápio'],
    nodes_dict['Resposta de pedido registrado'],
    nodes_dict['Redis — limpar após falha'],
    nodes_dict['Resposta de falha de gravação'],
    nodes_dict['Redis — limpar solicitação inválida'],
    nodes_dict['Responder instrução do cardápio']
]

# Update connections
new_connections = {
    "Entrada do workflow principal": {
        "main": [
            [{"node": "Redis — ler confirmação", "type": "main", "index": 0}]
        ]
    },
    "Redis — ler confirmação": {
        "main": [
            [{"node": "Preparar contexto /cardapio", "type": "main", "index": 0}]
        ]
    },
    "Preparar contexto /cardapio": {
        "main": [
            [{"node": "Comando direto?", "type": "main", "index": 0}]
        ]
    },
    "Comando direto?": {
        "main": [
            # True output (index 0) -> direct to Interpretar /cardapio
            [{"node": "Interpretar /cardapio", "type": "main", "index": 0}],
            # False output (index 1) -> call Ollama
            [{"node": "Ollama — Interpretar Pedido", "type": "main", "index": 0}]
        ]
    },
    "Ollama — Interpretar Pedido": {
        "main": [
            [{"node": "Interpretar /cardapio", "type": "main", "index": 0}]
        ]
    },
    "Interpretar /cardapio": {
        "main": [
            [{"node": "Precisa confirmar?", "type": "main", "index": 0}]
        ]
    },
    "Precisa confirmar?": {
        "main": [
            [{"node": "Redis — salvar confirmação", "type": "main", "index": 0}],
            [{"node": "Pedido confirmado?", "type": "main", "index": 0}]
        ]
    },
    "Redis — salvar confirmação": {
        "main": [
            [{"node": "Responder resumo do pedido", "type": "main", "index": 0}]
        ]
    },
    "Pedido confirmado?": {
        "main": [
            [{"node": "Sheets — registrar pedido", "type": "main", "index": 0}],
            [{"node": "Redis — limpar solicitação inválida", "type": "main", "index": 0}]
        ]
    },
    "Sheets — registrar pedido": {
        "main": [
            [{"node": "Redis — limpar após pedido", "type": "main", "index": 0}],
            [{"node": "Redis — limpar após falha", "type": "main", "index": 0}]
        ]
    },
    "Redis — limpar após pedido": {
        "main": [
            [{"node": "Redis — encerrar modo Cardápio", "type": "main", "index": 0}]
        ]
    },
    "Redis — encerrar modo Cardápio": {
        "main": [
            [{"node": "Resposta de pedido registrado", "type": "main", "index": 0}]
        ]
    },
    "Redis — limpar após falha": {
        "main": [
            [{"node": "Resposta de falha de gravação", "type": "main", "index": 0}]
        ]
    },
    "Redis — limpar solicitação inválida": {
        "main": [
            [{"node": "Responder instrução do cardápio", "type": "main", "index": 0}]
        ]
    }
}

wf['nodes'] = all_nodes
wf['connections'] = new_connections

with open(wf_path, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write('\n')

print("Workflow successfully rebuilt and written to", wf_path)
