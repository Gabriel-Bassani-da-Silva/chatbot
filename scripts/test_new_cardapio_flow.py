import json
import requests
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read current JS code of Interpretar /cardapio
with open('workflows/subworkflows/Comando _cardapio — Google Sheets.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

for n in wf['nodes']:
    if n['name'] == 'Interpretar /cardapio':
        js_code = n['parameters']['jsCode']
        js_code = js_code.replace(
            "const rawItems = Array.isArray(parsed.itens_carrinho) ? parsed.itens_carrinho : (sameSession && Array.isArray(oldState?.rawItems) ? oldState.rawItems : []);",
            "const rawItems = (Array.isArray(parsed.itens_carrinho) && parsed.itens_carrinho.length > 0) ? parsed.itens_carrinho : (sameSession && Array.isArray(oldState?.rawItems) ? oldState.rawItems : []);"
        )
        js_code = js_code.replace(
            "let observacoes = null;",
            "let observacoes = 'Nenhuma';"
        )
        js_code = js_code.replace(
            "const mergedState = {\n    sessionKey,\n    summaryAt,\n    ...(oldState && sameSession ? oldState : {}),\n    ...stateData\n  };",
            "const mergedState = {\n    ...(oldState && sameSession ? oldState : {}),\n    sessionKey,\n    summaryAt,\n    ...stateData\n  };"
        )
        js_code = js_code.replace(
            "oldState = typeof value === 'string' ? JSON.parse(value) : (value && typeof value === 'object' ? value : null);",
            "oldState = typeof value === 'string' ? JSON.parse(value) : (value && typeof value === 'object' ? value : null);\n  if (typeof oldState === 'string') { try { oldState = JSON.parse(oldState); } catch { oldState = null; } }"
        )
        break

system_prompt = """Você atende somente o aplicativo independente Cardápio demonstrativo de uma lanchonete fictícia para um projeto de TCC da Fatec Bebedouro. Responda em português brasileiro.

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
}
"""

def call_ollama(user_msg):
    payload = {
        "model": "qwen3:4b",
        "format": "json",
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ],
        "options": {"temperature": 0.1, "num_ctx": 4096}
    }
    r = requests.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=20)
    return r.json()["message"]["content"]

def simulate_node(user_text, prev_pending_state=None, ollama_output=None):
    runner = f"""
    const $ = (nodeName) => {{
        if (nodeName === 'Entrada do workflow principal') {{
            return {{
                item: {{
                    json: {{
                        contentText: {json.dumps(user_text)},
                        appSessionKey: 'cardapio:test:39',
                        conversationId: '39',
                        messageId: '100',
                        phone_number: '+5517991516006'
                    }}
                }}
            }};
        }}
        if (nodeName === 'Redis — ler confirmação') {{
            return {{
                item: {{
                    json: {{
                        pendingState: {json.dumps(prev_pending_state)}
                    }}
                }}
            }};
        }}
        return {{ item: {{ json: {{}} }} }};
    }};

    let $json = {json.dumps(ollama_output) if ollama_output else '{}'};
    if (typeof $json === 'string') {{
        try {{ $json = JSON.parse($json); }} catch(e) {{}}
    }}

    function run() {{
        {js_code}
    }}

    console.log(JSON.stringify(run()));
    """
    res = subprocess.run(['docker', 'exec', '-i', 'chatbot_n8n-n8n-1', 'node'], input=runner.encode('utf-8'), capture_output=True)
    out = res.stdout.decode('utf-8').strip()
    err = res.stderr.decode('utf-8').strip()
    if err:
        print("Node error:", err)
    return json.loads(out)

print("=== STEP 1: /cardapio ===")
res1 = simulate_node("/cardapio")
print("Action:", res1['json']['action'])
print("Output snippet:\n", res1['json']['output'][:150])
assert res1['json']['action'] == 'pending'
assert 'CARDÁPIO DEMONSTRATIVO' in res1['json']['output']

print("\n=== STEP 2: Order items (voice transcription) ===")
voice_msg = "Quero um cheeseburger junto com anel de cebola, quero um suco de laranja, quero com carne extra o meu hambúrguer e eu quero que tire tomate."
ollama_out2 = call_ollama(voice_msg)
print("Ollama raw output:\n", ollama_out2)
res2 = simulate_node(voice_msg, prev_pending_state=None, ollama_output=json.loads(ollama_out2))
print("Action:", res2['json']['action'])
print("Output snippet:\n", res2['json']['output'])
assert res2['json']['action'] == 'pending'
assert '3 item(ns)' in res2['json']['output'] or 'carrinho' in res2['json']['output'].lower()
pending_state_2 = res2['json']['pendingState']
print("Pending state saved successfully (len):", len(pending_state_2))

print("\n=== STEP 3: Client info (Name and Payment) ===")
client_msg = "Meu nome é Gabriel Bassani e vou pagar no Pix"
ollama_out3 = call_ollama(client_msg)
print("Ollama raw output:\n", ollama_out3)
res3 = simulate_node(client_msg, prev_pending_state=pending_state_2, ollama_output=json.loads(ollama_out3))
print("Action:", res3['json']['action'])
print("Output snippet:\n", res3['json']['output'])
assert res3['json']['action'] == 'pending'
assert 'Gabriel Bassani' in res3['json']['output']
assert 'Pix' in res3['json']['output']
assert 'TOTAL:' in res3['json']['output']
pending_state_3 = res3['json']['pendingState']

print("\n=== STEP 4: Confirmation ('sim') ===")
res4 = simulate_node("sim", prev_pending_state=pending_state_3, ollama_output={})
print("Action:", res4['json']['action'])
print("Order data to sheet:", res4['json'].get('nome'), res4['json'].get('forma_pagamento'), res4['json'].get('itens'))
assert res4['json']['action'] == 'sheet'
assert res4['json']['nome'] == 'Gabriel Bassani'
assert res4['json']['forma_pagamento'] == 'Pix'

print("\n>>> TODOS OS PASSOS TESTADOS E APROVADOS COM SUCESSO ABSOLUTO! <<<")
