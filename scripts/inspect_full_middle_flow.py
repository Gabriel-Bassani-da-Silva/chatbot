import json

with open('workflows/Agente RAG Fatec.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

nodes = {n['name']: n for n in wf['nodes']}

for name in [
    'Verificar tipo de entrada e documentos',
    'Liberar conteúdo textual para o agente',
    'Verificar limite de texto',
    'Verificar se comando imediato',
    'Postgres — Salvar Mensagem no Buffer',
    'Aguardar janela de digitação',
    'Postgres — Checar Última Mensagem',
    'Decidir se janela fechou',
    'Postgres — Consolidar e Limpar Buffer',
    'Aplicar texto consolidado',
    'Postgres — Consultar Estado Permanente',
    'Redis — ler aplicação ativa',
    'Classificar comando'
]:
    n = nodes.get(name)
    if n:
        print(f"=== {name} ({n['type']}) ===")
        print("Parameters:", json.dumps(n.get('parameters'), indent=2, ensure_ascii=False)[:300])
