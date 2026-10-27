import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT e.id, e.status, d.data FROM execution_entity e JOIN execution_data d ON e.id = d."executionId" WHERE e."workflowId" = \'PUcBETeUWZ8fC251\' ORDER BY e.id DESC LIMIT 1;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
raw = res.stdout.strip()
if raw:
    parts = raw.split('|', 2)
    eid, status, payload = parts[0], parts[1], parts[2]
    print(f"Exec {eid} - Status: {status}")
    d = json.loads(payload)
    if isinstance(d, list) and len(d) > 0 and isinstance(d[0], dict):
        res_data = d[0].get('resultData')
        print("resultData:", res_data)
        if isinstance(res_data, int):
            print(f"res_data is index {res_data}:", d[res_data])
        if len(d) > 2 and 'runData' in d[2]:
            rd = d[2]['runData']
            print("rd type/value:", rd)
            if isinstance(rd, int):
                print(f"rd points to index {rd}:", d[rd])





