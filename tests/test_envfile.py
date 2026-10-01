import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from envfile import read_env, update_env  # noqa: E402


class UpdateEnvTests(unittest.TestCase):
    def _update_and_read(self, initial: bytes, value: str) -> tuple[str, dict[str, str]]:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_bytes(initial)
            update_env(env_path, {"CHATWOOT_INBOX_ID": value})
            text = env_path.read_text(encoding="utf-8")
            return text, read_env(env_path)

    def test_empty_assignment_can_be_updated_without_splitting_line(self) -> None:
        for newline in (b"\n", b"\r\n"):
            with self.subTest(newline=newline):
                text, values = self._update_and_read(
                    b"CHATWOOT_INBOX_ID=" + newline + b"NEXT=kept" + newline,
                    "42",
                )
                self.assertEqual(values["CHATWOOT_INBOX_ID"], "42")
                self.assertEqual(values["NEXT"], "kept")
                self.assertEqual(len(text.splitlines()), 2)

    def test_empty_value_update_is_idempotent(self) -> None:
        for newline in (b"\n", b"\r\n"):
            with self.subTest(newline=newline):
                text, values = self._update_and_read(
                    b"CHATWOOT_INBOX_ID=" + newline + b"NEXT=kept" + newline,
                    "",
                )
                self.assertEqual(values["CHATWOOT_INBOX_ID"], "")
                self.assertEqual(values["NEXT"], "kept")
                self.assertEqual(len(text.splitlines()), 2)

    def test_export_and_horizontal_whitespace_are_preserved(self) -> None:
        text, values = self._update_and_read(
            b"export CHATWOOT_INBOX_ID \t= \t\nNEXT=kept\n",
            "42",
        )
        self.assertIn("export CHATWOOT_INBOX_ID \t= \t'42'\n", text)
        self.assertEqual(values["CHATWOOT_INBOX_ID"], "42")
        self.assertEqual(len(text.splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
