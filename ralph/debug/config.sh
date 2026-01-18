#!/bin/bash
# RALPH Debug Mode - Configuration
# Bug-based debugging analogous to Feature Ralph

# ============================================
# Bug Processing
# ============================================
MAX_ITERATIONS=${MAX_ITERATIONS:-3}
TIMEOUT_MINUTES=${TIMEOUT_MINUTES:-15}


# ============================================
# Split Mode - tmux split screen
# ============================================
SPLIT_MODE=${SPLIT_MODE:-false}
LIVE_LOG_FILE="logs/claude_live.log"

# ============================================
# Output Configuration
# ============================================
LOG_DIR="logs"
TASKS_FILE="tasks.json"

# ============================================
# Claude CLI Configuration
# ============================================
CLAUDE_ALLOWED_TOOLS="Write,Edit,Read,Bash,Glob,Grep"

# ============================================
# Model Selection
# ============================================
# Sonnet for bug fixes (fast, cheap)
CLAUDE_MODEL=${CLAUDE_MODEL:-"claude-sonnet-4-20250514"}
# Opus as fallback for difficult bugs (after FALLBACK_THRESHOLD failed attempts)
CLAUDE_MODEL_FALLBACK=${CLAUDE_MODEL_FALLBACK:-"claude-opus-4-5-20251101"}
# After how many failed attempts to switch to Opus
FALLBACK_THRESHOLD=${FALLBACK_THRESHOLD:-2}

# ============================================
# Over-Engineering Check
# ============================================
# If Sonnet fix changes more than X lines, perform Opus review
OVERENGINEERING_THRESHOLD=${OVERENGINEERING_THRESHOLD:-100}
# Enable/Disable the over-engineering check
OVERENGINEERING_CHECK_ENABLED=${OVERENGINEERING_CHECK_ENABLED:-true}

# ============================================
# Circuit Breaker Thresholds
# ============================================
CB_NO_PROGRESS_THRESHOLD=${CB_NO_PROGRESS_THRESHOLD:-3}
CB_SAME_ERROR_THRESHOLD=${CB_SAME_ERROR_THRESHOLD:-5}

# Colors are loaded via lib/colors.sh (via logger.sh)

# Export used variables
export MAX_ITERATIONS
export TIMEOUT_MINUTES
export LOG_DIR
export TASKS_FILE
export CLAUDE_ALLOWED_TOOLS
export CLAUDE_MODEL
export CLAUDE_MODEL_FALLBACK
export FALLBACK_THRESHOLD
export OVERENGINEERING_THRESHOLD
export OVERENGINEERING_CHECK_ENABLED
export SPLIT_MODE
export LIVE_LOG_FILE
export CB_NO_PROGRESS_THRESHOLD
export CB_SAME_ERROR_THRESHOLD
