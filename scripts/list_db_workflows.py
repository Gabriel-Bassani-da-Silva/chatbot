import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT json_agg(json_build_object(\'id\', id, \'name\', name, \'active\', active, \'isArchived\', "isArchived")) FROM workflow_entity;'
]

res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode != 0:
    print("Error:", res.stderr)
    sys.exit(1)

data = json.loads(res.stdout.strip())
for row in sorted(data, key=lambda x: (not x['active'], x['isArchived'], x['name'])):
    print(f"{row['id']:<20} | active: {str(row['active']):<5} | archived: {str(row['isArchived']):<5} | {row['name']}")
