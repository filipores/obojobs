#!/usr/bin/env bash
set -e

# ============================================
# Initialisierung
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# MacOS timeout compatibility
if command -v gtimeout &>/dev/null; then
    TIMEOUT_CMD="gtimeout"
elif command -v timeout &>/dev/null; then
    TIMEOUT_CMD="timeout"
else
    # Fallback: run without timeout on MacOS
    TIMEOUT_CMD=""
fi

# Source configuration
source "$SCRIPT_DIR/config.sh"

# Source shared libraries (from parent lib/)
SHARED_LIB="$SCRIPT_DIR/../lib"
source "$SHARED_LIB/colors.sh"
source "$SHARED_LIB/date_utils.sh"
source "$SHARED_LIB/file_lock.sh"
source "$SHARED_LIB/logger.sh"
source "$SHARED_LIB/circuit_breaker.sh"
source "$SHARED_LIB/context_builder.sh"

# Source mode-specific libraries
source "$SCRIPT_DIR/lib/rate_limiter.sh"
source "$SCRIPT_DIR/lib/response_analyzer.sh"

# Override LOG_DIR to be absolute path
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Session tracking
RALPH_STARTED_AT=$(get_iso_timestamp)
export RALPH_STARTED_AT

# ============================================
# Help Function
# ============================================
show_help() {
    cat << EOF
RALF Feature Mode - PRD-basierte Feature-Entwicklung

Usage: ./ralph.sh [OPTIONS]

Optionen:
    -h, --help              Zeige diese Hilfe
    -c, --calls NUM         Max API-Calls pro Stunde (default: $MAX_CALLS_PER_HOUR)
    -t, --timeout MIN       Claude Timeout in Minuten (default: $TIMEOUT_MINUTES)
    --status                Zeige aktuellen Status
    --reset-circuit         Reset Circuit Breaker
    --circuit-status        Zeige Circuit Breaker Status

EOF
}

# ============================================
# Helper: Validate numeric argument
# ============================================
validate_numeric_arg() {
    local value="$1"
    local arg_name="$2"
    if ! [[ "$value" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Error: $arg_name requires a positive integer, got: '$value'${NC}"
        exit 1
    fi
    if [[ "$value" -le 0 ]]; then
        echo -e "${RED}Error: $arg_name must be greater than 0${NC}"
        exit 1
    fi
}

# ============================================
# Command Line Arguments
# ============================================
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--calls)
            if [[ -z "$2" || "$2" == -* ]]; then
                echo -e "${RED}Error: --calls requires a value${NC}"
                exit 1
            fi
            validate_numeric_arg "$2" "--calls"
            MAX_CALLS_PER_HOUR="$2"
            shift 2
            ;;
        -t|--timeout)
            if [[ -z "$2" || "$2" == -* ]]; then
                echo -e "${RED}Error: --timeout requires a value${NC}"
                exit 1
            fi
            validate_numeric_arg "$2" "--timeout"
            TIMEOUT_MINUTES="$2"
            shift 2
            ;;
        --status)
            if [[ -f "$LOG_DIR/status.json" ]]; then
                cat "$LOG_DIR/status.json" | jq .
            else
                echo "Kein Status gefunden. RALF läuft nicht."
            fi
            exit 0
            ;;
        --reset-circuit)
            reset_circuit_breaker "Manual reset via CLI"
            exit 0
            ;;
        --circuit-status)
            show_circuit_status
            exit 0
            ;;
        *)
            echo "Unbekannte Option: $1"
            show_help
            exit 1
            ;;
    esac
done

# ============================================
# Validation
# ============================================
cd "$PROJECT_ROOT"

# Check if tasks.json exists
if [[ ! -f "$SCRIPT_DIR/tasks.json" ]]; then
    log_error "Keine tasks.json gefunden in $SCRIPT_DIR"
    echo "Erstelle zuerst eine PRD mit dem Plan-RALF oder manuell."
    exit 1
fi

# Check if prompt.md exists
if [[ ! -f "$SCRIPT_DIR/prompt.md" ]]; then
    log_error "Keine prompt.md gefunden in $SCRIPT_DIR"
    exit 1
fi

# ============================================
# PRD Info (mit Fehlerbehandlung)
# ============================================
if ! jq -e '.' "$SCRIPT_DIR/tasks.json" > /dev/null 2>&1; then
    log_error "tasks.json ist kein gültiges JSON"
    exit 1
fi

PRD_BRANCH=$(jq -r '.branchName // "main"' "$SCRIPT_DIR/tasks.json") || {
    log_error "Konnte branchName nicht aus tasks.json lesen"
    PRD_BRANCH="main"
}
PRD_DESC=$(jq -r '.description // "No description"' "$SCRIPT_DIR/tasks.json") || {
    log_error "Konnte description nicht aus tasks.json lesen"
    PRD_DESC="No description"
}
TOTAL_STORIES=$(jq '.userStories | length' "$SCRIPT_DIR/tasks.json") || {
    log_error "Konnte userStories nicht aus tasks.json lesen"
    exit 1
}
PASSED_STORIES=$(jq '[.userStories[] | select(.passes == true)] | length' "$SCRIPT_DIR/tasks.json") || {
    PASSED_STORIES=0
}

