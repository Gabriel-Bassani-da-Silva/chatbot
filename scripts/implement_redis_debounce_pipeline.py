import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

filepath = 'workflows/Agente RAG Fatec.json'
with open(filepath, 'r', encoding='utf-8') as f:
    wf = json.load(f)

nodes = wf.get('nodes', [])
connections = wf.get('connections', {})

nodes_to_remove = {
    'Postgres — Salvar Mensagem no Buffer',
    'Postgres \u2014 Salvar Mensagem no Buffer',
    'Postgres — Checar Última Mensagem',
    'Postgres \u2014 Checar \u00daltima Mensagem',
    'Decidir se janela fechou',
    'Postgres — Consolidar e Limpar Buffer',
    'Postgres \u2014 Consolidar e Limpar Buffer',
    'Aplicar texto consolidado',
    'Redis — Resetar Locks e Invalidar Buffer',
    'Redis — Rate Limit Check',
    'Rate Limit Excedido?',
    'Redis — Salvar Mensagem no Buffer',
    'Redis — Consolidar Buffer e Lock de Inferência',
    'Chatwoot — Ativar Digitando',
    'Redis — Marcar Áudio Pendente',
    'Redis — Liberar Lock de Inferência',
    'Error Trigger',
    'Redis — Liberar Lock no Erro',
    'Redis — Limpar Áudio Pendente no Erro'
}

new_nodes = [n for n in nodes if n.get('name') not in nodes_to_remove and not any(k in n.get('name', '') for k in ['Salvar Mensagem no Buffer', 'Checar \u00daltima Mensagem', 'Checar Ultima Mensagem', 'Consolidar e Limpar Buffer', 'Aplicar texto consolidado', 'Decidir se janela fechou'])]

REDIS_CONN_JS = """const redis = new Redis('redis://:f81a34c353b25e714182ab9345737beec9630d4380d9c6106f34c1afa33a6f8c@redis:6379/0');"""

