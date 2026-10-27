import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

sql = '''SELECT "executionId", data FROM execution_data ORDER BY "executionId" DESC LIMIT 1;'''
cmd = ['docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8', '-i', 'chatbot_n8n-postgres-1', 'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A']
res = subprocess.run(cmd, input=sql.encode('utf-8'), capture_output=True)
out = res.stdout.decode('utf-8', errors='replace').strip()

if '|' in out:
    eid, data_str = out.split('|', 1)
    print(f"Latest Execution with data: {eid}")
    try:
        data = json.loads(data_str)
        if isinstance(data, list):
            print("Data is a list of length:", len(data))
            for i, d in enumerate(data):
                if isinstance(d, str):
                    try:
                        d = json.loads(d)
                    except:
                        pass
                if isinstance(d, dict):
                    err = d.get('resultData', {}).get('error', {})
                    if err:
                        print(f"Item {i} Error message:", err.get('message'))
                        print(f"Item {i} Error node:", err.get('node', {}).get('name'))
                    run_data = d.get('resultData', {}).get('runData', {})
                    if run_data:
                        print(f"Item {i} runData keys:", list(run_data.keys()))
        elif isinstance(data, dict):
            err = data.get('resultData', {}).get('error', {})
            print("Error message:", err.get('message'))
            print("Error node:", err.get('node', {}).get('name'))
            print("Error stack:", err.get('stack', '')[:300])
    except Exception as e:
        print("JSON parse error:", e)
else:
    print("No execution data output.")
