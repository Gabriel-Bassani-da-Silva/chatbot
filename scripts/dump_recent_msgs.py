import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

sql = """
SELECT json_agg(row_to_json(m)) 
FROM (
    SELECT id, message_type, content, created_at 
    FROM messages 
    WHERE id >= 625 
    ORDER BY id ASC
) m;
"""
cmd = ['docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8', '-i', 'chatbot_n8n-postgres-1', 'psql', '-U', 'postgres', '-d', 'chatwoot_production', '-t', '-A']
res = subprocess.run(cmd, input=sql.encode('utf-8'), capture_output=True)
raw = res.stdout.decode('utf-8', errors='replace').strip()

msgs = json.loads(raw)
for m in msgs:
    mtype = "BOT" if m['message_type'] == 1 else "USER"
    print(f"=== Msg #{m['id']} ({mtype}) | {m['created_at'][:19]} ===")
    print(m['content'])
    print()
