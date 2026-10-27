# Credenciais e Integrações dos Workflows no n8n

No ecossistema do chatbot (`WhatsApp (WAHA) ⇄ Chatwoot ⇄ n8n`), o n8n atua como o motor de orquestração, RAG e execução de subworkflows. Este documento detalha a configuração de todas as credenciais necessárias no n8n, com foco especial no passo a passo de autenticação **OAuth 2.0 do Google** (Google Sheets, Google Calendar e Google Drive) e na conexão com o microsserviço de áudio **Speaches**.

---

## 1. Credenciais dos Serviços Internos da Stack

No painel do n8n (**Credentials → Add Credential**), configure:

| Serviço | Tipo de Credencial no n8n | Parâmetros de Conexão | Onde é Utilizado |
| :--- | :--- | :--- | :--- |
| **Postgres** | `Postgres` | **Host**: `postgres`<br>**Port**: `5432`<br>**Database**: `${POSTGRES_DB}` (`n8n`)<br>**User**: `${POSTGRES_USER}`<br>**Password**: `${POSTGRES_PASSWORD}` | PGVector Tool (`fatec_rag_vectors_poc`) no workflow principal `Agente RAG Fatec`. |
| **Redis** | `Redis` | **Host**: `redis`<br>**Port**: `6379`<br>**DB**: `0`<br>**Password**: `${REDIS_PASSWORD}`<br>*(Deixar usuário em branco)* | Memória conversacional LangChain e controle de travas de confirmação do `/agenda` e `/cardapio`. |
| **Ollama** | `Ollama` | **Base URL**: `http://host.docker.internal:11434`<br>*(Sem autenticação por padrão)* | Modelos de linguagem (`llama3.1:latest`) e embeddings (`qwen3-embedding:0.6b`). |
| **Chatwoot** | `Header Auth` | **Name**: `api_access_token`<br>**Value**: `${CHATWOOT_ACCOUNT_TOKEN}`<br>**URL nos nós HTTP**: `http://chatwoot-web:3000` | Envio de mensagens de resposta e controle de conversas no Chatwoot. |

---

## 2. Passo a Passo Completo: Conexão Google (Sheets, Calendar e Drive)

As integrações com planilhas, agendamento de calendário e arquivos utilizam o protocolo **OAuth 2.0** do Google, garantindo acesso seguro e com escopos granulares.

### 2.1. Etapa 1: Configuração no Google Cloud Console

