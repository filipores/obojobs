#!/bin/bash
# RALF Feature Mode - Konfiguration
# Angepasst von ralph-claude-code

# ============================================
# Rate Limiting
# ============================================
MAX_CALLS_PER_HOUR=${MAX_CALLS_PER_HOUR:-50}

# ============================================
# Timeout
# ============================================
TIMEOUT_MINUTES=${TIMEOUT_MINUTES:-15}

# ============================================
# Circuit Breaker Thresholds
# ============================================
CB_NO_PROGRESS_THRESHOLD=3      # Öffne nach N Loops ohne Fortschritt
CB_SAME_ERROR_THRESHOLD=5       # Öffne nach N Loops mit gleichem Fehler
CB_OUTPUT_DECLINE_THRESHOLD=70  # Öffne wenn Output um >70% sinkt

# ============================================
# Exit Detection
# ============================================
MAX_CONSECUTIVE_TEST_LOOPS=3
MAX_CONSECUTIVE_DONE_SIGNALS=2
MAX_STUCK_ITERATIONS=3

# ============================================
# Session Management
# ============================================
CLAUDE_SESSION_EXPIRY_HOURS=${CLAUDE_SESSION_EXPIRY_HOURS:-24}
CLAUDE_USE_CONTINUE=true

# ============================================
# Claude CLI Configuration
# ============================================
CLAUDE_OUTPUT_FORMAT="json"
CLAUDE_ALLOWED_TOOLS="Write,Edit,Read,Bash,Glob,Grep,WebFetch,WebSearch"
CLAUDE_MIN_VERSION="2.0.76"

# ============================================
# Model Selection
# ============================================
# Opus für Implementation und QA
CLAUDE_MODEL_IMPL=${CLAUDE_MODEL_IMPL:-"claude-opus-4-5-20251101"}

# ============================================
# Split Mode - tmux split screen
# ============================================
SPLIT_MODE=${SPLIT_MODE:-false}
LIVE_LOG_FILE="logs/claude_live.log"

# ============================================
# Pfade (relativ zu SCRIPT_DIR)
# ============================================
LOG_DIR="logs"
PRD_FILE="prd.json"
PROMPT_FILE="prompt.md"
PROGRESS_FILE="progress.txt"
STATUS_FILE="logs/status.json"

# ============================================
# State Files
# ============================================
CALL_COUNT_FILE=".call_count"
TIMESTAMP_FILE=".last_reset"
EXIT_SIGNALS_FILE=".exit_signals"
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
NC='\033[0m'

# Export alle Variablen
export MAX_CALLS_PER_HOUR
export TIMEOUT_MINUTES
export CB_NO_PROGRESS_THRESHOLD
export CB_SAME_ERROR_THRESHOLD
export MAX_CONSECUTIVE_TEST_LOOPS
export MAX_CONSECUTIVE_DONE_SIGNALS
export MAX_STUCK_ITERATIONS
export CLAUDE_SESSION_EXPIRY_HOURS
export CLAUDE_USE_CONTINUE
export CLAUDE_OUTPUT_FORMAT
export CLAUDE_ALLOWED_TOOLS
export CLAUDE_MODEL_IMPL
export SPLIT_MODE
export LIVE_LOG_FILE
export LOG_DIR
export PRD_FILE
export PROMPT_FILE
export STATUS_FILE
