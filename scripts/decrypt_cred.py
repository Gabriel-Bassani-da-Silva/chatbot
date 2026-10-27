import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_js = """
const crypto = require('crypto');
// CryptoJS AES decryption in Node
// n8n stores OpenSSL encrypted ciphertext (starts with Salted__)
const encryptedBase64 = 'U2FsdGVkX19wvE6EDdNRJ+JxpXw/IWmknFyxgqxti5umD+nolTer8kV93NdXFdN9DgJE5gIhB9TiIIFq8MJo6ZFlQSkhqbivXNWvIksJaPA=';
const password = process.env.N8N_ENCRYPTION_KEY;

// Decrypt using CryptoJS or OpenSSL format
const cipherTextBuf = Buffer.from(encryptedBase64, 'base64');
const salt = cipherTextBuf.slice(8, 16);
const cipherText = cipherTextBuf.slice(16);

// OpenSSL EVP_BytesToKey
function evpBytesToKey(password, salt, keyLen, ivLen) {
  let d = Buffer.alloc(0);
  let d_i = Buffer.alloc(0);
  while (d.length < keyLen + ivLen) {
    const hash = crypto.createHash('md5');
    hash.update(d_i);
    hash.update(password);
    hash.update(salt);
    d_i = hash.digest();
    d = Buffer.concat([d, d_i]);
  }
  return { key: d.slice(0, keyLen), iv: d.slice(keyLen, keyLen + ivLen) };
}

const { key, iv } = evpBytesToKey(Buffer.from(password, 'utf8'), salt, 32, 16);
const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);
let decrypted = decipher.update(cipherText, null, 'utf8');
decrypted += decipher.final('utf8');
console.log('Decrypted credential:', decrypted);
"""

cmd = ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', test_js]
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print("Stdout:\n", res.stdout)
print("Stderr:\n", res.stderr)
