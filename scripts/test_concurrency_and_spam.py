import requests
import json
import time
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

CONV_ID = 39
WEBHOOK_URL = "http://127.0.0.1:5678/webhook/chatwoot-rag-fatec-poc"
REDIS_PASS = "f81a34c353b25e714182ab9345737beec9630d4380d9c6106f34c1afa33a6f8c"

def redis_cli(*args):
    cmd = ['docker', 'exec', 'chatbot_n8n-redis-1', 'redis-cli', '-a', REDIS_PASS] + [str(a) for a in args]
    res = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace')
    out = (res.stdout or '').strip()
    lines = [l for l in out.split('\n') if not l.startswith('Warning:')]
    return '\n'.join(lines).strip()

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

def send_chatwoot_msg_async(text, msg_id=None):
    if not msg_id:
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
        "account": {"id": 1}
    }
    return requests.post(WEBHOOK_URL, json=payload, timeout=10)

def wait_for_new_bot_reply(after_id, timeout=40):
    start = time.time()
    while time.time() - start < timeout:
        mid, mtype, content = get_latest_chatwoot_msg()
        if mid > after_id and mtype == 1:
            return mid, content, time.time() - start
        time.sleep(1)
    return 0, "", time.time() - start

print("=================================================================")
print("  TESTE DO NOVO PIPELINE REDIS: DEBOUNCE, RATE LIMIT E BYPASS")
print("=================================================================")

# 0. Limpar chaves Redis de teste
print("\n--- [PASSO 0] Resetando chaves de teste no Redis ---")
redis_cli('DEL', f'chatwoot:ratelimit:conv:{CONV_ID}')
redis_cli('DEL', f'chatwoot:last_token:conv:{CONV_ID}')
redis_cli('DEL', f'chatwoot:buffer:conv:{CONV_ID}')
redis_cli('DEL', f'chatwoot:infer_lock:conv:{CONV_ID}')
redis_cli('DEL', f'chatwoot:audio_pending:conv:{CONV_ID}')
print("Chaves de teste resetadas!")

# 1. Teste de Bypass Imediato (/limpar_contexto)
print("\n--- [PASSO 1] Testando Bypass Imediato: /limpar_contexto ---")
last_id, _, _ = get_latest_chatwoot_msg()
t0 = time.time()
send_chatwoot_msg_async("/limpar_contexto")
bot_id, reply, elapsed = wait_for_new_bot_reply(last_id, timeout=15)
print(f"Resposta do bot ({elapsed:.1f}s): {reply}")
assert bot_id > 0, "Bot não respondeu ao comando /limpar_contexto!"
assert "Contexto reiniciado" in reply or "Como posso te ajudar hoje" in reply, f"Resposta inesperada: {reply}"
assert elapsed < 10, f"Bypass demorou mais de 10s: {elapsed:.1f}s"
print("✓ PASSO 1 PASSOU: Bypass Imediato executou sem aguardar debounce!")

# 2. Teste de Agrupamento Concorrente (Burst de 3 mensagens)
print("\n--- [PASSO 2] Testando Agrupamento Concorrente (3 mensagens em < 1s) ---")
last_id, _, _ = get_latest_chatwoot_msg()
base_time = int(time.time() * 1000) % 2000000000

print("Enviando Msg 1: 'Oi'")
send_chatwoot_msg_async("Oi", msg_id=base_time + 1)
time.sleep(0.3)

print("Enviando Msg 2: 'Tudo bem?'")
send_chatwoot_msg_async("Tudo bem?", msg_id=base_time + 2)
time.sleep(0.3)

print("Enviando Msg 3: 'Quais cursos de graduação a Fatec oferece?'")
send_chatwoot_msg_async("Quais cursos de graduação a Fatec oferece?", msg_id=base_time + 3)