1. **Acessar o Console**:
   - Entre em [console.cloud.google.com](https://console.cloud.google.com/) com a sua conta Google (ex: `seu-email@gmail.com`).
2. **Criar ou Selecionar o Projeto**:
   - No topo da página, clique no menu de projetos e selecione **Novo Projeto**.
   - Defina o nome (ex: `Fatec-Chatbot-n8n`) e clique em **Criar**.
3. **Ativar as APIs Necessárias**:
   - Acesse **APIs e Serviços → Biblioteca**.
   - Pesquise e clique em **Ativar** para cada uma das APIs:
     1. **Google Sheets API** (para gravação dos pedidos do `/cardapio`).
     2. **Google Calendar API** (para verificação de disponibilidade e criação de eventos do `/agenda`).
     3. **Google Drive API** (para armazenamento e permissões de planilhas/anexos).
4. **Configurar a Tela de Permissão OAuth (OAuth Consent Screen)**:
   - Acesse **APIs e Serviços → Tela de permissão OAuth**.
   - Selecione o tipo de usuário: **Externo** (External) e clique em **Criar**.
   - Preencha os campos básicos:
     - **Nome do App**: `Fatec Bot n8n`
     - **E-mail de suporte do usuário**: Selecione seu e-mail.
     - **Dados de contato do desenvolvedor**: Seu e-mail.
     - Clique em **Salvar e continuar**.
   - **Escopos (Scopes)**:
     - Clique em **Adicionar ou remover escopos** e adicione:
       - `https://www.googleapis.com/auth/spreadsheets`
       - `https://www.googleapis.com/auth/calendar`
       - `https://www.googleapis.com/auth/calendar.events`
       - `https://www.googleapis.com/auth/drive` ou `https://www.googleapis.com/auth/drive.file`
     - Clique em **Atualizar** e depois em **Salvar e continuar**.
   - **Usuários de Teste (Test Users)**:
     - ⚠️ **Obrigatório**: Enquanto o app estiver em modo de teste, somente contas cadastradas aqui conseguirão se autenticar no n8n.
     - Clique em **+ Add Users**, insira seu e-mail (`seu-email@gmail.com`) e salve.
5. **Criar as Credenciais OAuth 2.0 (Client ID e Secret)**:
   - Acesse **APIs e Serviços → Credenciais → + Criar Credenciais → ID do cliente OAuth**.
   - **Tipo de aplicativo**: `Aplicativo da Web` (Web application).
   - **Nome**: `n8n OAuth Integration`.
   - **URIs de redirecionamento autorizados** (Authorized Redirect URIs):
     - Insira a URL de callback do n8n:
       - Modo com Cloudflare Tunnel: `https://n8n.fatecn8nabc.dpdns.org/rest/oauth2-credential/callback`
       - Modo local: `http://localhost:5678/rest/oauth2-credential/callback`
   - Clique em **Criar** e copie o **Client ID** e o **Client Secret**.

---

### 2.2. Etapa 2: Cadastro das Credenciais no n8n

No n8n (**Credentials → Add Credential**), configure cada integração:

#### A. Google Sheets (`Google Sheets OAuth2 API`)
- Escolha **Google Sheets OAuth2 API**.
- Insira o **Client ID** e o **Client Secret**.
- Clique em **Sign in with Google** (ou "Connect my account").
- Na janela pop-up, selecione sua conta e clique em **Avançado → Acessar Fatec Bot n8n (não seguro)**.
- Conceda as permissões de acesso às planilhas.
- O n8n exibirá: `Connection tested successfully`.
- Salve a credencial como `Google Sheets account`.

#### B. Google Calendar (`Google Calendar OAuth2 API`)
- Escolha **Google Calendar OAuth2 API**.
- Preencha os mesmos **Client ID** e **Client Secret**.
- Realize o login e autorize a permissão para consultar e criar eventos na agenda.
- Salve a credencial como `Google Calendar account`.

#### C. Google Drive (`Google Drive OAuth2 API`)
- Escolha **Google Drive OAuth2 API**.
- Preencha o **Client ID** e o **Client Secret** e conceda acesso aos arquivos.
- Salve a credencial como `Google Drive account`.

---

### 2.3. Etapa 3: Parametrização nos Nós dos Workflows

#### 1. Subworkflow `/cardapio` (`Comando _cardapio — Google Sheets.json`):
- **Nó**: `Sheets — registrar pedido` (`n8n-nodes-base.googleSheets`)
- **Credential**: `Google Sheets account`
- **Document**: ID `<ID_DA_SUA_PLANILHA>` (`Pedidos - Cardápio (n8n)`)
- **Sheet**: `Página1`
- **Operation**: `appendOrUpdate` (com `matchingColumns: ["pedido_id"]`)
- **Colunas Mapeadas**:
  - `pedido_id`: `={{ $json.pedido_id }}`
  - `criado_em`: `={{ $json.criado_em }}`
  - `nome`: `={{ $json.nome }}`
  - `contato`: `={{ $json.contato }}`
  - `itens`: `={{ $json.itens }}`
  - `observacoes`: `={{ $json.observacoes }}`
  - `status`: `={{ $json.status }}`

#### 2. Subworkflow `/agenda` (`Comando _agenda — Google Calendar.json`):
- **Nó 1**: `Calendar — verificar disponibilidade`
  - **Credential**: `Google Calendar account`
  - **Calendar**: `seu-email@gmail.com`
  - **Operation**: `availability`
  - **Janela de Busca**: `timeMin = ={{ $json.startISO }}`, `timeMax = ={{ $json.endISO }}`
- **Nó 2**: `Calendar — criar agendamento`
  - **Credential**: `Google Calendar account`
  - **Calendar**: `seu-email@gmail.com`
  - **Operation**: `create`
  - **Start**: `={{ $("Interpretar /agenda").item.json.startISO }}`
  - **End**: `={{ $("Interpretar /agenda").item.json.endISO }}`
  - **Summary**: `={{ $("Interpretar /agenda").item.json.eventTitle }}`
  - **Description**: `={{ $("Interpretar /agenda").item.json.eventDescription }}`
  - **Visibility**: `private`, **Show Me As**: `opaque`

#### 3. Google Drive (Nós Opcionais de Armazenamento):
- Em nós de envio de arquivos ou cópias de segurança de planilhas/áudios, utilize a credencial `Google Drive account` com a ação **File → Upload**.

---

### 2.4. Resolução de Problemas (Troubleshooting)

| Erro / Comportamento | Causa | Como Resolver |
| :--- | :--- | :--- |
| **`redirect_uri_mismatch` (400)** | A URL no Google Cloud Console difere da URL do n8n. | No console do Google Cloud, adicione exatamente o callback informado pelo n8n (atenção ao `https://` e à ausência de barra no final). |
| **`access_denied` ao autorizar** | A conta Google não está na lista de usuários de teste. | No GCP > Tela de consentimento OAuth > Usuários de teste, adicione o e-mail que está efetuando o login. |
| **Token OAuth expirando a cada 7 dias** | O app no GCP está com status "Em teste". | Na Tela de consentimento OAuth do GCP, clique em **Publicar aplicativo** (Publish App). Em modo de produção, o Refresh Token não expira em 7 dias. |
| **Erro de Permissão 403 na Planilha** | A conta autorizada no n8n não tem acesso à planilha. | Abra a planilha no Google Sheets e compartilhe-a com o e-mail conectado com permissão de "Editor". |

---

## 3. Conexão do Speaches (Áudio STT Local com GPU)

O **Speaches** é o microsserviço de transcrição local baseado em `faster-whisper`. Ele opera dentro da rede Docker dedicada `speech` e não exige chaves de API externas.

- **Endereço Interno**: `http://speaches:8000/v1/audio/transcriptions`
- **Porta Local no Host**: `127.0.0.1:8000` (não exposta publicamente no Caddy).
- **Parâmetros da Requisição no n8n**:
  - **Método**: `POST`
  - **Tipo de Envio**: `multipart/form-data`
  - **Campos**:
    - `file`: Arquivo binário de áudio (baixado do Chatwoot).
    - `model`: `Systran/faster-whisper-small`.
    - `language`: `pt`.
    - `prompt`: `"Transcrição fiel de uma mensagem de voz em português do Brasil, com palavras e letras soletradas."`
- **Validação de Limites no Workflow**: Áudios com duração superior a **60 segundos** ou tamanho maior que **10 MiB** são bloqueados preventivamente pelo nó `Validar URL e formato` no subworkflow `Processar anexos`.

---

## 4. Guias Ilustrados Passo a Passo (com Imagens)

- [**Guia ilustrado — Conexão com Google Sheets, Calendar e Drive**](./google/Guia%20ilustrado%20%E2%80%94%20conex%C3%A3o%20com%20Google%20Sheets,%20Calendar%20e%20Drive.md): Telas do Google Cloud Console, tela de consentimento OAuth, criação do cliente web e parametrização dos nós do n8n.
- [**Guia ilustrado — Transcrição de Áudio com Speaches**](./speaches/Guia%20ilustrado%20%E2%80%94%20transcri%C3%A7%C3%A3o%20de%20%C3%A1udio%20com%20Speaches.md): Diagrama da esteira multimodal, parâmetros do nó HTTP Request e limites operacionais.
- [**Guia ilustrado — Rotas do Cloudflare Tunnel**](./cloudflare/Guia%20ilustrado%20%E2%80%94%20rotas%20do%20Cloudflare%20Tunnel.md): Configuração de hostnames públicos e mapeamento de rotas para o Caddy.
