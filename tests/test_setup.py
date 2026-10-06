import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

SPEC = importlib.util.spec_from_file_location("n8n_setup", PROJECT_ROOT / "scripts" / "setup.py")
assert SPEC is not None and SPEC.loader is not None
setup_script = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup_script)


class RunScriptTests(unittest.TestCase):
    def test_bash_receives_relative_posix_path_and_root_cwd(self) -> None:
        relative_path = "scripts/chatwoot/1_create_inbox.sh"
        script_path = PROJECT_ROOT / relative_path
        completed = SimpleNamespace(stdout="", stderr="", returncode=0)

        with patch.object(setup_script.subprocess, "run", return_value=completed) as run:
            result = setup_script.run_script(script_path, {}, timeout=17)

        self.assertEqual(result, 0)
        self.assertEqual(run.call_args.args[0], ["bash", relative_path])
        self.assertEqual(run.call_args.kwargs["cwd"], str(PROJECT_ROOT))
        self.assertEqual(run.call_args.kwargs["timeout"], 17)


class PreflightWebhookTests(unittest.TestCase):
    @staticmethod
    def valid_values() -> dict:
        return {
            "DOMAIN": "example.test",
            "CHATWOOT_FRONTEND_URL": "https://chatwoot.example.test",
            "CHATWOOT_ACCOUNT_TOKEN": "synthetic-account-token",
            "WAHA_API_KEY": "synthetic-waha-key",
            "N8N_WEBHOOK_URL": "https://n8n.example.test",
        }

    def test_accepts_current_n8n_webhook_variable(self) -> None:
        setup_script.preflight(self.valid_values())

    def test_accepts_legacy_webhook_variable_as_fallback(self) -> None:
        values = self.valid_values()
        values.pop("N8N_WEBHOOK_URL")
        values["WEBHOOK_URL"] = "https://legacy.example.test"

        setup_script.preflight(values)

    def test_rejects_invalid_current_webhook_even_if_legacy_value_is_valid(self) -> None:
        values = self.valid_values()
        values["N8N_WEBHOOK_URL"] = "not-a-url"
        values["WEBHOOK_URL"] = "https://legacy.example.test"

        with patch.object(setup_script, "abort", side_effect=SystemExit(1)):
            with self.assertRaises(SystemExit):
                setup_script.preflight(values)


if __name__ == "__main__":
    unittest.main()
