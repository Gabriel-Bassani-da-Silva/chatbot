"""
Script para implementar o Buffer Agregador com Janela de Debounce no n8n (Agente RAG Fatec.json).
Solução para mensagens consecutivas/picadas (2 a 5 segundos) no WhatsApp.
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

WF_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows", "Agente RAG Fatec.json")

def apply_debounce_buffer():
    with open(WF_PATH, "r", encoding="utf-8") as f:
        wf = json.load(f)

    nodes = wf["nodes"]
    connections = wf["connections"]

    pg_cred = {
        "postgres": {
            "id": "WXVjpdoSEtoJGCvg",
            "name": "Postgres account"
        }
    }

    # 1. Nó: Verificar se Comando Imediato (IF bypass para /cancelar ou /limpar_contexto)
    node_bypass_check = {
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": False,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 2
                },
                "conditions": [
                    {
                        "leftValue": "={{ String($json.contentText || '').trim() }}",
                        "operator": {
                            "type": "string",
                            "operation": "regex"
                        },
                        "rightValue": "^/(?:cancelar|limpar_contexto|limpar|reset|reiniciar)\\b"
                    }
                ],
                "combinator": "or"
            },
            "options": {}
        },
        "id": "debounce-check-bypass-001",
        "name": "Verificar se comando imediato",
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [1560, 0]
    }

    # 2. Nó: Salvar no Buffer do PostgreSQL
    node_save_buffer = {
        "parameters": {
            "operation": "executeQuery",
            "query": (
                "INSERT INTO fatec_message_buffer (conversation_id, message_id, content_text)\n"
                "VALUES (\n"
                "  '{{ $json.conversationId }}',\n"
                "  '{{ $json.messageId }}',\n"
                "  '{{ $json.contentText.replace(/'/g, \"''\") }}'\n"
                ")\n"
                "RETURNING id;"
            ),
            "options": {}
        },
        "id": "debounce-save-buffer-001",
        "name": "Postgres — Salvar Mensagem no Buffer",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [1760, 100],
        "credentials": pg_cred
    }

    # 3. Nó: Aguardar Janela de Digitação (Wait de 3.5 segundos)
    node_wait_typing = {
        "parameters": {
            "resume": "timeInterval",
            "amount": 3.5,
            "unit": "seconds"
        },
        "id": "debounce-wait-typing-001",
        "name": "Aguardar janela de digitação",
        "type": "n8n-nodes-base.wait",
        "typeVersion": 1.1,
        "position": [1960, 100],
        "webhookId": "debounce-wait-webhook-001"
    }

    # 4. Nó: Checar se houve mensagem mais nova
    node_check_latest = {
        "parameters": {
            "operation": "executeQuery",
            "query": (
                "SELECT \n"
                "  COALESCE(MAX(id), 0) AS max_id,\n"
                "  {{ $('Postgres — Salvar Mensagem no Buffer').item.json.id }} AS my_id\n"
                "FROM fatec_message_buffer\n"
                "WHERE conversation_id = '{{ $('Verificar tipo de entrada e documentos').item.json.conversationId }}';"
            ),
            "options": {}
        },
        "id": "debounce-check-latest-001",
        "name": "Postgres — Checar Última Mensagem",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [2160, 100],
        "credentials": pg_cred
    }

    # 5. Nó: Decidir se Janela Fechou (se max_id > my_id, encerra em silêncio)
    node_decide_window = {
        "parameters": {
            "jsCode": (
                "const items = $input.all();\n"
                "const item = items[0]?.json || {};\n"
                "const maxId = Number(item.max_id || 0);\n"
                "const myId = Number(item.my_id || 0);\n\n"
                "// Se maxId > myId, uma mensagem mais recente chegou enquanto esperávamos.\n"
                "// Esta execução encerra silenciosamente; a mais recente responderá tudo.\n"
                "if (maxId > myId) {\n"
                "  return [];\n"
                "}\n\n"
                "// Nenhuma mensagem nova chegou. Esta execução consolida o buffer!\n"
                "return items;"
            )
        },
        "id": "debounce-decide-window-001",
        "name": "Decidir se janela fechou",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [2360, 100]
    }

    # 6. Nó: Consolidar e Limpar Buffer (Deleta tudo e retorna string_agg em ordem de chegada)
    node_consolidate_buffer = {
        "parameters": {
            "operation": "executeQuery",
            "query": (
                "WITH deleted AS (\n"
                "  DELETE FROM fatec_message_buffer\n"
                "  WHERE conversation_id = '{{ $('Verificar tipo de entrada e documentos').item.json.conversationId }}'\n"
                "  RETURNING id, content_text\n"
                ")\n"
                "SELECT \n"
                "  COALESCE(string_agg(content_text, E'\\n' ORDER BY id ASC), '') AS combined_text,\n"
                "  count(*) AS message_count\n"
                "FROM deleted;"
            ),
            "options": {}
        },
        "id": "debounce-consolidate-buffer-001",
        "name": "Postgres — Consolidar e Limpar Buffer",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [2560, 100],
        "credentials": pg_cred
    }

    # 7. Nó: Aplicar Texto Consolidado ao Payload
    node_apply_consolidated = {
        "parameters": {
            "mode": "runOnceForEachItem",
            "jsCode": (
                "const original = $('Liberar conteúdo textual para o agente').item.json ?? {};\n"
                "const docMeta = $('Verificar tipo de entrada e documentos').item.json ?? {};\n"
                "const combined = String($json.combined_text || original.contentText || docMeta.contentText || '').trim();\n"
                "const messageCount = Number($json.message_count || 1);\n\n"
                "return {\n"
                "  json: {\n"
                "    ...docMeta,\n"
                "    ...original,\n"
                "    contentText: combined,\n"
                "    userTextChars: Array.from(combined).length,\n"
                "    aggregatedMessagesCount: messageCount\n"
                "  }\n"
                "};"
            )
        },
        "id": "debounce-apply-text-001",
        "name": "Aplicar texto consolidado",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [2760, 100]
    }

    # Limpar nós de debounce anteriores se já existirem
    debounce_node_names = [
        "Verificar se comando imediato",
        "Postgres — Salvar Mensagem no Buffer",
        "Aguardar janela de digitação",
        "Postgres — Checar Última Mensagem",
        "Decidir se janela fechou",
        "Postgres — Consolidar e Limpar Buffer",
        "Aplicar texto consolidado"
    ]
    nodes = [n for n in nodes if n["name"] not in debounce_node_names]
    nodes.extend([
        node_bypass_check,
        node_save_buffer,
        node_wait_typing,
        node_check_latest,
        node_decide_window,
        node_consolidate_buffer,
        node_apply_consolidated
    ])
    wf["nodes"] = nodes

    # Reconfigurar conexões:
    # A. Saída 1 de 'Verificar limite de texto' (dentro do limite) -> conecta em 'Verificar se comando imediato'
    connections["Verificar limite de texto"]["main"][1] = [
        {"node": "Verificar se comando imediato", "type": "main", "index": 0}
    ]

    # B. 'Verificar se comando imediato':
    #    Output 0 (True = Comando imediato / bypass): vai direto para 'Postgres — Consultar Estado Permanente'
    #    Output 1 (False = Mensagem normal / buffer): vai para 'Postgres — Salvar Mensagem no Buffer'
    connections["Verificar se comando imediato"] = {
        "main": [
            [{"node": "Postgres — Consultar Estado Permanente", "type": "main", "index": 0}],
            [{"node": "Postgres — Salvar Mensagem no Buffer", "type": "main", "index": 0}]
        ]
    }

    # C. 'Postgres — Salvar Mensagem no Buffer' -> 'Aguardar janela de digitação'
    connections["Postgres — Salvar Mensagem no Buffer"] = {
        "main": [
            [{"node": "Aguardar janela de digitação", "type": "main", "index": 0}]
        ]
    }

    # D. 'Aguardar janela de digitação' -> 'Postgres — Checar Última Mensagem'
    connections["Aguardar janela de digitação"] = {
        "main": [
            [{"node": "Postgres — Checar Última Mensagem", "type": "main", "index": 0}]
        ]
    }

    # E. 'Postgres — Checar Última Mensagem' -> 'Decidir se janela fechou'
    connections["Postgres — Checar Última Mensagem"] = {
        "main": [
            [{"node": "Decidir se janela fechou", "type": "main", "index": 0}]
        ]
    }

    # F. 'Decidir se janela fechou' -> 'Postgres — Consolidar e Limpar Buffer'
    connections["Decidir se janela fechou"] = {
        "main": [
            [{"node": "Postgres — Consolidar e Limpar Buffer", "type": "main", "index": 0}]
        ]
    }

    # G. 'Postgres — Consolidar e Limpar Buffer' -> 'Aplicar texto consolidado'
    connections["Postgres — Consolidar e Limpar Buffer"] = {
        "main": [
            [{"node": "Aplicar texto consolidado", "type": "main", "index": 0}]
        ]
    }

    # H. 'Aplicar texto consolidado' -> 'Postgres — Consultar Estado Permanente'
    connections["Aplicar texto consolidado"] = {
        "main": [
            [{"node": "Postgres — Consultar Estado Permanente", "type": "main", "index": 0}]
        ]
    }

    wf["connections"] = connections

    with open(WF_PATH, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)

    print(f"[SUCESSO] Workflow {WF_PATH} atualizado com Buffer Agregador e Janela de Debounce!")

if __name__ == "__main__":
    apply_debounce_buffer()
