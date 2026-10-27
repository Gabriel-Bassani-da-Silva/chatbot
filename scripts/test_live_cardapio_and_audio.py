import requests
import json
import time
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

CONV_ID = 39
WEBHOOK_URL = "http://127.0.0.1:5678/webhook/chatwoot-rag-fatec-poc"
REDIS_PASS = "f81a34c353b25e714182ab9345737beec9630d4380d9c6106f34c1afa33a6f8c"

def get_latest_chatwoot_msg():
    cmd = [
        'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8', 'chatbot_n8n-postgres-1',
        'psql', '-U', 'postgres', '-d', 'chatwoot_production', '-t', '-A',
        '-c', f"SELECT id, message_type, content FROM messages WHERE conversation_id = {CONV_ID} ORDER BY id DESC LIMIT 1;"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    raw = res.stdout.strip()
    if not raw or '|' not in raw:
        return 0, 0, ""
    parts = raw.split('|', 2)
    mid = int(parts[0])
    mtype = int(parts[1])
    content = parts[2] if len(parts) > 2 else ""
    return mid, mtype, content

def get_redis_mode():
    cmd = ['docker', 'exec', 'chatbot_n8n-redis-1', 'redis-cli', '-a', REDIS_PASS, 'GET', f'n8n:demo:chat:mode:{CONV_ID}']
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = res.stdout.strip()
    # Remove warning if present
    lines = [l for l in out.split('\n') if not l.startswith('Warning:')]
    return '\n'.join(lines).strip()

def send_chatwoot_message(text, timeout=35):
    last_id, _, _ = get_latest_chatwoot_msg()
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
    
    t0 = time.time()
    resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
    if resp.status_code != 200:
        raise Exception(f"Webhook returned {resp.status_code}: {resp.text}")
    
    # Wait for bot response in Chatwoot (message_type == 1 is outgoing/bot)
    deadline = t0 + timeout
    while time.time() < deadline:
        time.sleep(1.5)
        cur_id, cur_type, cur_content = get_latest_chatwoot_msg()
        if cur_id > last_id and cur_type == 1 and cur_content.strip():
            return cur_content, time.time() - t0
    
    raise TimeoutError(f"Bot did not reply within {timeout}s (last msg ID={last_id})")

def run_suite():
    print("=================================================================")
    print("  TESTE AO VIVO: FLUXO COMPLETO DO CARDÁPIO & CONTEXTO SUBMÓDULO")
    print("=================================================================\n")
    
    # Resetar chaves de controle no Redis para a conversa de teste
    for k in [f'chatwoot:ratelimit:conv:{CONV_ID}', f'chatwoot:infer_lock:conv:{CONV_ID}', f'chatwoot:audio_pending:conv:{CONV_ID}', f'chatwoot:buffer:conv:{CONV_ID}']:
        subprocess.run(['docker', 'exec', 'chatbot_n8n-redis-1', 'redis-cli', '-a', REDIS_PASS, 'DEL', k], capture_output=True)

    # STEP 1: Ativar /cardapio
    print("--- [PASSO 1] Enviando comando '/cardapio' ---")
    resp, elapsed = send_chatwoot_message("/cardapio")
    print(f"Tempo de resposta: {elapsed:.2f}s")
    print(f"Início da resposta: {resp[:120]}...\n")
    assert "CARDÁPIO DEMONSTRATIVO" in resp or "Lanchonete Exemplo" in resp, "Falha ao exibir o cardápio!"
    redis_mode = get_redis_mode()
    print(f"Modo no Redis: {redis_mode}\n")
    assert '"app":"cardapio"' in redis_mode, "Modo cardápio não ativado no Redis!"
    print(">>> PASSO 1: APROVADO! <<<\n")
    
    time.sleep(2)
    
    # STEP 2: Enviar pedido transcrito do áudio real do usuário
    user_audio_text = "Quero um cheeseburger junto com anel de cebola, quero um suco de laranja, quero com carne extra o meu hambúrguer e eu quero que tire tomate."
    print("--- [PASSO 2] Enviando texto do pedido real por voz ---")
    print(f"Mensagem do usuário: \"{user_audio_text}\"")
    resp, elapsed = send_chatwoot_message(user_audio_text, timeout=45)
    print(f"Tempo de resposta: {elapsed:.2f}s")
    print(f"Resposta do bot:\n{resp}\n")
    
    assert "Não posso atender a esse pedido" not in resp, "ERRO CRÍTICO: O bot recusou com resposta acadêmica da Fatec!"
    assert "Cheeseburger" in resp or "B2" in resp or "hambúrguer" in resp.lower(), "Cheeseburger não foi reconhecido!"
    assert "seu nome" in resp.lower() or "forma de pagamento" in resp.lower() or "cliente" in resp.lower(), "Não pediu dados do cliente!"
    print(">>> PASSO 2: APROVADO! O submódulo reteve o contexto com sucesso! <<<\n")
    
    time.sleep(2)
    
    # STEP 3: Enviar dados do cliente (Nome e Forma de Pagamento)
    client_info = "Meu nome é Gabriel Bassani e vou pagar no Pix"
    print("--- [PASSO 3] Enviando dados do cliente ---")
    print(f"Mensagem do usuário: \"{client_info}\"")
    resp, elapsed = send_chatwoot_message(client_info, timeout=45)
    print(f"Tempo de resposta: {elapsed:.2f}s")
    print(f"Resposta do bot:\n{resp}\n")
    
    assert "Gabriel" in resp, "Nome do cliente não incluído no resumo!"
    assert "Pix" in resp, "Forma de pagamento Pix não incluída no resumo!"
    assert "Total" in resp or "TOTAL" in resp or "R$" in resp, "Total do pedido não calculado!"
    assert "sim" in resp.lower() and "não" in resp.lower(), "Instrução de confirmação sim/não ausente!"
    print(">>> PASSO 3: APROVADO! Resumo do pedido gerado com sucesso! <<<\n")
    
    time.sleep(2)
    
    # STEP 4: Confirmar o pedido ("sim")
    print("--- [PASSO 4] Enviando confirmação 'sim' ---")
    resp, elapsed = send_chatwoot_message("sim", timeout=45)
    print(f"Tempo de resposta: {elapsed:.2f}s")
    print(f"Resposta do bot:\n{resp}\n")
    
    assert "registrado com sucesso" in resp.lower() or "confirmado" in resp.lower(), "Pedido não foi registrado!"
    assert "Sobre o Projeto de TCC" in resp or "Trabalho de Conclusão de Curso" in resp or "nenhum pagamento" in resp, "Explicação acadêmica do TCC não enviada!"
    print(">>> PASSO 4: APROVADO! Pedido registrado e explicação do TCC enviada! <<<\n")
    
    time.sleep(2)
    
    # STEP 5: Retorno ao modo Fatec e pergunta acadêmica
    print("--- [PASSO 5] Pergunta acadêmica sobre a Fatec ---")
    fatec_query = "Quais cursos a Fatec Bebedouro oferece?"
    resp, elapsed = send_chatwoot_message(fatec_query, timeout=45)
    print(f"Tempo de resposta: {elapsed:.2f}s")
    print(f"Resposta do bot:\n{resp}\n")
    
    assert "Logística" in resp or "Big Data" in resp, "Falha na resposta acadêmica da Fatec!"
    print(">>> PASSO 5: APROVADO! Retorno fluído ao RAG da Fatec! <<<\n")
    
    print("=================================================================")
    print("  TODOS OS 5 PASSOS DO TESTE AO VIVO PASSARAM COM 100% DE SUCESSO!")
    print("=================================================================")

if __name__ == '__main__':
    run_suite()
