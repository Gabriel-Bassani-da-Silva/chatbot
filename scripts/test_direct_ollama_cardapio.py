import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

system_prompt = """Você atende somente o Cardápio demonstrativo de uma lanchonete fictícia.
Retorne EXCLUSIVAMENTE um objeto JSON com o formato:
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

CARDÁPIO:
Hambúrgueres: B1 Clássico (R$ 19,90), B2 Cheeseburger (R$ 22,90), B3 Duplo (R$ 29,90), B4 Frango (R$ 24,90).
Acompanhamentos: A1 Batata pequena (R$ 9,90), A2 Batata grande (R$ 14,90), A3 Anéis de cebola (R$ 12,90).
Bebidas: D1 Cola (R$ 6,00), D2 Cola Zero (R$ 6,00), D3 Guaraná (R$ 6,00), D4 Água (R$ 4,00), D5 Suco de laranja (R$ 8,00).
Extras permitidos: queijo, bacon, carne.
Remoções permitidas: cebola, picles, tomate, alface, queijo, molho da casa.
"""

user_msg = "Quero um cheeseburger junto com anel de cebola, quero um suco de laranja, quero com carne extra o meu hambúrguer e eu quero que tire tomate."

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
resp = r.json()
print("Direct Ollama response:")
print(resp["message"]["content"])
parsed = json.loads(resp["message"]["content"])
print("\nParsed items:")
for it in parsed.get("itens_carrinho", []):
    print(" -", it)
