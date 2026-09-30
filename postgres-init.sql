-- postgres-init.sql
-- Cria o banco da aplicação separado do banco interno do n8n.
-- Este script é executado automaticamente pelo Postgres na primeira inicialização
-- (somente quando o volume pgdata está vazio).
CREATE DATABASE fatec;

-- chatwoot-init.sql
CREATE USER chatwoot WITH PASSWORD '***REMOVED***';
CREATE DATABASE chatwoot_production OWNER chatwoot;
GRANT ALL PRIVILEGES ON DATABASE chatwoot_production TO chatwoot;

-- chatwoot-extensions
\c chatwoot_production
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
