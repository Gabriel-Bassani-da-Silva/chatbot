import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_js = """
const { https } = require('/usr/local/lib/node_modules/n8n/node_modules/.pnpm/node_modules/follow-redirects');
const url = 'https://chatwoot.fatecn8nabc.dpdns.org/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBXUT09IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--2c9d909fe14e849bdddd4e69e662b125a95b61cf/no-filename.oga';

function parseOggOpus(buffer) {
  if (buffer.length < 27 || buffer.toString('ascii', 0, 4) !== 'OggS') return null;
  let offset = 0, maxGranule = null, preSkip = 0, found = false;
  const unset = 0xffffffffffffffffn;
  while (offset + 27 <= buffer.length) {
    if (buffer.toString('ascii', offset, offset + 4) !== 'OggS' || buffer[offset + 4] !== 0) return null;
    const count = buffer[offset + 26], table = offset + 27, payload = table + count;
    if (payload > buffer.length) return null;
    let length = 0;
    for (let i = 0; i < count; i++) length += buffer[table + i];
    const end = payload + length;
    if (end > buffer.length) return null;
    if (!found) {
      const marker = buffer.indexOf('OpusHead', payload, 'ascii');
      if (marker >= payload && marker + 12 <= end) { preSkip = buffer.readUInt16LE(marker + 10); found = true; }
    }
    const granule = buffer.readBigUInt64LE(offset + 6);
    if (granule !== unset && (maxGranule === null || granule > maxGranule)) maxGranule = granule;
    offset = end;
  }
  if (!found || maxGranule === null) return null;
  const samples = Number(maxGranule) - preSkip;
  return Number.isFinite(samples) && samples >= 0 ? samples / 48000 : null;
}

const req = https.get(url, (res) => {
  const chunks = [];
  res.on('data', chunk => chunks.push(chunk));
  res.on('end', () => {
    const buffer = Buffer.concat(chunks);
    console.log('Buffer len:', buffer.length);
    console.log('Header 0..4:', buffer.toString('ascii', 0, 4));
    const duration = parseOggOpus(buffer);
    console.log('parseOggOpus result:', duration);
  });
});
"""

cmd = ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', test_js]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Stdout:\n", res.stdout)
print("Stderr:\n", res.stderr)
