import subprocess

# 1. Check if ioredis or redis is in n8n container
res1 = subprocess.run(
    ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', 'try { require("ioredis"); console.log("ioredis: AVAILABLE"); } catch(e) { console.log("ioredis: NOT AVAILABLE", e.message); }'],
    capture_output=True, text=True
)
print(res1.stdout.strip())

# 2. Check redis npm package
res2 = subprocess.run(
    ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', 'try { require("redis"); console.log("redis: AVAILABLE"); } catch(e) { console.log("redis: NOT AVAILABLE", e.message); }'],
    capture_output=True, text=True
)
print(res2.stdout.strip())

# 3. Find Redis.node.js
res3 = subprocess.run(
    ['docker', 'exec', 'chatbot_n8n-n8n-1', 'find', '/usr/local/lib/node_modules/n8n', '-name', 'Redis.node.js'],
    capture_output=True, text=True
)
path = res3.stdout.strip().split('\n')[0]
print("Redis.node.js path:", path)
if path:
    res4 = subprocess.run(
        ['docker', 'exec', 'chatbot_n8n-n8n-1', 'node', '-e', f'const fs = require("fs"); const s = fs.readFileSync("{path}", "utf8"); const m = s.match(/value:\\s*[\'"][a-zA-Z]+[\'"]/g); console.log([...new Set(m)]);'],
        capture_output=True, text=True
    )
    print("Operations in Redis node:", res4.stdout.strip())
