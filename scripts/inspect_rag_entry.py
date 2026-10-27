import json

with open('workflows/Agente RAG Fatec.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

print("Total nodes:", len(wf['nodes']))
for n in sorted(wf['nodes'], key=lambda x: x.get('position', [0, 0])[0]):
    pos = n.get('position', [0, 0])
    print(f"{pos[0]:>5}, {pos[1]:>5} | {n['name']} ({n['type']})")

print("\n--- CONNECTIONS FROM WEBHOOK ---")
conns = wf.get('connections', {})
curr = "Webhook Chatwoot"
visited = set()
def trace(node_name, depth=0):
    if depth > 10 or node_name in visited:
        return
    visited.add(node_name)
    node_conns = conns.get(node_name, {})
    for out_type, out_list in node_conns.items():
        for branch_idx, targets in enumerate(out_list):
            for t in targets:
                print("  " * depth + f"[{out_type}:{branch_idx}] -> {t['node']}")
                trace(t['node'], depth + 1)

trace("Webhook Chatwoot RAG")
