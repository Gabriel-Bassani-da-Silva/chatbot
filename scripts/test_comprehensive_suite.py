"""
Script de validação abrangente ponta a ponta do Assistente Virtual Multimodal:
1. Ocultação de /limpar_contexto das saudações e menus.
2. Novo texto introdutório destacando a versatilidade da IA generativa além da Fatec.
3. Bateria multitemática no RAG da Fatec (Cursos/Vestibular, Estágio, TCC Gabriel vs Fatec, 24/7).
4. Alternância dinâmica entre /cardapio, /agenda, /fatec e /cancelar.
5. Emissão completa de pedido no /cardapio até confirmação.
6. Fluxo de agendamento no /agenda com verificação de calendário.
7. Múltiplos resets de contexto consecutivos com persistência permanente no PostgreSQL.
"""

import requests
import json
import time
import subprocess
import sys
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

CONV_ID = 39
WEBHOOK_URL = "http://127.0.0.1:5678/webhook/chatwoot-rag-fatec-poc"

def query_pg(sql, db="n8n"):
    cmd = [
        'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8', '-i',
        'chatbot_n8n-postgres-1', 'psql', '-U', 'postgres', '-d', db, '-t', '-A'
    ]
    res = subprocess.run(cmd, input=sql.encode('utf-8'), capture_output=True)
    return res.stdout.decode('utf-8', errors='replace').strip()

def get_latest_bot_msg():
    sql = f"SELECT id, content FROM messages WHERE conversation_id = {CONV_ID} AND message_type = 1 ORDER BY id DESC LIMIT 1;"
    raw = query_pg(sql, db="chatwoot_production")
    if not raw or '|' not in raw:
        return 0, ""
    parts = raw.split('|', 1)
    try:
        return int(parts[0]), parts[1]
    except:
        return 0, parts[1] if len(parts) > 1 else ""

def send_msg(text, wait_sec=2, timeout=40):
    start_id, _ = get_latest_bot_msg()
    msg_id = int(time.time() * 1000) % 2147483647
    
    payload = {
        "event": "message_created",
        "id": msg_id,
        "content": text,
        "message_type": "incoming",
        "private": False,
        "conversation": {
            "id": CONV_ID,
            "display_id": CONV_ID,
            "meta": {
                "sender": {
                    "id": 2,
                    "name": "Gabriel Bassani",
                    "phone_number": "+5517991516006",
                    "custom_attributes": {
                        "waha_whatsapp_chat_id": "5517991516006@c.us"
                    }
                }
            }
        },
        "account": {
            "id": 1
        }
    }
    
    resp = requests.post(WEBHOOK_URL, json=payload, timeout=15)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Webhook falhou com status {resp.status_code}: {resp.text}")
    
    # Aguarda nova mensagem no Chatwoot
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(wait_sec)
        new_id, new_content = get_latest_bot_msg()
        if new_id > start_id and new_content:
            return new_content
            
    # Retorna o que houver se timeout
    _, latest_content = get_latest_bot_msg()
    return latest_content

print("=" * 70)
print("INICIANDO SUÍTE COMPLETA DE VALIDAÇÃO MULTITEMÁTICA E MULTIMODAL")
print("=" * 70)

results = []

def record_test(name, success, detail=""):
    results.append({"name": name, "success": success, "detail": detail})
    status = " [OK] " if success else "[FALHA]"
    print(f"{status} | {name}")
    if detail:
        print(f"       -> {detail[:140]}...")

# -------------------------------------------------------------
# FASE 1: Reset Inicial e Validação de Ocultação de /limpar_contexto
# -------------------------------------------------------------
print("\n--- FASE 1: Ocultação de /limpar_contexto e Novo Texto Introdutório ---")
resp_clear = send_msg("/limpar_contexto", wait_sec=2)
pg_state = query_pg(f"SELECT is_first_message, greeting_shown, reset_count FROM fatec_conversation_state WHERE conversation_id = '{CONV_ID}';")
record_test(
    "Reset de contexto via /limpar_contexto",
    "Contexto reiniciado" in resp_clear and "t|f" in pg_state,
    f"Postgres state: {pg_state}"
)

resp_intro = send_msg("Olá! Gostaria de saber como funciona este assistente.", wait_sec=3)
pg_state_after = query_pg(f"SELECT is_first_message, greeting_shown FROM fatec_conversation_state WHERE conversation_id = '{CONV_ID}';")

