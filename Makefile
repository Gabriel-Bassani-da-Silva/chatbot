# ============================================================
# Comandos do projeto
# ============================================================
# O arquivo .env real contém credenciais e nunca deve ser versionado.
# Os comandos usam versions.env para fixar as versões das imagens.
#
# Modo local (padrão):
#   make up
#
# Modo público, com Caddy e Cloudflare Tunnel:
#   make public up
#   make public logs
#   make public down
#
# `public` é um seletor de modo: escreva-o antes do comando desejado.
# ============================================================

# Compose base: PostgreSQL, Redis, n8n, WAHA e Chatwoot.
# O overlay público acrescenta Caddy e Cloudflare Tunnel.
COMPOSE_FILES := -f compose.yml
ifneq ($(filter public,$(MAKECMDGOALS)),)
COMPOSE_FILES += -f compose.public.yml
endif

# Comando compartilhado pelos alvos Docker.
# O .env deve vir de .env.example (local) ou .env.public.example (público).
DC ?= docker compose --env-file versions.env --env-file .env $(COMPOSE_FILES)
PYTHON ?= python3

.PHONY: help public up down restart logs ps rebuild test validate-compose wipe

# Seletor para invocar os comandos com o Compose público.
# Use `make public <comando>`; sem `public`, os comandos usam o modo local.
public:
	@:

# Mostra os comandos disponíveis e exemplos de uso.
help:
	@printf '\n\033[36m  n8n-stack\033[0m\n'
	@printf '\033[90m  Uso: make [public] <comando>\033[0m\n\n'
	@printf '  Execução e diagnóstico:\n'
	@printf '    up                Inicia os serviços em segundo plano\n'
	@printf '    down              Para os serviços, preservando volumes\n'
	@printf '    restart           Reinicia os serviços\n'
	@printf '    logs              Acompanha os logs; Ctrl+C encerra só a visualização\n'
	@printf '    ps                Lista os serviços e seus estados\n'
	@printf '    rebuild           Reconstrói imagens locais e inicia os serviços\n'
	@printf '\n  Verificação e limpeza:\n'
	@printf '    test              Executa os testes e valida a sintaxe dos scripts\n'
	@printf '    validate-compose  Valida os Compose local/público; requer Docker Compose\n'
	@printf '    wipe              Remove todos os volumes; exige CONFIRM_WIPE=YES\n'
	@printf '\n  Exemplos locais:\n'
	@printf '    make up\n'
	@printf '    make logs\n'
	@printf '\n  Exemplos públicos:\n'
	@printf '    make public up\n'
	@printf '    make public logs\n'
	@printf '    make public wipe CONFIRM_WIPE=YES\n\n'

# Inicia os serviços sem bloquear o terminal.
# Sem o seletor public, usa somente compose.yml.
# Com `make public up`, usa compose.yml + compose.public.yml.
up:
	$(DC) up -d

# Para os containers, mas preserva os volumes e os dados persistentes.
down:
	$(DC) down

# Reinicia os containers sem reconstruir as imagens.
restart:
	$(DC) restart

# Acompanha os logs dos serviços.
# Ctrl+C encerra a visualização; os containers continuam em execução.
logs:
	$(DC) logs -f

# Mostra os containers gerenciados pelo Compose e seus estados.
ps:
	$(DC) ps

# Reconstrói as imagens que possuem build local e inicia os serviços.
# No modo público, isso também reconstrói a imagem local do Caddy.
rebuild:
	$(DC) up -d --build

# Executa a suíte Python, compila os scripts e valida a sintaxe Bash.
# Não inicia containers nem chama APIs externas.
test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m py_compile scripts/*.py tests/*.py
	bash -n scripts/lib.sh scripts/chatwoot/*.sh scripts/waha/*.sh

# Confere interpolação e estrutura dos Compose local/público com valores sintéticos.
# Não inicia containers e não usa o .env real; requer Docker Compose v2 instalado.
validate-compose:
	$(PYTHON) scripts/validate_compose.py

# Remove os volumes do Compose selecionado e limpa marcadores gerados pelo setup.
#
# ATENÇÃO: apaga dados persistentes do PostgreSQL, n8n, Redis, WAHA e Chatwoot.
# No modo público, também remove os volumes do Caddy. É irreversível.
# Confirme explicitamente o escopo com um dos comandos abaixo:
#   make wipe CONFIRM_WIPE=YES
#   make public wipe CONFIRM_WIPE=YES
wipe:
	@if [ "$(CONFIRM_WIPE)" != "YES" ]; then \
		printf 'Recusado: este alvo apaga TODOS os volumes do projeto.\n' >&2; \
		printf 'Revise o escopo e execute `$(if $(filter public,$(MAKECMDGOALS)),make public wipe,make wipe) CONFIRM_WIPE=YES` se realmente quiser continuar.\n' >&2; \
		exit 2; \
	fi
	@if [ ! -f .env ] || [ ! -r .env ] || [ ! -w .env ]; then \
		printf 'Erro: .env precisa existir e estar legível/escrevível antes de remover volumes.\n' >&2; \
		exit 1; \
	fi
	@printf 'Removendo volumes dos serviços selecionados...\n'
	$(DC) down -v
	$(PYTHON) scripts/reset_state.py
