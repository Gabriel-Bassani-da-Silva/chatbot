import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

wf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows", "Agente RAG Fatec.json")
with open(wf_path, "r", encoding="utf-8") as f:
    wf = json.load(f)

# 1. Resposta de boas-vindas Fatec
intro_text = (
    "🏛️ *Assistente Virtual Inteligente*\\n"
    "Projeto de TCC de *Gabriel Bassani da Silva* (Big Data no Agronegócio — Fatec Bebedouro).\\n\\n"
    "Olá! Seja bem-vindo!\\n"
    "Este assistente virtual demonstra uma arquitetura avançada de IA generativa multimodal (texto e voz 24/7). Embora tenha sido desenvolvido com foco inicial na *Fatec Bebedouro* como caso de estudo acadêmico, esta solução é totalmente versátil e personalizável para diversos outros cenários do mercado — como atendimento comercial a clientes, suporte a vendas, pedidos e agendamentos corporativos.\\n\\n"
    "*Comandos e Demonstrações Disponíveis:*\\n"
    "• 🏛️ */fatec:* Atendimento acadêmico (cursos, vestibular, estágio supervisionado e secretaria)\\n"
    "• 🍔 */cardapio:* Atendimento comercial com pedidos, carrinho e registro em planilha (Google Sheets)\\n"
    "• 📅 */agenda:* Agendamento de consultas e serviços com verificação de disponibilidade (Google Calendar)\\n"
    "• ❌ */cancelar:* Cancela um pedido ou agendamento em andamento e retorna ao modo principal\\n\\n"
    "Como posso te ajudar hoje?"
)

# 2. Resposta de contexto limpo (sem emoji)
clear_text = "*Contexto reiniciado com sucesso!*\\n\\nComo posso te ajudar hoje?"

for n in wf["nodes"]:
    if n["name"] == "Resposta de boas-vindas Fatec":
        n["parameters"]["jsCode"] = f"return {{\n  json: {{\n    output: '{intro_text}'\n  }}\n}};"
        print("Updated 'Resposta de boas-vindas Fatec'")
    elif n["name"] == "Resposta de contexto limpo":
        n["parameters"]["jsCode"] = f"return {{\n  json: {{\n    output: '{clear_text}'\n  }}\n}};"
        print("Updated 'Resposta de contexto limpo'")

with open(wf_path, "w", encoding="utf-8") as f:
    json.dump(wf, f, ensure_ascii=False, indent=2)

print("Saved workflow successfully.")
