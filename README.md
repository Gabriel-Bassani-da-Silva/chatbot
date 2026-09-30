# Plataforma de Assistente Virtual RAG

Este projeto utiliza o Docker e o `make` (opcional) para facilitar a inicialização e o gerenciamento de um ecossistema completo para assistentes virtuais integrados ao WhatsApp.

## Arquitetura e Roteamento

A infraestrutura foi desenhada para operar de forma segura usando subdomínios, gerenciados localmente pelo **Caddy** (Proxy Reverso) e expostos para a internet via **Cloudflare Tunnel**, sem abrir portas no firewall da sua máquina.

Tudo é regido pela variável global `DOMAIN` configurada no seu arquivo `.env` (ex: `seu-dominio.com`).

O roteamento padrão funciona da seguinte forma:
- **`seu-dominio.com`**: Página inicial estática (Portal de acesso rápido).
- **`n8n.seu-dominio.com`**: Editor do n8n e recepção de webhooks.
- **`chatwoot.seu-dominio.com`**: Painel de atendimento humano do Chatwoot.
- **`localhost:3000`**: WAHA (WhatsApp HTTP API) - Isolado da internet por segurança.

## Documentação Complementar

- [Guia Ilustrado — Rotas do Cloudflare Tunnel](docs/cloudflare/Guia%20ilustrado%20%E2%80%94%20rotas%20do%20Cloudflare%20Tunnel.md)

---

## Pré-requisitos

Antes de iniciar, certifique-se de ter os seguintes programas instalados:

1. **Docker e Docker Compose:** Necessários para rodar a infraestrutura.
2. **Ollama:** Necessário para rodar os modelos (Llama / Nomic) localmente.
3. **Um smartphone com WhatsApp:** Para escanear o QR Code da API do WAHA.
4. **Make (Opcional):** Utilizado para executar atalhos do projeto.

### Links Oficiais
- **Docker Desktop:** [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
- **Ollama:** [https://ollama.com/download](https://ollama.com/download)
- **Make (Windows):** Instale via PowerShell com `choco install make` (requer Chocolatey).

---

## Como usar o projeto

Depois de instalar os requisitos, copie o arquivo `.env.example` para `.env` e configure o seu domínio e senhas.

No terminal (na mesma pasta onde está o arquivo `Makefile`), você pode usar os seguintes comandos:

- **Iniciar todos os serviços:** `make up` *(ou `docker compose --env-file .env --env-file versions.env up -d`)*
- **Mostrar os logs:** `make logs`
- **Desligar os containers:** `make down`

---

## Primeiro deploy — Configuração Inicial

Após subir os containers pela **primeira vez**, siga a ordem abaixo para colocar o sistema no ar.

### Passo 1: Configurar as Rotas no Cloudflare
Antes de conseguir acessar o Chatwoot e o n8n pela web, você deve configurar o Tunnel.
Siga o **[Guia Ilustrado — Rotas do Cloudflare Tunnel](docs/cloudflare/Guia%20ilustrado%20%E2%80%94%20rotas%20do%20Cloudflare%20Tunnel.md)** para apontar o tráfego da nuvem para o container do Caddy.

### Passo 2: Pegar a Conta Admin e o Token no Chatwoot
1. Acesse a URL pública do seu Chatwoot (ex: `https://chatwoot.seu-dominio.com`) e complete o cadastro inicial.
2. Após o login, clique no seu **Perfil** (canto inferior esquerdo) → **Configurações de Perfil**.
3. Role até o final da página e copie o seu **Access Token**.
4. Cole esse código no seu arquivo `.env`, na variável `CHATWOOT_ACCOUNT_TOKEN`.

### Passo 3: Executar a Automação Segura (Orquestrador)
Com as credenciais no lugar, rode o orquestrador. Ele fará todo o trabalho pesado (criar a Caixa de Entrada, gerar o Agent Bot, vincular contas e configurar a sessão do WAHA) de forma protegida e sem vazar as suas senhas.

No terminal, execute:
```bash
python scripts/setup.py
```
*Opcional: Você pode rodar com a flag `--dry-run` para validar suas variáveis do `.env` antes sem chamar as APIs.*

### Passo 4: Escanear o QR code do WhatsApp
Finalizada a orquestração, o WAHA estará pronto. 
Acesse `http://localhost:3000/dashboard` no seu navegador, certifique-se que a sessão `default` está "STARTING" ou "ONLINE", e escaneie o QR code no seu WhatsApp.

---

### Após reinícios normais
Nenhuma reconfiguração é necessária. A sessão, o App Chatwoot e a autenticação ficam salvos nos volumes e são restaurados automaticamente ao reiniciar o Docker.
