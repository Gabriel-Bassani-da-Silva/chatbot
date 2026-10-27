import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT id, "workflowId", status, "startedAt" FROM execution_entity ORDER BY id DESC LIMIT 15;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Stdout:\n", res.stdout)
print("Stderr:\n", res.stderr)
