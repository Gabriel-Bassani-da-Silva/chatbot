import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Test if global fetch, FormData, Blob are accessible in n8n's Code node runner
test_js = """
console.log('fetch:', typeof fetch);
console.log('FormData:', typeof FormData);
console.log('Blob:', typeof Blob);
console.log('Buffer:', typeof Buffer);
"""

cmd = ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', test_js]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Output:\n", res.stdout)
