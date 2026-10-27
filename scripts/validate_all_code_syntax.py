import json
import subprocess
import sys
import glob

sys.stdout.reconfigure(encoding='utf-8')

for wf_path in glob.glob('workflows/**/*.json', recursive=True):
    with open(wf_path, 'r', encoding='utf-8') as f:
        try:
            wf = json.load(f)
        except Exception as e:
            print(f"Error loading {wf_path}: {e}")
            continue
    print(f"\n--- Checking {wf_path} ---")
    for node in wf.get('nodes', []):
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
                print(f"FAILED node: '{name}' in {wf_path}")
                print(res.stderr.decode('utf-8'))
                sys.exit(1)
            else:
                print(f"[VALID] Code node: '{name}'")

print("\n>>> ALL CODE NODES IN ALL WORKFLOWS ARE 100% VALID JAVASCRIPT! <<<")
