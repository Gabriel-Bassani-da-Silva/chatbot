import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', "SELECT id, name, nodes FROM workflow_entity WHERE id IN ('bt9Uy01vkUsIgq2V', 'EvumHYCUx2nTIL7U');"
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print(res.stdout[:500])
