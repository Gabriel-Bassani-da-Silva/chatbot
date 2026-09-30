#!/usr/bin/env bash
# Registra (ou atualiza) o app Chatwoot no WAHA. O PUT permite repetição segura.
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib.sh"
setup_init
require_vars WAHA_API_KEY CHATWOOT_ACCOUNT_TOKEN CHATWOOT_INBOX_ID CHATWOOT_INBOX_IDENTIFIER

WAHA_PORT_VALUE="${WAHA_PORT:-3000}"
ACCOUNT_ID="$(chatwoot_account_id)"
if [[ ! "$WAHA_PORT_VALUE" =~ ^[0-9]+$ ]] || (( WAHA_PORT_VALUE < 1 || WAHA_PORT_VALUE > 65535 )); then
  echo "[ERRO]: WAHA_PORT inválida." >&2
  exit 1
fi
if [[ ! "$ACCOUNT_ID" =~ ^[0-9]+$ || ! "$CHATWOOT_INBOX_ID" =~ ^[0-9]+$ ]]; then
  echo "[ERRO]: CHATWOOT_ACCOUNT_ID e CHATWOOT_INBOX_ID precisam ser numéricos." >&2
  exit 1
fi

PAYLOAD="$(python3 - <<'PY'
import json, os
print(json.dumps({
    "id": "chatwoot",
    "app": "chatwoot",
    "session": "default",
    "config": {
        "accountId": int(os.environ.get("CHATWOOT_ACCOUNT_ID") or "1"),
        "accountToken": os.environ["CHATWOOT_ACCOUNT_TOKEN"],
        "inboxId": int(os.environ["CHATWOOT_INBOX_ID"]),
        "inboxIdentifier": os.environ["CHATWOOT_INBOX_IDENTIFIER"],
        "url": "http://chatwoot-web:3000",
        "reopenConversation": True,
        "autoCreateContact": True,
    },
}))
PY
)"

URL="$(waha_api_base)/api/apps/chatwoot"
echo "[INFO]: Registrando/atualizando o app Chatwoot no WAHA..."
if ! RESPONSE="$(curl --silent --show-error --connect-timeout 5 --max-time 30 \
  --write-out $'\n%{http_code}' -X PUT "$URL" \
  -H "X-Api-Key: ${WAHA_API_KEY}" \
  -H "Content-Type: application/json" \
  --data-binary "$PAYLOAD")"; then
  echo "[ERRO]: Não foi possível conectar à API do WAHA para registrar o app Chatwoot." >&2
  exit 1
fi

STATUS="$(http_status "$RESPONSE")"
if is_http_success "$STATUS"; then
  echo "[SUCESSO]: App Chatwoot registrado/atualizado no WAHA."
else
  echo "[ERRO]: Registro do app Chatwoot falhou (HTTP ${STATUS:-desconhecido})." >&2
  exit 1
fi
