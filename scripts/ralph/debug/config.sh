#!/bin/bash
# RALF Debug Mode - Konfiguration
# Bug-basiertes Debugging analog zu Feature-Ralph

# ============================================
# Bug Processing
# ============================================
MAX_FIX_ATTEMPTS=${MAX_FIX_ATTEMPTS:-3}
TIMEOUT_MINUTES=${TIMEOUT_MINUTES:-15}

# ============================================
# Circuit Breaker Thresholds
# ============================================
CB_NO_PROGRESS_THRESHOLD=3
CB_SAME_ERROR_THRESHOLD=5

# ============================================
# Split Mode - tmux split screen
# ============================================
SPLIT_MODE=${SPLIT_MODE:-false}
LIVE_LOG_FILE="logs/claude_live.log"

# ============================================
# Output Configuration
# ============================================
LOG_DIR="logs"
BUGS_FILE="bugs.json"
LEARNINGS_FILE="learnings.md"
PROGRESS_FILE="progress.txt"

# ============================================
# Claude CLI Configuration
# ============================================
CLAUDE_OUTPUT_FORMAT="json"
CLAUDE_ALLOWED_TOOLS="Write,Edit,Read,Bash,Glob,Grep"

# ============================================
# Model Selection (Token-Optimierung)
# ============================================
# Sonnet für Bug-Fixes (ausreichend für die meisten Fixes)
CLAUDE_MODEL_IMPL=${CLAUDE_MODEL_IMPL:-"claude-sonnet-4-20250514"}
# Haiku für QA-Verifikation
CLAUDE_MODEL_QA=${CLAUDE_MODEL_QA:-"claude-haiku-4-5-20251001"}
ENABLE_QA_PHASE=${ENABLE_QA_PHASE:-true}

# ============================================
# State Files
# ============================================
CIRCUIT_BREAKER_FILE=".circuit_breaker_state"
SESSION_FILE=".ralph_session"

# ============================================
# Farben für Terminal Output
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Export alle Variablen
export MAX_FIX_ATTEMPTS
export TIMEOUT_MINUTES
export CB_NO_PROGRESS_THRESHOLD
export CB_SAME_ERROR_THRESHOLD
export LOG_DIR
export BUGS_FILE
export LEARNINGS_FILE
export CLAUDE_OUTPUT_FORMAT
export CLAUDE_ALLOWED_TOOLS
export CLAUDE_MODEL_IMPL
export CLAUDE_MODEL_QA
export ENABLE_QA_PHASE
export SPLIT_MODE
export LIVE_LOG_FILE