new_nodes_to_add = [
    {
        "parameters": {
            "jsCode": f"""return (async () => {{
  const Redis = require('ioredis');
  {REDIS_CONN_JS}

  try {{
    const item = $input.first()?.json ?? {{}};
    let convId = String(item.conversationId || item.conversation_id || '');
    if (!convId) {{
      try {{
        convId = String($('Webhook Chatwoot RAG').first()?.json?.body?.conversation?.id || '');
      }} catch (e) {{}}
    }}
    if (convId) {{
      const pipeline = redis.pipeline();
      pipeline.set(`chatwoot:last_token:conv:${{convId}}`, 'cancelled', 'EX', 120);
      pipeline.del(`chatwoot:buffer:conv:${{convId}}`);
      pipeline.del(`chatwoot:infer_lock:conv:${{convId}}`);
      pipeline.del(`chatwoot:audio_pending:conv:${{convId}}`);
      await pipeline.exec();
    }}
  }} finally {{
    redis.disconnect();
  }}

  return $input.all();
}})();"""
        },
        "id": "redis-bypass-cancel-001",
        "name": "Redis — Resetar Locks e Invalidar Buffer",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1600, -140]
    },
    {
        "parameters": {
            "jsCode": f"""return (async () => {{
  const Redis = require('ioredis');
  {REDIS_CONN_JS}

  try {{
    const item = $input.first()?.json ?? {{}};
    let convId = String(item.conversationId || item.conversation_id || '');
    if (!convId) {{
      try {{
        convId = String($('Webhook Chatwoot RAG').first()?.json?.body?.conversation?.id || '');
      }} catch (e) {{}}
    }}
    const rateLimitKey = `chatwoot:ratelimit:conv:${{convId}}`;

    const luaScript = `
      local count = redis.call('INCR', KEYS[1])
      if count == 1 then
        redis.call('EXPIRE', KEYS[1], 30)
      end
      return count
    `;

    const count = await redis.eval(luaScript, 1, rateLimitKey);

    // Da 12ª em diante: descarte silencioso sem alocar nó Wait
    if (count > 11) {{
      return [];
    }}

    // Na 11ª mensagem: aviso educativo único de bloqueio temporário de 30s e invalidação de pendências
    if (count === 11) {{
      const pipeline = redis.pipeline();
      pipeline.set(`chatwoot:last_token:conv:${{convId}}`, 'rate_limited', 'EX', 120);
      pipeline.del(`chatwoot:buffer:conv:${{convId}}`);
      pipeline.del(`chatwoot:infer_lock:conv:${{convId}}`);
      pipeline.del(`chatwoot:audio_pending:conv:${{convId}}`);
      await pipeline.exec();

      return [{{
        json: {{
          ...item,
          isRateLimited: true,
          output: 'Você enviou muitas mensagens em um curto intervalo de tempo. Para garantir a estabilidade do atendimento, suas mensagens foram pausadas por 30 segundos. Por favor, aguarde esse período para enviar novas perguntas.'
        }}
      }}];
    }}

    // Até 10 mensagens: prossegue normalmente
    return [{{
      json: {{
        ...item,
        isRateLimited: false
      }}
    }}];
  }} finally {{
    redis.disconnect();
  }}
}})();"""
        },
        "id": "redis-ratelimit-check-001",
        "name": "Redis — Rate Limit Check",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1750, 100]
    },
    {
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 2
                },
                "conditions": [
                    {
                        "leftValue": "={{ $json.isRateLimited }}",
                        "operator": {
                            "type": "boolean",
                            "operation": "true",
                            "singleValue": True
                        }
                    }
                ],
                "combinator": "and"
            },
            "options": {}
        },
        "id": "if-ratelimit-exceeded-001",
        "name": "Rate Limit Excedido?",
        "type": "n8n-nodes-base.if",
        "typeVersion": 2,
        "position": [1950, 100]
    },
    {
        "parameters": {
            "jsCode": f"""return (async () => {{
  const Redis = require('ioredis');
  {REDIS_CONN_JS}

  try {{
    const item = $input.first()?.json ?? {{}};
    let convId = String(item.conversationId || item.conversation_id || '');
    if (!convId) {{
      try {{
        convId = String($('Webhook Chatwoot RAG').first()?.json?.body?.conversation?.id || '');
      }} catch (e) {{}}
    }}
    const msgId = Number(item.messageId) || Number($('Webhook Chatwoot RAG').first()?.json?.body?.id) || Date.now();
    const text = String(item.contentText || '').trim();
    const createdAt = Number(item.body?.created_at || item.body?.message?.created_at || $('Webhook Chatwoot RAG').first()?.json?.body?.created_at) || Date.now();
    
    const executionId = String($execution?.id || Date.now());
    const myToken = `${{msgId}}_${{executionId}}`;

    const bufferKey = `chatwoot:buffer:conv:${{convId}}`;
    const tokenKey = `chatwoot:last_token:conv:${{convId}}`;
    const audioPendingKey = `chatwoot:audio_pending:conv:${{convId}}`;

    const payload = JSON.stringify({{
      messageId: msgId,
      text: text,
      createdAt: createdAt
    }});

    const isAudio = Boolean(item.isAudioPendingIncremented || item.inputType === 'audio');

    const pipeline = redis.pipeline();
    pipeline.rpush(bufferKey, payload);
    pipeline.expire(bufferKey, 120);
    pipeline.set(tokenKey, myToken, 'EX', 120);
    
    if (isAudio) {{
      pipeline.decr(audioPendingKey);
    }}

    const results = await pipeline.exec();

    if (isAudio && results && results[3]) {{
      const remaining = Number(results[3][1]);
      if (remaining <= 0) {{
        await redis.del(audioPendingKey);
      }}
    }}

    return [{{
      json: {{
        ...item,
        myToken,
        convId,
        bufferKey,
        tokenKey,
        audioPendingKey
      }}
    }}];
  }} finally {{
    redis.disconnect();
  }}
}})();"""
        },
        "id": "redis-save-buffer-001",
        "name": "Redis — Salvar Mensagem no Buffer",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [2150, 100]
    },
    {
        "parameters": {
            "jsCode": f"""return (async () => {{
  const Redis = require('ioredis');
  {REDIS_CONN_JS}

  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  try {{
    const item = $input.first()?.json ?? {{}};
    let convId = String(item.convId || item.conversationId || item.conversation_id || '');
    if (!convId) {{
      try {{
        convId = String($('Webhook Chatwoot RAG').first()?.json?.body?.conversation?.id || '');
      }} catch (e) {{}}
    }}
    const myToken = String(item.myToken || '');
    const tokenKey = `chatwoot:last_token:conv:${{convId}}`;
    const lockKey = `chatwoot:infer_lock:conv:${{convId}}`;
    const bufferKey = `chatwoot:buffer:conv:${{convId}}`;
    const audioPendingKey = `chatwoot:audio_pending:conv:${{convId}}`;

    // Lua script: valida token, audio_pending e infer_lock atomicamente
    const luaScript = `
      local last_token = redis.call('GET', KEYS[1])
      if last_token ~= ARGV[1] then
        return {{ -1, {{}} }}
      end
      local audio_pending = tonumber(redis.call('GET', KEYS[4]) or '0')
      if audio_pending and audio_pending > 0 then
        return {{ 0, {{}} }}
      end
      local lock = redis.call('GET', KEYS[2])
      if lock and lock ~= '' then
        return {{ 0, {{}} }}
      end
      redis.call('SET', KEYS[2], ARGV[1], 'EX', 60)
      local msgs = redis.call('LRANGE', KEYS[3], 0, -1)
      redis.call('DEL', KEYS[3])
      return {{ 1, msgs }}
    `;

    let attempts = 0;
    const maxAttempts = 15; // até 30s de espera
    let rawMessages = null;

    while (attempts < maxAttempts) {{
      const res = await redis.eval(luaScript, 4, tokenKey, lockKey, bufferKey, audioPendingKey, myToken);
      const status = Number(res[0]);

      if (status === -1) {{
        // Outra mensagem mais recente assumiu a vez ou comando imediato invalidou
        return [];
      }}

      if (status === 1) {{
        rawMessages = res[1];
        break;
      }}

      // status === 0: lock ocupado ou áudio ainda em transcrição no Speaches AI
      attempts++;
      await sleep(2000);
    }}

    if (!rawMessages || rawMessages.length === 0) {{
      return [];
    }}

    // Parse e ordenação cronológica crescente (createdAt, depois messageId)
    const parsed = [];
    for (const raw of rawMessages) {{
      try {{
        parsed.push(JSON.parse(raw));
      }} catch (e) {{
        parsed.push({{ messageId: 0, text: String(raw), createdAt: 0 }});
      }}
    }}

    parsed.sort((a, b) => {{
      const tDiff = (Number(a.createdAt) || 0) - (Number(b.createdAt) || 0);
      if (tDiff !== 0) return tDiff;
      return (Number(a.messageId) || 0) - (Number(b.messageId) || 0);
    }});

    const combinedText = parsed.map(m => m.text).filter(Boolean).join('\\n').trim();
    const original = $('Liberar conteúdo textual para o agente').item.json ?? item;
    const docMeta = $('Verificar tipo de entrada e documentos').item.json ?? {{}};

    return [{{
      json: {{
        ...docMeta,
        ...original,
        ...item,
        contentText: combinedText,
        userTextChars: Array.from(combinedText).length,
        aggregatedMessagesCount: parsed.length,
        inferLockAcquired: true,
        lockKey
      }}
    }}];
  }} finally {{
    redis.disconnect();
  }}
}})();"""
        },
        "id": "redis-consolidate-infer-001",
        "name": "Redis — Consolidar Buffer e Lock de Inferência",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [2550, 100]
    },
    {
        "parameters": {
            "method": "POST",
            "url": "=http://chatwoot-web:3000/api/v1/accounts/{{ $('Webhook Chatwoot RAG').item.json.body.account?.id || 1 }}/conversations/{{ $('Webhook Chatwoot RAG').item.json.body.conversation.id }}/toggle_typing_status",
            "authentication": "genericCredentialType",
            "genericAuthType": "httpHeaderAuth",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "{\"typing_status\": \"on\"}",
            "options": {}
        },
        "id": "chatwoot-typing-on-001",
        "name": "Chatwoot — Ativar Digitando",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.5,
        "position": [2750, 100],
        "credentials": {
            "httpHeaderAuth": {
                "id": "RU2a92xV2to4mSwo",
                "name": "Header Auth account"
            }
        },
        "onError": "continueRegularOutput"
    },
    {
        "parameters": {
            "jsCode": f"""return (async () => {{
  const Redis = require('ioredis');
  {REDIS_CONN_JS}

  try {{
    const item = $input.first()?.json ?? {{}};
    let convId = String(item.conversationId || item.conversation_id || '');
    if (!convId) {{
      try {{
        convId = String($('Webhook Chatwoot RAG').first()?.json?.body?.conversation?.id || '');
      }} catch (e) {{}}
    }}
    const msgId = String(item.messageId || $('Webhook Chatwoot RAG').first()?.json?.body?.id || Date.now());
    if (convId) {{
      const pipeline = redis.pipeline();
      pipeline.set(`chatwoot:last_token:conv:${{convId}}`, `audio_pending_${{msgId}}`, 'EX', 120);
      pipeline.incr(`chatwoot:audio_pending:conv:${{convId}}`);
      pipeline.expire(`chatwoot:audio_pending:conv:${{convId}}`, 60);
      await pipeline.exec();
    }}
    return [{{
      json: {{
        ...item,
        isAudioPendingIncremented: true
      }}
    }}];
  }} finally {{
    redis.disconnect();
  }}
}})();"""
        },
        "id": "redis-audio-pending-001",
        "name": "Redis — Marcar Áudio Pendente",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1020, 200]
    },
    {
        "parameters": {
            "jsCode": f"""return (async () => {{
  const Redis = require('ioredis');
  {REDIS_CONN_JS}

  try {{
    const item = $input.first()?.json ?? {{}};
    let convId = String(item.conversation_id || item.conversationId || '');
    if (!convId) {{
      try {{
        convId = String($('Webhook Chatwoot RAG').first()?.json?.body?.conversation?.id || '');
      }} catch (e) {{}}
    }}
    if (convId) {{
      const val = await redis.decr(`chatwoot:audio_pending:conv:${{convId}}`);
      if (val <= 0) {{
        await redis.del(`chatwoot:audio_pending:conv:${{convId}}`);
      }}
    }}
  }} catch (e) {{
    // Silently continue
  }} finally {{
    redis.disconnect();
  }}

  return $input.all();
}})();"""
        },
        "id": "redis-clean-audio-pending-err-001",
        "name": "Redis — Limpar Áudio Pendente no Erro",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [2060, 360]
    },
    {
        "parameters": {
            "jsCode": f"""return (async () => {{
  const Redis = require('ioredis');
  {REDIS_CONN_JS}

  try {{
    const item = $input.first()?.json ?? {{}};
    let convId = String(item.conversation_id || item.conversationId || '');
    if (!convId) {{
      try {{
        convId = String($('Webhook Chatwoot RAG').first()?.json?.body?.conversation?.id || '');
      }} catch (e) {{}}
    }}
    if (convId) {{
      await redis.del(`chatwoot:infer_lock:conv:${{convId}}`);
      await redis.del(`chatwoot:audio_pending:conv:${{convId}}`);
    }}
  }} catch (e) {{
    // Silently continue
  }} finally {{
    redis.disconnect();
  }}

  return $input.all();
}})();"""
        },
        "id": "redis-release-infer-lock-001",
        "name": "Redis — Liberar Lock de Inferência",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [4750, 240]
    },
    {
        "parameters": {},
        "id": "error-trigger-001",
        "name": "Error Trigger",
        "type": "n8n-nodes-base.errorTrigger",
        "typeVersion": 1,
        "position": [4512, 450]
    },
    {
        "parameters": {
            "jsCode": f"""return (async () => {{
  const Redis = require('ioredis');
  {REDIS_CONN_JS}

  try {{
    const root = $input.first()?.json ?? {{}};
    const execution = root.execution ?? {{}};
    const failedExecId = String(execution.id || root.executionId || '');
    
    // Tenta extrair conversationId caso exista em alguma propriedade do erro
    let convId = String(
      root.workflowData?.conversationId ||
      execution.data?.resultData?.runData?.['Webhook Chatwoot RAG']?.[0]?.data?.main?.[0]?.[0]?.json?.body?.conversation?.id ||
      root.conversationId ||
      ''
    );

    const luaScript = `
      local failed_exec_id = ARGV[1]
      local target_conv_id = ARGV[2]
      local cleaned_keys = {{}}

      if target_conv_id and target_conv_id ~= '' then
        local lock_key = 'chatwoot:infer_lock:conv:' .. target_conv_id
        local val = redis.call('GET', lock_key)
        if val then
          redis.call('DEL', lock_key)
          table.insert(cleaned_keys, lock_key)
        end
        local ap_key = 'chatwoot:audio_pending:conv:' .. target_conv_id
        redis.call('DEL', ap_key)
        table.insert(cleaned_keys, ap_key)
      end

      if failed_exec_id and failed_exec_id ~= '' then
        local pattern = 'chatwoot:infer_lock:conv:*'
        local keys = redis.call('KEYS', pattern)
        for _, key in ipairs(keys) do
          local val = redis.call('GET', key)
          if val and string.find(val, '_' .. failed_exec_id .. '$') then
            redis.call('DEL', key)
            table.insert(cleaned_keys, key)
            local cid = string.match(key, 'chatwoot:infer_lock:conv:(.+)')
            if cid then
              local ap_key = 'chatwoot:audio_pending:conv:' .. cid
              redis.call('DEL', ap_key)
              table.insert(cleaned_keys, ap_key)
            end
          end
        end
      end

      return cleaned_keys
    `;

    const cleanedKeys = await redis.eval(luaScript, 0, failedExecId, convId);

    return [{{
      json: {{
        success: true,
        failedExecId,
        convId,
        cleanedKeys: Array.isArray(cleanedKeys) ? cleanedKeys : []
      }}
    }}];
  }} catch (err) {{
    return [{{
      json: {{
        success: false,
        error: err.message
      }}
    }}];
  }} finally {{
    redis.disconnect();
  }}
}})();"""
        },
        "id": "redis-release-error-lock-001",
        "name": "Redis — Liberar Lock no Erro",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [4750, 450]
    }
]

