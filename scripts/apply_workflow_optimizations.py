import json
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Update workflows/Agente RAG Fatec.json
wf_path = 'workflows/Agente RAG Fatec.json'
with open(wf_path, 'r', encoding='utf-8') as f:
    wf = json.load(f)

nodes_to_remove = {
    'Restaurar contexto Agenda',
    'Restaurar contexto Cardápio',
    'Restaurar contexto Fatec',
    'Restaurar contexto cancelamento'
}

new_nodes = []
for node in wf.get('nodes', []):
    name = node['name']
    if name in nodes_to_remove:
        continue
    
    # Update Ollama keepAlive to 30m
    if name == 'Ollama — LLM':
        node.setdefault('parameters', {}).setdefault('options', {})['keepAlive'] = '30m'
    
    # Adjust positions cleanly
    if name == 'Redis — retornar à Fatec':
        node['position'] = [2700, -780]
    elif name == 'Redis — ativar modo Agenda':
        node['position'] = [2700, -100]
    elif name == 'Redis — ativar modo Cardápio':
        node['position'] = [2700, 260]
    elif name == 'Redis — cancelar confirmação':
        node['position'] = [2700, 600]
    elif name == 'Redis — limpar resumo Agenda':
        node['position'] = [2700, 720]
    elif name == 'Redis — limpar resumo Cardápio':
        node['position'] = [2700, 840]
    elif name == 'Resposta de cancelamento':
        node['position'] = [3072, 720]
        
    new_nodes.append(node)

wf['nodes'] = new_nodes

conns = wf.get('connections', {})

# Remove connections originating from deleted or end-of-branch Redis nodes
keys_to_clean = list(nodes_to_remove) + [
    'Redis — retornar à Fatec',
    'Redis — ativar modo Agenda',
    'Redis — ativar modo Cardápio',
    'Redis — cancelar confirmação',
    'Redis — limpar resumo Agenda',
    'Redis — limpar resumo Cardápio'
]
for k in keys_to_clean:
    if k in conns:
        del conns[k]

# Wire Roteador de comandos outputs
# Output 0: Fatec (RAG) -> Agente RAG Fatec + Redis retornar à Fatec
# Output 1: Agenda -> Executar /agenda + Redis ativar modo Agenda
# Output 2: Cardápio -> Executar /cardapio + Redis ativar modo Cardápio
# Output 3: Cancelar -> Resposta de cancelamento + 3 Redis deletions in parallel
# Output 4: Ajuda / Outro -> Resposta a confirmação sem comando
conns['Roteador de comandos'] = {
    'main': [
        [
            {'node': 'Agente RAG Fatec', 'type': 'main', 'index': 0},
            {'node': 'Redis — retornar à Fatec', 'type': 'main', 'index': 0}
        ],
        [
            {'node': 'Executar /agenda', 'type': 'main', 'index': 0},
            {'node': 'Redis — ativar modo Agenda', 'type': 'main', 'index': 0}
        ],
        [
            {'node': 'Executar /cardapio', 'type': 'main', 'index': 0},
            {'node': 'Redis — ativar modo Cardápio', 'type': 'main', 'index': 0}
        ],
        [
            {'node': 'Resposta de cancelamento', 'type': 'main', 'index': 0},
            {'node': 'Redis — cancelar confirmação', 'type': 'main', 'index': 0},
            {'node': 'Redis — limpar resumo Agenda', 'type': 'main', 'index': 0},
            {'node': 'Redis — limpar resumo Cardápio', 'type': 'main', 'index': 0}
        ],
        [
            {'node': 'Resposta a confirmação sem comando', 'type': 'main', 'index': 0}
        ],
        []
    ]
}

wf['connections'] = conns

with open(wf_path, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)

print("Updated workflows/Agente RAG Fatec.json successfully.")
print(f"Total nodes now: {len(wf['nodes'])}")

# 2. Archive gdrive_upload_test_1 in postgres
archive_sql = (
    'UPDATE workflow_entity '
    'SET active = false, "isArchived" = true, "updatedAt" = NOW() '
    'WHERE id = \'gdrive_upload_test_1\';'
)
cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-c', archive_sql
]
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode == 0:
    print("Archived gdrive_upload_test_1 successfully in Postgres.")
else:
    print("Warning updating gdrive_upload_test_1:", res.stderr)
