# Utilitários de Manutenção da Base de Conhecimento RAG

Esta pasta contém ferramentas operacionais para gestão, sincronização e validação da base de conhecimento da Fatec Bebedouro.

---

### Scripts Disponíveis

| Script | Descrição | Como Executar |
| :--- | :--- | :--- |
| [`check_vectors.py`](check_vectors.py) | Exibe o diagnóstico do PGVector e da tabela `fatec_rag_documents`, listando quantidade de vetores, documentos cadastrados e vínculo com o Google Drive. | `python scripts/rag/check_vectors.py` |
| [`validate_knowledge_base.py`](validate_knowledge_base.py) | Valida a conformidade do schema de todos os 22 arquivos JSON em `base-conhecimento/` (campos obrigatórios, integridade de FAQs e seções). | `python scripts/rag/validate_knowledge_base.py` |
| [`test_semantic_search.py`](test_semantic_search.py) | Testa a busca semântica por similaridade de cosseno contra o PGVector via Ollama, retornando os 5 trechos mais relevantes com score. | `python scripts/rag/test_semantic_search.py "sua pergunta"` |
| [`ingest_knowledge_base.py`](ingest_knowledge_base.py) | Lê todos os arquivos JSON locais, gera embeddings no Ollama (modelo dinâmico do n8n) e atualiza o PGVector com índice HNSW e o Postgres com os JSONs puros. | `python scripts/rag/ingest_knowledge_base.py` |
| [`sync_gdrive.js`](sync_gdrive.js) | Sincroniza a base local com a pasta do Google Drive (`1AtN4X4jp5okt8ChlwRmYMpI4XwQuurF0`), atualizando in-place sem criar duplicatas. | `Get-Content scripts/rag/sync_gdrive.js \| docker exec -i chatbot_n8n-n8n-1 node -` |
