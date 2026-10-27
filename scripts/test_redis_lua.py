import subprocess

test_js = """
const Redis = require('ioredis');
const redis = new Redis('redis://:f81a34c353b25e714182ab9345737beec9630d4380d9c6106f34c1afa33a6f8c@redis:6379/0');

async function test() {
    const convId = 'test_conv_999';
    const lastTokenKey = 'chatwoot:last_token:conv:' + convId;
    const bufferKey = 'chatwoot:buffer:conv:' + convId;
    const lockKey = 'chatwoot:infer_lock:conv:' + convId;

    // 1. Set token & push 2 items
    const token = 'msg_101_exec_1';
    await redis.set(lastTokenKey, token, 'EX', 120);
    await redis.rpush(bufferKey, JSON.stringify({ messageId: 101, text: 'Oi', createdAt: 1000 }));
    await redis.rpush(bufferKey, JSON.stringify({ messageId: 102, text: 'Tudo bem?', createdAt: 2000 }));

    // 2. Run Lua Script
    const luaScript = `
        local currentToken = redis.call('GET', KEYS[1])
        if currentToken ~= ARGV[1] then
            return {0, 'token_mismatch'}
        end
        local activeLock = redis.call('GET', KEYS[3])
        if activeLock then
            return {1, 'infer_locked'}
        end
        redis.call('SET', KEYS[3], ARGV[1], 'EX', tonumber(ARGV[2]))
        local items = redis.call('LRANGE', KEYS[2], 0, -1)
        redis.call('DEL', KEYS[2])
        return {2, items}
    `;

    const res = await redis.eval(luaScript, 3, lastTokenKey, bufferKey, lockKey, token, 60);
    console.log('Lua result code:', res[0]);
    console.log('Items extracted count:', res[1].length);
    console.log('Items:', res[1]);

    const lockVal = await redis.get(lockKey);
    console.log('Lock set:', lockVal);

    // Clean up
    await redis.del(lastTokenKey, bufferKey, lockKey);
    redis.disconnect();
}
test().catch(console.error);
"""

res = subprocess.run(
    ['docker', 'exec', '-i', '-e', 'NODE_PATH=/usr/local/lib/node_modules/n8n/node_modules', 'chatbot_n8n-n8n-1', 'node'],
    input=test_js,
    capture_output=True,
    text=True
)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
