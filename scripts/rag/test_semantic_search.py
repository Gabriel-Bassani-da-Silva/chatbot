#!/usr/bin/env python3
"""
Teste de Busca Semântica por Similaridade de Cosseno no PGVector.
Gera embedding da pergunta via Ollama e executa a busca top-k no banco.
Uso: python test_semantic_search.py "sua pergunta aqui"
"""

import urllib.request
import json
import subprocess
import sys

def get_active_model():
    cmd = [
        'docker', 'exec', '-i', 'chatbot_n8n-postgres-1',
        'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A', '-c',
        "SELECT n->'parameters'->>'model' FROM workflow_entity w, LATERAL json_array_elements(w.nodes) AS n WHERE w.id = 'vKrMSyZ4jMDtbjW7' AND n->>'type' = '@n8n/n8n-nodes-langchain.embeddingsOllama' LIMIT 1;"
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    model = p.stdout.strip()
    return model or 'qwen3-embedding:0.6b'

def main():
    query = sys.argv[1] if len(sys.argv) > 1 else 'Quem é a diretora da unidade?'
    model = get_active_model()
    print(f"Pergunta: '{query}'")
    print(f"Modelo de Embedding: '{model}'")

    # Gerar embedding via Ollama
    req = urllib.request.Request(
        'http://localhost:11434/api/embeddings',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'model': model, 'prompt': query}).encode('utf-8')
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            emb = res.get('embedding', [])
    except Exception as e:
        print(f"[ERRO] Falha ao comunicar com Ollama (http://localhost:11434): {e}")
        sys.exit(1)

    if not emb:
        print("[ERRO] Ollama retornou vetor vazio.")
        sys.exit(1)

    emb_str = '[' + ','.join(str(x) for x in emb) + ']'
    sql = f"""
    SELECT 
        ROUND((1 - (embedding <=> '{emb_str}'))::numeric, 4) as similaridade,
        metadata->>'file' as arquivo,
        metadata->>'categoria' as categoria,
        COALESCE(metadata->>'pergunta', SUBSTRING(document, 1, 60)) as trecho
    FROM fatec_rag_vectors_poc 
    ORDER BY embedding <=> '{emb_str}' 
    LIMIT 5;
    """

    cmd = ['docker', 'exec', '-i', 'chatbot_n8n-postgres-1', 'psql', '-U', 'postgres', '-d', 'n8n']
    p = subprocess.run(cmd, input=sql.encode('utf-8'), capture_output=True)
    print("\nResultados mais similares:")
    print(p.stdout.decode('utf-8', errors='ignore'))

if __name__ == '__main__':
    main()
