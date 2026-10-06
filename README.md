# Plataforma de Assistente Virtual RAG

Este projeto utiliza Docker e o `make` (opcional) para executar um ecossistema de assistente virtual integrado ao WhatsApp, Chatwoot, WAHA, n8n, Redis e PostgreSQL.

## Modos de execução

A base comum está em `compose.yml` e funciona localmente, sem domínio público, Caddy ou Cloudflare Tunnel.

A execução pública usa `compose.yml` com o overlay `compose.public.yml`. Nesse modo, Caddy e Cloudflare Tunnel publicam os subdomínios configurados.

### Rotas públicas

- **`seu-dominio.com`**: Página inicial estática.
- **`n8n.seu-dominio.com`**: Editor do n8n e recepção de webhooks.
- **`chatwoot.seu-dominio.com`**: Painel de atendimento humano do Chatwoot.
- **`localhost:3000`**: WAHA, mantido somente no host local.

### Acessos locais

- **n8n:** `http://localhost:5678`
- **Chatwoot:** `http://localhost:3001`
- **WAHA:** `http://localhost:3000`

## Documentação Complementar

- [Guia Ilustrado — Rotas do Cloudflare Tunnel](https://github.com/Gabriel-Bassani-da-Silva/chatbot/blob/main/docs/cloudflare/Guia%20ilustrado%20%E2%80%94%20rotas%20do%20Cloudflare%20Tunnel.md)

---

## Pré-requisitos

Antes de iniciar, certifique-se de ter os seguintes programas instalados:

1. **Docker e Docker Compose:** Necessários para rodar a infraestrutura.
2. **Ollama:** Necessário para rodar os modelos (Llama / Nomic) localmente. [Download oficial](https://ollama.com/download).
3. **Um smartphone com WhatsApp:** Para escanear o QR Code da API do WAHA.
4. **Make (Opcional):** Utilizado para executar atalhos do projeto.

### Links oficiais

- **Docker Desktop:** https://www.docker.com/products/docker-desktop/
- **WAHA — WhatsApp HTTP API:** https://waha.devlike.pro/docs/
- **GNU Make:** https://www.gnu.org/software/make/

---

## Como usar o projeto

Escolha um dos modos abaixo. O `.env` real não deve ser versionado.

### Modo local

1. Copie o exemplo local:

   ```bash
   cp .env.example .env
   ```

2. Preencha os valores obrigatórios no `.env`.
3. Inicie os serviços locais:

   ```bash
   make up
   ```

4. Abra o Chatwoot em `http://localhost:3001`, conclua o cadastro e obtenha o `CHATWOOT_ACCOUNT_TOKEN`.
5. Execute o setup:

   ```bash
   python3 scripts/setup.py
   ```

6. Abra `http://localhost:3000/dashboard`, confirme a sessão `default` e escaneie o QR Code do WhatsApp.

### Modo público

1. Copie o exemplo público:

   ```bash
   cp .env.public.example .env
   ```

2. Preencha o domínio, o token do Cloudflare Tunnel e os demais valores obrigatórios no `.env`.
3. Configure as rotas do Tunnel conforme o **[Guia Ilustrado — Rotas do Cloudflare Tunnel](https://github.com/Gabriel-Bassani-da-Silva/chatbot/blob/main/docs/cloudflare/Guia%20ilustrado%20%E2%80%94%20rotas%20do%20Cloudflare%20Tunnel.md)**.
4. Inicie a stack pública:

   ```bash
   make public up
   ```

5. Conclua o cadastro do Chatwoot pela URL pública, obtenha o `CHATWOOT_ACCOUNT_TOKEN` e salve-o no `.env`.
6. Execute o setup:

   ```bash
   python3 scripts/setup.py
   ```

7. Abra `http://localhost:3000/dashboard`, confirme a sessão `default` e escaneie o QR Code do WhatsApp.

### Alternativa sem `setup.py`

Execute os scripts na ordem abaixo, na raiz do projeto:

```bash
bash scripts/chatwoot/1_create_inbox.sh
bash scripts/chatwoot/2_create_agent_bot.sh
bash scripts/waha/2_create_session.sh
bash scripts/waha/1_setup_chatwoot_app.sh
```

Antes de executar o setup, valide o `.env` sem chamar APIs:

```bash
python3 scripts/setup.py --dry-run
```

Após reinícios normais, a sessão, o App Chatwoot e a autenticação permanecem salvos nos volumes.
