# ===========================================
# OboJobs Makefile
# ===========================================
# Zentrale Befehle fuer Frontend, Backend und Ralph

.PHONY: help install dev dev-frontend dev-backend build test lint clean \
        db-migrate db-upgrade db-downgrade db-reset \
        ralph ralph-status ralph-report ralph-reset ralph-headed ralph-split \
        logs docker-build docker-up docker-down

# Default target
.DEFAULT_GOAL := help

# ===========================================
# Variablen
# ===========================================
FRONTEND_DIR := frontend
BACKEND_DIR := backend
RALPH_DIR := ralph/test
VENV := $(BACKEND_DIR)/venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
FLASK := $(VENV)/bin/flask

# Farben
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m

# ===========================================
# Help
# ===========================================
help:
	@echo ""
	@echo "$(CYAN)OboJobs - Verfuegbare Befehle$(NC)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make install        - Installiere alle Dependencies (Frontend + Backend)"
	@echo "  make dev            - Starte Frontend + Backend parallel"
	@echo "  make dev-frontend   - Starte nur Frontend (Vite)"
	@echo "  make dev-backend    - Starte nur Backend (Flask)"
	@echo ""
	@echo "$(GREEN)Build & Test:$(NC)"
	@echo "  make build          - Build Frontend fuer Production"
	@echo "  make test           - Alle Tests ausfuehren"
	@echo "  make test-frontend  - Frontend Tests (Vitest)"
	@echo "  make test-backend   - Backend Tests (Pytest)"
	@echo "  make lint           - Linting (Frontend + Backend)"
	@echo "  make lint-fix       - Lint und auto-fix"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make db-migrate m=\"msg\"  - Neue Migration erstellen"
	@echo "  make db-upgrade     - Migrationen anwenden"
	@echo "  make db-downgrade   - Letzte Migration rueckgaengig"
	@echo "  make db-reset       - DB komplett zuruecksetzen"
	@echo ""
	@echo "$(GREEN)Ralph (UI Testing):$(NC)"
	@echo "  make ralph          - Ralph Tests starten"
	@echo "  make ralph-status   - Test-Fortschritt anzeigen"
	@echo "  make ralph-report   - Finalen Report generieren"
	@echo "  make ralph-reset    - Test-State zuruecksetzen"
	@echo "  make ralph-headed   - Tests mit sichtbarem Browser"
	@echo "  make ralph-split    - Split-Screen (tmux)"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-build   - Docker Images bauen"
	@echo "  make docker-up      - Container starten"
	@echo "  make docker-down    - Container stoppen"
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@echo "  make logs           - Backend Logs anzeigen"
	@echo "  make clean          - Build-Artefakte loeschen"
	@echo ""

# ===========================================
# Installation
# ===========================================
install: install-frontend install-backend
	@echo "$(GREEN)Alle Dependencies installiert$(NC)"

install-frontend:
	@echo "$(CYAN)Installiere Frontend Dependencies...$(NC)"
	cd $(FRONTEND_DIR) && npm install

install-backend:
	@echo "$(CYAN)Installiere Backend Dependencies...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		python3 -m venv $(VENV); \
	fi
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt

# ===========================================
# Development
# ===========================================
dev:
	@echo "$(CYAN)Starte Frontend und Backend...$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(NC)"
	@echo "$(YELLOW)Backend:  http://localhost:5001$(NC)"
	@echo ""
	@trap 'kill 0' SIGINT; \
	(cd $(FRONTEND_DIR) && npm run dev) & \
	($(PYTHON) -m flask --app $(BACKEND_DIR)/app run --debug --port 5001) & \
	wait

dev-frontend:
	@echo "$(CYAN)Starte Frontend (Vite)...$(NC)"
	cd $(FRONTEND_DIR) && npm run dev

dev-backend:
	@echo "$(CYAN)Starte Backend (Flask)...$(NC)"
	$(PYTHON) -m flask --app $(BACKEND_DIR)/app run --debug --port 5001

# ===========================================
# Build & Test
# ===========================================
build:
	@echo "$(CYAN)Build Frontend...$(NC)"
	cd $(FRONTEND_DIR) && npm run build

test: test-frontend test-backend
	@echo "$(GREEN)Alle Tests abgeschlossen$(NC)"

test-frontend:
	@echo "$(CYAN)Frontend Tests (Vitest)...$(NC)"
	cd $(FRONTEND_DIR) && npm run test

test-frontend-watch:
	@echo "$(CYAN)Frontend Tests im Watch-Modus...$(NC)"
	cd $(FRONTEND_DIR) && npm run test:watch

test-frontend-coverage:
	@echo "$(CYAN)Frontend Tests mit Coverage...$(NC)"
	cd $(FRONTEND_DIR) && npm run test:coverage

