import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Let's test Identificar modalidade e normalizar anexos in bf1MReoTnd7QMPBC
item_json = {
  "body": {
    "event": "message_created",
    "id": 547,
    "content": None,
    "created_at": "2026-10-26T03:43:28.248395",
    "message_type": "incoming",
    "content_type": "text",
    "content_attributes": None,
    "sender": {"id": 2, "name": "Gabriel Bassani"},
    "account": {"id": 1, "name": "Fatec"},
    "conversation": {"id": 39, "display_id": 39},
    "attachments": [
      {
        "id": 72,
        "message_id": 547,
        "file_type": "audio",
        "account_id": 1,
        "extension": "oga",
        "content_type": "audio/opus",
        "data_url": "https://chatwoot.fatecn8nabc.dpdns.org/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBXUT09IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--2c9d909fe14e849bdddd4e69e662b125a95b61cf/no-filename.oga",
        "file_size": 58411
      }
    ]
  },
  "accountId": "1",
  "conversationId": "39",
  "displayId": "39",
  "messageId": "547",
  "inputType": "audio",
  "routeIndex": 1,
  "caption": "",
  "contentText": "",
  "userTextChars": 0,
  "normalizationStatus": "pending",
  "attachmentCount": 1,
  "attachments": [
    {
      "id": "72",
      "kind": "audio",
      "fileType": "audio",
      "mimeType": "audio/opus",
      "extension": "oga",
      "fileName": "",
      "dataUrl": "https://chatwoot.fatecn8nabc.dpdns.org/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBXUT09IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--2c9d909fe14e849bdddd4e69e662b125a95b61cf/no-filename.oga",
      "sizeBytes": 58411,
      "durationSeconds": None
    }
  ]
}

wf = json.load(open('workflows/subworkflows/Subworkflow - Normalização multimodal Chatwoot.json', encoding='utf-8'))
for n in wf['nodes']:
    if n['name'] == 'Identificar modalidade e normalizar anexos':
        code = n['parameters']['jsCode']
        break

test_js = f"""
const $json = {json.dumps(item_json)};
let $binary = undefined;
const run = () => {{
  {code}
}};
console.log(JSON.stringify(run(), null, 2));
"""

cmd = ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', test_js]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Identificar modalidade output:\n", res.stdout)
print("Stderr:\n", res.stderr)
