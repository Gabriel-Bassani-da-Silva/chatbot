import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Get message 547 and conversation 39 from chatwoot_production
cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'chatwoot_production', '-t', '-A',
    '-c', """
    SELECT json_build_object(
        'event', 'message_created',
        'id', m.id,
        'content', m.content,
        'created_at', m.created_at,
        'message_type', 'incoming',
        'content_type', 'text',
        'content_attributes', m.content_attributes,
        'sender', json_build_object('id', m.sender_id, 'name', 'Gabriel Bassani'),
        'account', json_build_object('id', m.account_id, 'name', 'Fatec'),
        'conversation', json_build_object('id', m.conversation_id, 'display_id', m.conversation_id),
        'attachments', (SELECT json_agg(json_build_object(
            'id', a.id,
            'message_id', a.message_id,
            'file_type', 'audio',
            'account_id', a.account_id,
            'extension', a.extension,
            'content_type', 'audio/opus',
            'data_url', 'https://chatwoot.fatecn8nabc.dpdns.org/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBXUT09IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--2c9d909fe14e849bdddd4e69e662b125a95b61cf/no-filename.oga',
            'file_size', 58411
        )) FROM attachments a WHERE a.message_id = m.id)
    ) FROM messages m WHERE m.id = 547;
    """
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Payload from DB:\n", res.stdout.strip())
