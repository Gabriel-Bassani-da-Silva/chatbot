"""
Script para implementar persistência permanente do estado da conversa no PostgreSQL no n8n.
Tabela: fatec_conversation_state (is_first_message, greeting_shown, current_mode, etc.)
"""

import json
import os
import sys

WF_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows", "Agente RAG Fatec.json")

def apply_postgres_state():
    with open(WF_FILE, "r", encoding="utf-8") as f:
        wf = json.load(f)

    nodes = wf["nodes"]
    connections = wf["connections"]

    # 1. Atualizar nó 'Verificar tipo de entrada e documentos' para extrair senderPhone e senderName
    node_tipo_entrada = next((n for n in nodes if n.get("name") == "Verificar tipo de entrada e documentos"), None)
    if node_tipo_entrada:
        code = node_tipo_entrada["parameters"]["jsCode"]
        if "senderPhone" not in code:
            old_str = "const accountId = String(payload.account?.id ?? payload.account_id ?? '');"
            new_str = (
                "const accountId = String(payload.account?.id ?? payload.account_id ?? '');\n"
                "  const sender = conversation.meta?.sender ?? payload.sender ?? message.sender ?? {};\n"
                "  const senderPhone = String(sender.phone_number ?? sender.custom_attributes?.waha_whatsapp_chat_id ?? '').replace(/@c\\.us$/i, '');\n"
                "  const senderName = String(sender.name ?? '').trim();"
            )
            code = code.replace(old_str, new_str)
            old_ret = "attachmentCount: attachments.length,"
            new_ret = "senderPhone,\n    senderName,\n    attachmentCount: attachments.length,"
            code = code.replace(old_ret, new_ret)
            node_tipo_entrada["parameters"]["jsCode"] = code
            print(" -> Atualizado 'Verificar tipo de entrada e documentos' com senderPhone/senderName.")

    # 2. Criar os novos nós do PostgreSQL
    pg_cred = {
        "postgres": {
            "id": "WXVjpdoSEtoJGCvg",
            "name": "Postgres account"
        }
    }

    # Nó: Consultar Estado Permanente no PostgreSQL
    node_pg_check = {
        "parameters": {
            "operation": "executeQuery",
            "query": (
                "SELECT \n"
                "  COALESCE(cs.is_first_message, true) AS is_first_message,\n"
                "  COALESCE(cs.greeting_shown, false) AS greeting_shown,\n"
                "  COALESCE(cs.current_mode, 'fatec') AS current_mode,\n"
                "  COALESCE(cs.reset_count, 0) AS reset_count\n"
                "FROM (SELECT '{{ $('Verificar tipo de entrada e documentos').item.json.conversationId }}' AS cid) q\n"
                "LEFT JOIN fatec_conversation_state cs ON cs.conversation_id = q.cid;"
            ),
            "options": {}
        },
        "id": "pg-check-conv-state-001",
        "name": "Postgres — Consultar Estado Permanente",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [1650, 0],
        "credentials": pg_cred
    }

    # Nó: Gravar Boas-Vindas Enviada no PostgreSQL
    node_pg_save_welcome = {
        "parameters": {
            "operation": "executeQuery",
            "query": (
                "INSERT INTO fatec_conversation_state (conversation_id, sender_phone, sender_name, is_first_message, greeting_shown, current_mode, first_seen_at, last_seen_at)\n"
                "VALUES (\n"
                "  '{{ $('Verificar tipo de entrada e documentos').item.json.conversationId }}',\n"
                "  '{{ $('Verificar tipo de entrada e documentos').item.json.senderPhone }}',\n"
                "  '{{ $('Verificar tipo de entrada e documentos').item.json.senderName }}',\n"
                "  false,\n"
                "  true,\n"
                "  'fatec',\n"
                "  NOW(),\n"
                "  NOW()\n"
                ")\n"
                "ON CONFLICT (conversation_id) DO UPDATE SET\n"
                "  is_first_message = false,\n"
                "  greeting_shown = true,\n"
                "  last_seen_at = NOW();"
            ),
            "options": {}
        },
        "id": "pg-save-welcome-state-001",
        "name": "Postgres — Gravar Boas-Vindas Enviada",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [2700, -900],
        "credentials": pg_cred
    }

    # Nó: Resetar Estado Permanente no PostgreSQL
    node_pg_reset = {
        "parameters": {
            "operation": "executeQuery",
            "query": (
                "INSERT INTO fatec_conversation_state (conversation_id, sender_phone, sender_name, is_first_message, greeting_shown, current_mode, reset_count, last_reset_at, last_seen_at)\n"
                "VALUES (\n"
                "  '{{ $('Verificar tipo de entrada e documentos').item.json.conversationId }}',\n"
                "  '{{ $('Verificar tipo de entrada e documentos').item.json.senderPhone }}',\n"
                "  '{{ $('Verificar tipo de entrada e documentos').item.json.senderName }}',\n"
                "  true,\n"
                "  false,\n"
                "  'fatec',\n"
                "  1,\n"
                "  NOW(),\n"
                "  NOW()\n"
                ")\n"
                "ON CONFLICT (conversation_id) DO UPDATE SET\n"
                "  is_first_message = true,\n"
                "  greeting_shown = false,\n"
                "  current_mode = 'fatec',\n"
                "  reset_count = fatec_conversation_state.reset_count + 1,\n"
                "  last_reset_at = NOW(),\n"
                "  last_seen_at = NOW();"
            ),
            "options": {}
        },
        "id": "pg-reset-conv-state-001",
        "name": "Postgres — Resetar Estado Permanente",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [2700, 1000],
        "credentials": pg_cred
    }

    # Remover nós anteriores se já existirem
    nodes = [n for n in nodes if n["name"] not in [
        "Postgres — Consultar Estado Permanente",
        "Postgres — Gravar Boas-Vindas Enviada",
        "Postgres — Resetar Estado Permanente"
    ]]
    nodes.extend([node_pg_check, node_pg_save_welcome, node_pg_reset])
    wf["nodes"] = nodes

    # 3. Atualizar o nó 'Classificar comando'
    node_classificar = next((n for n in nodes if n.get("name") == "Classificar comando"), None)
    if node_classificar:
        node_classificar["parameters"]["jsCode"] = (
            "const prev = $('Liberar conteúdo textual para o agente').item.json ?? {};\n"
            "const docMeta = $('Verificar tipo de entrada e documentos').item.json ?? {};\n"
            "const text = String($json.contentText ?? prev.contentText ?? docMeta.contentText ?? '').trim();\n"
            "const conversationId = String($json.conversationId ?? prev.conversationId ?? docMeta.conversationId ?? '').trim();\n"
            "const messageId = String($json.messageId ?? prev.messageId ?? Date.now());\n"
            "const now = Date.now();\n\n"
            "// 1. Estado Permanente no PostgreSQL (Persistência no banco de dados)\n"
            "const pgState = $('Postgres — Consultar Estado Permanente').item?.json ?? {};\n"
            "const isFirstMessageInPostgres = pgState.is_first_message === true || pgState.greeting_shown === false;\n"
            "const pgCurrentMode = pgState.current_mode || 'fatec';\n\n"
            "// 2. Estado em Memória no Redis (para sessões ativas de submódulos)\n"
            "let stored = null;\n"
            "try {\n"
            "  const raw = $json.appMode;\n"
            "  stored = typeof raw === 'string' ? JSON.parse(raw) : (raw && typeof raw === 'object' ? raw : null);\n"
            "} catch { stored = null; }\n\n"
            "const validStoredSubmodule = stored && ['agenda', 'cardapio'].includes(stored.app) && typeof stored.sessionKey === 'string' && Number.isFinite(Number(stored.updatedAt)) && (now - Number(stored.updatedAt) >= 0) && (now - Number(stored.updatedAt) <= 15 * 60 * 1000);\n\n"
            "const hasAlreadyGreeted = !isFirstMessageInPostgres && Boolean(pgState.greeting_shown || (stored && stored.greeted));\n\n"
            "const normText = text.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase().replace(/[^a-z0-9/]+/g, ' ').trim();\n\n"
            "// Comandos explícitos de modo\n"
            "const isCardapioCommand = /^\\/cardapio(?:\\s|$)/i.test(text) || /^\\/menu(?:\\s|$)/i.test(text) || /^(cardapio|menu)$/i.test(normText);\n"
            "const isAgendaCommand = /^\\/agenda(?:\\s|$)/i.test(text) || /^(agenda|agendamento)$/i.test(normText);\n"
            "const isCancelCommand = /^\\/cancelar(?:\\s|$)/i.test(text) || /^(cancelar|parar)$/i.test(normText);\n"
            "const isClearContextCommand = /^\\/(?:limpar_contexto|limparcontexto|limpar|reset|reiniciar)(?:\\s|$)/i.test(text) || /^(limpar contexto|limpar conversa|reiniciar conversa|resetar)$/i.test(normText);\n\n"
            "const isPureFatecCommand = /^\\/fatec\\s*$/i.test(text) || /^(fatec|sair|voltar)$/i.test(normText) || /^(atendimento fatec|voltar pra fatec|voltar para fatec|falar com a fatec)$/i.test(normText);\n"
            "const isFatecWithQuery = /^\\/fatec\\s+(.+)/i.test(text);\n\n"
            "const isGreeting = /^(oi|ola|olá|bom dia|boa tarde|boa noite|e ai|e aí|opa|fala|tudo bem|tudo bom|salve|hello|hi)\\b/i.test(text) ||\n"
            "  /^(oi|ola|olá|bom dia|boa tarde|boa noite|e ai|e aí|opa|fala|tudo bem|tudo bom|salve|hello|hi)$/i.test(normText);\n\n"
            "let route = 'rag';\n"
            "let appSessionKey = null;\n"
            "let appModeValue = null;\n"
            "let routedText = text;\n"
            "const writeMode = (app, sessionKey, greeted = true) => JSON.stringify({ app, sessionKey, greeted, updatedAt: now });\n\n"
            "if (isClearContextCommand) {\n"
            "  route = 'clear_context';\n"
            "  appModeValue = null;\n"
            "} else if (isCancelCommand) {\n"
            "  route = 'cancel';\n"
            "} else if (isPureFatecCommand) {\n"
            "  route = 'fatec_welcome';\n"
            "  appModeValue = writeMode('fatec', null, true);\n"
            "} else if (isFatecWithQuery) {\n"
            "  route = 'rag';\n"
            "  routedText = text.replace(/^\\/fatec\\s+/i, '').trim();\n"
            "  appModeValue = writeMode('fatec', null, true);\n"
            "} else if (isCardapioCommand) {\n"
            "  route = 'cardapio';\n"
            "  appSessionKey = 'cardapio:' + conversationId + ':' + now;\n"
            "  appModeValue = writeMode('cardapio', appSessionKey, true);\n"
            "} else if (isAgendaCommand) {\n"
            "  route = 'agenda';\n"
            "  appSessionKey = 'agenda:' + conversationId + ':' + now;\n"
            "  appModeValue = writeMode('agenda', appSessionKey, true);\n"
            "} else if (validStoredSubmodule) {\n"
            "  route = stored.app;\n"
            "  appSessionKey = stored.sessionKey;\n"
            "  appModeValue = writeMode(stored.app, stored.sessionKey, true);\n"
            "} else if (isFirstMessageInPostgres || (isGreeting && !hasAlreadyGreeted)) {\n"
            "  // REGRA PERMANENTE NO POSTGRESQL: PRIMEIRA MENSAGEM OU SAUDAÇÃO SEM APRESENTAÇÃO\n"
            "  route = 'fatec_welcome';\n"
            "  appModeValue = writeMode('fatec', null, true);\n"
            "} else {\n"
            "  route = 'rag';\n"
            "  appModeValue = writeMode('fatec', null, true);\n"
            "}\n\n"
            "return {\n"
            "  json: {\n"
            "    ...prev,\n"
            "    ...$json,\n"
            "    contentText: routedText,\n"
            "    route,\n"
            "    appSessionKey,\n"
            "    appModeValue,\n"
            "    isFirstMessageInPostgres,\n"
            "    greetingShownInPostgres: Boolean(pgState.greeting_shown)\n"
            "  }\n"
            "};"
        )
        print(" -> Atualizado 'Classificar comando' com verificação de estado permanente no Postgres.")

    # 4. Atualizar as Conexões do Workflow
    # A: Saída de 'Verificar limite de texto' (índice 1 = falso / dentro do limite) -> conecta em 'Postgres — Consultar Estado Permanente'
    connections["Verificar limite de texto"]["main"][1] = [
        {"node": "Postgres — Consultar Estado Permanente", "type": "main", "index": 0}
    ]

    # B: 'Postgres — Consultar Estado Permanente' -> conecta em 'Redis — ler aplicação ativa'
    connections["Postgres — Consultar Estado Permanente"] = {
        "main": [
            [{"node": "Redis — ler aplicação ativa", "type": "main", "index": 0}]
        ]
    }

    # C: Limpar nós de Postgres da saída 3 (Cancelar) se foram colocados por engano
    connections["Roteador de comandos"]["main"][3] = [
        c for c in connections["Roteador de comandos"]["main"][3]
        if "Postgres" not in c["node"]
    ]

    # D: 'Roteador de comandos' saída 4 ('Boas-vindas Fatec' / index 4) -> adiciona 'Postgres — Gravar Boas-Vindas Enviada'
    welcome_branch = [c for c in connections["Roteador de comandos"]["main"][4] if "Postgres" not in c["node"]]
    welcome_branch.append({"node": "Postgres — Gravar Boas-Vindas Enviada", "type": "main", "index": 0})
    connections["Roteador de comandos"]["main"][4] = welcome_branch

    # E: 'Roteador de comandos' saída 5 ('Limpar Contexto' / index 5) -> adiciona 'Postgres — Resetar Estado Permanente'
    clear_branch = [c for c in connections["Roteador de comandos"]["main"][5] if "Postgres" not in c["node"]]
    clear_branch.append({"node": "Postgres — Resetar Estado Permanente", "type": "main", "index": 0})
    connections["Roteador de comandos"]["main"][5] = clear_branch

    wf["connections"] = connections

    with open(WF_FILE, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)

    print(f"[SUCESSO] Workflow {WF_FILE} atualizado e corrigido com conexões precisas!")

if __name__ == "__main__":
    apply_postgres_state()
