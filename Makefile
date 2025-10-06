SHELL := /bin/bash

# Variables
COMPOSE := docker compose
API_CONTAINER := gad_api_dev
COMPOSE_PROD := docker compose -f docker/docker-compose.prod.yml
API_CONTAINER_PROD := gad_api_prod

.PHONY: help up down ps logs-api migrate smoke ws-smoke test test-cov lint type fmt \
	backup backup-verify backup-list backup-restore backup-service backup-service-down \
	ci ci-local build-api release-check release-check-strict \
	prod-up prod-up-local prod-down prod-down-local prod-ps prod-logs-api prod-migrate prod-smoke prod-ws-smoke prod-smoke-local

help:
	@echo "Targets disponibles"
	@echo "- Dev:   up, down, ps, logs-api, migrate, smoke, ws-smoke, test, test-cov, lint, type, fmt"
	@echo "- CI/CD: ci, ci-local, build-api, release-check, release-check-strict"
	@echo "- Backup: backup, backup-verify, backup-list, backup-restore, backup-service, backup-service-down"
	@echo "- Prod:  prod-up, prod-up-local, prod-down, prod-down-local, prod-ps, prod-logs-api, prod-migrate, prod-smoke, prod-ws-smoke"
	@echo "          prod-smoke-local (puerto 8001)"

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
	poetry run python scripts/ws_smoke_test.py

test:
	poetry run python -m pytest -q

test-cov:
	# Ejecuta pytest con reporte de cobertura (config en pyproject.toml/pytest.ini)
	poetry run python -m pytest --cov=src --cov-report=term-missing

lint:
	poetry run ruff check .

type:
	poetry run mypy src config

fmt:
	poetry run ruff check --fix .

# --- Producción ---

prod-up:
	$(COMPOSE_PROD) up -d --build

prod-up-local:
	docker compose -f docker/docker-compose.prod.local.yml up -d --build

prod-down:
	$(COMPOSE_PROD) down

prod-down-local:
	docker compose -f docker/docker-compose.prod.local.yml down -v

prod-ps:
	docker compose -f docker/docker-compose.prod.local.yml ps

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

prod-smoke-local:
	@set -e; \
	max=15; i=1; \
	until [ $$i -gt $$max ]; do \
	  code=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/health || true); \
	  if [ "$$code" = "200" ]; then echo "[OK] /api/v1/health => 200"; break; fi; \
	  echo "[wait] health=$$code (intent $$i/$$max)"; \
	  i=$$((i+1)); sleep 2; \
	 done; \
	if [ "$$code" != "200" ]; then echo "[FAIL] /api/v1/health => $$code"; exit 1; fi; \
	code=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/metrics); \
	if [ "$$code" != "200" ]; then echo "[FAIL] /metrics => $$code"; exit 1; fi; \
	echo "[OK] HTTP smoke passed (prod-local:8001)"
# --- Backups ---

# Ejecutar un backup manual
backup:
	@echo "Ejecutando backup manual de la base de datos..."
	@mkdir -p backups
	@scripts/backup/postgres_backup.sh

# Verificar un backup existente sin restaurarlo
backup-verify:
	@if [ -z "$$BACKUP_FILE" ]; then \
		echo "Error: Debe especificar el archivo de backup a verificar."; \
		echo "Uso: make backup-verify BACKUP_FILE=path/to/backup.sql.gz"; \
		exit 1; \
	fi; \
	scripts/backup/postgres_restore.sh "$$BACKUP_FILE" --verify-only

# Listar backups disponibles
backup-list:
	@echo "Backups disponibles:"
	@find backups -name "postgres_*.sql.gz" -type f | sort -r

# Restaurar desde un backup
backup-restore:
	@if [ -z "$$BACKUP_FILE" ]; then \
		echo "Error: Debe especificar el archivo de backup a restaurar."; \
		echo "Uso: make backup-restore BACKUP_FILE=path/to/backup.sql.gz"; \
		exit 1; \
	fi; \
	scripts/backup/postgres_restore.sh "$$BACKUP_FILE"

# Iniciar servicio de backups programados (requiere que la red gad_network esté creada)
backup-service:
	docker network inspect gad_network >/dev/null 2>&1 || docker network create gad_network
	docker compose -f docker-compose.backup.yml up -d

# Detener servicio de backups programados
backup-service-down:
	docker compose -f docker-compose.backup.yml down

# --- CI/CD ---

# Simular pipeline de CI localmente
ci:
	@echo "🚀 Ejecutando pipeline de CI localmente..."
	@$(MAKE) lint
	@$(MAKE) type
	@$(MAKE) test
	@$(MAKE) build-api
	@echo "✅ Pipeline de CI completado exitosamente"

# Ejecutar CI con Docker (más cercano al ambiente real)
ci-local:
	@echo "🚀 Ejecutando CI con Docker..."
	docker compose -f docker-compose.yml up -d db redis
	@sleep 5
	@$(MAKE) test
	@$(MAKE) smoke
	@$(MAKE) ws-smoke
	docker compose down
	@echo "✅ CI local completado exitosamente"

# Construir imagen de API
build-api:
	@echo "🏗️ Construyendo imagen de API..."
	docker build -f docker/Dockerfile.api -t grupogad/api:local .

# Validar que el proyecto está listo para release
release-check:
	@echo "🔍 Verificando que el proyecto está listo para release..."
	@$(MAKE) lint
	@$(MAKE) test-cov
	@$(MAKE) build-api
	@echo "✅ Proyecto listo para release"

# Validar que el proyecto está listo para release (con type checking estricto)
release-check-strict:
	@echo "🔍 Verificando que el proyecto está listo para release (modo estricto)..."
	@$(MAKE) lint
	@$(MAKE) type
	@$(MAKE) test-cov
	@$(MAKE) build-api
	@echo "✅ Proyecto listo para release (modo estricto)"