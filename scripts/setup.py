#!/usr/bin/env python3
"""Orquestra a configuração inicial de Chatwoot e WAHA a partir da raiz do projeto.

Requisitos: Python 3.9+, Bash e curl. O script não imprime tokens e pode ser
retomado depois de uma falha parcial sem recriar Inbox/Agent Bot já registrados.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from envfile import read_env

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
SCRIPTS: List[Tuple[str, str]] = [
    ("Chatwoot: criar ou reutilizar Inbox 'WhatsApp WAHA'", "scripts/chatwoot/1_create_inbox.sh"),
    ("Chatwoot: criar/reutilizar Agent Bot e vinculá-lo à Inbox", "scripts/chatwoot/2_create_agent_bot.sh"),
    ("WAHA: criar ou confirmar sessão 'default'", "scripts/waha/2_create_session.sh"),
    ("WAHA: registrar/atualizar app Chatwoot", "scripts/waha/1_setup_chatwoot_app.sh"),
]


def abort(message: str, code: int = 1) -> None:
    print("\n[ERRO]: %s" % message, file=sys.stderr)
    raise SystemExit(code)


def header(message: str) -> None:
    print("\n%s\n  %s\n%s" % ("=" * 66, message, "=" * 66))


def configured_domain(domain: str) -> bool:
    if not domain or "SEU_DOMINIO" in domain or "AQUI" in domain:
        return False
    return bool(re.fullmatch(r"(?:[A-Za-z0-9-]+\.)*[A-Za-z0-9-]+(?::[0-9]{1,5})?", domain))


def validate_port(values: Dict[str, str], name: str, default: str) -> None:
    value = values.get(name, "") or default
    if not value.isdigit() or not 1 <= int(value) <= 65535:
        abort("%s precisa ser uma porta entre 1 e 65535." % name)


def preflight(values: Dict[str, str]) -> None:
    required = ("DOMAIN", "CHATWOOT_FRONTEND_URL", "CHATWOOT_ACCOUNT_TOKEN", "WAHA_API_KEY")
    missing = [key for key in required if not values.get(key, "").strip()]
    if missing:
        abort("Preencha no .env antes de iniciar: %s." % ", ".join(missing))

    if not configured_domain(values["DOMAIN"].strip()):
        abort("DOMAIN deve conter o hostname público configurado, sem protocolo/caminho e sem o placeholder do .env.example.")

    frontend = urlparse(values["CHATWOOT_FRONTEND_URL"].strip())
    if frontend.scheme not in ("http", "https") or not frontend.netloc or "SEU_DOMINIO" in frontend.netloc:
        abort("CHATWOOT_FRONTEND_URL precisa ser uma URL http(s) pública válida, sem placeholders.")

    webhook = values.get("WEBHOOK_URL", "").strip()
    if webhook:
        parsed_webhook = urlparse(webhook)
        if parsed_webhook.scheme not in ("http", "https") or not parsed_webhook.netloc:
            abort("WEBHOOK_URL, quando preenchida, precisa ser uma URL http(s) válida.")

    validate_port(values, "CHATWOOT_PORT", "3001")
    validate_port(values, "WAHA_PORT", "3000")
    account_id = values.get("CHATWOOT_ACCOUNT_ID", "") or "1"
    if not account_id.isdigit() or int(account_id) < 1:
        abort("CHATWOOT_ACCOUNT_ID precisa ser um inteiro positivo.")

    inbox_id = values.get("CHATWOOT_INBOX_ID", "").strip()
    inbox_identifier = values.get("CHATWOOT_INBOX_IDENTIFIER", "").strip()
    if bool(inbox_id) != bool(inbox_identifier):
        abort("CHATWOOT_INBOX_ID e CHATWOOT_INBOX_IDENTIFIER precisam estar preenchidos juntos ou ambos vazios.")
    if inbox_id and not inbox_id.isdigit():
        abort("CHATWOOT_INBOX_ID precisa ser numérico.")

    bot_id = values.get("CHATWOOT_BOT_ID", "").strip()
    bot_token = values.get("CHATWOOT_BOT_TOKEN", "").strip()
    if bot_token and not bot_id:
        abort("CHATWOOT_BOT_TOKEN existe, mas CHATWOOT_BOT_ID está vazio; corrija o estado antes de evitar a criação de um Bot duplicado.")
    if bot_id and not bot_id.isdigit():
        abort("CHATWOOT_BOT_ID precisa ser numérico.")


def secret_values(values: Dict[str, str]) -> List[str]:
    secrets = []
    for key, value in values.items():
        if value and key.upper().endswith(("_TOKEN", "_PASSWORD", "_SECRET", "_KEY")):
            secrets.append(value)
    return sorted(set(secrets), key=len, reverse=True)


def redact(text: str, secrets: List[str]) -> str:
    for secret in secrets:
        text = text.replace(secret, "[REDACTED]")
    text = re.sub(
        r"(?i)(api_access_token|access_token|x-api-key)(\s*[:=]\s*)[^\s,}\"']+",
        r"\1\2[REDACTED]",
        text,
    )
    return text


def run_script(script_path: Path, values: Dict[str, str], timeout: int = 90) -> int:
    if not script_path.is_file():
        abort("Script não encontrado: %s" % script_path.relative_to(ROOT))

    env = os.environ.copy()
    env.update(values)
    try:
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        abort("Bash não encontrado. Instale Bash (Linux, WSL ou Git Bash) e tente novamente.")
    except subprocess.TimeoutExpired as exc:
        if exc.stdout:
            output = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout
            print(redact(output, secret_values(values)).rstrip())
        abort("A etapa excedeu %d segundos; nenhuma etapa seguinte foi iniciada." % timeout, 124)

    secrets = secret_values(values)
    if result.stdout.strip():
        print(redact(result.stdout, secrets).rstrip())
    if result.stderr.strip():
        print(redact(result.stderr, secrets).rstrip(), file=sys.stderr)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Configura a integração Chatwoot/WAHA em etapas retomáveis.")
    parser.add_argument("--dry-run", action="store_true", help="valida .env e mostra a sequência, sem chamar serviços")
    parser.add_argument("--timeout", type=int, default=90, help="timeout por etapa em segundos (padrão: 90)")
    args = parser.parse_args()

    if args.timeout < 1:
        abort("--timeout precisa ser maior que zero.")
    if not ENV_FILE.is_file():
        abort("Arquivo .env não encontrado. Copie .env.example para .env e preencha os valores.")

    try:
        values = read_env(ENV_FILE)
    except (OSError, UnicodeError, ValueError) as exc:
        abort("Não foi possível ler .env: %s" % exc)
    preflight(values)

    header("Setup Chatwoot + WAHA")
    print("Raiz do projeto: %s" % ROOT)
    print("Segredos serão gravados no .env e mascarados na saída do orquestrador.")

    if args.dry_run:
        print("\n[DRY-RUN]: validação aprovada; nenhuma API foi chamada.")
        for index, (label, relative_path) in enumerate(SCRIPTS, start=1):
            print("  [%d/%d] %s (%s)" % (index, len(SCRIPTS), label, relative_path))
        return

    for index, (label, relative_path) in enumerate(SCRIPTS, start=1):
        print("\n[%d/%d] %s" % (index, len(SCRIPTS), label))
        return_code = run_script(ROOT / relative_path, values, timeout=args.timeout)
        if return_code != 0:
            abort("Etapa falhou (%s, código %d). As etapas seguintes não foram executadas; corrija o problema e rode novamente para retomar." % (relative_path, return_code), return_code)
        # Scripts persistem a saída diretamente no .env. Re-read it so the next
        # child receives newly generated Inbox/Bot values, without logging them.
        try:
            values = read_env(ENV_FILE)
        except (OSError, UnicodeError, ValueError) as exc:
            abort("A etapa terminou, mas não foi possível reler .env: %s" % exc)

    port = values.get("WAHA_PORT", "") or "3000"
    header("Setup concluído")
    print("Dashboard WAHA: http://localhost:%s/dashboard" % port)
    print("Próximo passo: confirme a sessão e escaneie o QR Code pelo Dashboard do WAHA.")
    print("Para repetir com segurança, execute novamente este setup; Inbox e Agent Bot salvos são reutilizados.")


if __name__ == "__main__":
    main()
