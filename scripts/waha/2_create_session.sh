#!/usr/bin/env bash
# Cria a sessão default no WAHA; uma sessão existente é um resultado idempotente.
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib.sh"
setup_init
require_vars WAHA_API_KEY

WAHA_PORT_VALUE="${WAHA_PORT:-3000}"
if [[ ! "$WAHA_PORT_VALUE" =~ ^[0-9]+$ ]] || (( WAHA_PORT_VALUE < 1 || WAHA_PORT_VALUE > 65535 )); then
  echo "[ERRO]: WAHA_PORT inválida." >&2
  exit 1
fi

URL="$(waha_api_base)/api/sessions"
echo "[INFO]: Criando sessão 'default' no WAHA..."
if ! RESPONSE="$(curl --silent --show-error --connect-timeout 5 --max-time 30 \
  --write-out $'\n%{http_code}' -X POST "$URL" \
  -H "X-Api-Key: ${WAHA_API_KEY}" \
  -H "Content-Type: application/json" \
  --data-binary '{"name":"default"}')"; then
  echo "[ERRO]: Não foi possível conectar à API do WAHA para criar a sessão." >&2
  exit 1
fi

STATUS="$(http_status "$RESPONSE")"
if [[ "$STATUS" == "409" || "$STATUS" == "422" ]]; then
  echo "[INFO]: Sessão 'default' já existe; nenhuma ação necessária."
elif is_http_success "$STATUS"; then
  echo "[SUCESSO]: Sessão 'default' criada. Abra http://localhost:${WAHA_PORT_VALUE}/dashboard e escaneie o QR Code."
else
  echo "[ERRO]: Criação da sessão falhou (HTTP ${STATUS:-desconhecido})." >&2
  exit 1
fi
