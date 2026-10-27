import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = [
    'docker', 'exec', '-e', 'PGCLIENTENCODING=UTF8',
    'chatbot_n8n-postgres-1',
    'psql', '-U', 'postgres', '-d', 'n8n', '-t', '-A',
    '-c', 'SELECT "data" FROM execution_data WHERE "executionId" = 1233;'
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
d = json.loads(res.stdout.strip())

# The attachment in 1233 was at d[86]
att_raw = d[86]
att_resolved = {}
for k, v in att_raw.items():
    if isinstance(v, str) and v.isdigit() and int(v) < len(d):
        att_resolved[k] = d[int(v)]
    else:
        att_resolved[k] = v

print("Resolved raw attachment:", json.dumps(att_resolved, indent=2))

test_code = """
const attachment = {
  kind: 'audio',
  fileType: 'audio',
  mimeType: 'audio/opus',
  extension: 'oga',
  fileName: '',
  dataUrl: '""" + att_resolved['data_url'] + """',
  sizeBytes: """ + str(att_resolved['file_size']) + """,
  durationSeconds: null
};

const kind = String(attachment.kind ?? 'unknown').toLowerCase();
const MAX_AUDIO_SECONDS = 60;
const MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024;
const rawSize = attachment.sizeBytes;
const fileSize = rawSize === null || rawSize === undefined || rawSize === '' ? null : Number(rawSize);
let status = 'unsupported';
let step = 'unsupported_attachment_type';
let downloadUrl = '';
const candidate = String(attachment.dataUrl ?? '').trim();
function readDurationSeconds(value) {
  if (typeof value === 'number' && Number.isFinite(value) && value >= 0) return value;
  if (typeof value !== 'string' || !value.trim()) return null;
  const raw = value.trim();
  if (/^\\d+(?:\\.\\d+)?$/.test(raw)) return Number(raw);
  const parts = raw.split(':').map(Number);
  if (parts.some(part => !Number.isFinite(part) || part < 0) || parts.length > 3) return null;
  return parts.reduce((total, part) => total * 60 + part, 0);
}
function resolveAllowedUrl(value) {
  try {
    const url = value.startsWith('/') && !value.startsWith('//') ? new URL('http://chatwoot-web:3000' + value) : new URL(value);
    const internal = url.protocol === 'http:' && url.hostname === 'chatwoot-web' && url.port === '3000';
    const publicChatwoot = url.protocol === 'https:' && url.hostname === 'chatwoot.fatecn8nabc.dpdns.org' && !url.port;
    return (internal || publicChatwoot) && !url.username && !url.password ? url.toString() : '';
  } catch { return ''; }
}
const durationSeconds = readDurationSeconds(attachment.durationSeconds);
if (fileSize === null || !Number.isFinite(fileSize) || fileSize < 0) {
  step = 'attachment_size_unavailable';
} else if (fileSize > MAX_ATTACHMENT_BYTES) {
  step = 'attachment_exceeds_10mb_limit';
} else if (kind === 'image') {
  step = 'image_content_not_processed';
} else if (kind === 'document') {
  step = 'document_content_not_read_by_policy';
} else if (kind === 'audio') {
  if (durationSeconds !== null && durationSeconds > MAX_AUDIO_SECONDS) {
    step = 'audio_over_60_seconds';
  } else {
    downloadUrl = resolveAllowedUrl(candidate);
    if (downloadUrl) {
      status = 'readyForDownload';
      step = durationSeconds === null ? 'duration_will_be_checked_after_download' : '';
    } else {
      status = 'pending';
      step = 'attachment_url_missing_or_invalid';
    }
  }
}
console.log('Result:', { status, step, downloadUrl, durationSeconds, fileSize });
"""

cmd2 = ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', test_code]
res2 = subprocess.run(cmd2, capture_output=True, text=True, encoding='utf-8')
print("Node test output:\n", res2.stdout)
