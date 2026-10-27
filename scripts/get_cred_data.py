import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', "SELECT id, name, type, data FROM credentials_entity WHERE id = 'RU2a92xV2to4mSwo';"
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Credential row:\n", res.stdout.strip())
