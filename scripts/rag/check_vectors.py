#!/usr/bin/env python3
"""
Utilitário de Diagnóstico do Banco Vetorial e Documentos RAG.
Exibe contagem de vetores no PGVector, documentos no Postgres e status de sincronização com Google Drive.
"""

import subprocess
import sys

def main():
    sql = """
    SELECT 
        (SELECT count(*) FROM fatec_rag_documents) as total_docs,
        (SELECT count(*) FROM fatec_rag_documents WHERE file_id_gdrive IS NOT NULL) as docs_in_gdrive,
        (SELECT count(*) FROM fatec_rag_vectors_poc) as total_vectors;
    """
    cmd = ['docker', 'exec', '-i', 'chatbot_n8n-postgres-1', 'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A', '-F', '|', '-c', sql]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

    if p.returncode != 0:
        print("[ERRO] Não foi possível consultar o PostgreSQL:", p.stderr)
        sys.exit(1)

    parts = p.stdout.strip().split('|')
    if len(parts) >= 3:
        total_docs, docs_gdrive, total_vectors = parts[0], parts[1], parts[2]
        print(f"\n========================================================")
        print(f"DIAGNÓSTICO DO BANCO RAG (PostgreSQL & PGVector)")
        print(f"Documentos Registrados (fatec_rag_documents): {total_docs}")
        print(f"Documentos Vinculados ao Google Drive:       {docs_gdrive}")
        print(f"Total de Vetores no PGVector (chunks):       {total_vectors}")
        print(f"========================================================\n")

    # Detalhar contagem por documento
    detail_sql = """
    SELECT 
        file_name, 
        vector_count, 
        CASE WHEN file_id_gdrive IS NOT NULL THEN 'Sim' ELSE 'Não' END as gdrive, 
        SUBSTRING(content_hash, 1, 10) || '...' as hash
    FROM fatec_rag_documents 
    ORDER BY file_name;
    """
    p2 = subprocess.run(['docker', 'exec', '-i', 'chatbot_n8n-postgres-1', 'psql', '-U', 'postgres', '-d', 'n8n', '-c', detail_sql], capture_output=True, text=True, encoding='utf-8')
    print(p2.stdout)

if __name__ == '__main__':
    main()
