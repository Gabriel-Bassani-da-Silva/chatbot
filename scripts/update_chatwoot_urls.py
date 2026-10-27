import json

path = 'workflows/Agente RAG Fatec.json'
with open(path, 'r', encoding='utf-8') as f:
    wf = json.load(f)

for node in wf['nodes']:
    url = node.get('parameters', {}).get('url', '')
    if 'chatwoot-web:3000/api/v1/accounts/' in url:
        new_url = "=http://chatwoot-web:3000/api/v1/accounts/{{ $('Webhook Chatwoot RAG').item.json.body.account?.id || 1 }}/conversations/{{ $('Webhook Chatwoot RAG').item.json.body.conversation.id }}/messages"
        node['parameters']['url'] = new_url
        print(f"Updated url in node: {node['name']}")

with open(path, 'w', encoding='utf-8') as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write('\n')

print("Updated Chatwoot outgoing URLs with account?.id || 1 fallback.")