# Update Aguardar janela de digitação position
for n in new_nodes:
    if 'Aguardar janela' in n.get('name', ''):
        n['position'] = [2350, 100]

new_nodes.extend(new_nodes_to_add)
wf['nodes'] = new_nodes

# Clean up and rebuild connections
cleaned_connections = {}
for src, outputs in connections.items():
    if any(k in src for k in ['Salvar Mensagem no Buffer', 'Checar \u00daltima Mensagem', 'Checar Ultima Mensagem', 'Consolidar e Limpar Buffer', 'Aplicar texto consolidado', 'Decidir se janela fechou', 'Limpar Áudio Pendente no Erro']):
        continue
    new_outputs = {}
    for o_type, o_groups in outputs.items():
        new_groups = []
        for grp in o_groups:
            new_grp = [c for c in grp if not any(k in c.get('node', '') for k in ['Salvar Mensagem no Buffer', 'Checar \u00daltima Mensagem', 'Checar Ultima Mensagem', 'Consolidar e Limpar Buffer', 'Aplicar texto consolidado', 'Decidir se janela fechou', 'Limpar Áudio Pendente no Erro'])]
            new_groups.append(new_grp)
        new_outputs[o_type] = new_groups
    cleaned_connections[src] = new_outputs

# A. Roteador de tipo de mensagem (Output 1: audio) -> Redis — Marcar Áudio Pendente -> Baixar áudio — Chatwoot
for r_name in list(cleaned_connections.keys()):
    if 'Roteador de tipo de mensagem' in r_name:
        cleaned_connections[r_name]['main'][1] = [{'node': 'Redis — Marcar Áudio Pendente', 'type': 'main', 'index': 0}]

