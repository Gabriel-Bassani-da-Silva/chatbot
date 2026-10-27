import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT json_build_object(\'id\', id, \'workflowId\', "workflowId", \'status\', status, \'startedAt\', "startedAt", \'stoppedAt\', "stoppedAt") FROM execution_entity WHERE id = 1235;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Execution 1235 row:\n", res.stdout.strip())