# ============================================
# Header
# ============================================
echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}       RALF Feature Mode${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "PRD:           ${BLUE}$PRD_DESC${NC}"
echo -e "Branch:        ${BLUE}$PRD_BRANCH${NC}"
echo -e "Stories:       ${BLUE}$PASSED_STORIES/$TOTAL_STORIES passed${NC}"
echo -e "Rate Limit:    ${BLUE}$MAX_CALLS_PER_HOUR calls/hour${NC}"
echo -e "Timeout:       ${BLUE}$TIMEOUT_MINUTES minutes${NC}"
if [[ "$RALPH_IN_SPLIT_MODE" == "true" ]]; then
    echo -e "Split-Mode:    ${PURPLE}AKTIV - Claude Output im rechten Pane${NC}"
fi
echo ""
echo -e "${GREEN}==========================================${NC}"
echo ""

# ============================================
# Branch Setup
# ============================================
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "$PRD_BRANCH" ]]; then
    log_info "Wechsle zu Branch: $PRD_BRANCH"
    git checkout -B "$PRD_BRANCH" 2>/dev/null || git checkout "$PRD_BRANCH"
fi

# ============================================
# Initialize Tracking
# ============================================
init_rate_limiter
init_circuit_breaker

# ============================================
# Get Current Story
# ============================================
get_current_story() {
    # Find first story with passes: false, ordered by priority
    jq -r '.userStories | sort_by(.priority) | map(select(.passes == false)) | .[0].id // "NONE"' "$SCRIPT_DIR/tasks.json"
}

# ============================================
# Execute Claude - Helper Functions
# ============================================

# Build context string for Claude
build_claude_context() {
    local loop_count=$1
    local current_story=$2

    local relevant_files=$(get_story_context "$current_story")
    local file_context=$(build_context_string "$relevant_files")

    echo "Loop #${loop_count}. Current Story: ${current_story}. Stories remaining: $((TOTAL_STORIES - PASSED_STORIES)).
${file_context}"
}

# Run Claude in split mode (tmux)
run_claude_split_mode() {
    local context="$1"
    local output_file="$2"
    local timeout_prefix="$3"
    local loop_count="$4"
    local current_story="$5"

    # Write header to live log
    {
        echo ""
        echo "═══════════════════════════════════════"
        echo " Story: $current_story | Loop #$loop_count"
        echo " $(date '+%H:%M:%S')"
        echo "═══════════════════════════════════════"
        echo ""
    } >> "$RALPH_LIVE_LOG"

    local result=0
    if $timeout_prefix claude \
        --model "$CLAUDE_MODEL" \
        --output-format stream-json --verbose \
        --allowedTools "$CLAUDE_ALLOWED_TOOLS" \
        --append-system-prompt "$context" \
        -p "$(cat "$SCRIPT_DIR/prompt.md")" \
        2>&1 | tee -a "$RALPH_LIVE_LOG" > "$output_file"; then
        result=0
    else
        result=$?
    fi

    echo "" >> "$RALPH_LIVE_LOG"
    echo "─────────────────────────────────────────" >> "$RALPH_LIVE_LOG"

    return $result
}

# Run Claude in normal mode
run_claude_normal_mode() {
    local context="$1"
    local output_file="$2"
    local timeout_prefix="$3"

    if $timeout_prefix claude \
        --model "$CLAUDE_MODEL" \
        --output-format json \
        --allowedTools "$CLAUDE_ALLOWED_TOOLS" \
        --append-system-prompt "$context" \
        -p "$(cat "$SCRIPT_DIR/prompt.md")" \
        > "$output_file" 2>&1; then
        return 0
    else
        return $?
    fi
}

# Handle successful Claude result
handle_claude_success() {
    local output_file="$1"
    local loop_count="$2"
    local current_story="$3"

    log_success "Claude Code Ausführung abgeschlossen"

    # Analyze response
    analyze_response "$output_file" "$loop_count"
    update_exit_signals
    log_analysis_summary

    # Get file changes for circuit breaker
    local files_changed=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')

    # Extract error if any
    local error_message=""
    if grep -qE '(^Error:|^ERROR:|Exception|Fatal)' "$output_file" 2>/dev/null; then
        error_message=$(grep -E '(^Error:|^ERROR:|Exception|Fatal)' "$output_file" | head -1)
    fi

    # Record in circuit breaker
    check_stuck_pattern "$loop_count" "$current_story" "$error_message" "$files_changed"
    return $?
}

# Handle failed Claude result
handle_claude_failure() {
    local exec_result="$1"
    local output_file="$2"

    if [[ $exec_result -eq 124 ]]; then
        log_error "Timeout nach $TIMEOUT_MINUTES Minuten!"
        return 2  # Timeout
    fi

    if detect_api_limit "$output_file"; then
        return 4  # API limit
    fi

    log_error "Claude Code Ausführung fehlgeschlagen"
    return 1  # Error
}

