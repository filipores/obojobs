#!/bin/bash
# RALF Test Mode - Konfiguration
# Explorative Frontend-Tests mit MCP Playwright

# ============================================
# Git Configuration
# ============================================
DEFAULT_BASE_BRANCH="main"
COMMIT_RANGE_BASE=${COMMIT_RANGE_BASE:-$DEFAULT_BASE_BRANCH}

# ============================================
# MCP Playwright (@playwright/mcp)
# Docs: https://github.com/microsoft/playwright-mcp
# ============================================
MCP_PLAYWRIGHT_SERVER="playwright"
BROWSER_TYPE=${BROWSER_TYPE:-"chromium"}
HEADLESS=${HEADLESS:-true}
VIEWPORT_SIZE=${VIEWPORT_SIZE:-"1280x720"}

# Capabilities: core (default), vision, pdf, testing, tracing
# testing = Test-Assertions (verify_element_visible, etc.)
# tracing = Trace-Aufzeichnung für Debugging
MCP_CAPABILITIES=${MCP_CAPABILITIES:-"testing"}

# Trace und Video für Debugging
SAVE_TRACE=${SAVE_TRACE:-false}
SAVE_VIDEO=${SAVE_VIDEO:-false}

# Timeouts (in ms)
TIMEOUT_ACTION=${TIMEOUT_ACTION:-5000}
TIMEOUT_NAVIGATION=${TIMEOUT_NAVIGATION:-60000}

# ============================================
# Test Configuration
# ============================================
MAX_TEST_ITERATIONS=${MAX_TEST_ITERATIONS:-40}
TIMEOUT_MINUTES=${TIMEOUT_MINUTES:-10}
SCREENSHOT_ON_FAILURE=${SCREENSHOT_ON_FAILURE:-true}

# ============================================
# Frontend Server
# ============================================
FRONTEND_URL=${FRONTEND_URL:-"http://localhost:3000"}
BACKEND_URL=${BACKEND_URL:-"http://localhost:5001"}
AUTO_START_SERVERS=${AUTO_START_SERVERS:-false}

# ============================================
# Circuit Breaker Thresholds
# ============================================
CB_NO_PROGRESS_THRESHOLD=3
CB_SAME_ERROR_THRESHOLD=5

# ============================================
# Output Configuration
# ============================================
REPORT_FORMAT="json"
REPORTS_DIR="reports"
LOG_DIR="logs"

# Split mode - tmux split screen (links Ralph, rechts Claude logs)
SPLIT_MODE=${SPLIT_MODE:-false}
LIVE_LOG_FILE="$LOG_DIR/claude_live.log"

# ============================================
# Claude CLI Configuration
# ============================================
CLAUDE_OUTPUT_FORMAT="json"
# Standard Tools + alle MCP Playwright Tools (via Wildcard)
# Das offizielle @playwright/mcp Paket wird verwendet
CLAUDE_ALLOWED_TOOLS="Write,Edit,Read,Bash,Glob,Grep,mcp__playwright__*"

# ============================================
# Test Documents (fuer Upload in Tests)
# ============================================
TEST_DOCS_DIR="/Users/filipores/Documents/Bewerbungsunterlagen/Batch"
TEST_CV_FILE="$TEST_DOCS_DIR/cv-ger.pdf"
TEST_ZEUGNIS_FILE="$TEST_DOCS_DIR/Filip Zeugnis.pdf"

# Test User Credentials (fuer Login)
TEST_USER_EMAIL=${TEST_USER_EMAIL:-"test@example.com"}
TEST_USER_PASSWORD=${TEST_USER_PASSWORD:-"TestPassword123!"}

# ============================================
# State Files
# ============================================
FEATURES_FILE="features.json"
TEST_RESULTS_FILE="test_results.json"
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
export DEFAULT_BASE_BRANCH
export COMMIT_RANGE_BASE
export MCP_PLAYWRIGHT_SERVER
export BROWSER_TYPE
export HEADLESS
export VIEWPORT_WIDTH
export VIEWPORT_HEIGHT
export MAX_TEST_ITERATIONS
export TIMEOUT_MINUTES
export SCREENSHOT_ON_FAILURE
export FRONTEND_URL
export BACKEND_URL
export AUTO_START_SERVERS
export CB_NO_PROGRESS_THRESHOLD
export CB_SAME_ERROR_THRESHOLD
export REPORT_FORMAT
export REPORTS_DIR
export LOG_DIR
export CLAUDE_OUTPUT_FORMAT
export CLAUDE_ALLOWED_TOOLS
export SPLIT_MODE
export LIVE_LOG_FILE
