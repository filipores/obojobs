#!/bin/bash
# RALF Explore Mode - Konfiguration
# Autonome explorative Tests mit MCP Playwright

# ============================================
# Exploration Configuration
# ============================================
# Keine max iterations - läuft bis manuell unterbrochen
# Aber wir setzen einen sehr hohen Default als Sicherheit
MAX_EXPLORE_ITERATIONS=${MAX_EXPLORE_ITERATIONS:-999999}
TIMEOUT_MINUTES=${TIMEOUT_MINUTES:-15}

# Pause zwischen Explorationen (Sekunden)
EXPLORE_PAUSE=${EXPLORE_PAUSE:-5}

# ============================================
# Server URLs
# ============================================
FRONTEND_URL=${FRONTEND_URL:-"http://localhost:3000"}
BACKEND_URL=${BACKEND_URL:-"http://localhost:5001"}
AUTO_START_SERVERS=${AUTO_START_SERVERS:-false}

# ============================================
# Test User Credentials (für Auth-Tests)
# ============================================
TEST_USER_EMAIL=${TEST_USER_EMAIL:-"test@example.com"}
TEST_USER_PASSWORD=${TEST_USER_PASSWORD:-"Test1234!"}

# ============================================
# Deduplication
# ============================================
# Ignoriere Bugs/Suggestions die bereits existieren
DEDUPE_ENABLED=${DEDUPE_ENABLED:-true}

# ============================================
# Output Configuration
# ============================================
LOG_DIR="logs"
BUGS_FILE="bugs.json"
SUGG_FILE="sugg.json"
SESSION_FILE="session.json"

# ============================================
# Claude CLI Configuration
# ============================================
CLAUDE_OUTPUT_FORMAT="json"
# Alle Tools für Fullstack-Exploration
CLAUDE_ALLOWED_TOOLS="Write,Edit,Read,Bash,Glob,Grep,mcp__playwright__*"

# ============================================
# Model Selection
# ============================================
# Sonnet für Exploration (schnell, kostengünstig)
CLAUDE_MODEL_EXPLORE=${CLAUDE_MODEL_EXPLORE:-"claude-sonnet-4-20250514"}

# ============================================
# Circuit Breaker Thresholds
# ============================================
# Nach wie vielen gleichen Fehlern stoppen
CB_SAME_ERROR_THRESHOLD=${CB_SAME_ERROR_THRESHOLD:-5}
# Nach wie vielen Loops ohne neuen Fund warnen
CB_NO_DISCOVERY_THRESHOLD=${CB_NO_DISCOVERY_THRESHOLD:-10}

# ============================================
# Farben für Terminal Output
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
ORANGE='\033[38;5;208m'
NC='\033[0m'

# Export alle Variablen
export MAX_EXPLORE_ITERATIONS
export TIMEOUT_MINUTES
export EXPLORE_PAUSE
export FRONTEND_URL
export BACKEND_URL
export AUTO_START_SERVERS
export TEST_USER_EMAIL
export TEST_USER_PASSWORD
export DEDUPE_ENABLED
export LOG_DIR
export BUGS_FILE
export SUGG_FILE
export SESSION_FILE
export CLAUDE_OUTPUT_FORMAT
export CLAUDE_ALLOWED_TOOLS
export CLAUDE_MODEL_EXPLORE
export CB_SAME_ERROR_THRESHOLD
export CB_NO_DISCOVERY_THRESHOLD
