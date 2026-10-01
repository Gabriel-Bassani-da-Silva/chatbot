import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from envfile import read_env  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "reset_state", PROJECT_ROOT / "scripts" / "reset_state.py"
)
assert SPEC is not None and SPEC.loader is not None
reset_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reset_state)


class ResetStateTests(unittest.TestCase):
    def test_clears_only_chatwoot_runtime_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            env_path = root / ".env"
            env_path.write_text(
                "POSTGRES_PASSWORD=synthetic-test-value\n"
                "CHATWOOT_ACCOUNT_TOKEN=synthetic-token\n"
                "CHATWOOT_INBOX_ID=17\n"
                "CHATWOOT_INBOX_IDENTIFIER=synthetic-inbox\n"
                "CUSTOM_SETTING=keep\n",
                encoding="utf-8",
            )

            with patch.object(reset_state, "ROOT", root):
                with contextlib.redirect_stdout(io.StringIO()):
                    reset_state.main()

            values = read_env(env_path)
            for key in reset_state.VOLATILE_KEYS:
                with self.subTest(key=key):
                    self.assertEqual(values[key], "")
            self.assertEqual(values["POSTGRES_PASSWORD"], "synthetic-test-value")
            self.assertEqual(values["CUSTOM_SETTING"], "keep")

    def test_missing_env_exits_without_creating_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch.object(reset_state, "ROOT", root):
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        reset_state.main()

            self.assertEqual(raised.exception.code, 1)
            self.assertFalse((root / ".env").exists())


if __name__ == "__main__":
    unittest.main()
