#!/usr/bin/env bash
# Cria a Inbox API do WAHA no Chatwoot, ou reutiliza o ID já salvo no .env.
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib.sh"
setup_init

require_vars CHATWOOT_FRONTEND_URL CHATWOOT_ACCOUNT_TOKEN

if [[ -n "${CHATWOOT_INBOX_ID:-}" && -n "${CHATWOOT_INBOX_IDENTIFIER:-}" ]]; then
  echo "[INFO]: Inbox já configurada (ID ${CHATWOOT_INBOX_ID}); etapa ignorada."
  exit 0
fi
if [[ -n "${CHATWOOT_INBOX_ID:-}" || -n "${CHATWOOT_INBOX_IDENTIFIER:-}" ]]; then
  echo "[ERRO]: CHATWOOT_INBOX_ID e CHATWOOT_INBOX_IDENTIFIER precisam estar definidos juntos." >&2
  exit 1
fi

ACCOUNT_ID="$(chatwoot_account_id)"
CHATWOOT_PORT_VALUE="${CHATWOOT_PORT:-3001}"
if [[ ! "$ACCOUNT_ID" =~ ^[0-9]+$ || ! "$CHATWOOT_PORT_VALUE" =~ ^[0-9]+$ ]] || (( ACCOUNT_ID < 1 || CHATWOOT_PORT_VALUE < 1 || CHATWOOT_PORT_VALUE > 65535 )); then
  echo "[ERRO]: CHATWOOT_ACCOUNT_ID ou CHATWOOT_PORT inválido." >&2
  exit 1
fi

URL="$(chatwoot_api_base)/api/v1/accounts/${ACCOUNT_ID}/inboxes"
if ! RESPONSE="$(curl --silent --show-error --connect-timeout 5 --max-time 30 \
  --write-out $'\n%{http_code}' -X POST "$URL" \
  -H "api_access_token: ${CHATWOOT_ACCOUNT_TOKEN}" \
  -H "Content-Type: application/json" \
  --data-binary '{"name":"WhatsApp WAHA","channel":{"type":"api"}}')"; then
  echo "[ERRO]: Não foi possível conectar à API do Chatwoot para criar a Inbox." >&2
  exit 1
fi

STATUS="$(http_status "$RESPONSE")"
BODY="$(http_body "$RESPONSE")"
if ! is_http_success "$STATUS"; then
  echo "[ERRO]: Criação da Inbox falhou (HTTP ${STATUS:-desconhecido})." >&2
  exit 1
fi

INBOX_ID="$(printf '%s' "$BODY" | json_field id)" || {
  echo "[ERRO]: Resposta do Chatwoot não contém um ID de Inbox válido." >&2
  exit 1
}
INBOX_IDENTIFIER="$(printf '%s' "$BODY" | json_field inbox_identifier)" || {
  echo "[ERRO]: Resposta do Chatwoot não contém inbox_identifier." >&2
  exit 1
}
if [[ ! "$INBOX_ID" =~ ^[0-9]+$ || -z "$INBOX_IDENTIFIER" ]]; then
  echo "[ERRO]: Resposta da API contém dados incompletos da Inbox." >&2
  exit 1
fi

persist_env_values CHATWOOT_INBOX_ID "$INBOX_ID" CHATWOOT_INBOX_IDENTIFIER "$INBOX_IDENTIFIER"
echo "[SUCESSO]: Inbox criada; CHATWOOT_INBOX_ID e CHATWOOT_INBOX_IDENTIFIER foram salvos no .env."
