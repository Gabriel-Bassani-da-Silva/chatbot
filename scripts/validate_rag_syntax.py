import json
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('workflows/Agente RAG Fatec.json', 'r', encoding='utf-8') as f:
    wf = json.load(f)

for node in wf['nodes']:
    if node['type'] == 'n8n-nodes-base.code':
        code = node.get('parameters', {}).get('jsCode', '')
        name = node.get('name', 'unnamed')
        if not code:
            continue
        test_script = f"""
        const code = {json.dumps(code)};
        try {{
            new Function('$input', '$json', '$', code);
            console.log("OK");
        }} catch(e) {{
            console.error("SYNTAX ERROR in node '{name}':", e.message);
            process.exit(1);
        }}
        """
        res = subprocess.run(['docker', 'exec', '-i', 'chatbot_n8n-n8n-1', 'node'], input=test_script.encode('utf-8'), capture_output=True)
        if res.returncode != 0:
            print(f"FAILED node: '{name}'")
            print(res.stderr.decode('utf-8'))
        else:
            print(f"[VALID] Code node: '{name}'")
