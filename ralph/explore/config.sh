#!/bin/bash
# RALPH Explore Mode - Configuration
# Autonomous exploratory tests with MCP Playwright

# ============================================
# Exploration Configuration
# ============================================
# No max iterations - runs until manually interrupted
# But we set a very high default as safety
MAX_ITERATIONS=${MAX_ITERATIONS:-999999}
TIMEOUT_MINUTES=${TIMEOUT_MINUTES:-15}

# Pause between explorations (seconds)
EXPLORE_PAUSE=${EXPLORE_PAUSE:-5}

# ============================================
# Server URLs
# ============================================
FRONTEND_URL=${FRONTEND_URL:-"http://localhost:3000"}
BACKEND_URL=${BACKEND_URL:-"http://localhost:5001"}
AUTO_START_SERVERS=${AUTO_START_SERVERS:-false}

# ============================================
# Test User Credentials (for auth tests)
# ============================================
TEST_USER_EMAIL=${TEST_USER_EMAIL:-"test@example.com"}
TEST_USER_PASSWORD=${TEST_USER_PASSWORD:-"Test1234!"}

# ============================================
# Deduplication
# ============================================
# Ignore bugs/suggestions that already exist
DEDUPE_ENABLED=${DEDUPE_ENABLED:-true}

# ============================================
# Output Configuration
# ============================================
LOG_DIR="logs"
TASKS_FILE="tasks.json"
SUGG_FILE="sugg.json"
SESSION_FILE="session.json"

# ============================================
# Claude CLI Configuration
# ============================================
CLAUDE_OUTPUT_FORMAT="json"
# All tools for fullstack exploration
CLAUDE_ALLOWED_TOOLS="Write,Edit,Read,Bash,Glob,Grep,mcp__playwright__*"

# ============================================
# Model Selection
# ============================================
# Sonnet for exploration (fast, cost-effective)
CLAUDE_MODEL=${CLAUDE_MODEL:-"claude-sonnet-4-20250514"}

# ============================================
# Circuit Breaker Thresholds
# ============================================
# After how many same errors to stop
CB_SAME_ERROR_THRESHOLD=${CB_SAME_ERROR_THRESHOLD:-5}
# After how many loops without new discovery to warn
CB_NO_DISCOVERY_THRESHOLD=${CB_NO_DISCOVERY_THRESHOLD:-10}

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
export EXPLORE_PAUSE
export FRONTEND_URL
export BACKEND_URL
export AUTO_START_SERVERS
export TEST_USER_EMAIL
export TEST_USER_PASSWORD
export DEDUPE_ENABLED
export LOG_DIR
export TASKS_FILE
export SUGG_FILE
export SESSION_FILE
export CLAUDE_OUTPUT_FORMAT
export CLAUDE_ALLOWED_TOOLS
export CLAUDE_MODEL
export CB_SAME_ERROR_THRESHOLD
export CB_NO_DISCOVERY_THRESHOLD