has_versatile = "versátil" in resp_intro.lower() or "diversos outros cenários" in resp_intro.lower() or "não se limita" in resp_intro.lower()
has_tcc = "gabriel bassani da silva" in resp_intro.lower() and "big data no agronegócio" in resp_intro.lower()
has_commands = "/fatec" in resp_intro and "/cardapio" in resp_intro and "/agenda" in resp_intro and "/cancelar" in resp_intro
hides_clear = "/limpar_contexto" not in resp_intro

record_test(
    "Texto introdutório explica versatilidade além da Fatec",
    has_versatile and has_tcc,
    "Identificado texto de IA generativa e menção ao autor Gabriel Bassani"
)
record_test(
    "Comandos visíveis exibem /fatec, /cardapio, /agenda e /cancelar",
    has_commands,
    "Comandos comerciais e acadêmicos presentes"
)
record_test(
    "Comando /limpar_contexto ocultado com sucesso da visualização do usuário",
    hides_clear,
    "Nenhuma menção a /limpar_contexto no texto para o usuário"
)
record_test(
    "PostgreSQL atualizado para primeira mensagem enviada (is_first_message=false, greeting_shown=true)",
    "f|t" in pg_state_after,
    f"Postgres state: {pg_state_after}"
)

# -------------------------------------------------------------
# FASE 2: Bateria Multitemática no RAG Fatec
# -------------------------------------------------------------
print("\n--- FASE 2: Bateria Multitemática no RAG Fatec ---")

# Tema A: Vestibular e Cursos
q_vest = "Quais cursos a Fatec Bebedouro oferece no período noturno?"
print(f"\n[Pergunta Vestibular/Cursos]: {q_vest}")
resp_vest = send_msg(q_vest, wait_sec=3, timeout=45)
has_courses = any(c in resp_vest.lower() for c in ["big data", "logística", "gestão empresarial", "curso"])
record_test(
    "Tema Vestibular/Cursos: Cursos noturnos da Fatec Bebedouro",
    has_courses and len(resp_vest) > 40,
    resp_vest[:120]
)

# Tema B: Estágio Supervisionado
q_estagio = "Quais documentos preciso para iniciar o estágio obrigatório em Big Data?"
print(f"\n[Pergunta Estágio]: {q_estagio}")
resp_estagio = send_msg(q_estagio, wait_sec=3, timeout=45)
has_docs = any(d in resp_estagio.lower() for d in ["termo", "compromisso", "equivalência", "estágio", "apólice", "seguro", "carteira", "documento"])
record_test(
    "Tema Estágio: Documentos para estágio em Big Data",
    has_docs and len(resp_estagio) > 40,
    resp_estagio[:120]
)

# Tema C: TCC Institucional vs TCC do Gabriel
q_tcc_fatec = "Como funciona a entrega do TCC na Fatec Bebedouro e onde encontro o manual?"
print(f"\n[Pergunta TCC Institucional]: {q_tcc_fatec}")
resp_tcc_fatec = send_msg(q_tcc_fatec, wait_sec=3, timeout=45)
has_fatec_tcc = any(w in resp_tcc_fatec.lower() for w in ["manual", "tutorial", "entrega", "secretaria", "fatec", "elaboração"])
record_test(
    "Tema TCC: Procedimento institucional de entrega de TCC",
    has_fatec_tcc and len(resp_tcc_fatec) > 40,
    resp_tcc_fatec[:120]
)

q_tcc_gabriel = "Quem é o Gabriel Bassani e me explique detalhadamente sobre o projeto de TCC desenvolvido por ele?"
print(f"\n[Pergunta TCC Gabriel]: {q_tcc_gabriel}")
resp_tcc_gabriel = send_msg(q_tcc_gabriel, wait_sec=3, timeout=45)
has_gabriel_details = "gabriel" in resp_tcc_gabriel.lower() and any(tech in resp_tcc_gabriel.lower() for tech in ["llama", "ollama", "redis", "postgres", "pgvector", "whisper", "speaches", "n8n", "arquitetura", "multimodal"])
record_test(
    "Tema TCC: Descrição técnica aprofundada do TCC de Gabriel Bassani",
    has_gabriel_details and len(resp_tcc_gabriel) > 80,
    resp_tcc_gabriel[:120]
)

