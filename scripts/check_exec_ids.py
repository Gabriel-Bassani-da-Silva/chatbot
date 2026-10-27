import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT "executionId", length(data) FROM execution_data WHERE "executionId" IN (\'1238\', \'1239\');'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Execution data lengths:\n", res.stdout.strip())
