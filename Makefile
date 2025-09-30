SHELL := /bin/bash

# Variables
COMPOSE := docker compose
API_CONTAINER := gad_api_dev
COMPOSE_PROD := docker compose -f docker/docker-compose.prod.yml
API_CONTAINER_PROD := gad_api_prod

.PHONY: help up down ps logs-api migrate smoke ws-smoke test test-cov lint type fmt \
        prod-up prod-down prod-ps prod-logs-api prod-migrate prod-smoke prod-ws-smoke

help:
	@echo "Targets disponibles"
	@echo "- Dev:   up, down, ps, logs-api, migrate, smoke, ws-smoke, test, test-cov, lint, type, fmt"
	@echo "- Prod:  prod-up, prod-down, prod-ps, prod-logs-api, prod-migrate, prod-smoke, prod-ws-smoke"

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

test-cov:
	# Ejecuta pytest con reporte de cobertura (config en pyproject.toml/pytest.ini)
	python -m pytest --cov=src --cov-report=term-missing

lint:
	ruff check .

type:
	mypy src config

fmt:
	ruff check --fix .

# --- Producción ---

prod-up:
	$(COMPOSE_PROD) up -d --build

prod-down:
	$(COMPOSE_PROD) down

prod-ps:
	docker compose -f docker/docker-compose.prod.yml ps

prod-logs-api:
	docker logs -f $(API_CONTAINER_PROD)

prod-migrate:
	docker exec $(API_CONTAINER_PROD) alembic upgrade head

prod-smoke:
	@set -e; \
	code=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/metrics); \
	if [ "$$code" != "200" ]; then echo "[FAIL] /metrics => $$code"; exit 1; fi; \
	code=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health); \
	if [ "$$code" != "200" ]; then echo "[FAIL] /api/v1/health => $$code"; exit 1; fi; \
	echo "[OK] HTTP smoke passed (prod)"

prod-ws-smoke:
	python scripts/ws_smoke_test.py
