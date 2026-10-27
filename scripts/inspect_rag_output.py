import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

for eid in [1261, 1263, 1264, 1265]:
    cmd = [
        'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
        'chatbot_n8n-postgres-1',
        'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
        '-c', f'SELECT data FROM execution_data WHERE "executionId" = {eid};'
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    raw = res.stdout.strip()
    if not raw:
        continue
    d = json.loads(raw)
    print(f"\n================ EXECUTION {eid} ================")
    # Search for strings containing "JSON" or "estágio" or the output of Agente RAG Fatec
    if isinstance(d, list):
        for idx, item in enumerate(d):
            if isinstance(item, str) and ('JavaScript Object Notation' in item or 'estrutura de dados em formato JSON' in item):
                print(f"Found suspicious LLM response at index {idx}:")
                print(item[:400])
                print("...")
            elif isinstance(item, str) and ('fatec_rag_vectors' in item or 'Base de conhecimento' in item):
                print(f"Found vector store reference at index {idx}: {item[:150]}")
