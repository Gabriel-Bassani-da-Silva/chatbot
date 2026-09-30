#!/usr/bin/env bash
# Cria (ou reutiliza) o Agent Bot e vincula-o à Inbox do WAHA.
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib.sh"
setup_init

require_vars DOMAIN CHATWOOT_FRONTEND_URL CHATWOOT_ACCOUNT_TOKEN CHATWOOT_INBOX_ID CHATWOOT_INBOX_IDENTIFIER

if [[ ! "$DOMAIN" =~ ^([A-Za-z0-9-]+\.)*[A-Za-z0-9-]+(:[0-9]{1,5})?$ || "$DOMAIN" == *"SEU_DOMINIO"* || "$DOMAIN" == *"AQUI"* ]]; then
  echo "[ERRO]: DOMAIN não parece configurado; use somente o hostname público, sem protocolo ou caminho." >&2
  exit 1
fi
if [[ ! "$CHATWOOT_INBOX_ID" =~ ^[0-9]+$ ]]; then
  echo "[ERRO]: CHATWOOT_INBOX_ID precisa ser numérico." >&2
  exit 1
fi

ACCOUNT_ID="$(chatwoot_account_id)"
CHATWOOT_PORT_VALUE="${CHATWOOT_PORT:-3001}"
if [[ ! "$ACCOUNT_ID" =~ ^[0-9]+$ || ! "$CHATWOOT_PORT_VALUE" =~ ^[0-9]+$ ]] || (( ACCOUNT_ID < 1 || CHATWOOT_PORT_VALUE < 1 || CHATWOOT_PORT_VALUE > 65535 )); then
  echo "[ERRO]: CHATWOOT_ACCOUNT_ID ou CHATWOOT_PORT inválido." >&2
  exit 1
fi

WEBHOOK_BASE="${WEBHOOK_URL:-https://n8n.${DOMAIN}}"
WEBHOOK_BASE="${WEBHOOK_BASE%/}"
if [[ ! "$WEBHOOK_BASE" =~ ^https?://[^[:space:]]+$ || "$WEBHOOK_BASE" == *"SEU_DOMINIO"* ]]; then
  echo "[ERRO]: WEBHOOK_URL não parece configurada e DOMAIN não gerou uma URL válida." >&2
  exit 1
fi
N8N_WEBHOOK="${WEBHOOK_BASE}/webhook/chatwoot"
export N8N_WEBHOOK
CHATWOOT_BASE="$(chatwoot_api_base)"
BOT_ID="${CHATWOOT_BOT_ID:-}"

if [[ -z "$BOT_ID" ]]; then
  if [[ -n "${CHATWOOT_BOT_TOKEN:-}" ]]; then
    echo "[ERRO]: CHATWOOT_BOT_TOKEN existe, mas CHATWOOT_BOT_ID não. Corrija o estado no .env antes de criar outro Bot." >&2
    exit 1
  fi

  echo "[INFO]: Criando Agent Bot 'Assistente RAG'..."
  BOT_PAYLOAD="$(python3 - <<'PY'
import json, os
print(json.dumps({
    "name": "Assistente RAG",
    "description": "IA primária de atendimento",
    "outgoing_url": os.environ["N8N_WEBHOOK"],
}))
PY
)"
  if ! RESPONSE_BOT="$(curl --silent --show-error --connect-timeout 5 --max-time 30 \
    --write-out $'\n%{http_code}' -X POST "${CHATWOOT_BASE}/api/v1/accounts/${ACCOUNT_ID}/agent_bots" \
    -H "api_access_token: ${CHATWOOT_ACCOUNT_TOKEN}" \
    -H "Content-Type: application/json" \
    --data-binary "$BOT_PAYLOAD")"; then
    echo "[ERRO]: Não foi possível conectar à API do Chatwoot para criar o Agent Bot." >&2
    exit 1
  fi

  STATUS_BOT="$(http_status "$RESPONSE_BOT")"
  BODY_BOT="$(http_body "$RESPONSE_BOT")"
  if ! is_http_success "$STATUS_BOT"; then
    echo "[ERRO]: Criação do Agent Bot falhou (HTTP ${STATUS_BOT:-desconhecido})." >&2
    exit 1
  fi

  BOT_ID="$(printf '%s' "$BODY_BOT" | json_field id)" || {
    echo "[ERRO]: Resposta do Chatwoot não contém ID do Agent Bot." >&2
    exit 1
  }
  BOT_TOKEN="$(printf '%s' "$BODY_BOT" | json_field access_token)" || {
    echo "[ERRO]: Resposta do Chatwoot não contém access_token do Agent Bot." >&2
    exit 1
  }
  if [[ ! "$BOT_ID" =~ ^[0-9]+$ || -z "$BOT_TOKEN" ]]; then
    echo "[ERRO]: Resposta da API contém dados incompletos do Agent Bot." >&2
    exit 1
  fi

  # Salva o ID e o segredo imediatamente; se a associação falhar, a próxima
  # execução reutiliza o mesmo Bot em vez de criar outro.
  persist_env_values CHATWOOT_BOT_ID "$BOT_ID" CHATWOOT_BOT_TOKEN "$BOT_TOKEN"
else
  if [[ ! "$BOT_ID" =~ ^[0-9]+$ ]]; then
    echo "[ERRO]: CHATWOOT_BOT_ID precisa ser numérico." >&2
    exit 1
  fi
  echo "[INFO]: Reutilizando Agent Bot ID ${BOT_ID}."
fi

if [[ "${CHATWOOT_BOT_LINKED_INBOX_ID:-}" == "$CHATWOOT_INBOX_ID" ]]; then
  echo "[INFO]: Agent Bot já consta como vinculado à Inbox ${CHATWOOT_INBOX_ID}; etapa ignorada."
  exit 0
fi

if ! RESPONSE_LINK="$(curl --silent --show-error --connect-timeout 5 --max-time 30 \
  --write-out $'\n%{http_code}' -X POST \
  "${CHATWOOT_BASE}/api/v1/accounts/${ACCOUNT_ID}/inboxes/${CHATWOOT_INBOX_ID}/agent_bot" \
  -H "api_access_token: ${CHATWOOT_ACCOUNT_TOKEN}" \
  -H "Content-Type: application/json" \
  --data-binary "{\"agent_bot\":${BOT_ID}}")"; then
  echo "[ERRO]: Não foi possível conectar à API do Chatwoot para vincular o Bot." >&2
  exit 1
fi

STATUS_LINK="$(http_status "$RESPONSE_LINK")"
if ! is_http_success "$STATUS_LINK"; then
  echo "[ERRO]: Vínculo do Agent Bot à Inbox falhou (HTTP ${STATUS_LINK:-desconhecido}); o ID e o token já foram salvos para retomar sem duplicar o Bot." >&2
  exit 1
fi
persist_env_value CHATWOOT_BOT_LINKED_INBOX_ID "$CHATWOOT_INBOX_ID"
echo "[SUCESSO]: Agent Bot ${BOT_ID} vinculado à Inbox ${CHATWOOT_INBOX_ID}; segredo salvo no .env sem exibi-lo."
