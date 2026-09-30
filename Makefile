# --- Variaveis de projeto ---
DC          := docker compose --env-file versions.env --env-file .env
CONTAINER   := n8n-stack-postgres-1
PG_USER     := n8n

.PHONY: help up down restart logs ps config rebuild rebuild-caddy

# ------------------------------------------------------------------------------
help:
	@echo ""
	@echo -e "\033[36m  n8n-stack\033[0m"
	@echo -e "\033[90m  Uso: make <comando>\033[0m"
	@echo ""
	@echo "  Comandos:"
	@echo "    up               Sobe os containers"
	@echo "    down             Para os containers"
	@echo "    restart          Reinicia os containers"
	@echo "    logs             Logs ao vivo (Ctrl+C para sair)"
	@echo "    ps               Lista containers e status"
	@echo "    config           Valida o compose.yml"
	@echo "    rebuild          Reconstrói TODAS as imagens e reinicia"
	@echo "    rebuild-caddy    Reconstrói só o Caddy (útil ao mudar o Caddyfile)"
	@echo ""

# ------------------------------------------------------------------------------
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

config:
	$(DC) config

rebuild:
	$(DC) up -d --build

rebuild-caddy:
	$(DC) up -d --build caddy
