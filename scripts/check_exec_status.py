import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT id, "workflowId", status, "startedAt", "stoppedAt" FROM execution_entity WHERE id >= 1233;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Executions >= 1233:\n", res.stdout.strip())
