import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

sql = """
SELECT e.id, e.status, e.mode, e."startedAt", e."stoppedAt", COALESCE(w.name, e."workflowId") as workflow_name
FROM execution_entity e
LEFT JOIN workflow_entity w ON w.id = e."workflowId"
ORDER BY e.id DESC LIMIT 20;
"""

cmd = ['docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8', '-i', 'chatbot_n8n-postgres-1', 'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A']
res = subprocess.run(cmd, input=sql.encode('utf-8'), capture_output=True)
lines = res.stdout.decode('utf-8', errors='replace').strip().split('\n')

print(f"{'ID':<6} | {'STATUS':<10} | {'DURAÇÃO (s)':<12} | {'HORÁRIO (UTC)':<20} | {'WORKFLOW'}")
print("-" * 80)

for line in lines:
    if not line.strip() or '|' not in line:
        continue
    parts = line.split('|')
    eid = parts[0]
    status = parts[1]
    mode = parts[2]
    started = parts[3]
    stopped = parts[4] if len(parts) > 4 else ""
    wname = parts[5] if len(parts) > 5 else ""
    
    duration = "N/A"
    if started and stopped:
        try:
            from datetime import datetime
            t1 = datetime.fromisoformat(started.replace('Z', '+00:00'))
            t2 = datetime.fromisoformat(stopped.replace('Z', '+00:00'))
            duration = f"{(t2 - t1).total_seconds():.2f}s"
        except:
            pass

    start_str = started.split('.')[0] if started else ""
    print(f"{eid:<6} | {status:<10} | {duration:<12} | {start_str:<20} | {wname}")
