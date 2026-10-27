import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT data FROM execution_data WHERE "executionId" = 1264;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
d = json.loads(res.stdout.strip())
for idx, item in enumerate(d):
    if isinstance(item, str):
        if any(k in item.lower() for k in ['estagio', 'big data', 'human', 'chat_history', 'input']):
            print(f"[{idx}] length={len(item)}: {repr(item[:200])}\n")

