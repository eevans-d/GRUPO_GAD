SHELL := /bin/bash

# Variables
COMPOSE := docker compose
API_CONTAINER := gad_api_dev

.PHONY: up down ps logs-api migrate smoke ws-smoke test lint type fmt

up:
	$(COMPOSE) up -d db redis api

down:
	$(COMPOSE) down

ps:
	docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | (grep -E 'gad_(db|redis|api)_dev|NAMES' || true)

logs-api:
	docker logs -f $(API_CONTAINER)

migrate:
	docker exec $(API_CONTAINER) alembic upgrade head

smoke:
	@set -e; \
	code=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/metrics); \
	if [ "$$code" != "200" ]; then echo "[FAIL] /metrics => $$code"; exit 1; fi; \
	code=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health); \
	if [ "$$code" != "200" ]; then echo "[FAIL] /api/v1/health => $$code"; exit 1; fi; \
	echo "[OK] HTTP smoke passed"

ws-smoke:
	python scripts/ws_smoke_test.py

test:
	python -m pytest -q

lint:
	ruff check .

type:
	mypy src config

fmt:
	ruff check --fix .
