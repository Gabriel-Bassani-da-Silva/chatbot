#!/usr/bin/env python3
"""Reseta as variáveis de estado do .env que dependem do banco de dados."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from envfile import update_env  # noqa: E402

VOLATILE_KEYS = {
    "CHATWOOT_ACCOUNT_TOKEN": "",
    "CHATWOOT_INBOX_ID": "",
    "CHATWOOT_INBOX_IDENTIFIER": "",
    "CHATWOOT_BOT_TOKEN": "",
    "CHATWOOT_BOT_ID": "",
    "CHATWOOT_BOT_LINKED_INBOX_ID": "",
}

def main() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("[ERRO] Arquivo .env não encontrado na raiz do projeto.")
        sys.exit(1)
        
    print("[INFO] Limpando variáveis de estado do banco de dados no .env...")
    update_env(env_path, VOLATILE_KEYS)
    print("[SUCESSO] Variáveis dinâmicas do Chatwoot resetadas!")
    print("Agora você pode recriar a infraestrutura (ex: docker compose down -v) e rodar o orquestrador do zero, sem conflitos.")

if __name__ == "__main__":
    main()
