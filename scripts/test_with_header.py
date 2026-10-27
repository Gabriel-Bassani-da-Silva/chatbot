import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_js = """
const { https } = require('/usr/local/lib/node_modules/n8n/node_modules/.pnpm/node_modules/follow-redirects');
const url = 'https://chatwoot.fatecn8nabc.dpdns.org/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBXUT09IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--2c9d909fe14e849bdddd4e69e662b125a95b61cf/no-filename.oga';

const opts = {
  headers: {
    'api_access_token': 'vkNy1QWnDLfte2EEhEtkkni5'
  }
};

const req = https.get(url, opts, (res) => {
  console.log('Status with header:', res.statusCode);
  let bytes = 0;
  res.on('data', chunk => bytes += chunk.length);
  res.on('end', () => console.log('Downloaded bytes:', bytes));
});
req.on('error', err => console.error('Error with header:', err));
"""

cmd = ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', test_js]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Stdout:\n", res.stdout)
print("Stderr:\n", res.stderr)
