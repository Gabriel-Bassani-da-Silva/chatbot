/**
 * Sincronizador de Backup: Base de Conhecimento Local -> Google Drive
 * Lê os arquivos JSON de fatec_rag_documents e envia/atualiza no Google Drive.
 * Utiliza autenticação OAuth2 descriptografada do n8n para atualizar in-place (sem duplicatas).
 *
 * Execução:
 *   Get-Content scripts/rag/sync_gdrive.js | docker exec -i chatbot_n8n-n8n-1 node -
 */

const { Client } = require('/usr/local/lib/node_modules/n8n/node_modules/pg');
const { Cipher, CipherAes256GCM, CipherAes256CBC } = require('/usr/local/lib/node_modules/n8n/node_modules/n8n-core');
const fs = require('fs');
const https = require('https');

const FOLDER_ID = '1AtN4X4jp5okt8ChlwRmYMpI4XwQuurF0';

function httpsRequest(options, postData) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve({ status: res.statusCode, data: parsed, raw: data });
        } catch (e) {
          resolve({ status: res.statusCode, data: null, raw: data });
        }
      });
    });
    req.on('error', reject);
    if (postData) {
      req.write(postData);
    }
    req.end();
  });
}

async function getValidAccessToken(credData) {
  const oauth = credData.oauthTokenData;
  let accessToken = oauth.access_token;

  const testRes = await httpsRequest({
    hostname: 'www.googleapis.com',
    path: `/drive/v3/files?pageSize=1&fields=files(id,name)`,
    method: 'GET',
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });

  if (testRes.status === 200) {
    return accessToken;
  }

  console.log('Token de acesso expirado. Renovando via refresh_token...');
  const postData = new URLSearchParams({
    client_id: credData.clientId,
    client_secret: credData.clientSecret,
    refresh_token: oauth.refresh_token,
    grant_type: 'refresh_token'
  }).toString();

  const refreshRes = await httpsRequest({
    hostname: 'oauth2.googleapis.com',
    path: '/token',
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Content-Length': Buffer.byteLength(postData)
    }
  }, postData);

  if (refreshRes.status !== 200) {
    throw new Error('Falha ao renovar token OAuth do Google: ' + refreshRes.raw);
  }

  console.log('Token de acesso renovado com sucesso!');
  return refreshRes.data.access_token;
}

async function listFilesInFolder(accessToken) {
  const query = encodeURIComponent(`'${FOLDER_ID}' in parents and trashed = false`);
  const res = await httpsRequest({
    hostname: 'www.googleapis.com',
    path: `/drive/v3/files?q=${query}&fields=files(id,name,mimeType,size,md5Checksum)&pageSize=100`,
    method: 'GET',
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  if (res.status !== 200) {
    throw new Error('Falha ao listar arquivos no Google Drive: ' + res.raw);
  }
  return res.data.files || [];
}

async function uploadNewFile(accessToken, fileName, jsonContent) {
  const boundary = '-------314159265358979323846';
  const delimiter = `\r\n--${boundary}\r\n`;
  const closeDelimiter = `\r\n--${boundary}--`;

  const metadata = {
    name: fileName,
    parents: [FOLDER_ID],
    mimeType: 'application/json'
  };

  const multipartRequestBody =
    delimiter +
    'Content-Type: application/json; charset=UTF-8\r\n\r\n' +
    JSON.stringify(metadata) +
    delimiter +
    'Content-Type: application/json\r\n\r\n' +
    jsonContent +
    closeDelimiter;

  const res = await httpsRequest({
    hostname: 'www.googleapis.com',
    path: '/upload/drive/v3/files?uploadType=multipart&fields=id,name,size,md5Checksum',
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': `multipart/related; boundary=${boundary}`,
      'Content-Length': Buffer.byteLength(multipartRequestBody)
    }
  }, multipartRequestBody);

  if (res.status < 200 || res.status >= 300) {
    throw new Error(`Falha ao criar ${fileName}: ` + res.raw);
  }

  return res.data;
}

async function updateExistingFile(accessToken, fileId, jsonContent) {
  const res = await httpsRequest({
    hostname: 'www.googleapis.com',
    path: `/upload/drive/v3/files/${fileId}?uploadType=media&fields=id,name,size,md5Checksum`,
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(jsonContent)
    }
  }, jsonContent);

  if (res.status < 200 || res.status >= 300) {
    throw new Error(`Falha ao atualizar ${fileId}: ` + res.raw);
  }

  return res.data;
}

async function main() {
  const config = JSON.parse(fs.readFileSync('/home/node/.n8n/config', 'utf8'));
  const cipher = new Cipher(
    { encryptionKey: config.encryptionKey },
    new CipherAes256GCM(),
    new CipherAes256CBC(),
    null
  );

  const client = new Client({
    host: process.env.DB_POSTGRESDB_HOST || 'postgres',
    port: process.env.DB_POSTGRESDB_PORT || 5432,
    user: process.env.DB_POSTGRESDB_USER || 'postgres',
    password: process.env.DB_POSTGRESDB_PASSWORD,
    database: process.env.DB_POSTGRESDB_DATABASE || 'n8n'
  });
  await client.connect();

  const res = await client.query("SELECT data FROM credentials_entity WHERE id = 'zEFeidm3PGLdb0x5';");
  if (res.rows.length === 0) {
    throw new Error('Credencial zEFeidm3PGLdb0x5 (Google Drive) não encontrada no banco do n8n.');
  }

  const cred = JSON.parse(cipher.decrypt(res.rows[0].data));
  const accessToken = await getValidAccessToken(cred);

  // 1. Mapear arquivos já existentes no Google Drive
  const existingFiles = await listFilesInFolder(accessToken);
  const existingMap = new Map();
  for (const f of existingFiles) {
    existingMap.set(f.name, f);
  }
  console.log(`Pasta do Google Drive possui ${existingFiles.length} arquivo(s).`);

  // 2. Carregar documentos do Postgres
  const docsRes = await client.query("SELECT file_name, raw_json, content_hash FROM fatec_rag_documents ORDER BY file_name;");
  console.log(`Verificando ${docsRes.rows.length} documento(s) cadastrados no Postgres...`);

  let countNew = 0;
  let countUpdated = 0;

  for (let i = 0; i < docsRes.rows.length; i++) {
    const row = docsRes.rows[i];
    const fileName = row.file_name;
    const jsonStr = JSON.stringify(row.raw_json, null, 2);
    const existing = existingMap.get(fileName);

    let driveFileId = null;
    if (existing) {
      // Atualização in-place no mesmo ID
      const resFile = await updateExistingFile(accessToken, existing.id, jsonStr);
      driveFileId = resFile.id;
      countUpdated++;
      console.log(`[${i+1}/${docsRes.rows.length}] ATUALIZADO: ${fileName} (id: ${driveFileId})`);
    } else {
      // Criação de novo arquivo
      const resFile = await uploadNewFile(accessToken, fileName, jsonStr);
      driveFileId = resFile.id;
      countNew++;
      console.log(`[${i+1}/${docsRes.rows.length}] CRIADO: ${fileName} (id: ${driveFileId})`);
    }

    await client.query("UPDATE fatec_rag_documents SET file_id_gdrive = $1 WHERE file_name = $2;", [driveFileId, fileName]);
  }

  console.log(`\nSincronização concluída! Criados: ${countNew}, Atualizados: ${countUpdated}.`);
  await client.end();
}

main().catch(console.error);