print("Aguardando consolidação do debounce (espera ~3.5s de buffer + inferência)...")
bot_id, reply, elapsed = wait_for_new_bot_reply(last_id, timeout=45)
print(f"Resposta do bot ({elapsed:.1f}s):\n{reply}\n")
assert bot_id > 0, "Bot não respondeu ao burst consolidado!"
assert any(k in reply.lower() for k in ['big data', 'agro', 'gestão', 'logística', 'cursos', 'bebedouro']), f"Resposta incompleta: {reply}"
print("✓ PASSO 2 PASSOU: Burst de mensagens consolidado com sucesso!")

# 3. Teste de Rate Limiting (Flooding/Spam)
print("\n--- [PASSO 3] Testando Rate Limit Pré-Wait (15 mensagens rápidas) ---")
# Resetar chave de rate limit para teste limpo
redis_cli('DEL', f'chatwoot:ratelimit:conv:{CONV_ID}')
last_id, _, _ = get_latest_chatwoot_msg()
spam_base = int(time.time() * 1000) % 2000000000

warning_received = False
for i in range(1, 16):
    mid = spam_base + 100 + i
    txt = f"Spam teste {i}"
    send_chatwoot_msg_async(txt, msg_id=mid)
    time.sleep(0.1)

print("15 mensagens disparadas. Verificando aviso educativo da 11ª mensagem...")
bot_id, reply, elapsed = wait_for_new_bot_reply(last_id, timeout=20)
print(f"Resposta recebida ({elapsed:.1f}s): {reply}")

assert "muitas mensagens em um curto intervalo" in reply or "pausadas por 30 segundos" in reply or "bloqueio temporário" in reply, f"Aviso de rate limit não recebido! Resposta: {reply}"
print("✓ PASSO 3 PASSOU: Aviso educativo da 11ª mensagem emitido com sucesso!")

# Verificar que mensagens 12 a 15 não geraram mais respostas adicionais
time.sleep(5)
new_last_id, _, _ = get_latest_chatwoot_msg()
assert new_last_id == bot_id, f"Mensagens 12+ geraram respostas adicionais indesejadas (id {new_last_id} > {bot_id})!"
print("✓ Descarte silencioso validado: mensagens 12+ foram descartadas sem novas respostas!")

# 4. Verificar liberação de infer_lock
lock_val = redis_cli('GET', f'chatwoot:infer_lock:conv:{CONV_ID}')
print(f"\nValor do infer_lock após finalização: '{lock_val}'")
assert not lock_val or lock_val == "", f"infer_lock não foi liberado! Valor: {lock_val}"
print("✓ PASSO 4 PASSOU: infer_lock liberado com sucesso após conclusão da resposta!")

# 5. Teste de Blindagem da Race Condition de Áudio (audio_pending)
print("\n--- [PASSO 5] Testando Blindagem de Áudio Pendente (audio_pending) ---")
test_conv = 999
for k in [f'chatwoot:last_token:conv:{test_conv}', f'chatwoot:infer_lock:conv:{test_conv}', f'chatwoot:buffer:conv:{test_conv}', f'chatwoot:audio_pending:conv:{test_conv}']:
    redis_cli('DEL', k)
redis_cli('SET', f'chatwoot:last_token:conv:{test_conv}', '102_execTexto')
redis_cli('SET', f'chatwoot:audio_pending:conv:{test_conv}', '1')
redis_cli('RPUSH', f'chatwoot:buffer:conv:{test_conv}', '{"messageId":102,"text":"escuta aí","createdAt":1000}')

# Avalia o script Lua exatamente como roda no nó 'Redis — Consolidar Buffer e Lock de Inferência'
lua_eval = """
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
"""
status_with_pending = redis_cli(
    'EVAL', lua_eval, '4',
    f'chatwoot:last_token:conv:{test_conv}',
    f'chatwoot:infer_lock:conv:{test_conv}',
    f'chatwoot:buffer:conv:{test_conv}',
    f'chatwoot:audio_pending:conv:{test_conv}',
    '102_execTexto'
)
print(f"Status do Lua com audio_pending=1 (esperado 0 para segurar o texto): {status_with_pending}")
assert status_with_pending.startswith('0'), f"Texto atropelou áudio! Status retornado: {status_with_pending}"

