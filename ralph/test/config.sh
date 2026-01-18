#!/bin/bash
# RALPH Test Mode - Configuration
# Exploratory frontend tests with MCP Playwright

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
# testing = Test assertions (verify_element_visible, etc.)
# tracing = Trace recording for debugging
MCP_CAPABILITIES=${MCP_CAPABILITIES:-"testing"}

# ============================================
# Test Configuration
# ============================================
MAX_ITERATIONS=${MAX_ITERATIONS:-40}
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

# Split mode - tmux split screen (left Ralph, right Claude logs)
SPLIT_MODE=${SPLIT_MODE:-false}
LIVE_LOG_FILE="$LOG_DIR/claude_live.log"

# ============================================
# Claude CLI Configuration
# ============================================
CLAUDE_OUTPUT_FORMAT="json"
# Standard tools + all MCP Playwright tools (via wildcard)
# The official @playwright/mcp package is used
CLAUDE_ALLOWED_TOOLS="Write,Edit,Read,Bash,Glob,Grep,mcp__playwright__*"

# ============================================
# Test Documents (for upload in tests)
# Can be overridden via environment variables
# ============================================
TEST_DOCS_DIR="${TEST_DOCS_DIR:-$HOME/Documents/test-docs}"
TEST_CV_FILE="${TEST_CV_FILE:-$TEST_DOCS_DIR/cv.pdf}"
TEST_ZEUGNIS_FILE="${TEST_ZEUGNIS_FILE:-$TEST_DOCS_DIR/zeugnis.pdf}"

# Test User Credentials (for login)
TEST_USER_EMAIL=${TEST_USER_EMAIL:-"test@example.com"}
TEST_USER_PASSWORD=${TEST_USER_PASSWORD:-"TestPassword123!"}

# ============================================
# State Files (all in logs/ for consistency)
# ============================================
TASKS_FILE="tasks.json"
TEST_RESULTS_FILE="test_results.json"
CIRCUIT_BREAKER_FILE="logs/.circuit_breaker_state"

# ============================================
# Colors for Terminal Output
# ============================================
# Use central color definitions from lib/colors.sh
# These are loaded by ralph.sh

# Export all variables
export DEFAULT_BASE_BRANCH
export COMMIT_RANGE_BASE
export MCP_PLAYWRIGHT_SERVER
export BROWSER_TYPE
export HEADLESS
export VIEWPORT_SIZE
export MAX_ITERATIONS
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