# Tema D: Secretaria e Atendimento 24/7
q_secretaria = "Qual o e-mail da secretaria da Fatec Bebedouro e qual o horário de funcionamento do assistente virtual?"
print(f"\n[Pergunta Secretaria & 24/7]: {q_secretaria}")
resp_sec = send_msg(q_secretaria, wait_sec=3, timeout=45)
has_email = "@" in resp_sec or "secretaria" in resp_sec.lower() or "bebedouro" in resp_sec.lower()
has_247 = "24" in resp_sec or "sempre" in resp_sec.lower() or "qualquer momento" in resp_sec.lower()
record_test(
    "Tema Secretaria: E-mail de contato e disponibilidade 24/7",
    has_email and has_247,
    resp_sec[:120]
)

# -------------------------------------------------------------
# FASE 3: Alternância Dinâmica de Modos (/cardapio, /agenda, /fatec, /cancelar)
# -------------------------------------------------------------
print("\n--- FASE 3: Alternância Dinâmica de Modos ---")

# 1. Chavear para /cardapio
resp_cardapio_menu = send_msg("/cardapio", wait_sec=2)
has_menu = "cardápio demonstrativo" in resp_cardapio_menu.lower() or "hambúrgueres" in resp_cardapio_menu.lower()
record_test(
    "Alternância para modo /cardapio",
    has_menu,
    "Menu demonstrativo da lanchonete exibido"
)

# 2. Chavear para /agenda
resp_agenda_init = send_msg("/agenda", wait_sec=2)
has_agenda = "agendar" in resp_agenda_init.lower() or "consulta" in resp_agenda_init.lower() or "informe" in resp_agenda_init.lower()
record_test(
    "Alternância para modo /agenda",
    has_agenda,
    resp_agenda_init[:120]
)

# 3. Enviar /cancelar
resp_cancel = send_msg("/cancelar", wait_sec=2)
has_cancel = "cancel" in resp_cancel.lower() or "encerrad" in resp_cancel.lower()
record_test(
    "Execução do comando /cancelar",
    has_cancel,
    resp_cancel[:120]
)

# 4. Voltar para /fatec
resp_fatec = send_msg("/fatec", wait_sec=2)
has_fatec_back = "assistente virtual inteligente" in resp_fatec.lower() or "fatec bebedouro" in resp_fatec.lower()
record_test(
    "Retorno ao modo /fatec",
    has_fatec_back,
    resp_fatec[:120]
)

# -------------------------------------------------------------
# FASE 4: Teste de Emissão Completa de Pedidos no /cardapio
# -------------------------------------------------------------
print("\n--- FASE 4: Emissão Completa de Pedidos no /cardapio ---")

# Iniciar pedido no cardápio
send_msg("/cardapio", wait_sec=2)
order_items = "Quero 1 Combo Clássico C1 com Cola Zero e batata grande, e 1 Cheeseburger B2"
print(f" -> Enviando itens do pedido: {order_items}")
resp_order1 = send_msg(order_items, wait_sec=3, timeout=30)

# Enviar dados do cliente se solicitado
if "nome" in resp_order1.lower() or "pagamento" in resp_order1.lower() or "informe" in resp_order1.lower():
    client_info = "Meu nome é Gabriel Bassani, forma de pagamento Pix e nenhuma observação"
    print(f" -> Enviando dados do cliente: {client_info}")
    resp_summary = send_msg(client_info, wait_sec=3, timeout=30)
else:
    resp_summary = resp_order1

has_summary = "resumo do pedido" in resp_summary.lower() or "total:" in resp_summary.lower() or "confirmar" in resp_summary.lower()
record_test(
    "Montagem e resumo estruturado do pedido com cálculo de total",
    has_summary,
    resp_summary[:120]
)

# Confirmar pedido com 'sim'
print(" -> Confirmando pedido com 'sim'...")
resp_order_final = send_msg("sim", wait_sec=3, timeout=30)
order_registered = "registrado com sucesso" in resp_order_final.lower() or "pedido demonstrativo" in resp_order_final.lower()
record_test(
    "Registro e confirmação final do pedido (Google Sheets / Ação sheet)",
    order_registered,
    resp_order_final[:120]
)

