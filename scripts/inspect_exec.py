import subprocess
import json

def check_exec(exec_id):
    cmd = [
        'docker', 'exec', 'chatbot_n8n-postgres-1',
        'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
        '-c', f"SELECT status, data FROM execution_entity WHERE id = {exec_id};"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    raw = res.stdout.strip()
    if not raw or '|' not in raw:
        print(f"Exec {exec_id}: empty or no pipe")
        return
    parts = raw.split('|', 1)
    status = parts[0]
    print(f"=== Execution {exec_id} (Status: {status}) ===")
    if len(parts) > 1 and parts[1]:
        try:
            data = json.loads(parts[1])
            res_data = data.get('resultData', {})
            err = res_data.get('error')
            if err:
                print("ERROR:", err.get('message') or err)
            run_data = res_data.get('runData', {})
            print("Executed nodes:", list(run_data.keys()))
            for name, items in run_data.items():
                if 'output' in str(items):
                    for idx, it in enumerate(items):
                        main_out = it.get('data', {}).get('main', [])
                        print(f"  Node [{name}] item {idx} output keys:", [list(x.keys()) for x in main_out])
        except Exception as e:
            print("JSON parse error:", e)

if __name__ == '__main__':
    for eid in [1596, 1592, 1590, 1586, 1583]:
        check_exec(eid)
