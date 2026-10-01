import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PostgresInitTests(unittest.TestCase):
    def test_chatwoot_role_password_comes_from_environment(self):
        sql = (ROOT / "postgres-init.sql").read_text(encoding="utf-8")
        self.assertRegex(
            sql,
            r"(?m)^\\getenv chatwoot_password CHATWOOT_POSTGRES_PASSWORD$",
        )
        self.assertRegex(
            sql,
            r"(?m)^CREATE USER chatwoot WITH PASSWORD :'chatwoot_password';$",
        )
        self.assertNotRegex(
            sql,
            r"(?i)CREATE USER chatwoot WITH PASSWORD\s+'[^']*'",
        )

    def test_postgres_service_passes_password_variable_to_init_process(self):
        compose = (ROOT / "compose.yml").read_text(encoding="utf-8")
        match = re.search(
            r"(?ms)^  postgres:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)",
            compose,
        )
        self.assertIsNotNone(match)
        postgres_service = match.group(1)
        self.assertIn(
            "CHATWOOT_POSTGRES_PASSWORD: ${CHATWOOT_POSTGRES_PASSWORD:?CHATWOOT_POSTGRES_PASSWORD is required}",
            postgres_service,
        )


if __name__ == "__main__":
    unittest.main()
