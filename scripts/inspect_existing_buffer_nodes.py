import json

with open('workflows/Agente RAG Fatec.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

for n in wf['nodes']:
    name = n['name']
    t = n['type']
    if any(k in name.lower() for k in ['buffer', 'wait', 'janela', 'comando imediato', 'rate limit', 'imediato']):
        print(f"Node: {name} ({t}) - position: {n.get('position')}")
