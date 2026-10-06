# Setup inicial de Chatwoot + WAHA

Este conjunto de scripts prepara a Inbox API do Chatwoot, cria/vincula o Agent Bot, confirma a sessão `default` do WAHA e registra o app Chatwoot no WAHA.

## Pré-requisitos

- Executar na raiz do projeto (o caminho é resolvido automaticamente pelo `setup.py`).

- Bash, Python 3.9+ e `curl` disponíveis.

- Copiar `.env.example` para `.env` no modo local ou `.env.public.example` para `.env` no modo público. Preencher `CHATWOOT_ACCOUNT_TOKEN` e `WAHA_API_KEY`, além dos demais campos obrigatórios do exemplo escolhido.

- O Chatwoot e o WAHA precisam estar ativos e acessíveis pelas portas locais definidas em `CHATWOOT_PORT` e `WAHA_PORT`.

- Configure `N8N_WEBHOOK_URL` com a URL que o Chatwoot deve chamar. `WEBHOOK_URL` antigo ainda é aceito como fallback durante a migração.

## Executar

```bash
python3 scripts/setup.py --dry-run
python3 scripts/setup.py
```

O `--dry-run` valida as variáveis e mostra a ordem sem chamar APIs. O fluxo real tem timeout por etapa (90 s por padrão); personalize com `--timeout 120`.

A ordem é Inbox → Agent Bot e vínculo → sessão WAHA → registro do app WAHA. Inbox e Agent Bot já anotados no `.env` são reutilizados; a criação da sessão considera `409`/`422` como sessão existente e o registro do app usa `PUT`, permitindo repetição. Se a associação do Bot falhar após a criação, o ID e token são salvos antes do vínculo para a execução seguinte retomar sem criar outro Bot.

## Segredos e estado

- `scripts/envfile.py` interpreta `.env` como dados; não executa o arquivo como shell.

- Tokens gerados são gravados no `.env` por substituição atômica, sem imprimi-los; chaves relacionadas (por exemplo, ID e token do Bot) são salvas juntas. Ao gravar chave sensível, o arquivo passa a ter permissões `0600` no Linux.

- O `.env` real contém credenciais: não o versione nem compartilhe. O `.env.example` contém somente placeholders/valores não secretos.

- `CHATWOOT_ACCOUNT_ID` é opcional e usa `1` como padrão. `CHATWOOT_BOT_ID` e `CHATWOOT_BOT_LINKED_INBOX_ID` permitem retomar o fluxo sem duplicar o Bot ou repetir a associação.

- Para recriar uma Inbox ou um Bot deliberadamente, revise e remova as variáveis de estado correspondentes do `.env` antes da execução; isso pode criar recursos novos na API.

Os testes unitários locais podem ser executados com `python3 -m unittest discover -s tests`. Eles não fazem chamadas a Chatwoot, WAHA, n8n ou Docker. `make validate-compose` exige Docker Compose, valida os Compose local e público usando valores sintéticos e não inicia containers.