cleaned_connections['Redis — Marcar Áudio Pendente'] = {
    'main': [[{'node': 'Baixar áudio — Chatwoot', 'type': 'main', 'index': 0}]]
}

# Conexão de erro de áudio -> Redis — Limpar Áudio Pendente no Erro
audio_err_name = next(n['name'] for n in new_nodes if 'Responder erro de áudio' in n['name'])
cleaned_connections[audio_err_name] = {
    'main': [[{'node': 'Redis — Limpar Áudio Pendente no Erro', 'type': 'main', 'index': 0}]]
}

# B. Verificar se comando imediato
for v_name in list(cleaned_connections.keys()):
    if 'Verificar se comando imediato' in v_name:
        cleaned_connections[v_name]['main'] = [
            [{'node': 'Redis — Resetar Locks e Invalidar Buffer', 'type': 'main', 'index': 0}],
            [{'node': 'Redis — Rate Limit Check', 'type': 'main', 'index': 0}]
        ]

cleaned_connections['Redis — Resetar Locks e Invalidar Buffer'] = {
    'main': [[{'node': 'Postgres — Consultar Estado Permanente', 'type': 'main', 'index': 0}]]
}

# C. Redis — Rate Limit Check -> Rate Limit Excedido?
cleaned_connections['Redis — Rate Limit Check'] = {
    'main': [[{'node': 'Rate Limit Excedido?', 'type': 'main', 'index': 0}]]
}

