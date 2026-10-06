import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import validate_compose  # noqa: E402


class ValidateComposeTests(unittest.TestCase):
    def test_checks_local_public_and_legacy_webhook_without_starting_containers(self) -> None:
        observed = []

        def fake_run(command, **kwargs):
            env_files = [
                Path(command[index + 1])
                for index, arg in enumerate(command[:-1])
                if arg == "--env-file"
            ]
            observed.append((command, env_files[-1].read_text(encoding="utf-8")))
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch.object(validate_compose.subprocess, "run", side_effect=fake_run) as run:
            result = validate_compose.main()

        self.assertEqual(result, 0)
        self.assertEqual(run.call_count, 3)
        self.assertIn("N8N_WEBHOOK_URL=https://n8n.example.test", observed[0][1])
        self.assertIn("-f", observed[1][0])
        self.assertIn("compose.public.yml", observed[1][0])
        self.assertIn("WEBHOOK_URL=https://n8n.example.test", observed[2][1])
        for command, _ in observed:
            self.assertEqual(command[-2:], ["config", "--quiet"])
            self.assertNotIn("up", command)

    def test_reports_compose_validation_failure(self) -> None:
        failed = SimpleNamespace(returncode=1, stdout="", stderr="invalid compose config")
        with patch.object(validate_compose.subprocess, "run", return_value=failed):
            self.assertEqual(validate_compose.main(), 1)


if __name__ == "__main__":
    unittest.main()
