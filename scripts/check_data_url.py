import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT "data" FROM execution_data WHERE "executionId" = 1233;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
d = json.loads(res.stdout.strip())
print("d[101] (data_url):", d[101])
