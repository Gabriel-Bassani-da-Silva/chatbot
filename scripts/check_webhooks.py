import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT "webhookPath", "method", "workflowId" FROM webhook_entity;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Webhook entities:\n", res.stdout.strip())
