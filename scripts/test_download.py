import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_js = """
async function run() {
  const url = 'https://chatwoot.fatecn8nabc.dpdns.org/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBXUT09IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--2c9d909fe14e849bdddd4e69e662b125a95b61cf/no-filename.oga';
  const res = await fetch(url, { redirect: 'manual' });
  console.log('Manual redirect status:', res.status);
  console.log('Location:', res.headers.get('location'));
  const res2 = await fetch(url, { redirect: 'follow' });
  console.log('Follow redirect status:', res2.status, 'url:', res2.url);
  const buf = await res2.arrayBuffer();
  console.log('Downloaded bytes:', buf.byteLength);
}
run().catch(console.error);
"""

cmd = ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', test_js]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Stdout:\n", res.stdout)
print("Stderr:\n", res.stderr)
