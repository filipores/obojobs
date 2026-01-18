#!/usr/bin/env bash
# RALPH Feature Mode - Configuration
# Adapted from ralph-claude-code

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
CB_NO_PROGRESS_THRESHOLD=3      # Open after N loops without progress
CB_SAME_ERROR_THRESHOLD=5       # Open after N loops with same error
CB_OUTPUT_DECLINE_THRESHOLD=70  # Open when output drops by >70%

# ============================================
# Exit Detection
# ============================================
MAX_CONSECUTIVE_TEST_LOOPS=3
MAX_CONSECUTIVE_DONE_SIGNALS=2
MAX_STUCK_ITERATIONS=3

# ============================================
# History Limits
# ============================================
MAX_HISTORY_ENTRIES=50          # Max entries in history files

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
# Opus for implementation and QA
CLAUDE_MODEL=${CLAUDE_MODEL:-"claude-opus-4-5-20251101"}

# ============================================
# Split Mode - tmux split screen
# ============================================
SPLIT_MODE=${SPLIT_MODE:-false}
LIVE_LOG_FILE="logs/claude_live.log"

# ============================================
# Paths (relative to SCRIPT_DIR)
# ============================================
LOG_DIR="logs"
TASKS_FILE="tasks.json"
PROMPT_FILE="prompt.md"
STATUS_FILE="logs/status.json"

# ============================================
# State Files (all in logs/ for consistency)
# ============================================
# Note: rate_limiter.sh uses logs/rate_limit.json internally
EXIT_SIGNALS_FILE="logs/.exit_signals"
CIRCUIT_BREAKER_FILE="logs/.circuit_breaker_state"
PROGRESS_FILE="logs/progress.txt"

# ============================================
# Colors for Terminal Output
# ============================================
# Colors are loaded from lib/colors.sh (via ralph.sh)

# Export all variables
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
export CLAUDE_MODEL
export SPLIT_MODE
export LIVE_LOG_FILE
export LOG_DIR
export TASKS_FILE
export PROMPT_FILE
export STATUS_FILE
export MAX_HISTORY_ENTRIES
