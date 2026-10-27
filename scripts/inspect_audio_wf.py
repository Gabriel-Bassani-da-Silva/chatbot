import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

wf = json.load(open('workflows/subworkflows/Normalização de áudio — Chatwoot.json', encoding='utf-8'))
nodes = {n['name']: n for n in wf['nodes']}
conns = wf['connections']
print("Nodes in Normalização de áudio:")
for name, n in nodes.items():
    print(f"  {name} ({n['type']})")

print("\nConnections:")
print(json.dumps(conns, indent=2, ensure_ascii=False))
