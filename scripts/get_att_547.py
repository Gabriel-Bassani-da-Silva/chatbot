import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'chatwoot_production', '-t', '-A',
    '-c', 'SELECT json_agg(t) FROM attachments t WHERE message_id = 547;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Attachments for 547:\n", res.stdout.strip())
