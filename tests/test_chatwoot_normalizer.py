import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NODE = PROJECT_ROOT / "nodes" / "chatwoot_normalizer.js"


class ChatwootNormalizerTests(unittest.TestCase):
    def run_node(self, payload: dict) -> dict:
        script = r"""
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
const payload = JSON.parse(process.argv[2]);
const result = vm.runInNewContext(`(function () {\n${source}\n})()`, {
  $json: payload,
  $binary: undefined,
});
process.stdout.write(JSON.stringify(result));
"""
        completed = subprocess.run(
            ["node", "-e", script, str(NODE), json.dumps(payload)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_incoming_message_is_normalized(self) -> None:
        result = self.run_node(
            {
                "event": "message_created",
                "id": 9003,
                "message_type": "incoming",
                "content": "Olá",
                "private": False,
                "conversation": {"id": 322},
                "sender": {"id": 78},
            }
        )

        self.assertTrue(result["json"]["process"])
        self.assertEqual(result["json"]["source"], "chatwoot")
        self.assertEqual(result["json"]["session_id"], "chatwoot:322")
        self.assertEqual(result["json"]["conversation_id"], "322")
        self.assertEqual(result["json"]["message_id"], "9003")

    def test_outgoing_message_is_ignored_without_return_array(self) -> None:
        result = self.run_node(
            {
                "event": "message_created",
                "id": 9004,
                "message_type": "outgoing",
                "content": "Resposta do bot",
                "private": False,
                "conversation": {"id": 322},
            }
        )

        self.assertFalse(result["json"]["process"])
        self.assertEqual(result["json"]["message_id"], "9004")

    def test_private_message_is_ignored(self) -> None:
        result = self.run_node(
            {
                "event": "message_created",
                "id": 9005,
                "message_type": "incoming",
                "content": "Nota interna",
                "private": True,
                "conversation": {"id": 322},
            }
        )

        self.assertFalse(result["json"]["process"])


if __name__ == "__main__":
    unittest.main()
