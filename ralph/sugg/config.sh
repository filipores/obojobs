#!/bin/bash
# RALPH Sugg Mode - Configuration
# Code analysis and improvement suggestions

# ============================================
# Suggestion Configuration
# ============================================
MAX_ITERATIONS=${MAX_ITERATIONS:-10}
TIMEOUT_MINUTES=${TIMEOUT_MINUTES:-15}

# Pause between analysis loops (seconds)
SUGG_PAUSE=${SUGG_PAUSE:-3}

# ============================================
# Analysis Scope
# ============================================
# Directories to analyze (relative to project root)
ANALYZE_DIRS=${ANALYZE_DIRS:-"frontend/src backend"}
# File patterns to include
ANALYZE_PATTERNS=${ANALYZE_PATTERNS:-"*.ts,*.tsx,*.vue,*.py,*.sh"}
# Files/dirs to exclude
ANALYZE_EXCLUDE=${ANALYZE_EXCLUDE:-"node_modules,__pycache__,dist,build,.git,venv"}

# ============================================
# Deduplication
# ============================================
DEDUPE_ENABLED=${DEDUPE_ENABLED:-true}

# ============================================
# Output Configuration
# ============================================
LOG_DIR="logs"
TASKS_FILE="tasks.json"
SESSION_FILE="session.json"

# ============================================
# Claude CLI Configuration
# ============================================
CLAUDE_OUTPUT_FORMAT="json"
# Read-only tools for code analysis
CLAUDE_ALLOWED_TOOLS="Read,Glob,Grep,Bash(ls:*),Bash(find:*),Bash(wc:*)"

# ============================================
# Model Selection
# ============================================
# Sonnet for fast code analysis
CLAUDE_MODEL=${CLAUDE_MODEL:-"claude-sonnet-4-20250514"}

# ============================================
# Circuit Breaker Thresholds
# ============================================
CB_SAME_ERROR_THRESHOLD=${CB_SAME_ERROR_THRESHOLD:-3}
CB_NO_DISCOVERY_THRESHOLD=${CB_NO_DISCOVERY_THRESHOLD:-5}

# ============================================
# Colors for Terminal Output
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
ORANGE='\033[38;5;208m'
NC='\033[0m'

# Export all variables
export MAX_ITERATIONS
export TIMEOUT_MINUTES
export SUGG_PAUSE
export ANALYZE_DIRS
export ANALYZE_PATTERNS
export ANALYZE_EXCLUDE
export DEDUPE_ENABLED
export LOG_DIR
export TASKS_FILE
export SESSION_FILE
export CLAUDE_OUTPUT_FORMAT
export CLAUDE_ALLOWED_TOOLS
export CLAUDE_MODEL
export CB_SAME_ERROR_THRESHOLD
export CB_NO_DISCOVERY_THRESHOLD
