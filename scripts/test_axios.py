import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_js = """
const axios = require('axios');
async function run() {
  const url = 'https://chatwoot.fatecn8nabc.dpdns.org/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBXUT09IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--2c9d909fe14e849bdddd4e69e662b125a95b61cf/no-filename.oga';
  try {
    const res = await axios.get(url, { responseType: 'arraybuffer', maxRedirects: 3 });
    console.log('Axios status:', res.status, 'bytes:', res.data.length);
  } catch (err) {
    console.error('Axios error:', err.message, err.response?.status, err.code);
  }
}
run();
"""

cmd = ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', test_js]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Stdout:\n", res.stdout)
print("Stderr:\n", res.stderr)
