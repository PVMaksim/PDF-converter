# ===========================================================================
# PDF Converter Bot — Makefile
# ===========================================================================
# Usage: make <command>
# Example: make up, make test, make deploy
# ===========================================================================

.PHONY: help up down build logs shell test lint clean backup migrate frontend-dev

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
PROJECT_NAME := pdf_converter
DOCKER_COMPOSE := docker-compose
PYTHON := python3
PIP := pip3
ALEMBIC := alembic
NPM := npm

# ---------------------------------------------------------------------------
# Docker Compose commands
# ---------------------------------------------------------------------------

## Start all services in background
up:
	$(DOCKER_COMPOSE) up -d --build

## Start all services in foreground (with logs)
up-logs:
	$(DOCKER_COMPOSE) up --build

## Stop all services
down:
	$(DOCKER_COMPOSE) down

## Stop all services and remove volumes
down-v:
	$(DOCKER_COMPOSE) down -v

## Restart all services
restart:
	$(DOCKER_COMPOSE) restart

## Show logs from all services
logs:
	$(DOCKER_COMPOSE) logs -f

## Show logs from specific service (e.g., make logs-backend SERVICE=backend)
logs-%:
	$(DOCKER_COMPOSE) logs -f $(SERVICE)

## Build all images
build:
	$(DOCKER_COMPOSE) build

## Rebuild without cache
build-no-cache:
	$(DOCKER_COMPOSE) build --no-cache

## Open shell in backend container
shell:
	$(DOCKER_COMPOSE) exec backend /bin/bash

## Open shell in celery worker container
shell-worker:
	$(DOCKER_COMPOSE) exec celery_worker /bin/bash

## Run database migrations
migrate:
	$(DOCKER_COMPOSE) exec backend alembic upgrade head

## Create new migration (e.g., make migration NAME=add_user_field)
migration:
	$(DOCKER_COMPOSE) exec backend alembic revision --autogenerate -m "$(NAME)"

## Show migration status
migration-status:
	$(DOCKER_COMPOSE) exec backend alembic current

# ---------------------------------------------------------------------------
# Frontend commands
# ---------------------------------------------------------------------------

## Start frontend development server
frontend-dev:
	cd frontend && $(NPM) install && $(NPM) run dev

## Build frontend
frontend-build:
	cd frontend && $(NPM) install && $(NPM) run build

## Run frontend tests
frontend-test:
	cd frontend && $(NPM) test

## Lint frontend
frontend-lint:
	cd frontend && $(NPM) run lint

## Format frontend code
frontend-format:
	cd frontend && $(NPM) run format

# ---------------------------------------------------------------------------
# Testing commands
# ---------------------------------------------------------------------------

## Run unit tests
test:
	$(PYTHON) -m pytest tests/unit -v

## Run integration tests
test-integration:
	$(PYTHON) -m pytest tests/integration -v

## Run all tests with coverage
test-coverage:
	$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=html

## Run tests and generate XML report (for CI)
test-ci:
	$(PYTHON) -m pytest tests/ -v --tb=short --maxfail=1

# ---------------------------------------------------------------------------
# Development commands
# ---------------------------------------------------------------------------

## Install dependencies locally
install:
	$(PIP) install -r requirements.txt

## Install dev dependencies
install-dev:
	$(PIP) install -r requirements.txt pytest pytest-asyncio flake8 black mypy

## Run linter
lint:
	flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics

## Run black formatter
format:
	black src/ tests/

## Run mypy type checker
type-check:
	mypy src/ --ignore-missing-imports

## Check code style
check: lint type-check

## Clean Python cache
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/ .coverage htmlcov/ .mypy_cache/

# ---------------------------------------------------------------------------
# Database commands
# ---------------------------------------------------------------------------

## Backup database
backup:
	./scripts/backup.sh

## Open psql shell in database container
psql:
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d pdf_bot

## Show database tables
db-tables:
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d pdf_bot -c "\dt"

# ---------------------------------------------------------------------------
# Deployment commands
# ---------------------------------------------------------------------------

## Deploy to production (pull and restart)
deploy:
	$(DOCKER_COMPOSE) pull
	$(DOCKER_COMPOSE) up -d --remove-orphans

## Show running containers
ps:
	$(DOCKER_COMPOSE) ps

## Health check
health:
	./scripts/health_check.sh

## Prune unused Docker resources
prune:
	docker system prune -a --volumes --force

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

## Show this help message
help:
	@echo "PDF Converter Bot - Available Commands"
	@echo "======================================="
	@echo ""
	@echo "Docker Compose:"
	@echo "  make up              - Start all services"
	@echo "  make down            - Stop all services"
	@echo "  make logs            - Show logs"
	@echo "  make build           - Build images"
	@echo "  make shell           - Open shell in backend"
	@echo ""
	@echo "Frontend:"
	@echo "  make frontend-dev    - Start frontend dev server"
	@echo "  make frontend-build  - Build frontend"
	@echo "  make frontend-lint   - Lint frontend code"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-coverage   - Run tests with coverage"
	@echo ""
	@echo "Development:"
	@echo "  make install         - Install dependencies"
	@echo "  make lint            - Run linter"
	@echo "  make format          - Format code"
	@echo "  make clean           - Clean cache files"
	@echo ""
	@echo "Database:"
	@echo "  make migrate         - Run migrations"
	@echo "  make backup          - Backup database"
	@echo "  make psql            - Open psql shell"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy          - Deploy to production"
	@echo "  make health          - Health check"
	@echo ""
