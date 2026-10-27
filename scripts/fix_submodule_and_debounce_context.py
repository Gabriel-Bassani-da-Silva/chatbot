import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

wf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows", "Agente RAG Fatec.json")
with open(wf_path, "r", encoding="utf-8") as f:
    wf = json.load(f)

# 1. Corrigir nó 'Redis — ler aplicação ativa' para usar conversationId do nó 'Verificar tipo de entrada e documentos'
for n in wf["nodes"]:
    if n["name"] == "Redis — ler aplicação ativa":
        n["parameters"]["key"] = "={{ 'n8n:demo:chat:mode:' + $('Verificar tipo de entrada e documentos').item.json.conversationId }}"
        print("Updated 'Redis — ler aplicação ativa' key!")
        
    elif n["name"] == "Postgres — Consultar Estado Permanente":
        # Incluir conversation_id no SELECT para enriquecer o json
        query = (
            "SELECT \n"
            "  q.cid AS conversation_id,\n"
            "  COALESCE(cs.is_first_message, true) AS is_first_message,\n"
            "  COALESCE(cs.greeting_shown, false) AS greeting_shown,\n"
            "  COALESCE(cs.current_mode, 'fatec') AS current_mode,\n"
            "  COALESCE(cs.reset_count, 0) AS reset_count\n"
            "FROM (SELECT '{{ $('Verificar tipo de entrada e documentos').item.json.conversationId }}' AS cid) q\n"
            "LEFT JOIN fatec_conversation_state cs ON cs.conversation_id = q.cid;"
        )
        n["parameters"]["query"] = query
        print("Updated 'Postgres — Consultar Estado Permanente' query!")

    elif n["name"] == "Classificar comando":
        old_code = n["parameters"]["jsCode"]
        new_header = (
            "const prev = $('Liberar conteúdo textual para o agente').item.json ?? {};\n"
            "const docMeta = $('Verificar tipo de entrada e documentos').item.json ?? {};\n"
            "let consolidated = {};\n"
            "try { consolidated = $('Aplicar texto consolidado').item.json ?? {}; } catch {}\n"
            "const text = String(consolidated.contentText ?? $json.contentText ?? prev.contentText ?? docMeta.contentText ?? '').trim();\n"
            "const conversationId = String(consolidated.conversationId ?? $json.conversationId ?? prev.conversationId ?? docMeta.conversationId ?? '').trim();\n"
            "const messageId = String(consolidated.messageId ?? $json.messageId ?? prev.messageId ?? Date.now());\n"
            "const now = Date.now();"
        )
        
        target = (
            "const prev = $('Liberar conteúdo textual para o agente').item.json ?? {};\n"
            "const docMeta = $('Verificar tipo de entrada e documentos').item.json ?? {};\n"
            "const text = String($json.contentText ?? prev.contentText ?? docMeta.contentText ?? '').trim();\n"
            "const conversationId = String($json.conversationId ?? prev.conversationId ?? docMeta.conversationId ?? '').trim();\n"
            "const messageId = String($json.messageId ?? prev.messageId ?? Date.now());\n"
            "const now = Date.now();"
        )
        
        if target in old_code:
            n["parameters"]["jsCode"] = old_code.replace(target, new_header)
            print("Updated 'Classificar comando' to read consolidated text and valid conversationId!")
        else:
            print("Target header in 'Classificar comando' not matched exactly; check manually.")

with open(wf_path, "w", encoding="utf-8") as f:
    json.dump(wf, f, ensure_ascii=False, indent=2)

print("Saved workflow changes.")
