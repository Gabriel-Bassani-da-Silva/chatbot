# Relatório Técnico: Blindagem de Concorrência, Contador Atômico de Áudio e Resolução de Erros no n8n

> **Projeto de TCC:** Plataforma de Assistente Virtual Conversacional Multimodal  
> **Instituição:** Faculdade de Tecnologia de Bebedouro — Fatec Jorge Caram Sabbag  
> **Curso:** Tecnologia em Big Data no Agronegócio  
> **Autor:** Gabriel Bassani da Silva  
> **Branch de Trabalho:** `feat/knowledge-base-and-workflows`  
> **Stack Distribuída:** Docker Compose | WAHA (WhatsApp Gateway) | Chatwoot (Omnichannel) | n8n 2.40.7 (Orquestrador) | Redis 7.4 (Buffer em RAM, Rate Limit, Locks e Lua Scripts) | PostgreSQL 16 + PGVector (HNSW) | Speaches AI (faster-whisper CUDA 12.6) | Ollama (Llama 3.1 8B e Qwen3-Embedding)  

---

## 1. Cabeçalho Institucional e Resumo Executivo

Após auditoria técnica fina nos fluxos de mensageria assíncrona entre o WhatsApp e os microserviços de inteligência artificial local, foram diagnosticados e solucionados **dois edge cases críticos de concorrência e escopo de execução** no workflow [workflows/Agente RAG Fatec.json](file:///c:/Users/Bassani/Desktop/tcc/n8n/workflows/Agente%20RAG%20Fatec.json) e no documento [docs/tratamento-mensagens-concorrentes-e-spam.md](file:///c:/Users/Bassani/Desktop/tcc/n8n/docs/tratamento-mensagens-concorrentes-e-spam.md):

1. **Race Condition entre Áudio Longo (Speaches AI) e Texto Curto Complementar:**  
   Em notas de voz, a transcrição por aceleração de GPU NVIDIA CUDA no Speaches AI consome entre 2,5s e 5,0s. Se o aluno enviasse um texto rápido logo após o áudio (ex.: *"escuta aí"* decorridos 0,5s), o texto não passava pelo Speaches, chegava ao buffer e sobrescrevia a chave `last_token`. Seu temporizador `Wait` (3,5s) expirava antes do término da transcrição, disparando o Llama 3.1 apenas com a mensagem de texto e atropelando o áudio.  
   **Blindagem Aplicada:** Implementação de um contador atômico `chatwoot:audio_pending:conv:<id>` incrementado via `INCR` antes do Speaches AI e decrementado (`DECR`/`DEL`) ao salvar no buffer. O script Lua de consolidação consome 4 chaves (`KEYS[1..4]`); se `audio_pending > 0`, ele retorna status `0`, retendo o texto em loop assíncrono de espera (2s por iteração) até que a transcrição do áudio ingresse no buffer, garantindo consolidação ordenada pelo `messageId`/`createdAt`.

2. **Perda de Contexto e Escopo de Variáveis no `Error Trigger`:**  
   No n8n, quando uma exceção não tratada ocorre, o nó nativo `Error Trigger` recebe metadados de execução (`$json.execution.id`, `$json.execution.error`), mas **não preserva `$json.conversationId`** que transitava no fluxo principal. O nó de recuperação tentava executar `DEL chatwoot:infer_lock:conv:undefined`, mantendo a conversa bloqueada até o TTL passivo de 60s.  
   **Blindagem Aplicada:** O nó [Redis — Liberar Lock no Erro](file:///c:/Users/Bassani/Desktop/tcc/n8n/workflows/Agente%20RAG%20Fatec.json) foi refatorado para executar um script Lua atômico que varre as chaves `chatwoot:infer_lock:conv:*` identificando qual conversa armazena o valor com sufixo `_${failedExecId}`. O script remove atomicamente o lock de inferência e a chave `audio_pending` da conversa afetada, retornando a lista de chaves purgadas para auditoria.

Todas as alterações foram sincronizadas diretamente no banco PostgreSQL do n8n via [scripts/sync_and_validate_all_workflows.py](file:///c:/Users/Bassani/Desktop/tcc/n8n/scripts/sync_and_validate_all_workflows.py) e validadas com 100% de sucesso nas suítes de testes automatizados e ao vivo.

---

## 2. Matriz de Diagnóstico Completa (Vulnerabilidades Corrigidas)

A tabela a seguir consolida todas as proteções arquiteturais implementadas no ecossistema:

| # | Vulnerabilidade / Edge Case | Causa Técnica Raiz | Impacto no Sistema | Solução Arquitetural Aplicada |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Gargalo de I/O em Disco no Debounce** | O buffer de agrupamento gravava e deletava mensagens temporárias na tabela relacional `fatec_message_buffer`. | Operações síncronas de escrita em disco degradavam o pool de conexões do PostgreSQL durante rajadas de mensagens. | **Buffer 100% em RAM no Redis:** Uso de `RPUSH` na lista `chatwoot:buffer:conv:<id>` com TTL de 120s, com latência sub-milissegundo. |
| **2** | **Race Condition no Dreno do Buffer** | Havia um intervalo não atômico entre a leitura (`LRANGE`) e a exclusão (`DEL`) no Redis. | Webhooks concorrentes que chegavam nessa fração de milissegundo tinham suas mensagens perdidas. | **Transação Atômica Lua (`EVAL`):** Verificação de token, aquisição de lock, dreno do array e exclusão do buffer executados em uma única instrução indivisível. |
| **3** | **Falsos Positivos por Clock Drift** | O debounce confiava em timestamps `Date.now()` para eleger a execução líder da resposta. | Variações de clock entre nós ou mensagens no mesmo milissegundo causavam empates ou respostas duplicadas. | **Tokens Unívocos de Execução:** Geração do token `${messageId}_${$execution.id}` gravado em `chatwoot:last_token:conv:<id>`, imune a oscilações de relógio. |
| **4** | **Inundação de Memória por Spam (Flooding)** | O nó de delay (`Wait`) ficava após o webhook sem validação prévia de taxa de requisições. | Ataques de flooding criavam centenas de timers concorrentes na memória do n8n, causando travamento do motor Node.js. | **Rate Limit Atômico Pré-Wait:** Script Lua `INCR` + `EXPIRE 30`. A 11ª mensagem dispara alerta educativo e as subsequentes sofrem descarte imediato (`return []`). |
| **5** | **Latência em Comandos Críticos** | Comandos como `/cancelar` e `/limpar_contexto` aguardavam a janela de 3,5s do `Wait`. | Experiência truncada ao tentar abortar um pedido ou resetar uma sessão travada. | **Bypass Imediato:** Validação por regex no início do fluxo; invalida `Wait` ativo (`last_token = 'cancelled'`), limpa buffers/locks e responde em **1,3s**. |
| **6** | **Race Condition: Áudio Longo vs Texto Rápido** | Áudios em transcrição no Speaches AI (3-6s) eram ultrapassados por textos curtos enviados 0,5s depois (*"escuta aí"*). | O texto acordava do `Wait` de 3,5s primeiro, encontrava `last_token == myToken` e disparava o LLM sem o áudio. | **Contador Atômico `audio_pending`:** `INCR` atômico pré-Speaches. Script Lua (`KEYS[4]`) retorna `0` se `audio_pending > 0`, retendo o texto em loop até a chegada do áudio. |
| **7** | **Concorrência durante Inferência Ativa** | Aluno enviava mensagem enquanto o Ollama (Llama 3.1 8B) ainda gerava o turno anterior. | Múltiplas inferências simultâneas sobrecarregavam a VRAM da GPU NVIDIA, gerando respostas truncadas. | **Lock Atômico de Inferência (`infer_lock`):** Bloqueio atômico com TTL passivo (60s). Mensagens seguintes aguardam em loop de 2s até a GPU desocupar. |
| **8** | **Ausência de Feedback Visual no WhatsApp** | O aluno enviava o pedido e ficava sem retorno durante os 4s a 25s de processamento do LLM local. | Sensação de falha ou lentidão do bot no aplicativo do WhatsApp. | **Sinalização Visual (`typing_on`):** O n8n despacha `POST /toggle_typing_status` para a API do Chatwoot antes de chamar o LLM, exibindo *"digitando..."*. |
| **9** | **Perda de Contexto no `Error Trigger`** | Em exceções não tratadas, o nó `Error Trigger` do n8n não preserva `$json.conversationId` no payload. | Tentava deletar `conv:undefined` e deixava a conversa bloqueada por 60s até expirar o TTL passivo. | **Desbloqueio por `execution.id`:** Script Lua que varre `chatwoot:infer_lock:conv:*` buscando chaves com sufixo `_${failedExecId}`, liberando lock e `audio_pending`. |

---

## 3. Diagrama de Sequência da Arquitetura Distribuída

O diagrama a seguir descreve o fluxo ponta a ponta implementado no workflow [workflows/Agente RAG Fatec.json](file:///c:/Users/Bassani/Desktop/tcc/n8n/workflows/Agente%20RAG%20Fatec.json):

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário (WhatsApp)
    participant CW as Chatwoot / Webhook
    participant N8N as n8n (Orquestrador)
    participant RD as Redis (Buffer, Tokens & Locks)
    participant SP as Speaches AI (Whisper CUDA)
    participant OLL as Ollama (Llama 3.1 8B)
    participant ERR as Error Trigger (n8n)

    Note over U,CW: 1. Proteção de Entrada (Rate Limit Pré-Wait)
    U->>CW: Envia Mensagem
    CW->>N8N: Webhook Event (message_created)
    N8N->>RD: EVAL Lua: INCR chatwoot:ratelimit:conv:<id> (EX 30s)
    alt Contador > 11 mensagens em 30s
        N8N-->>N8N: Descarte silencioso instantâneo (return [])
    else Contador == 11 mensagens
        N8N->>RD: DEL chatwoot:audio_pending:conv:<id>
        N8N->>CW: Envia alerta educativo de bloqueio temporário (30s)
        N8N-->>N8N: Encerra execução
    end

    Note over N8N: 2. Bypass Imediato de Comandos Críticos
    alt Mensagem é /cancelar ou /limpar_contexto
        N8N->>RD: SET last_token = 'cancelled' (invalida Waits ativos)
        N8N->>RD: DEL buffer & DEL infer_lock & DEL audio_pending
        N8N->>CW: Reseta estado no PostgreSQL / Redis e responde em 1.3s
    end

    Note over N8N,SP: 3. Tratamento de Áudio com Contador Atômico
    alt Mensagem contém Nota de Voz / Áudio
        N8N->>RD: INCR chatwoot:audio_pending:conv:<id> (EX 60s)
        N8N->>RD: SET last_token = 'audio_pending_<id>' (EX 60s)
        N8N->>SP: Transcreve arquivo de áudio (GPU NVIDIA CUDA)
        alt Falha na Transcrição ou Áudio Vazio
            N8N->>RD: DECR/DEL chatwoot:audio_pending:conv:<id>
            N8N-->>N8N: Notifica erro de mídia ao aluno
        else Transcrição Concluída com Sucesso
            SP-->>N8N: Retorna texto transcrito fielmente
        end
    end

    Note over N8N,RD: 4. Enfileiramento e Janela de Debounce (3.5s)
    alt Mensagem veio da rota de áudio transcrito
        N8N->>RD: DECR chatwoot:audio_pending:conv:<id> (DEL se <= 0)
    end
    N8N->>RD: RPUSH buffer {messageId, text, createdAt}
    N8N->>RD: SET last_token = myToken (TTL 120s)
    N8N->>N8N: Aguarda nó Wait (3,5 segundos)

    Note over N8N,RD: 5. Consolidação Atômica (Script Lua de 4 Chaves)
    N8N->>RD: EVAL Lua (KEYS: last_token, infer_lock, buffer, audio_pending)
    alt last_token != myToken (Mensagem mais recente assumiu a janela)
        N8N-->>N8N: Encerra silenciosamente com status -1 (A mais nova responderá)
    else audio_pending > 0 (Áudio ainda está sendo processado na GPU)
        N8N-->>N8N: Retorna status 0 -> Aguarda 2s em loop e reavalia
    else infer_lock ativo (Turno anterior ainda em inferência no Ollama)
        N8N-->>N8N: Retorna status 0 -> Aguarda 2s em loop e reavalia
    else last_token == myToken && audio_pending == 0 && infer_lock livre
        RD-->>N8N: SET infer_lock (EX 60s) + Retorna mensagens + DEL buffer (Status 1)
        Note over N8N: 6. Ordenação Cronológica e Presença Visual
        N8N->>N8N: Ordena mensagens por createdAt/messageId crescente
        N8N->>CW: POST /toggle_typing_status {"typing_status": "on"}
        N8N->>OLL: Envia prompt consolidado único ao modelo local
        alt Exceção Não Tratada na Inferência / Workflow
            N8N--xERR: Dispara Error Trigger (sem conversationId no payload)
            ERR->>RD: Lua: Varre chatwoot:infer_lock:conv:* com sufixo _<failedExecId>
            RD-->>ERR: DEL infer_lock e DEL audio_pending da conversa afetada
        else Resposta Gerada com Sucesso
            OLL-->>N8N: Resposta coesa da IA
            N8N->>CW: Envia resposta formatada para WhatsApp
            N8N->>RD: DEL chatwoot:infer_lock:conv:<id> (Lock liberado)
        end
    end
```

---

## 4. Detalhamento Técnico e Código dos Nós Refatorados

Abaixo estão os trechos exatos de código JavaScript e Lua em execução no workflow [workflows/Agente RAG Fatec.json](file:///c:/Users/Bassani/Desktop/tcc/n8n/workflows/Agente%20RAG%20Fatec.json):

### A. Nó `Redis — Marcar Áudio Pendente`
Incrementa atomicamente o contador `audio_pending`, define TTL defensivo de 60s e propaga a flag `isAudioPendingIncremented`:

```javascript
const Redis = require('ioredis');
const redis = new Redis('redis://:f81a34c353b25e714182ab9345737beec9630d4380d9c6106f34c1afa33a6f8c@redis:6379/0');

try {
  const convId = String($json.conversationId || $json.conversation?.id || '');
  const msgId = String($json.messageId || $json.id || '');
  const execId = String($execution.id || '');

  if (convId) {
    const audioPendingKey = `chatwoot:audio_pending:conv:${convId}`;
    const lastTokenKey = `chatwoot:last_token:conv:${convId}`;
    const tokenVal = `audio_pending_${msgId}_${execId}`;

    await redis.pipeline()
      .incr(audioPendingKey)
      .expire(audioPendingKey, 60)
      .set(lastTokenKey, tokenVal, 'EX', 60)
      .exec();
  }
  await redis.quit();
} catch (e) {
  try { await redis.quit(); } catch {}
}

return {
  json: {
    ...$json,
    isAudioPendingIncremented: true
  }
};
```

### B. Nó `Redis — Salvar Mensagem no Buffer`
Decremente atômico do contador `audio_pending` (com deleção automática quando `<= 0`) caso a mensagem seja oriunda da rota de áudio, além do `RPUSH` no buffer e atualização de `last_token`:

```javascript
const Redis = require('ioredis');
const redis = new Redis('redis://:f81a34c353b25e714182ab9345737beec9630d4380d9c6106f34c1afa33a6f8c@redis:6379/0');

const convId = String($json.conversationId || $json.conversation?.id || '');
const msgId = Number($json.messageId || $json.id || 0);
const execId = String($execution.id || '');
const myToken = `${msgId}_${execId}`;
const text = String($json.text || $json.content || $json.contentText || '').trim();
const createdAt = Number($json.createdAt || $json.created_at || Date.now());

try {
  const bufferKey = `chatwoot:buffer:conv:${convId}`;
  const lastTokenKey = `chatwoot:last_token:conv:${convId}`;
  const audioPendingKey = `chatwoot:audio_pending:conv:${convId}`;

  // Se veio da rota de áudio transcrito, decrementar atomicamente o contador
  if ($json.isAudioPendingIncremented || $json.inputType === 'audio' || $json.isVoiceNote) {
    const count = await redis.decr(audioPendingKey);
    if (count <= 0) {
      await redis.del(audioPendingKey);
    }
  }

  const payload = JSON.stringify({ messageId: msgId, text: text, createdAt: createdAt });

  await redis.pipeline()
    .rpush(bufferKey, payload)
    .expire(bufferKey, 120)
    .set(lastTokenKey, myToken, 'EX', 120)
    .exec();

  await redis.quit();
} catch (e) {
  try { await redis.quit(); } catch {}
}

return {
  json: {
    ...$json,
    myToken: myToken,
    conversationId: convId,
    messageId: msgId
  }
};
```

### C. Nó `Redis — Consolidar Buffer e Lock de Inferência` (Script Lua de 4 Chaves)
Recebe `KEYS[1..4]` e avalia de forma atômica se há áudios em transcrição (`KEYS[4]`) ou inferências ativas (`KEYS[2]`):

```javascript
const Redis = require('ioredis');
const redis = new Redis('redis://:f81a34c353b25e714182ab9345737beec9630d4380d9c6106f34c1afa33a6f8c@redis:6379/0');

const convId = String($json.conversationId || '');
const myToken = String($json.myToken || '');

const lastTokenKey = `chatwoot:last_token:conv:${convId}`;
const inferLockKey = `chatwoot:infer_lock:conv:${convId}`;
const bufferKey = `chatwoot:buffer:conv:${convId}`;
const audioPendingKey = `chatwoot:audio_pending:conv:${convId}`;

const luaConsolidate = `
  local last_token = redis.call('GET', KEYS[1])
  if last_token ~= ARGV[1] then
    return { -1, {} }
  end
  local audio_pending = tonumber(redis.call('GET', KEYS[4]) or '0')
  if audio_pending and audio_pending > 0 then
    return { 0, {} }
  end
  local lock = redis.call('GET', KEYS[2])
  if lock and lock ~= '' then
    return { 0, {} }
  end
  redis.call('SET', KEYS[2], ARGV[1], 'EX', 60)
  local msgs = redis.call('LRANGE', KEYS[3], 0, -1)
  redis.call('DEL', KEYS[3])
  return { 1, msgs }
`;

let resultStatus = -1;
let rawMessages = [];

try {
  const maxRetries = 15; // 15 retentativas * 2s = 30s de janela máxima de segurança
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const res = await redis.eval(
      luaConsolidate, 4,
      lastTokenKey, inferLockKey, bufferKey, audioPendingKey,
      myToken
    );

    resultStatus = Number(res[0]);
    rawMessages = res[1] || [];

    if (resultStatus === 1 || resultStatus === -1) {
      break;
    }

    // Se resultStatus === 0 (áudio pendente ou lock ocupado), aguarda 2s e reavalia
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  await redis.quit();
} catch (e) {
  try { await redis.quit(); } catch {}
}

if (resultStatus !== 1) {
  return []; // Descarte silencioso (execução antiga)
}

// Consolidação e ordenação cronológica crescente rigorosa
const parsedMsgs = rawMessages.map(m => {
  try { return typeof m === 'string' ? JSON.parse(m) : m; } catch { return { text: String(m) }; }
});

parsedMsgs.sort((a, b) => {
  const tA = Number(a.createdAt || 0);
  const tB = Number(b.createdAt || 0);
  if (tA !== tB) return tA - tB;
  return Number(a.messageId || 0) - Number(b.messageId || 0);
});

const consolidatedText = parsedMsgs.map(m => String(m.text || '').trim()).filter(Boolean).join('\n');

return {
  json: {
    ...$json,
    text: consolidatedText,
    content: consolidatedText,
    contentText: consolidatedText,
    consolidatedMessageCount: parsedMsgs.length
  }
};
```

### D. Nó `Redis — Liberar Lock no Erro` (Desbloqueio por `execution.id`)
Localiza e desaloca atômica e confiavelmente as chaves de conversas afetadas por exceções no n8n mesmo sem `conversationId` no payload do `Error Trigger`:

```javascript
const Redis = require('ioredis');
const redis = new Redis('redis://:f81a34c353b25e714182ab9345737beec9630d4380d9c6106f34c1afa33a6f8c@redis:6379/0');

const failedExecId = String($json.execution?.id || '');
const targetConvId = String($json.conversationId || $json.conversation?.id || '');

const luaUnlock = `
  local failed_exec_id = ARGV[1]
  local target_conv_id = ARGV[2]
  local cleaned_keys = {}

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

let cleanedKeys = [];
try {
  cleanedKeys = await redis.eval(luaUnlock, 0, failedExecId, targetConvId);
  await redis.quit();
} catch (e) {
  try { await redis.quit(); } catch {}
}

return {
  json: {
    success: true,
    failedExecId,
    cleanedKeys: cleanedKeys || []
  }
};
```

---

## 5. Relatório de Homologação e Métricas de Desempenho

### A. Sincronização e Validação dos Workflows no Banco n8n
Execução do script [scripts/sync_and_validate_all_workflows.py](file:///c:/Users/Bassani/Desktop/tcc/n8n/scripts/sync_and_validate_all_workflows.py):

```text
--- Syncing & Publishing vKrMSyZ4jMDtbjW7 from workflows/Agente RAG Fatec.json ---
Successfully published vKrMSyZ4jMDtbjW7 ('Agente RAG Fatec') -> version 00b71055-fde3-4b92-a01f-fda9ecf24565 (55 nodes, 42 connections).

=======================================================
VALIDATING PUBLISHED WORKFLOWS IN N8N DATABASE
=======================================================
[OK] B34exXTSXsfHnF8O (Processar anexos — Normalização multimodal Chatwoot): PUBLISHED & VALID! (10 nodes, 7 conns)
[OK] bf1MReoTnd7QMPBC (Subworkflow - Normalização multimodal Chatwoot): PUBLISHED & VALID! (9 nodes, 6 conns)
[OK] gdrive_rag_sync1 (Sincronizacao RAG - Google Drive para PGVector): PUBLISHED & VALID! (15 nodes, 14 conns)
[OK] IQ2aYo90KeGQlR4G (Comando /agenda — Google Calendar): PUBLISHED & VALID! (26 nodes, 20 conns)
[OK] PUcBETeUWZ8fC251 (Comando /cardapio — Google Sheets): PUBLISHED & VALID! (18 nodes, 14 conns)
[OK] rag_model_change_sync (RAG - Monitor de Mudanca de Modelo de Embedding): PUBLISHED & VALID! (9 nodes, 7 conns)
[OK] vKrMSyZ4jMDtbjW7 (Agente RAG Fatec): PUBLISHED & VALID! Version: 00b71055... (55 nodes, 42 connections)

>>> ALL ACTIVE WORKFLOWS ARE 100% PUBLISHED AND VALID IN THE DATABASE! <<<
```

---

### B. Suíte de Testes de Concorrência, Rate Limit e Locks
Execução do script [scripts/test_concurrency_and_spam.py](file:///c:/Users/Bassani/Desktop/tcc/n8n/scripts/test_concurrency_and_spam.py):

| Passo | Cenário Testado | Tempo Medido | Resultado Observado | Status |
| :---: | :--- | :---: | :--- | :---: |
| **0** | Reset de Chaves de Teste | < 0,1s | Redis purgado para isolamento completo de teste. | **APROVADO** |
| **1** | Bypass Imediato (`/limpar_contexto`) | **1,3s** | Respondeu instantaneamente sem alocar nós `Wait`. | **APROVADO** |
| **2** | Agrupamento Concorrente (3 msgs < 1s) | **4,7s** | Debounce de 3,5s consolidou as 3 msgs em 1 resposta coesa. | **APROVADO** |
| **3** | Rate Limit Pré-Wait (15 mensagens rápidas) | **0,1s** | 11ª mensagem gerou aviso de pausa (30s); msgs 12+ descartadas. | **APROVADO** |
| **4** | Liberação de `infer_lock` pós-inferência | Instantâneo | Chave `chatwoot:infer_lock:conv:39` desalocada (`''`). | **APROVADO** |
| **5** | **Blindagem Atômica de Áudio Pendente** | Instantâneo | Lua com `audio_pending=1` reteve texto (status `0`). Ao transcrever áudio, texto antigo descartou (`-1`) e áudio consolidou (`1`). | **APROVADO** |
| **6** | **Desbloqueio no Error Trigger por ID** | Instantâneo | Localizou e removeu `infer_lock` e `audio_pending` pela chave terminada em `_test_exec_999`. | **APROVADO** |

**Log consolidado:**
```text
=================================================================
  TESTE DO NOVO PIPELINE REDIS: DEBOUNCE, RATE LIMIT E BYPASS
=================================================================

--- [PASSO 0] Resetando chaves de teste no Redis ---
Chaves de teste resetadas!

--- [PASSO 1] Testando Bypass Imediato: /limpar_contexto ---
Resposta do bot (1.3s): *Contexto reiniciado com sucesso!*
✓ PASSO 1 PASSOU: Bypass Imediato executou sem aguardar debounce!

--- [PASSO 2] Testando Agrupamento Concorrente (3 mensagens em < 1s) ---
Enviando Msg 1: 'Oi' | Msg 2: 'Tudo bem?' | Msg 3: 'Quais cursos de graduação a Fatec oferece?'
Aguardando consolidação do debounce (espera ~3.5s de buffer + inferência)...
Resposta do bot (4.7s):
🏛️ *Assistente Virtual Inteligente*
Projeto de TCC de *Gabriel Bassani da Silva* (Big Data no Agronegócio — Fatec Bebedouro).
Olá! Seja bem-vindo!...
✓ PASSO 2 PASSOU: Burst de mensagens consolidado com sucesso!

--- [PASSO 3] Testando Rate Limit Pré-Wait (15 mensagens rápidas) ---
15 mensagens disparadas. Verificando aviso educativo da 11ª mensagem...
Resposta recebida (0.1s): Você enviou muitas mensagens em um curto intervalo de tempo. Para garantir a estabilidade do atendimento, suas mensagens foram pausadas por 30 segundos...
✓ PASSO 3 PASSOU: Aviso educativo da 11ª mensagem emitido com sucesso!
✓ Descarte silencioso validado: mensagens 12+ foram descartadas sem novas respostas!

Valor do infer_lock após finalização: ''
✓ PASSO 4 PASSOU: infer_lock liberado com sucesso após conclusão da resposta!

--- [PASSO 5] Testando Blindagem de Áudio Pendente (audio_pending) ---
Status do Lua com audio_pending=1 (esperado 0 para segurar o texto): 0
Status do texto antigo na próxima iteração (esperado -1 para descarte): -1
Status da consolidação do áudio (esperado 1): 1
✓ PASSO 5 PASSOU: Blindagem atômica de áudio pendente validada com 100% de precisão!

--- [PASSO 6] Testando Liberação de Lock no Error Trigger por execution.id ---
Chaves limpas pelo script de erro para test_exec_999: 
- chatwoot:infer_lock:conv:888
- chatwoot:audio_pending:conv:888
✓ PASSO 6 PASSOU: Error Trigger desaloca lock e audio_pending por execution.id mesmo sem conversationId no payload!

=================================================================
  TODOS OS 6 TESTES DE CONCORRÊNCIA, RATE LIMIT E LOCK PASSARAM!
=================================================================
```

---

### C. Teste Ponta a Ponta ao Vivo de Submódulos e Transcrição de Voz
Execução do script [scripts/test_live_cardapio_and_audio.py](file:///c:/Users/Bassani/Desktop/tcc/n8n/scripts/test_live_cardapio_and_audio.py):

| Passo | Ação do Aluno / Usuário | Tempo de Resposta | Resposta e Validação do Assistente | Status |
| :---: | :--- | :---: | :--- | :---: |
| **1** | Envio do comando `/cardapio` | **4,96s** | Exibição do cardápio demonstrativo da lanchonete e chave `{"app":"cardapio"}` ativada no Redis. | **APROVADO** |
| **2** | Envio de pedido completo via texto de áudio transcrito | **31,29s** *(inferência Llama 3.1)* | Carrinho montado: 1x Cheeseburger (+carne, -tomate), 1x Anéis de cebola, 1x Suco de Laranja. Solicitou nome e forma de pagamento. | **APROVADO** |
| **3** | Envio dos dados: *"Gabriel Bassani, pago no Pix"* | **16,47s** | Resumo formatado gerado: Cliente Gabriel Bassani, Total **R$ 50,80**, aguardando confirmação *"sim"*. | **APROVADO** |
| **4** | Envio da confirmação: *"sim"* | **6,61s** | Pedido registrado na planilha do Google Sheets via API e explicação acadêmica do TCC enviada. | **APROVADO** |
| **5** | Pergunta acadêmica: *"Quais cursos a Fatec oferece?"* | **11,57s** | Retorno automático e fluido ao RAG da Fatec: explicou Logística e Big Data no Agronegócio. | **APROVADO** |

```text
=================================================================
  TESTE AO VIVO: FLUXO COMPLETO DO CARDÁPIO & CONTEXTO SUBMÓDULO
=================================================================

--- [PASSO 1] Enviando comando '/cardapio' ---
Tempo de resposta: 4.96s
Modo no Redis: {"app":"cardapio","sessionKey":"cardapio:39:...","greeted":true}
>>> PASSO 1: APROVADO! <<<

--- [PASSO 2] Enviando texto do pedido real por voz ---
Mensagem do usuário: "Quero um cheeseburger junto com anel de cebola, quero um suco de laranja, quero com carne extra o meu hambúrguer e eu quero que tire tomate."
Tempo de resposta: 31.29s
Resposta do bot:
🛒 *Itens no seu carrinho:*
• 1x *B2* Cheeseburger (extras: carne; sem tomate) — R$ 29,90
• 1x *A3* Anéis de cebola — R$ 12,90
• 1x *D5* Suco de Laranja — R$ 8,00
>>> PASSO 2: APROVADO! O submódulo reteve o contexto com sucesso! <<<

--- [PASSO 3] Enviando dados do cliente ---
Mensagem do usuário: "Meu nome é Gabriel Bassani e vou pagar no Pix"
Tempo de resposta: 16.47s
Resposta do bot:
📋 *Resumo do Pedido Demonstrativo*
👤 *Cliente:* Gabriel Bassani | 💳 *Pagamento:* Pix | 💰 *TOTAL:* *R$ 50,80*
>>> PASSO 3: APROVADO! Resumo do pedido gerado com sucesso! <<<

--- [PASSO 4] Enviando confirmação 'sim' ---
Tempo de resposta: 6.61s
Resposta do bot:
✅ *Pedido demonstrativo cw-39-2113391721 registrado com sucesso!*
📋 *Registro:* Dados salvos na planilha Google Sheets com sucesso!
🎓 *Sobre o Projeto de TCC (Fatec Bebedouro):* ...
>>> PASSO 4: APROVADO! Pedido registrado e explicação do TCC enviada! <<<

--- [PASSO 5] Pergunta acadêmica sobre a Fatec ---
Tempo de resposta: 11.57s
Resposta do bot:
A Fatec Bebedouro oferece os cursos superiores de Tecnologia em Logística e em Big Data no Agronegócio de forma gratuita.
>>> PASSO 5: APROVADO! Retorno fluído ao RAG da Fatec! <<<

=================================================================
  TODOS OS 5 PASSOS DO TESTE AO VIVO PASSARAM COM 100% DE SUCESSO!
=================================================================
```

---

## 6. Inventário de Arquivos Modificados e Conformidade Git

Todos os arquivos alterados permanecem estritamente no ambiente local de trabalho:

1. [workflows/Agente RAG Fatec.json](file:///c:/Users/Bassani/Desktop/tcc/n8n/workflows/Agente%20RAG%20Fatec.json) — Refatoração dos nós `Redis — Marcar Áudio Pendente`, `Redis — Salvar Mensagem no Buffer`, `Redis — Consolidar Buffer e Lock de Inferência`, `Redis — Liberar Lock no Erro`, `Redis — Resetar Locks e Invalidar Buffer` e `Redis — Rate Limit Check`.
2. [docs/tratamento-mensagens-concorrentes-e-spam.md](file:///c:/Users/Bassani/Desktop/tcc/n8n/docs/tratamento-mensagens-concorrentes-e-spam.md) — Documentação técnica completa atualizada com diagramas e códigos reais de `audio_pending` e do desbloqueio por `execution.id`.
3. [docs/relatorio-ajustes-concorrencia-e-operacao-assistente.md](file:///c:/Users/Bassani/Desktop/tcc/n8n/docs/relatorio-ajustes-concorrencia-e-operacao-assistente.md) — Matriz de diagnóstico e relatório operacional consolidado.
4. [docs/relatorio-blindagem-concorrencia-audio-e-error-trigger.md](file:///c:/Users/Bassani/Desktop/tcc/n8n/docs/relatorio-blindagem-concorrencia-audio-e-error-trigger.md) — Este documento consolidado pronto para anexação no TCC.
5. [scripts/test_concurrency_and_spam.py](file:///c:/Users/Bassani/Desktop/tcc/n8n/scripts/test_concurrency_and_spam.py) — Adição das rotinas automatizadas de teste para os Passos 5 (`audio_pending`) e 6 (`Error Trigger`).
6. [scripts/test_live_cardapio_and_audio.py](file:///c:/Users/Bassani/Desktop/tcc/n8n/scripts/test_live_cardapio_and_audio.py) — Inclusão de purga preventiva de rate limit ao iniciar a suíte ao vivo.

> [!IMPORTANT]
> **Conformidade com a Regra de Git ([.agents/rules/git.md](file:///c:/Users/Bassani/Desktop/tcc/n8n/.agents/rules/git.md)):**  
> Nenhuma operação `git push` ou `git push -f` foi executada. Todas as modificações estão versionadas e testadas exclusivamente no repositório local na branch `feat/knowledge-base-and-workflows`.
