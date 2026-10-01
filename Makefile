# Comandos do template. O .env real é local e não deve ser versionado.
DC ?= docker compose --env-file versions.env --env-file .env
PYTHON ?= python3

.PHONY: help up down restart logs ps rebuild test wipe

help:
	@printf '\n\033[36m  n8n-stack\033[0m\n'
	@printf '\033[90m  Uso: make <comando>\033[0m\n\n'
	@printf '  Comandos:\n'
	@printf '    up               Sobe os containers\n'
	@printf '    down             Para os containers, preservando volumes\n'
	@printf '    restart          Reinicia os containers\n'
	@printf '    logs             Mostra logs ao vivo (Ctrl+C para sair)\n'
	@printf '    ps               Lista containers e status\n'
	@printf '    rebuild          Reconstrói imagens locais (hoje só Caddy) e sobe a pilha\n'
	@printf '    test             Executa testes Python e valida sintaxe dos scripts\n'
	@printf '    wipe             Apaga todos os volumes; exige CONFIRM_WIPE=YES\n\n'

up:
	$(DC) up -d

down:
	$(DC) down

restart:
	$(DC) restart

logs:
	$(DC) logs -f

ps:
	$(DC) ps

# Reconstrói imagens de serviços que têm `build:` local no Compose.
rebuild:
	$(DC) up -d --build

test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m py_compile scripts/*.py tests/*.py
	bash -n scripts/lib.sh scripts/chatwoot/*.sh scripts/waha/*.sh

# `down -v` remove todos os volumes deste projeto, não apenas os bancos.
# Exige opt-in explícito para reduzir o risco de apagar dados por engano.
wipe:
	@if [ "$(CONFIRM_WIPE)" != "YES" ]; then \
		printf 'Recusado: este alvo apaga TODOS os volumes do projeto.\n' >&2; \
		printf 'Revise o escopo e execute `make wipe CONFIRM_WIPE=YES` se realmente quiser continuar.\n' >&2; \
		exit 2; \
	fi
	@if [ ! -f .env ] || [ ! -r .env ] || [ ! -w .env ]; then \
		printf 'Erro: .env precisa existir e estar legível/escrevível antes de remover volumes.\n' >&2; \
		exit 1; \
	fi
	@printf 'Removendo volumes PostgreSQL, n8n, Redis, WAHA, Caddy e Chatwoot...\n'
	$(DC) down -v
	$(PYTHON) scripts/reset_state.py
