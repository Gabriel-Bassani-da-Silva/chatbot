import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

wf = json.load(open('workflows/subworkflows/Processar anexos — Normalização multimodal Chatwoot.json', encoding='utf-8'))
conns = wf['connections']
print(json.dumps(conns.get('Encaminhar anexo ao processador', {}), indent=2))