# Simula chegada do áudio transcrito: decremente audio_pending e atualiza last_token
redis_cli('DEL', f'chatwoot:audio_pending:conv:{test_conv}')
redis_cli('SET', f'chatwoot:last_token:conv:{test_conv}', '101_execAudio')
redis_cli('RPUSH', f'chatwoot:buffer:conv:{test_conv}', '{"messageId":101,"text":"Áudio transcrito","createdAt":900}')

# Texto antigo tenta novamente -> deve retornar -1 (descarte) porque last_token mudou
status_old_text = redis_cli(
    'EVAL', lua_eval, '4',
    f'chatwoot:last_token:conv:{test_conv}',
    f'chatwoot:infer_lock:conv:{test_conv}',
    f'chatwoot:buffer:conv:{test_conv}',
    f'chatwoot:audio_pending:conv:{test_conv}',
    '102_execTexto'
)
print(f"Status do texto antigo na próxima iteração (esperado -1 para descarte): {status_old_text}")
assert status_old_text.startswith('-1'), f"Texto antigo não descartou! Status: {status_old_text}"

# Áudio consolida ambos com sucesso
status_audio = redis_cli(
    'EVAL', lua_eval, '4',
    f'chatwoot:last_token:conv:{test_conv}',
    f'chatwoot:infer_lock:conv:{test_conv}',
    f'chatwoot:buffer:conv:{test_conv}',
    f'chatwoot:audio_pending:conv:{test_conv}',
    '101_execAudio'
)
print(f"Status da consolidação do áudio (esperado 1): {status_audio}")
assert status_audio.startswith('1'), f"Falha na consolidação do áudio! Status: {status_audio}"
print("✓ PASSO 5 PASSOU: Blindagem atômica de áudio pendente validada com 100% de precisão!")

# 6. Teste de Liberação de Lock no Error Trigger por execution.id
print("\n--- [PASSO 6] Testando Liberação de Lock no Error Trigger por execution.id ---")
mock_exec_id = "test_exec_999"
mock_conv = 888
redis_cli('SET', f'chatwoot:infer_lock:conv:{mock_conv}', f'msg999_{mock_exec_id}', 'EX', 60)
redis_cli('SET', f'chatwoot:audio_pending:conv:{mock_conv}', '1', 'EX', 60)

error_unlock_lua = """
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
"""
cleaned_result = redis_cli('EVAL', error_unlock_lua, '0', mock_exec_id, '')
print(f"Chaves limpas pelo script de erro para {mock_exec_id}: {cleaned_result}")
lock_mock = redis_cli('GET', f'chatwoot:infer_lock:conv:{mock_conv}')
audio_mock = redis_cli('GET', f'chatwoot:audio_pending:conv:{mock_conv}')
assert not lock_mock, f"Lock mock não foi removido! Valor: {lock_mock}"
assert not audio_mock, f"Audio pending mock não foi removido! Valor: {audio_mock}"
print("✓ PASSO 6 PASSOU: Error Trigger desaloca lock e audio_pending por execution.id mesmo sem conversationId no payload!")

# Limpeza final dos mocks e chaves da conversa de teste
for k in [f'chatwoot:last_token:conv:{test_conv}', f'chatwoot:infer_lock:conv:{test_conv}', f'chatwoot:buffer:conv:{test_conv}', f'chatwoot:audio_pending:conv:{test_conv}', f'chatwoot:ratelimit:conv:{CONV_ID}', f'chatwoot:infer_lock:conv:{CONV_ID}']:
    redis_cli('DEL', k)

print("\n=================================================================")
print("  TODOS OS 6 TESTES DE CONCORRÊNCIA, RATE LIMIT E LOCK PASSARAM!")
print("=================================================================")

