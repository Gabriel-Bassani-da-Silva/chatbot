import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_js = """
const { https } = require('/usr/local/lib/node_modules/n8n/node_modules/.pnpm/node_modules/follow-redirects');
const url = 'https://chatwoot.fatecn8nabc.dpdns.org/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBXUT09IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--2c9d909fe14e849bdddd4e69e662b125a95b61cf/no-filename.oga';

const req = https.get(url, (res) => {
  const chunks = [];
  res.on('data', chunk => chunks.push(chunk));
  res.on('end', async () => {
    const buffer = Buffer.concat(chunks);
    const blob = new Blob([buffer], { type: 'audio/ogg' });
    const formData = new FormData();
    formData.append('file', blob, 'audio.oga');
    formData.append('model', 'Systran/faster-whisper-small');
    formData.append('language', 'pt');
    formData.append('prompt', 'Transcrição fiel de uma mensagem de voz em português do Brasil, com palavras e letras soletradas.');

    try {
      const resp = await fetch('http://speaches:8000/v1/audio/transcriptions', {
        method: 'POST',
        body: formData
      });
      console.log('Speaches status:', resp.status);
      const text = await resp.text();
      console.log('Speaches response:', text);
    } catch (e) {
      console.error('Speaches fetch error:', e);
    }
  });
});
"""

cmd = ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', test_js]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Stdout:\n", res.stdout)
print("Stderr:\n", res.stderr)
