import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

wf = json.load(open('workflows/subworkflows/Processar anexos — Normalização multimodal Chatwoot.json', encoding='utf-8'))
nodes = {n['name']: n for n in wf['nodes']}
conns = wf['connections']

# Find nodes with no outgoing connections
all_sources = set(conns.keys())
terminal_nodes = [name for name in nodes if name not in all_sources]
print("Terminal nodes in Processar anexos:")
for t in terminal_nodes:
    print(f"  - {t} (type: {nodes[t]['type']})")
