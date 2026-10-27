import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

item_from_splitout = {
  "source": "chatwoot",
  "channel": "chatwoot",
  "accountId": "1",
  "conversationId": "39",
  "messageId": "547",
  "senderId": "2",
  "sessionId": "chatwoot:39",
  "chatwootEvent": "message_created",
  "messageType": "incoming",
  "inputType": "attachments",
  "caption": "",
  "contentText": "",
  "normalizationStatus": "pending",
  "normalizationPendingStep": "",
  "attachmentCount": 1,
  "attachmentItem": {
    "id": "72",
    "kind": "audio",
    "fileType": "audio",
    "mimeType": "audio/opus",
    "extension": "oga",
    "fileName": "",
    "dataUrl": "https://chatwoot.fatecn8nabc.dpdns.org/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBXUT09IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--2c9d909fe14e849bdddd4e69e662b125a95b61cf/no-filename.oga",
    "thumbnailUrl": "",
    "sizeBytes": 58411,
    "durationSeconds": None,
    "downloadAvailable": True,
    "processingStatus": "pending"
  },
  "fromMe": False
}

wf = json.load(open('workflows/subworkflows/Processar anexos — Normalização multimodal Chatwoot.json', encoding='utf-8'))
for n in wf['nodes']:
    if n['name'] == 'Validar URL e formato':
        code = n['parameters']['jsCode']
        break

test_js = f"""
const $json = {json.dumps(item_from_splitout)};
const run = () => {{
  {code}
}};
console.log(JSON.stringify(run(), null, 2));
"""

cmd = ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', test_js]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Validar URL e formato output:\n", res.stdout)
print("Stderr:\n", res.stderr)