test-backend:
	@echo "$(CYAN)Backend Tests (Pytest)...$(NC)"
	$(PYTHON) -m pytest $(BACKEND_DIR) -v

lint: lint-frontend lint-backend
	@echo "$(GREEN)Linting abgeschlossen$(NC)"

lint-frontend:
	@echo "$(CYAN)Linting Frontend (ESLint)...$(NC)"
	cd $(FRONTEND_DIR) && npm run lint

lint-backend:
	@echo "$(CYAN)Linting Backend (Ruff)...$(NC)"
	$(VENV)/bin/ruff check $(BACKEND_DIR)

lint-fix:
	@echo "$(CYAN)Lint + Auto-Fix...$(NC)"
	cd $(FRONTEND_DIR) && npm run lint:fix
	$(VENV)/bin/ruff check $(BACKEND_DIR) --fix

# ===========================================
# Database
# ===========================================
db-migrate:
	@echo "$(CYAN)Erstelle Migration: $(m)$(NC)"
	$(PYTHON) -m flask --app $(BACKEND_DIR)/app db migrate -m "$(m)"

db-upgrade:
	@echo "$(CYAN)Migrationen anwenden...$(NC)"
	$(PYTHON) -m flask --app $(BACKEND_DIR)/app db upgrade

db-downgrade:
	@echo "$(CYAN)Letzte Migration rueckgaengig...$(NC)"
	$(PYTHON) -m flask --app $(BACKEND_DIR)/app db downgrade

db-reset:
	@echo "$(RED)ACHTUNG: Datenbank wird zurueckgesetzt!$(NC)"
	@read -p "Fortfahren? (y/n): " confirm && [ "$$confirm" = "y" ]
	rm -f $(BACKEND_DIR)/instance/*.db
	$(PYTHON) -m flask --app $(BACKEND_DIR)/app db upgrade
	@echo "$(GREEN)Datenbank zurueckgesetzt$(NC)"

db-shell:
	@echo "$(CYAN)Oeffne DB Shell...$(NC)"
	$(PYTHON) -m flask --app $(BACKEND_DIR)/app shell

# ===========================================
# Ralph (UI Testing)
# ===========================================
ralph:
	@echo "$(CYAN)Starte Ralph Tests...$(NC)"
	./$(RALPH_DIR)/ralph.sh

ralph-status:
	@echo "$(CYAN)Ralph Test Status$(NC)"
	./$(RALPH_DIR)/ralph.sh --status

ralph-report:
	@echo "$(CYAN)Generiere Ralph Report$(NC)"
	./$(RALPH_DIR)/ralph.sh --report

ralph-reset:
	@echo "$(YELLOW)Reset Ralph Test State$(NC)"
	./$(RALPH_DIR)/ralph.sh --reset

ralph-headed:
	@echo "$(CYAN)Ralph mit sichtbarem Browser$(NC)"
	./$(RALPH_DIR)/ralph.sh --headed

ralph-split:
	@echo "$(CYAN)Ralph im Split-Screen Modus$(NC)"
	./$(RALPH_DIR)/ralph.sh --split

# ===========================================
# Docker
# ===========================================
docker-build:
	@echo "$(CYAN)Docker Images bauen...$(NC)"
	docker-compose build

docker-up:
	@echo "$(CYAN)Docker Container starten...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Container gestartet$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(NC)"
	@echo "$(YELLOW)Backend:  http://localhost:5001$(NC)"

docker-down:
	@echo "$(CYAN)Docker Container stoppen...$(NC)"
	docker-compose down

docker-logs:
	docker-compose logs -f

# ===========================================
# Utilities
# ===========================================
logs:
	@echo "$(CYAN)Backend Logs$(NC)"
	@if [ -f "$(BACKEND_DIR)/logs/app.log" ]; then \
		tail -f $(BACKEND_DIR)/logs/app.log; \
	else \
		echo "Keine Log-Datei gefunden. Starte Backend mit: make dev-backend"; \
	fi

clean:
	@echo "$(CYAN)Loesche Build-Artefakte...$(NC)"
	rm -rf $(FRONTEND_DIR)/dist
	rm -rf $(FRONTEND_DIR)/node_modules/.vite
	rm -rf $(BACKEND_DIR)/__pycache__
	rm -rf $(BACKEND_DIR)/*/__pycache__
	rm -rf $(BACKEND_DIR)/.pytest_cache
	rm -rf $(BACKEND_DIR)/.ruff_cache
	find . -name "*.pyc" -delete
	find . -name ".DS_Store" -delete
	@echo "$(GREEN)Bereinigung abgeschlossen$(NC)"

# Shortcut Aliases
f: dev-frontend
b: dev-backend
t: test
l: lint
r: ralph
