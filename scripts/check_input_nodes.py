import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

wf = json.load(open('workflows/Agente RAG Fatec.json', encoding='utf-8'))
for n in wf['nodes']:
    if n['name'] in ['Validar evento, mensagem e atendimento humano', 'Verificar tipo de entrada e documentos']:
        print(f"\n=== Node: {n['name']} ===")
        print(n.get('parameters', {}).get('jsCode', ''))
