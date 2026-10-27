# Plataforma de Assistente Virtual RAG

Ecossistema de assistente virtual integrado ao WhatsApp, Chatwoot, WAHA, n8n, Redis e PostgreSQL utilizando Docker.

---

## Pré-requisitos

1. **[Docker e Docker Compose](https://www.docker.com/products/docker-desktop/):** Para executar a infraestrutura de containers.
2. **[Ollama](https://ollama.com/download):** Para rodar os modelos de IA (Llama / Nomic) localmente.
3. **Smartphone com WhatsApp:** Para escanear o QR Code da API do [WAHA](https://waha.devlike.pro/docs/).
4. **[GPU NVIDIA configurada no Docker](https://docs.docker.com/compose/how-tos/gpu-support/):** Necessária porque o Speaches usa CUDA e inicia junto com a stack padrão.
5. **[GNU Make](https://www.gnu.org/software/make/) (Opcional):** Para executar comandos e atalhos do projeto.

---

## Endereços de Acesso

| Serviço | Modo Local | Modo Público (Caddy + Cloudflare Tunnel) |
|---|---|---|
| **Página Inicial** | `public/index.html` *(Portal Local)* | `https://seu-dominio.com` |
| **n8n** | `http://localhost:5678` | `https://n8n.seu-dominio.com` |
| **Chatwoot** | `http://localhost:3001` | `https://chatwoot.seu-dominio.com` |
| **WAHA** | `http://localhost:3000/dashboard` | `http://localhost:3000/dashboard` *(restrito ao host local)* |

---

## Como usar o projeto

O arquivo `.env` contém credenciais e nunca deve ser versionado. Siga as etapas de acordo com o modo desejado:

| Passo / Etapa | Modo Local | Modo Público (Caddy + Tunnel) |
| :--- | :--- | :--- |
| **1.&nbsp;Criar&nbsp;.env** | `cp .env.example .env` | `cp .env.public.example .env` |
| **2.&nbsp;Configurar** | Preencha senhas e banco | Preencha `DOMAIN`, `TUNNEL_TOKEN` e senhas |
| **3.&nbsp;Iniciar&nbsp;stack** | `make up`<br>*(ou `docker compose --env-file versions.env --env-file .env -f compose.yml up -d`)* | `make up` *(detecta público pelo token)*<br>*(ou `docker compose --env-file versions.env --env-file .env -f compose.yml -f compose.public.yml up -d`)* |
| **4.&nbsp;Chatwoot** | Acesse `http://localhost:3001`, conclua o cadastro e copie o `CHATWOOT_ACCOUNT_TOKEN` (*Profile Settings*) | Acesse `https://chatwoot.seu-dominio.com`, conclua o cadastro e copie o `CHATWOOT_ACCOUNT_TOKEN` (*Profile Settings*) |
| **5.&nbsp;Integração** | Salve o token no `.env` e execute:<br>`python3 scripts/setup.py` | Salve o token no `.env` e execute:<br>`python3 scripts/setup.py` |
| **6.&nbsp;WhatsApp** | Abra `http://localhost:3000/dashboard` e escaneie o QR Code na sessão `default` | Abra `http://localhost:3000/dashboard` e escaneie o QR Code na sessão `default` |

---

## Validação e Alternativas

* **Validar o `.env` sem chamar APIs:**
  ```bash
  python3 scripts/setup.py --dry-run
  ```

* **Execução manual passo a passo (sem `setup.py`):**
  ```bash
  bash scripts/chatwoot/1_create_inbox.sh
  bash scripts/chatwoot/2_create_agent_bot.sh
  bash scripts/waha/2_create_session.sh
  bash scripts/waha/1_setup_chatwoot_app.sh
  ```

> [!NOTE]
> Após reinícios normais, as sessões, o App Chatwoot e as autenticações permanecem salvos nos volumes persistentes.

---

## Documentação Complementar

- [Guia Ilustrado — Transcrição de Áudio com Speaches](https://github.com/Gabriel-Bassani-da-Silva/chatbot/blob/main/docs/speaches/Guia%20ilustrado%20%E2%80%94%20transcri%C3%A7%C3%A3o%20de%20%C3%A1udio%20com%20Speaches.md)
- [Guia Ilustrado — Rotas do Cloudflare Tunnel](https://github.com/Gabriel-Bassani-da-Silva/chatbot/blob/main/docs/cloudflare/Guia%20ilustrado%20%E2%80%94%20rotas%20do%20Cloudflare%20Tunnel.md)
- [Guia Ilustrado — Conexão com Google Sheets, Calendar e Drive](https://github.com/Gabriel-Bassani-da-Silva/chatbot/blob/main/docs/google/Guia%20ilustrado%20%E2%80%94%20conex%C3%A3o%20com%20Google%20Sheets,%20Calendar%20e%20Drive.md)
- [Guia de Credenciais dos Workflows n8n](https://github.com/Gabriel-Bassani-da-Silva/chatbot/blob/main/docs/credenciais-workflows-n8n.md)
