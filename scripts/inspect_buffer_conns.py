import json

with open('workflows/Agente RAG Fatec.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

conns = wf.get('connections', {})
nodes = wf['nodes']
node_names = [n['name'] for n in nodes]

for name in node_names:
    if any(k in name.lower() for k in ['buffer', 'wait', 'janela', 'comando imediato', 'limite', 'consolidado']):
        print(f"\n--- Connections for: {name} ---")
        if name in conns:
            print("  Outputs:", json.dumps(conns[name], indent=2, ensure_ascii=False))
        # Find incoming
        incoming = []
        for src, out_dict in conns.items():
            for otype, blist in out_dict.items():
                for b_idx, targets in enumerate(blist):
                    for t in targets:
                        if t['node'] == name:
                            incoming.append(f"{src} ({otype}:{b_idx})")
        print("  Incoming:", incoming)
