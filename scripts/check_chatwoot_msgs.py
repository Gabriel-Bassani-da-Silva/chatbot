import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'chatwoot_production', '-t', '-A',
    '-c', 'SELECT id, message_type, content, created_at FROM messages ORDER BY id DESC LIMIT 6;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Recent Chatwoot messages:\n", res.stdout.strip())
