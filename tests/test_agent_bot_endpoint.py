import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "chatwoot" / "2_create_agent_bot.sh"


class AgentBotEndpointTests(unittest.TestCase):
    def test_association_uses_set_agent_bot_post_route(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertRegex(
            source,
            re.compile(r"-X POST[\s\\]*[\s\\]*\"\$\{CHATWOOT_BASE\}/api/v1/accounts/\$\{ACCOUNT_ID\}/inboxes/\$\{CHATWOOT_INBOX_ID\}/set_agent_bot\""),
        )


if __name__ == "__main__":
    unittest.main()
