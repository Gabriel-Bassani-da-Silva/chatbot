#!/usr/bin/env python3
"""
Ingestão e Re-indexação Local da Base de Conhecimento RAG com Texto 100% Limpo e Humanizado.
Lê todos os arquivos de 'base-conhecimento/', fatiando em seções granulares e FAQs.
NUNCA grava dados brutos em JSON nas colunas text/document do PGVector, evitando que
o LLM interprete os dados como código/JSON e gere meta-respostas sobre estrutura de dados.
"""

import os
import json
import hashlib
import urllib.request
import time
import subprocess
import sys

def get_active_model_from_n8n():
    """Detecta automaticamente o modelo de embedding ativo configurado no n8n."""
    default_model = 'qwen3-embedding:0.6b'
    try:
        cmd = [
            'docker', 'exec', '-i', 'chatbot_n8n-postgres-1',
            'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A', '-c',
            "SELECT n->'parameters'->>'model' FROM workflow_entity w, LATERAL json_array_elements(w.nodes) AS n WHERE w.id = 'vKrMSyZ4jMDtbjW7' AND n->>'type' = '@n8n/n8n-nodes-langchain.embeddingsOllama' LIMIT 1;"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        model = res.stdout.strip()
        if model:
            print(f"Modelo de embedding detectado no n8n: '{model}'")
            return model
    except Exception as e:
        print(f"Não foi possível consultar o modelo no n8n ({e}), usando padrão: '{default_model}'.")
    return default_model

def get_embedding(text, model):
    req = urllib.request.Request(
        'http://localhost:11434/api/embeddings',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'model': model, 'prompt': text}).encode('utf-8')
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        return res.get('embedding', [])

def detect_course(fname, item):
    lower_name = fname.lower()
    if 'big_data' in lower_name or 'bigdata' in lower_name or 'big-data' in lower_name:
        return 'Big Data no Agronegócio'
    if 'logistica' in lower_name:
        return 'Logística'
    return item.get('curso', 'Institucional / Geral')

