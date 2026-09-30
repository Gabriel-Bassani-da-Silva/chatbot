#!/usr/bin/env bash
# Shared helpers used by the Chatwoot and WAHA setup scripts.

set -Eeuo pipefail

setup_init() {
  local caller_dir
  caller_dir="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
  PROJECT_ROOT="$(cd "$caller_dir/../.." && pwd)"
  ENV_FILE="$PROJECT_ROOT/.env"
  ENVFILE_TOOL="$PROJECT_ROOT/scripts/envfile.py"

  if [[ ! -f "$ENV_FILE" ]]; then
    echo "[ERRO]: Arquivo .env não encontrado em: $ENV_FILE" >&2
    exit 1
  fi
  if [[ ! -f "$ENVFILE_TOOL" ]]; then
    echo "[ERRO]: Utilitário scripts/envfile.py não encontrado." >&2
    exit 1
  fi

  local key value
  while IFS= read -r -d '' key && IFS= read -r -d '' value; do
    export "$key=$value"
  done < <(python3 "$ENVFILE_TOOL" export0 "$ENV_FILE")
}

require_vars() {
  local name
  for name in "$@"; do
    if [[ -z "${!name:-}" ]]; then
      echo "[ERRO]: Variável $name ausente ou vazia no .env." >&2
      exit 1
    fi
  done
}

chatwoot_account_id() {
  printf '%s' "${CHATWOOT_ACCOUNT_ID:-1}"
}

chatwoot_api_base() {
  printf 'http://localhost:%s' "${CHATWOOT_PORT:-3001}"
}

waha_api_base() {
  printf 'http://localhost:%s' "${WAHA_PORT:-3000}"
}

persist_env_values() {
  if (( $# == 0 || $# % 2 != 0 )); then
    echo "[ERRO]: persist_env_values precisa receber pares KEY VALUE." >&2
    return 2
  fi
  local key value
  {
    while (( $# > 0 )); do
      key="$1"
      value="$2"
      shift 2
      printf '%s\0%s\0' "$key" "$value"
    done
  } | python3 "$ENVFILE_TOOL" set0 "$ENV_FILE"
}

persist_env_value() {
  persist_env_values "$1" "$2"
}

json_field() {
  local field="$1"
  python3 -c '
import json, sys
field = sys.argv[1]
try:
    value = json.load(sys.stdin)
    for part in field.split("."):
        value = value[part]
    if value is None:
        raise KeyError(field)
    print(value if isinstance(value, (str, int, float, bool)) else "")
except Exception:
    raise SystemExit(1)
' "$field"
}

http_status() {
  printf '%s' "${1##*$'\n'}"
}

http_body() {
  printf '%s' "${1%$'\n'*}"
}

is_http_success() {
  [[ "$1" == "200" || "$1" == "201" || "$1" == "202" || "$1" == "204" ]]
}