# ============================================
# Execute Claude (Main Function)
# ============================================
execute_claude() {
    local loop_count=$1
    local current_story=$2

    local timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local output_file="$LOG_DIR/claude_output_${timestamp}.log"

    log_loop "Starte Claude Code Ausführung (${CLAUDE_MODEL##*-})..."

    # Build context
    local context=$(build_claude_context "$loop_count" "$current_story")

    # Build timeout command prefix
    local timeout_prefix=""
    local timeout_seconds=$((TIMEOUT_MINUTES * 60))
    if [[ -n "$TIMEOUT_CMD" ]]; then
        timeout_prefix="$TIMEOUT_CMD ${timeout_seconds}s"
    fi

    # Execute based on mode
    local exec_result=0
    if [[ "$RALPH_IN_SPLIT_MODE" == "true" && -n "$RALPH_LIVE_LOG" ]]; then
        run_claude_split_mode "$context" "$output_file" "$timeout_prefix" "$loop_count" "$current_story"
        exec_result=$?
    else
        run_claude_normal_mode "$context" "$output_file" "$timeout_prefix"
        exec_result=$?
    fi

    # Handle result
    if [[ $exec_result -eq 0 ]]; then
        handle_claude_success "$output_file" "$loop_count" "$current_story"
        local success_result=$?
        if [[ $success_result -ne 0 ]]; then
            return 3  # Circuit breaker opened
        fi
        return 0
    else
        handle_claude_failure "$exec_result" "$output_file"
        return $?
    fi
}

# ============================================
# Main Loop
# ============================================
loop_count=0

# Cleanup on interrupt
cleanup() {
    log_info "RALF unterbrochen. Cleanup..."
    update_status "$loop_count" "$(get_remaining_calls)" "" "interrupted"
    exit 0
}
trap cleanup SIGINT SIGTERM

log_success "Starte RALF Feature Mode Loop..."

while true; do
    loop_count=$((loop_count + 1))

    # Get current story
    current_story=$(get_current_story)

    if [[ "$current_story" == "NONE" ]]; then
        log_success "Alle Stories abgeschlossen!"
        update_status "$loop_count" "$(get_remaining_calls)" "" "complete"
        break
    fi

    log_loop "=== Loop #$loop_count - Story: $current_story ==="

    # Check circuit breaker
    if should_halt_execution; then
        update_status "$loop_count" "$(get_remaining_calls)" "$current_story" "circuit_open"
        break
    fi

    # Check rate limit
    if ! check_rate_limit; then
        wait_for_reset
        continue
    fi

    # Check graceful exit
    exit_reason=$(should_exit_gracefully)
    if [[ -n "$exit_reason" ]]; then
        log_success "Graceful Exit: $exit_reason"
        update_status "$loop_count" "$(get_remaining_calls)" "$current_story" "complete" "$exit_reason"
        break
    fi

    # Update status
    update_status "$loop_count" "$(get_remaining_calls)" "$current_story" "running"

    # Increment call counter
    increment_call_count

    # Execute Claude
    execute_claude "$loop_count" "$current_story"
    exec_result=$?

    case $exec_result in
        0)
            # Success
            PASSED_STORIES=$(jq '[.userStories[] | select(.passes == true)] | length' "$SCRIPT_DIR/tasks.json")
            log_info "Stories passed: $PASSED_STORIES/$TOTAL_STORIES"
            update_status "$loop_count" "$(get_remaining_calls)" "$current_story" "success"
            sleep 5
            ;;
        2)
            # Timeout
            log_error "Timeout - warte 30 Sekunden vor Retry..."
            update_status "$loop_count" "$(get_remaining_calls)" "$current_story" "timeout"
            sleep 30
            ;;
        3)
            # Circuit breaker opened
            log_error "Circuit Breaker geöffnet - stoppe Loop"
            update_status "$loop_count" "$(get_remaining_calls)" "$current_story" "circuit_open"
            break
            ;;
        4)
            # API limit
            log_warn "API 5-Stunden-Limit erreicht"
            update_status "$loop_count" "$(get_remaining_calls)" "$current_story" "api_limit"

            echo ""
            echo "Optionen:"
            echo "  1) 60 Minuten warten und fortsetzen"
            echo "  2) Abbrechen"
            echo ""
            read -t 30 -p "Wahl (1/2): " choice

            if [[ "$choice" == "1" ]]; then
                log_info "Warte 60 Minuten..."
                sleep 3600
            else
                break
            fi
            ;;
        *)
            # Other error
            log_error "Fehler - warte 30 Sekunden vor Retry..."
            update_status "$loop_count" "$(get_remaining_calls)" "$current_story" "error"
            sleep 30
            ;;
    esac

    log_loop "=== Loop #$loop_count abgeschlossen ==="
    echo ""
done

# ============================================
# Final Summary
# ============================================
echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}       RALF Feature Mode beendet${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "Total Loops:   ${BLUE}$loop_count${NC}"
echo -e "Stories:       ${BLUE}$PASSED_STORIES/$TOTAL_STORIES passed${NC}"
echo -e "Logs:          ${BLUE}$LOG_DIR/${NC}"
echo ""
