#!/usr/bin/env python3
"""Valida os arquivos Compose sem iniciar containers ou usar credenciais reais."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

# Valores descartáveis usados somente para interpolar os arquivos Compose.
# Não copiar para um .env real nem usar em serviços.
SYNTHETIC_ENV: Dict[str, str] = {
    "DOMAIN": "example.test",
    "CHATWOOT_FRONTEND_URL": "https://chatwoot.example.test",
    "N8N_WEBHOOK_URL": "https://n8n.example.test",
    "N8N_EDITOR_BASE_URL": "https://n8n.example.test",
    "N8N_ENCRYPTION_KEY": "a" * 64,
    "POSTGRES_USER": "compose_test",
    "POSTGRES_PASSWORD": "compose-validation-postgres-only",
    "POSTGRES_DB": "n8n_test",
    "CHATWOOT_POSTGRES_USERNAME": "chatwoot_test",
    "CHATWOOT_POSTGRES_PASSWORD": "compose-validation-chatwoot-only",
    "CHATWOOT_SECRET_KEY_BASE": "b" * 64,
    "REDIS_PASSWORD": "compose-validation-redis-only",
    "WAHA_API_KEY": "compose-validation-waha-only",
    "WAHA_API_KEY_PLAIN": "compose-validation-waha-only",
    "WAHA_DASHBOARD_USERNAME": "compose_test",
    "WAHA_DASHBOARD_PASSWORD": "compose-validation-dashboard-only",
    "TUNNEL_TOKEN": "compose-validation-tunnel-only",
}


def _write_env(path: Path, values: Dict[str, str]) -> None:
    path.write_text("".join("%s=%s\n" % item for item in values.items()), encoding="utf-8")
    path.chmod(0o600)


def _compose_env(values: Dict[str, str]) -> Dict[str, str]:
    """Avoid caller environment values overriding the synthetic fixture."""
    env = os.environ.copy()
    for key in set(SYNTHETIC_ENV) | {"WEBHOOK_URL", "N8N_WEBHOOK_URL"}:
        env.pop(key, None)
    for key in list(env):
        if key.startswith("COMPOSE_"):
            env.pop(key, None)
    env.update(values)
    return env


def validate_configuration(label: str, compose_files: Iterable[str], env_values: Dict[str, str]) -> bool:
    with tempfile.TemporaryDirectory(prefix="n8n-compose-check-") as temp_dir:
        env_file = Path(temp_dir) / ".env.validation"
        _write_env(env_file, env_values)
        command: List[str] = [
            "docker",
            "compose",
            "--env-file",
            str(ROOT / "versions.env"),
            "--env-file",
            str(env_file),
        ]
        for compose_file in compose_files:
            command.extend(("-f", compose_file))
        command.extend(("config", "--quiet"))

        try:
            result = subprocess.run(
                command,
                cwd=str(ROOT),
                env=_compose_env(env_values),
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            print("Docker Compose CLI não está disponível; instale Docker Compose v2.", file=sys.stderr)
            return False

        if result.returncode:
            print("[FALHA] Configuração %s (código %d)." % (label, result.returncode), file=sys.stderr)
            if result.stderr.strip():
                print(result.stderr.rstrip(), file=sys.stderr)
            return False

    print("[OK] Configuração %s." % label)
    return True


def main() -> int:
    checks: List[Tuple[str, List[str], Dict[str, str]]] = [
        ("local com N8N_WEBHOOK_URL", ["compose.yml"], dict(SYNTHETIC_ENV)),
        (
            "pública com N8N_WEBHOOK_URL",
            ["compose.yml", "compose.public.yml"],
            dict(SYNTHETIC_ENV),
        ),
    ]
    legacy_env = dict(SYNTHETIC_ENV)
    legacy_env.pop("N8N_WEBHOOK_URL")
    legacy_env["WEBHOOK_URL"] = "https://n8n.example.test"
    checks.append(("local com WEBHOOK_URL legado", ["compose.yml"], legacy_env))

    failures = 0
    for label, compose_files, env_values in checks:
        if not validate_configuration(label, compose_files, env_values):
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
