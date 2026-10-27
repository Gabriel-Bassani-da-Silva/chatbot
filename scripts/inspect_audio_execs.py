import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect execution 1233, 1234, 1235, 1236, 1237
for exec_id in [1233, 1234, 1235, 1236, 1237]:
    cmd = [
        'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
        'chatbot_n8n-postgres-1',
        'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
        '-c', f'SELECT id, "workflowId", status, "startedAt", "stoppedAt" FROM execution_entity WHERE id = {exec_id};'
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    print(f"Exec {exec_id}: {res.stdout.strip()}")
