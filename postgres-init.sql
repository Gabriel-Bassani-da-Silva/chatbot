-- postgres-init.sql
-- Cria o banco da aplicação (Chatbot) separado do banco interno do n8n.
-- Este script é executado automaticamente pelo Postgres na primeira inicialização
-- (somente quando o volume pgdata está vazio).
CREATE DATABASE chatbot;

\c chatbot
CREATE EXTENSION IF NOT EXISTS vector;

-- chatwoot-init.sql
\c postgres
\getenv chatwoot_password CHATWOOT_POSTGRES_PASSWORD
CREATE USER chatwoot WITH PASSWORD :'chatwoot_password';
CREATE DATABASE chatwoot_production OWNER chatwoot;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_production TO chatwoot;

-- chatwoot-extensions
\c chatwoot_production
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- n8n-rag-vector
\c n8n
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS fatec_rag_collections_poc (
    uuid uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name character varying NOT NULL UNIQUE,
    cmetadata jsonb
);

CREATE TABLE IF NOT EXISTS fatec_rag_vectors_poc (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id uuid REFERENCES fatec_rag_collections_poc(uuid) ON DELETE CASCADE,
    embedding vector(1024),
    document text,
    cmetadata json,
    text text,
    metadata jsonb
);

CREATE INDEX IF NOT EXISTS idx_fatec_vectors_cosine ON fatec_rag_vectors_poc USING hnsw (embedding vector_cosine_ops);

-- Tabela de documentos brutos para armazenamento de JSON puro e prevencao de duplicacao
CREATE TABLE IF NOT EXISTS fatec_rag_documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name text NOT NULL UNIQUE,
    file_id_gdrive text,
    content_hash text NOT NULL,
    categoria text,
    titulo text,
    raw_json jsonb NOT NULL,
    vector_count integer DEFAULT 0,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fatec_docs_filename ON fatec_rag_documents(file_name);
CREATE INDEX IF NOT EXISTS idx_fatec_docs_hash ON fatec_rag_documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_fatec_docs_gdrive ON fatec_rag_documents(file_id_gdrive);

-- Tabela de estado permanente das conversas (controle de primeira mensagem e sessoes)
CREATE TABLE IF NOT EXISTS fatec_conversation_state (
    conversation_id text PRIMARY KEY,
    sender_phone text,
    sender_name text,
    is_first_message boolean DEFAULT true,
    greeting_shown boolean DEFAULT false,
    current_mode text DEFAULT 'fatec',
    first_seen_at timestamptz DEFAULT now(),
    last_seen_at timestamptz DEFAULT now(),
    reset_count integer DEFAULT 0,
    last_reset_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_fatec_state_conv_id ON fatec_conversation_state(conversation_id);
CREATE INDEX IF NOT EXISTS idx_fatec_state_phone ON fatec_conversation_state(sender_phone);

-- Tabela de buffer de mensagens concorrentes (debounce e agrupamento de mensagens consecutivas)
CREATE TABLE IF NOT EXISTS fatec_message_buffer (
    id serial PRIMARY KEY,
    conversation_id text NOT NULL,
    message_id text NOT NULL,
    content_text text NOT NULL,
    created_at timestamptz DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_fatec_msg_buffer_conv ON fatec_message_buffer(conversation_id);