def to_natural_text(val, indent=0):
    """Converte qualquer estrutura aninhada em texto natural em português sem sintaxe de JSON."""
    prefix = "  " * indent
    if isinstance(val, str):
        return f"{prefix}{val.strip()}"
    elif isinstance(val, (int, float, bool)):
        return f"{prefix}{val}"
    elif isinstance(val, dict):
        lines = []
        desc = val.get('description')
        other_keys = {k: v for k, v in val.items() if k.lower() not in ('description', 'type', '$schema')}
        if desc:
            lines.append(f"{prefix}{desc.strip()}")
        for k, v in other_keys.items():
            k_clean = k.replace('_', ' ').strip().capitalize()
            if isinstance(v, (str, int, float, bool)):
                lines.append(f"{prefix}• {k_clean}: {v}")
            else:
                lines.append(f"{prefix}• {k_clean}:")
                sub = to_natural_text(v, indent + 1)
                if sub:
                    lines.append(sub)
        return "\n".join(lines)
    elif isinstance(val, list):
        lines = []
        for item in val:
            if isinstance(item, (str, int, float, bool)):
                lines.append(f"{prefix}• {item}")
            else:
                sub = to_natural_text(item, indent + 1)
                if sub:
                    lines.append(sub)
        return "\n".join(lines)
    return ""

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    base_dir = os.path.join(root_dir, 'base-conhecimento')
    active_model = get_active_model_from_n8n()

    print(f"\nCarregando arquivos de: {base_dir}")
    files = sorted([f for f in os.listdir(base_dir) if f.endswith('.json')])
    if not files:
        print("[ERRO] Nenhum arquivo .json encontrado na pasta base-conhecimento.")
        sys.exit(1)

    probe_emb = get_embedding("probe_dimension", active_model)
    if not probe_emb:
        print(f"[ERRO] Não foi possível obter embedding do Ollama para '{active_model}'. Verifique se o Ollama está rodando.")
        sys.exit(1)

    embedding_dim = len(probe_emb)
    print(f"Dimensão do vetor para '{active_model}': {embedding_dim}d")

    chunks = []
    doc_records = []

    for fname in files:
        fpath = os.path.join(base_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content_str = f.read()

        try:
            data = json.loads(content_str)
        except Exception as e:
            print(f"Erro ao ler {fname}: {e}")
            continue

        content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        items = data if isinstance(data, list) else [data]
        file_chunks_count = 0

        for item in items:
            curso = detect_course(fname, item)
            categoria = item.get('categoria', 'geral')
            titulo = item.get('titulo', fname)
            fonte = item.get('fonte', 'Fatec Bebedouro')
            resumo = item.get('resumo', '').strip()

            # 1. Chunk de Resumo Institucional
            if resumo:
                text_resumo = (
                    f"Curso/Área: {curso}\n"
                    f"Documento: {titulo}\n"
                    f"Categoria: {categoria}\n"
                    f"Visão Geral / Resumo Institucional:\n{resumo}\n"
                    f"Fonte Oficial: {fonte}"
                )
                meta_resumo = {
                    'file': fname,
                    'file_name': fname,
                    'type': 'resumo',
                    'curso': curso,
                    'categoria': categoria,
                    'titulo': titulo,
                    'model': active_model
                }
                chunks.append({'text': text_resumo, 'meta': meta_resumo})
                file_chunks_count += 1

            # 2. Chunks de Seções Estruturadas (convertidas em texto natural)
            dados = item.get('dados_estruturados') or {}
            for secao, conteudo in dados.items():
                clean_content = to_natural_text(conteudo)
                if clean_content:
                    text_secao = (
                        f"Curso/Área: {curso}\n"
                        f"Documento: {titulo}\n"
                        f"Tópico / Assunto: {secao}\n"
                        f"Informações Oficiais:\n{clean_content}\n"
                        f"Fonte Oficial: {fonte}"
                    )
                    meta_secao = {
                        'file': fname,
                        'file_name': fname,
                        'type': 'doc',
                        'secao': secao,
                        'curso': curso,
                        'categoria': categoria,
                        'titulo': titulo,
                        'model': active_model
                    }
                    chunks.append({'text': text_secao, 'meta': meta_secao})
                    file_chunks_count += 1

            # 3. Chunks de Seções Extras (se houver)
            for extra_key in ['Informações Adicionais', 'estagio', 'total_de_aulas', 'fonte_detalhe_eixos']:
                if extra_key in item:
                    clean_extra = to_natural_text(item[extra_key])
                    if clean_extra:
                        text_extra = (
                            f"Curso/Área: {curso}\n"
                            f"Documento: {titulo}\n"
                            f"Tópico / Assunto: {extra_key}\n"
                            f"Informações Oficiais:\n{clean_extra}\n"
                            f"Fonte Oficial: {fonte}"
                        )
                        meta_extra = {
                            'file': fname,
                            'file_name': fname,
                            'type': 'doc',
                            'secao': extra_key,
                            'curso': curso,
                            'categoria': categoria,
                            'titulo': titulo,
                            'model': active_model
                        }
                        chunks.append({'text': text_extra, 'meta': meta_extra})
                        file_chunks_count += 1

            # 4. Chunks de FAQs
            faqs = item.get('perguntas_frequentes') or []
            for faq in faqs:
                q = faq.get('pergunta', '').strip()
                a = faq.get('resposta', '').strip()
                if q and a:
                    text_faq = (
                        f"Curso/Área: {curso}\n"
                        f"Documento: {titulo}\n"
                        f"Pergunta Frequente: {q}\n"
                        f"Resposta Oficial: {a}\n"
                        f"Fonte Oficial: {fonte}"
                    )
                    meta_faq = {
                        'file': fname,
                        'file_name': fname,
                        'type': 'faq',
                        'curso': curso,
                        'categoria': categoria,
                        'titulo': titulo,
                        'pergunta': q,
                        'model': active_model
                    }
                    chunks.append({'text': text_faq, 'meta': meta_faq})
                    file_chunks_count += 1

        first_item = items[0] if items else {}
        doc_records.append({
            'file_name': fname,
            'content_hash': content_hash,
            'categoria': first_item.get('categoria', 'geral'),
            'titulo': first_item.get('titulo', fname),
            'raw_json': data,
            'vector_count': file_chunks_count
        })

    print(f"Total de chunks granulares extraídos: {len(chunks)} em {len(files)} arquivos.")
    print("Gerando embeddings e preparando instruções SQL atômicas...")

    sql_statements = [
        "BEGIN;",
        "CREATE EXTENSION IF NOT EXISTS vector;",
        "CREATE TABLE IF NOT EXISTS fatec_rag_collections_poc (uuid uuid PRIMARY KEY DEFAULT gen_random_uuid(), name character varying NOT NULL, cmetadata jsonb);",
        "CREATE UNIQUE INDEX IF NOT EXISTS fatec_rag_collections_poc_name_idx ON fatec_rag_collections_poc (name);",
        f"CREATE TABLE IF NOT EXISTS fatec_rag_vectors_poc (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), collection_id uuid REFERENCES fatec_rag_collections_poc(uuid) ON DELETE CASCADE, embedding vector({embedding_dim}), document text, cmetadata json, text text, metadata jsonb);",
        f"ALTER TABLE fatec_rag_vectors_poc ALTER COLUMN embedding TYPE vector({embedding_dim});",
        "ALTER TABLE fatec_rag_vectors_poc ADD COLUMN IF NOT EXISTS text text;",
        "ALTER TABLE fatec_rag_vectors_poc ADD COLUMN IF NOT EXISTS metadata jsonb;",
        "DROP INDEX IF EXISTS idx_fatec_vectors_cosine;",
        "CREATE INDEX IF NOT EXISTS idx_fatec_vectors_cosine ON fatec_rag_vectors_poc USING hnsw (embedding vector_cosine_ops);",
        f"INSERT INTO fatec_rag_collections_poc (uuid, name, cmetadata) VALUES ('00000000-0000-0000-0000-000000000001', 'fatec_bebedouro_poc', jsonb_build_object('model', '{active_model}', 'dimension', {embedding_dim}, 'updated_at', NOW())) ON CONFLICT (uuid) DO UPDATE SET name = EXCLUDED.name, cmetadata = EXCLUDED.cmetadata;",
        "CREATE TABLE IF NOT EXISTS fatec_rag_documents (file_name text PRIMARY KEY, content_hash text, categoria text, titulo text, raw_json jsonb, vector_count integer, updated_at timestamp with time zone DEFAULT NOW());",
        "DELETE FROM fatec_rag_vectors_poc;"
    ]

    for doc in doc_records:
        escaped_fname = doc['file_name'].replace("'", "''")
        escaped_hash = doc['content_hash'].replace("'", "''")
        escaped_cat = doc['categoria'].replace("'", "''")
        escaped_tit = doc['titulo'].replace("'", "''")
        escaped_json = json.dumps(doc['raw_json'], ensure_ascii=False).replace("'", "''")
        sql_statements.append(f"""
        INSERT INTO fatec_rag_documents (file_name, content_hash, categoria, titulo, raw_json, vector_count, updated_at)
        VALUES ('{escaped_fname}', '{escaped_hash}', '{escaped_cat}', '{escaped_tit}', '{escaped_json}'::jsonb, {doc['vector_count']}, NOW())
        ON CONFLICT (file_name) DO UPDATE SET
            content_hash = EXCLUDED.content_hash,
            categoria = EXCLUDED.categoria,
            titulo = EXCLUDED.titulo,
            raw_json = EXCLUDED.raw_json,
            vector_count = EXCLUDED.vector_count,
            updated_at = NOW();
        """)

    t0 = time.time()
    for i, chunk in enumerate(chunks):
        emb = get_embedding(chunk['text'], active_model)
        if not emb or len(emb) != embedding_dim:
            print(f"Aviso: chunk #{i+1} falhou na geração do vetor. Pulando...")
            continue
        emb_str = "[" + ",".join(str(x) for x in emb) + "]"
        doc_escaped = chunk['text'].replace("'", "''")
        meta_escaped = json.dumps(chunk['meta'], ensure_ascii=False).replace("'", "''")
        sql = (
            "INSERT INTO fatec_rag_vectors_poc "
            "(collection_id, embedding, text, metadata, document, cmetadata) "
            f"VALUES ('00000000-0000-0000-0000-000000000001', '{emb_str}'::vector, "
            f"'{doc_escaped}', '{meta_escaped}'::jsonb, '{doc_escaped}', '{meta_escaped}'::json);"
        )
        sql_statements.append(sql)
        if (i + 1) % 25 == 0 or (i + 1) == len(chunks):
            print(f"Progresso: {i+1}/{len(chunks)} chunks processados em {time.time()-t0:.1f}s...")

    sql_statements.append("COMMIT;")
    full_sql = "\n".join(sql_statements)

    print("Gravando dados no PostgreSQL (banco n8n e banco chatbot)...")
    for db in ['n8n', 'chatbot']:
        p = subprocess.run(
            ['docker', 'exec', '-i', 'chatbot_n8n-postgres-1', 'psql', '-U', 'postgres', '-d', db, '-v', 'ON_ERROR_STOP=1'],
            input=full_sql.encode('utf-8'),
            capture_output=True
        )
        out = p.stdout.decode('utf-8', errors='ignore')
        err = p.stderr.decode('utf-8', errors='ignore')
        if p.returncode == 0:
            print(f"[SUCESSO] {len(chunks)} vetores ingeridos no PostgreSQL (db: {db}, modelo: {active_model}, {embedding_dim}d)!")
        else:
            print(f"[ERRO] Falha ao executar SQL no banco {db} (rc={p.returncode}):\nSTDOUT: {out[:300]}\nSTDERR: {err[:500]}")

if __name__ == '__main__':
    main()
