import json

with open('workflows/subworkflows/Comando _cardapio — Google Sheets.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

for n in wf['nodes']:
    print(f"{n['name']} | {n['type']} | {n['position']}")