# D. Rate Limit Excedido?
prep_name = next(n['name'] for n in new_nodes if 'Preparar resposta' in n['name'])
cleaned_connections['Rate Limit Excedido?'] = {
    'main': [
        [{'node': prep_name, 'type': 'main', 'index': 0}],
        [{'node': 'Redis — Salvar Mensagem no Buffer', 'type': 'main', 'index': 0}]
    ]
}

# E. Redis — Salvar Mensagem no Buffer -> Aguardar janela de digitação
wait_name = next(n['name'] for n in new_nodes if 'Aguardar janela' in n['name'])
cleaned_connections['Redis — Salvar Mensagem no Buffer'] = {
    'main': [[{'node': wait_name, 'type': 'main', 'index': 0}]]
}

# F. Aguardar janela de digitação -> Redis — Consolidar Buffer e Lock de Inferência
cleaned_connections[wait_name] = {
    'main': [[{'node': 'Redis — Consolidar Buffer e Lock de Inferência', 'type': 'main', 'index': 0}]]
}

# G. Redis — Consolidar Buffer e Lock de Inferência -> Chatwoot — Ativar Digitando
cleaned_connections['Redis — Consolidar Buffer e Lock de Inferência'] = {
    'main': [[{'node': 'Chatwoot — Ativar Digitando', 'type': 'main', 'index': 0}]]
}

# H. Chatwoot — Ativar Digitando -> Postgres — Consultar Estado Permanente
post_name = next(n['name'] for n in new_nodes if 'Consultar Estado Permanente' in n['name'])
cleaned_connections['Chatwoot — Ativar Digitando'] = {
    'main': [[{'node': post_name, 'type': 'main', 'index': 0}]]
}

# I. Enviar resposta ao Chatwoot -> Redis — Liberar Lock de Inferência
send_name = next(n['name'] for n in new_nodes if 'Enviar resposta ao Chatwoot' in n['name'])
cleaned_connections[send_name] = {
    'main': [[{'node': 'Redis — Liberar Lock de Inferência', 'type': 'main', 'index': 0}]]
}

# J. Error Trigger -> Redis — Liberar Lock no Erro
cleaned_connections['Error Trigger'] = {
    'main': [[{'node': 'Redis — Liberar Lock no Erro', 'type': 'main', 'index': 0}]]
}

wf['connections'] = cleaned_connections

with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

print(f"Workflow saved! Total nodes: {len(new_nodes)}, connections: {len(cleaned_connections)}")
