# Snappy - Docker Compose Management with Profiles
#
# Profiles:
#   minimal - Base infrastructure + ColPali only (no DeepSeek OCR, no DuckDB)
#   ml      - Base + ColPali + DeepSeek OCR (no DuckDB)
#   full    - All services including DuckDB
#
# Usage:
#   make up          - Start with full profile (all services)
#   make up-minimal  - Start with minimal profile
#   make up-ml       - Start with ML profile
#   make down        - Stop all services
#   make logs        - View logs from all running services
#   make clean       - Stop services and remove volumes

.PHONY: help up up-minimal up-ml up-full down logs clean restart ps build

# Docker Compose files
COMPOSE_FILES := -f docker/base.yml -f docker/ml.yml -f docker/app.yml
DOCKER_COMPOSE := docker compose $(COMPOSE_FILES)

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Snappy Docker Compose Management"
	@echo ""
	@echo "Available profiles:"
	@echo "  minimal - ColPali only (DEEPSEEK_OCR_ENABLED=false, DUCKDB_ENABLED=false)"
	@echo "  ml      - ColPali + DeepSeek OCR (DUCKDB_ENABLED=false)"
	@echo "  full    - All services (ColPali + DeepSeek OCR + DuckDB)"
	@echo ""
	@echo "Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: up-full ## Start all services (alias for up-full)

up-minimal: ## Start minimal profile (ColPali only)
	@echo "🚀 Starting minimal profile (ColPali only)..."
	DEEPSEEK_OCR_ENABLED=false DUCKDB_ENABLED=false $(DOCKER_COMPOSE) --profile minimal up --build -d
	@echo "✅ Services started with minimal profile"
	@echo "   - Base infrastructure (Qdrant, MinIO)"
	@echo "   - Application (Backend, Frontend)"
	@echo "   - ColPali (GPU/CPU auto-detect)"

up-ml: ## Start ML profile (ColPali + DeepSeek OCR)
	@echo "🚀 Starting ML profile (ColPali + DeepSeek OCR)..."
	DEEPSEEK_OCR_ENABLED=true DUCKDB_ENABLED=false $(DOCKER_COMPOSE) --profile ml up --build -d
	@echo "✅ Services started with ML profile"
	@echo "   - Base infrastructure (Qdrant, MinIO)"
	@echo "   - Application (Backend, Frontend)"
	@echo "   - ColPali (GPU/CPU auto-detect)"
	@echo "   - DeepSeek OCR (GPU required)"

up-full: ## Start full profile (all services)
	@echo "🚀 Starting full profile (all services)..."
	DEEPSEEK_OCR_ENABLED=true DUCKDB_ENABLED=true $(DOCKER_COMPOSE) --profile full up --build -d
	@echo "✅ Services started with full profile"
	@echo "   - Base infrastructure (Qdrant, MinIO)"
	@echo "   - Application (Backend, Frontend)"
	@echo "   - ColPali (GPU/CPU auto-detect)"
	@echo "   - DeepSeek OCR (GPU required)"
	@echo "   - DuckDB"

down: ## Stop all services
	@echo "🛑 Stopping all services..."
	$(DOCKER_COMPOSE) --profile full down
	@echo "✅ All services stopped"

logs: ## View logs from all running services
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## View backend logs only
	$(DOCKER_COMPOSE) logs -f backend

logs-frontend: ## View frontend logs only
	$(DOCKER_COMPOSE) logs -f frontend

logs-colpali: ## View ColPali logs only
	$(DOCKER_COMPOSE) logs -f colpali

logs-deepseek: ## View DeepSeek OCR logs only
	$(DOCKER_COMPOSE) logs -f deepseek-ocr

logs-duckdb: ## View DuckDB logs only
	$(DOCKER_COMPOSE) logs -f duckdb

clean: ## Stop services and remove volumes
	@echo "🧹 Cleaning up (stopping services and removing volumes)..."
	$(DOCKER_COMPOSE) --profile full down -v
	@echo "✅ Cleanup complete"

restart: down up ## Restart all services

restart-minimal: down up-minimal ## Restart with minimal profile

restart-ml: down up-ml ## Restart with ML profile

restart-full: down up-full ## Restart with full profile

ps: ## Show running services
	$(DOCKER_COMPOSE) ps

build: ## Rebuild all images
	@echo "🔨 Building all images..."
	$(DOCKER_COMPOSE) --profile full build
	@echo "✅ Build complete"

build-no-cache: ## Rebuild all images without cache
	@echo "🔨 Building all images (no cache)..."
	$(DOCKER_COMPOSE) --profile full build --no-cache
	@echo "✅ Build complete"

pull: ## Pull latest base images
	@echo "📥 Pulling latest base images..."
	$(DOCKER_COMPOSE) --profile full pull
	@echo "✅ Pull complete"

health: ## Check health of all services
	@echo "🏥 Service health status:"
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(CONTAINER|snappy|colpali|deepseek|duckdb|qdrant|minio|backend|frontend)"
