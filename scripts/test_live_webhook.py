import requests
import json
import subprocess
import time

payload = {
    "event": "message_created",
    "id": 999123,
    "content": "/fatec",
    "message_type": "incoming",
    "private": False,
    "conversation": {
        "id": 39,
        "display_id": 39,
        "meta": {
            "sender": {
                "id": 2,
                "name": "Gabriel Bassani",
                "phone_number": "+5517991516006",
                "custom_attributes": {
                    "waha_whatsapp_chat_id": "5517991516006@c.us"
                }
            }
        }
    },
    "account": {
        "id": 1
    }
}

print("Posting to webhook...")
try:
    resp = requests.post(
        "http://127.0.0.1:5678/webhook/chatwoot-rag-fatec-poc",
        json=payload,
        timeout=10
    )
    print("Webhook status:", resp.status_code)
except Exception as e:
    print("Error calling webhook:", e)

time.sleep(3)
# Check latest execution in n8n
cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT id, "workflowId", status, "startedAt" FROM execution_entity ORDER BY id DESC LIMIT 1;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Latest execution:", res.stdout.strip())
