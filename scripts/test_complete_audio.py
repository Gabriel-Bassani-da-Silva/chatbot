import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_js = """
async function run() {
  const item = {
    attachments: [
      {
        id: "72",
        kind: "audio",
        fileType: "audio",
        mimeType: "audio/opus",
        extension: "oga",
        dataUrl: "https://chatwoot.fatecn8nabc.dpdns.org/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBXUT09IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--2c9d909fe14e849bdddd4e69e662b125a95b61cf/no-filename.oga",
        sizeBytes: 58411,
        durationSeconds: null
      }
    ]
  };

  const attachments = Array.isArray(item.attachments) ? item.attachments : [];
  const rawAtt = attachments.find(a => a.kind === 'audio' || a.fileType === 'audio') ?? attachments[0] ?? {};
  const candidateUrl = String(rawAtt.dataUrl ?? rawAtt.data_url ?? rawAtt.url ?? '').trim();

  const resp = await fetch(candidateUrl);
  if (!resp.ok) throw new Error('HTTP ' + resp.status);
  const ab = await resp.arrayBuffer();
  const buffer = Buffer.from(ab);
  console.log('Downloaded bytes:', buffer.length);

  function parseOggOpus(buf) {
    if (buf.length < 27 || buf.toString('ascii', 0, 4) !== 'OggS') return null;
    let offset = 0, maxGranule = null, preSkip = 0, found = false;
    const unset = 0xffffffffffffffffn;
    while (offset + 27 <= buf.length) {
      if (buf.toString('ascii', offset, offset + 4) !== 'OggS' || buf[offset + 4] !== 0) return null;
      const count = buf[offset + 26], table = offset + 27, payload = table + count;
      if (payload > buf.length) return null;
      let length = 0;
      for (let i = 0; i < count; i++) length += buf[table + i];
      const end = payload + length;
      if (end > buf.length) return null;
      if (!found) {
        const marker = buf.indexOf('OpusHead', payload, 'ascii');
        if (marker >= payload && marker + 12 <= end) { preSkip = buf.readUInt16LE(marker + 10); found = true; }
      }
      const granule = buf.readBigUInt64LE(offset + 6);
      if (granule !== unset && (maxGranule === null || granule > maxGranule)) maxGranule = granule;
      offset = end;
    }
    if (!found || maxGranule === null) return null;
    const samples = Number(maxGranule) - preSkip;
    return Number.isFinite(samples) && samples >= 0 ? samples / 48000 : null;
  }

  const durationSeconds = parseOggOpus(buffer);
  console.log('Duration:', durationSeconds);

  const blob = new Blob([buffer], { type: rawAtt.mimeType || 'audio/ogg' });
  const form = new FormData();
  form.append('file', blob, rawAtt.fileName || 'audio.oga');
  form.append('model', 'Systran/faster-whisper-small');
  form.append('language', 'pt');
  form.append('prompt', 'Transcrição fiel de uma mensagem de voz em português do Brasil, com palavras e letras soletradas.');

  const sttResp = await fetch('http://speaches:8000/v1/audio/transcriptions', {
    method: 'POST',
    body: form
  });

  const sttJson = await sttResp.json();
  console.log('Result text:', sttJson.text);
}
run().catch(console.error);
"""

cmd = ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', test_js]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Execution output:\n", res.stdout)
print("Stderr:\n", res.stderr)
