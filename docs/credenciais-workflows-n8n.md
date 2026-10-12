# Credenciais dos workflows no n8n

No fluxo `WAHA → Chatwoot → n8n → Chatwoot → WAHA`, o n8n usa o Chatwoot. O WAHA conecta o WhatsApp ao Chatwoot; não é necessária uma credencial WAHA no n8n. O `setup.py` configura essa integração, mas não cria as credenciais do n8n.

No n8n, abra **Credentials → Create credential** e configure:

- **Postgres** — host `postgres`; porta `5432`; banco definido no ambiente para os workflows, separado do banco interno do n8n; usuário `POSTGRES_USER` e senha `POSTGRES_PASSWORD` do `.env`.
- **Redis** — host `redis`; porta `6379`; índice `0`; deixe usuário em branco e use a senha `REDIS_PASSWORD` do `.env`.
- **Ollama API** — URL `http://host.docker.internal:11434`; o Ollama precisa aceitar conexões do container `n8n`.
- **Chatwoot (Header Auth)** — cabeçalho `api_access_token`; valor de `CHATWOOT_ACCOUNT_TOKEN`. Nos nós HTTP, use `http://chatwoot-web:3000` como endereço interno do Chatwoot.

Depois, selecione cada credencial nos nós correspondentes. Se alterar a configuração ou as portas no Compose, atualize os valores usados pelos nós e credenciais.
