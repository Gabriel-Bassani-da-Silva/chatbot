# ============================================================
# Comandos do projeto  —  rode `make` para ver a ajuda
# ============================================================

# `make` sem argumentos mostra a ajuda.
.DEFAULT_GOAL := help

define HELP_TEXT

  (modo atual: $(MODE))
  Uso: make [public|local] <comando> [SERVICE=nome]

  Execução e diagnóstico
    up                  Inicia os serviços em segundo plano
    down                Para os serviços, preservando volumes
    restart             Reinicia os serviços (ou SERVICE=nome)
    logs                Acompanha os logs (Ctrl+C sai; ou SERVICE=nome)
    ps                  Lista os serviços e seus estados
    rebuild             Reconstrói imagens locais e inicia os serviços

  Verificação e limpeza
    test                Executa os testes e valida a sintaxe dos scripts
    validate-compose    Valida os Compose local/público (requer Docker Compose)
    wipe                Remove TODOS os volumes; pede confirmação (y/n)

  Modo (local ou público)
    Detectado automaticamente: se o .env tiver TUNNEL_TOKEN preenchido,
    usa o modo público (Caddy + Cloudflare Tunnel); senão, local.
    Seletores (escreva antes do comando) ou MODE=... forçam o modo.

  Exemplos
    make up                      # modo automático
    make public up               # força público
    make local up                # força local (ou MODE=local)
    make logs SERVICE=n8n        # logs só do n8n
    make wipe                    # pergunta y/n antes de apagar
    make wipe y                  # sem perguntar (ou CONFIRM_WIPE=YES)

endef
export HELP_TEXT

help:
	@printf '%s\n' "$$HELP_TEXT"

# Detecção automática: TUNNEL_TOKEN não vazio no .env => público.
# Aspas e espaços não contam: TUNNEL_TOKEN="" ou TUNNEL_TOKEN=   é vazio, como no Compose.
DETECTED_MODE := $(if $(shell sed -n "s/^TUNNEL_TOKEN=[[:space:]]*[\"']*[[:space:]]*\([^\"'[:space:]]\)/\1/p" .env 2>/dev/null),public,local)

# Prioridade: seletor na linha de comando > MODE=... > detecção automática.
ifneq ($(filter public,$(MAKECMDGOALS)),)
MODE := public
else ifneq ($(filter local,$(MAKECMDGOALS)),)
MODE := local
else ifeq ($(origin MODE),undefined)
MODE := $(DETECTED_MODE)
endif

# Compose base: PostgreSQL, Redis, n8n, WAHA e Chatwoot.
# O overlay público acrescenta Caddy e Cloudflare Tunnel.
COMPOSE_FILES := -f compose.yml
ifeq ($(MODE),public)
COMPOSE_FILES += -f compose.public.yml
endif

# Comando compartilhado pelos alvos Docker.
# O .env deve vir de .env.example (local) ou .env.public.example (público).
DC ?= docker compose --env-file versions.env --env-file .env $(COMPOSE_FILES)
PYTHON ?= python3

# Serviço opcional para logs/restart: make logs SERVICE=n8n
SERVICE ?=

.PHONY: help public local y yes up down restart logs ps rebuild test validate-compose wipe check-env

# Seletores para forçar o modo (sem eles, o modo é detectado pelo .env).
public local:
	@:

# Seletores de confirmação automática: make wipe y
y yes:
	@:

# Garante que o .env existe antes de usar o Docker Compose.
check-env:
	@if [ ! -f .env ]; then \
		printf '\033[31mErro:\033[0m arquivo .env não encontrado.\n' >&2; \
		printf 'Copie o modelo: cp $(if $(filter public,$(MODE)),.env.public.example,.env.example) .env\n' >&2; \
		exit 1; \
	fi

##@ Execução e diagnóstico
up: check-env ## Inicia os serviços em segundo plano
	$(DC) up -d

down: check-env ## Para os serviços, preservando volumes
	$(DC) down

restart: check-env ## Reinicia os serviços (ou SERVICE=nome)
	$(DC) restart $(SERVICE)

logs: check-env ## Acompanha os logs (Ctrl+C sai; ou SERVICE=nome)
	$(DC) logs -f $(SERVICE)

ps: check-env ## Lista os serviços e seus estados
	$(DC) ps

rebuild: check-env ## Reconstrói imagens locais e inicia os serviços
	$(DC) up -d --build

##@ Verificação e limpeza
test: ## Executa os testes e valida a sintaxe dos scripts (requer Node.js)
	@command -v node >/dev/null 2>&1 || { printf 'Erro: Node.js não encontrado no PATH; os testes do normalizador dependem dele.\n' >&2; exit 1; }
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m py_compile scripts/*.py tests/*.py
	bash -n scripts/lib.sh scripts/chatwoot/*.sh scripts/waha/*.sh

validate-compose: ## Valida os Compose local/público (requer Docker Compose)
	$(PYTHON) scripts/validate_compose.py

# ATENÇÃO: apaga dados persistentes do PostgreSQL, n8n, Redis, WAHA e Chatwoot.
# No modo público, também remove os volumes do Caddy. É irreversível.
wipe: ## Remove TODOS os volumes; pede confirmação (y/n)
	@if [ "$(CONFIRM_WIPE)" != "YES" ] && [ -z "$(filter y yes,$(MAKECMDGOALS))" ]; then \
		printf '\033[31mATENÇÃO:\033[0m isto apaga TODOS os volumes do projeto (modo: $(MODE)). É irreversível.\n'; \
		printf 'Continuar? [y/n] '; \
		read answer; \
		case "$$answer" in \
			y|Y|yes|YES) ;; \
			*) printf 'Cancelado.\n'; exit 1 ;; \
		esac; \
	fi
	@if [ ! -f .env ] || [ ! -r .env ] || [ ! -w .env ]; then \
		printf 'Erro: .env precisa existir e estar legível/escrevível antes de remover volumes.\n' >&2; \
		exit 1; \
	fi
	@printf 'Removendo volumes dos serviços selecionados...\n'
	$(DC) down -v
	$(PYTHON) scripts/reset_state.py