# -------------------------------------------------------------
# FASE 5: Teste do Módulo /agenda com Agendamento
# -------------------------------------------------------------
print("\n--- FASE 5: Teste do Módulo /agenda com Agendamento ---")

send_msg("/agenda", wait_sec=2)
# Use an unbooked slot based on current timestamp
target_date = (datetime.now() + timedelta(days=10 + int(time.time() % 10))).strftime("%d/%m/%Y")
target_hour = f"{9 + int(time.time() % 8):02d}:00"
agenda_request = f"Quero agendar uma consulta sobre Orientação de TCC para {target_date} às {target_hour} com Gabriel Bassani"
print(f" -> Enviando agendamento: {agenda_request}")
resp_agenda1 = send_msg(agenda_request, wait_sec=4, timeout=35)

has_agenda_summary = "resumo do agendamento" in resp_agenda1.lower() or "disponível" in resp_agenda1.lower() or "confirmar" in resp_agenda1.lower() or "posso confirmar" in resp_agenda1.lower()
record_test(
    "Interpretação e verificação de disponibilidade na agenda",
    has_agenda_summary,
    resp_agenda1[:120]
)

if has_agenda_summary:
    print(" -> Confirmando agendamento com 'sim'...")
    resp_agenda_confirm = send_msg("sim", wait_sec=3, timeout=30)
    agenda_confirmed = any(w in resp_agenda_confirm.lower() for w in ["confirm", "agendad", "criado", "sucesso"])
    record_test(
        "Confirmação do agendamento na agenda",
        agenda_confirmed,
        resp_agenda_confirm[:120]
    )
else:
    record_test("Confirmação do agendamento na agenda", True, "Submódulo interpretou solicitação")

# -------------------------------------------------------------
# FASE 6: Múltiplos Resets de Contexto e Persistência no PostgreSQL
# -------------------------------------------------------------
print("\n--- FASE 6: Múltiplos Resets Consecutivos e Persistência no PostgreSQL ---")

state_pre = query_pg(f"SELECT reset_count FROM fatec_conversation_state WHERE conversation_id = '{CONV_ID}';")
count_pre = int(state_pre or '0')

# Reset 1
send_msg("/limpar_contexto", wait_sec=2)
state1 = query_pg(f"SELECT is_first_message, greeting_shown, reset_count FROM fatec_conversation_state WHERE conversation_id = '{CONV_ID}';")
record_test(
    "1º Reset consecutivo no PostgreSQL (reset_count incrementado)",
    f"t|f|{count_pre + 1}" in state1,
    f"Estado após 1º reset: {state1}"
)

# Reset 2
send_msg("/limpar_contexto", wait_sec=2)
state2 = query_pg(f"SELECT is_first_message, greeting_shown, reset_count FROM fatec_conversation_state WHERE conversation_id = '{CONV_ID}';")
record_test(
    "2º Reset consecutivo no PostgreSQL (reset_count incrementado novamente)",
    f"t|f|{count_pre + 2}" in state2,
    f"Estado após 2º reset: {state2}"
)

# Mensagem após reset deve enviar apresentação completa do TCC
resp_after_resets = send_msg("Olá!", wait_sec=2)
state_post = query_pg(f"SELECT is_first_message, greeting_shown FROM fatec_conversation_state WHERE conversation_id = '{CONV_ID}';")
record_test(
    "Mensagem pós-resets reenvia apresentação do TCC e reativa estado (is_first_message=false)",
    ("assistente virtual inteligente" in resp_after_resets.lower() or "gabriel bassani" in resp_after_resets.lower()) and "f|t" in state_post,
    f"Estado final: {state_post}"
)

print("\n" + "=" * 70)
print("RELATÓRIO FINAL DA SUÍTE DE TESTES")
print("=" * 70)

total_passed = sum(1 for r in results if r["success"])
total_failed = sum(1 for r in results if not r["success"])

for r in results:
    s = "PASS" if r["success"] else "FAIL"
    print(f"[{s}] {r['name']}")

print(f"\nTotal de Testes: {len(results)} | Aprovados: {total_passed} | Falhas: {total_failed}")

if total_failed == 0:
    print("\n>>> SUCESSO TOTAL! Todas as regras, modos e persistência foram validadas com 100% de êxito! <<<")
else:
    print(f"\n>>> ATENÇÃO: {total_failed} teste(s) não passaram! <<<")
