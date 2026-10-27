import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT data FROM execution_data WHERE "executionId" = 1264;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
if not res.stdout.strip():
    print("No data found for 1254")
    # let's find latest execution with data
    cmd2 = [
        'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
        'chatbot_n8n-postgres-1',
        'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
        '-c', 'SELECT "executionId" FROM execution_data ORDER BY "executionId" DESC LIMIT 5;'
    ]
    res2 = subprocess.run(cmd2, capture_output=True, text=True, encoding='utf-8')
    print("Latest in execution_data:", res2.stdout.strip().splitlines())
else:
    d = json.loads(res.stdout.strip())
    if isinstance(d, dict):
        print("Keys in 1254 data:", list(d.keys()))
        run_data = d.get('resultData', {}).get('runData', {})
        print("Run nodes:", list(run_data.keys()))
    else:
        print("d[2] keys:", list(d[2].keys()))
        if 'error' in d[2]:
            print("Error:", d[int(d[2]['error'])])
        if 'runData' in d[2]:
            run_data_idx = int(d[2]['runData'])
            print("RunData keys in 1261:", list(d[run_data_idx].keys()))




