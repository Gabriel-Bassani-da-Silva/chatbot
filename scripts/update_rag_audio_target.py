import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

wf_path = 'workflows/Agente RAG Fatec.json'
with open(wf_path, 'r', encoding='utf-8') as f:
    wf = json.load(f)

for node in wf['nodes']:
    if node['name'] == 'Normalizar entrada — áudio':
        node['parameters']['workflowId']['value'] = 'RDtQNcfjRfXGKHZq'
        node['notes'] = 'Subworkflow direto de download, validação e transcrição de áudio via Speaches.'
        print("Updated Normalizar entrada — áudio to point to RDtQNcfjRfXGKHZq")

with open(wf_path, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

print("Saved Agente RAG Fatec.json successfully.")
