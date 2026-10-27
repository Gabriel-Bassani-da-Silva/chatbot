import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

sql = """
SELECT id, message_type, content, created_at 
FROM messages 
WHERE conversation_id = 39 
ORDER BY id DESC LIMIT 25;
"""
cmd = ['docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8', '-i', 'chatbot_n8n-postgres-1', 'psql', '-U', 'postgres', '-d', 'chatwoot_production', '-t', '-A']
res = subprocess.run(cmd, input=sql.encode('utf-8'), capture_output=True)
raw = res.stdout.decode('utf-8', errors='replace').strip()

# Split rows carefully
rows = raw.split('\n')
for r in rows:
    if '|' not in r:
        continue
    parts = r.split('|')
    if len(parts) >= 4:
        mid = parts[0]
        mtype = "BOT (Robô)" if parts[1] == "1" else "USUÁRIO"
        created = parts[-1].split('.')[0] if len(parts) > 3 else ""
        content = "|".join(parts[2:-1]).replace('\n', ' ')[:90]
        print(f"[{created}] #{mid:<4} {mtype:<10}: {content}")
