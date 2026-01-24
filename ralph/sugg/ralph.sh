#!/bin/bash
# RALPH Sugg Mode - Code Analysis and Improvement Suggestions
# Runs until max iterations or manually interrupted (Ctrl+C)

set -e

# ============================================
# Initialization
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# MacOS timeout compatibility
if command -v gtimeout &>/dev/null; then
    TIMEOUT_CMD="gtimeout"
elif command -v timeout &>/dev/null; then
    TIMEOUT_CMD="timeout"
else
    TIMEOUT_CMD=""
fi

# Source configuration
source "$SCRIPT_DIR/config.sh"

# Source shared libraries (from parent lib/)
SHARED_LIB="$SCRIPT_DIR/../lib"
source "$SHARED_LIB/date_utils.sh"
source "$SHARED_LIB/logger.sh"

# Override paths to be absolute
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
RALPH Sugg Mode - Code Analysis and Improvement Suggestions

Usage: ./ralph.sh [OPTIONS]

Options:
    -h, --help      Show this help
    --status        Show current analysis status
    --reset         Reset session and start fresh
    --summary       Show summary of all suggestions

Examples:
    ./ralph.sh              # Start analysis (runs up to $MAX_ITERATIONS iterations)
    ./ralph.sh --status     # Show status
    ./ralph.sh --summary    # Show suggestions summary

Note: Press Ctrl+C to stop early. Suggestions are saved automatically.

EOF
}

# ============================================
# Session Management
# ============================================
init_session() {
    local session_file="$SCRIPT_DIR/session.json"

    if [[ ! -f "$session_file" ]]; then
        cat > "$session_file" << 'EOF'
{
  "started_at": null,
  "last_updated": null,
  "analyzed_files": [],
  "covered_areas": [],
  "known_sugg_ids": [],
  "analysis_stats": {
    "total_loops": 0,
    "total_files_analyzed": 0
  }
}
EOF
    fi

    # Update session with start time
    local tmp_file="$session_file.tmp"
    jq --arg started "$(get_iso_timestamp)" '
        .started_at = (if .started_at == null then $started else .started_at end)
    ' "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"

    # Sync known IDs from tasks.json
    sync_known_ids

    log_info "Session initialized"
}

sync_known_ids() {
    local session_file="$SCRIPT_DIR/session.json"
    local tasks_file="$SCRIPT_DIR/tasks.json"

    local sugg_ids="[]"
    if [[ -f "$tasks_file" ]]; then
        sugg_ids=$(jq '[.suggestions[].id]' "$tasks_file" 2>/dev/null || echo "[]")
    fi

    local tmp_file="$session_file.tmp"
    jq --argjson sugg "$sugg_ids" '.known_sugg_ids = $sugg' "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"
}

save_session() {
    local session_file="$SCRIPT_DIR/session.json"
    local tmp_file="$session_file.tmp"

    jq --arg updated "$(get_iso_timestamp)" '.last_updated = $updated' "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"

    log_info "Session saved"
}

reset_session() {
    rm -f "$SCRIPT_DIR/session.json"
    rm -f "$SCRIPT_DIR/tasks.json"
    rm -f "$LOG_DIR"/*.log
    rm -f "$LOG_DIR"/*.json

    # Recreate tasks.json
    cat > "$SCRIPT_DIR/tasks.json" << 'EOF'
{
  "project": "obojobs",
  "mode": "sugg",
  "description": "Code improvement suggestions from RALPH Sugg Mode",
  "suggestions": []
}
EOF

    log_info "Session reset"
}

get_session_context() {
    local session_file="$SCRIPT_DIR/session.json"

    if [[ ! -f "$session_file" ]]; then
        echo "No session"
        return
    fi

    local files_count=$(jq '.analyzed_files | length' "$session_file" 2>/dev/null || echo "0")
    local known_sugg=$(jq '.known_sugg_ids | length' "$session_file" 2>/dev/null || echo "0")
    local areas=$(jq -r '.covered_areas | join(", ")' "$session_file" 2>/dev/null || echo "none")
    local sugg_ids=$(jq -r '.known_sugg_ids | join(", ")' "$session_file" 2>/dev/null || echo "none")

    echo "Files analyzed: $files_count. Known suggestions: $known_sugg (IDs: $sugg_ids). Areas covered: $areas"
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
        --status)
            show_sugg_status
            exit 0
            ;;
        --reset)
            log_info "Resetting session..."
            reset_session
            log_success "Reset complete"
            exit 0
            ;;
        --summary)
            show_sugg_summary
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# ============================================
# Pre-flight Checks
# ============================================
cd "$PROJECT_ROOT"

check_claude() {
    log_info "Checking Claude CLI..."

    if ! command -v claude &>/dev/null; then
        log_error "Claude CLI not found"
        exit 1
    fi

    log_success "Claude CLI available"
}

# ============================================
# Execute Analysis
# ============================================
execute_analysis() {
    local loop_count=$1

    local timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local output_file="$LOG_DIR/sugg_output_${timestamp}.log"

    log_loop "Starting analysis #$loop_count"

    local timeout_seconds=$((TIMEOUT_MINUTES * 60))

    # Build session context for Claude
    local session_context=$(get_session_context)
    local context="RALPH Sugg Mode - Loop #${loop_count}. Analyze: ${ANALYZE_DIRS}. Exclude: ${ANALYZE_EXCLUDE}.
Session Info: ${session_context}"

    # Build timeout prefix
    local timeout_prefix=""
    if [[ -n "$TIMEOUT_CMD" ]]; then
        timeout_prefix="$TIMEOUT_CMD ${timeout_seconds}s"
    fi

    # Execute Claude
    local exec_result=0

    if $timeout_prefix claude \
        --model "$CLAUDE_MODEL" \
        --output-format json \
        --allowedTools "$CLAUDE_ALLOWED_TOOLS" \
        --append-system-prompt "$context" \
        -p "$(cat "$SCRIPT_DIR/prompt.md")" \
        > "$output_file" 2>&1; then
        exec_result=0
    else
        exec_result=$?
    fi

    if [[ $exec_result -eq 0 ]]; then
        log_success "Analysis complete"
        parse_sugg_result "$output_file"
        return 0
    else
        if [[ $exec_result -eq 124 ]]; then
            log_error "Timeout after $TIMEOUT_MINUTES minutes"
            return 2
        fi
        log_error "Analysis failed"
        return 1
    fi
}

# ============================================
# Result Parsing
# ============================================
parse_sugg_result() {
    local output_file=$1

    if [[ ! -f "$output_file" ]]; then
        log_warn "Output file not found: $output_file"
        return 1
    fi

    local raw_result=""

    if jq -e '.result' "$output_file" >/dev/null 2>&1; then
        raw_result=$(jq -r '.result' "$output_file" 2>/dev/null)
    else
        raw_result=$(cat "$output_file")
    fi

    local result_json=""
    if echo "$raw_result" | grep -q "RALPH_SUGG_RESULT"; then
        result_json=$(echo "$raw_result" | \
            sed -n '/---RALPH_SUGG_RESULT---/,/---END_RALPH_SUGG_RESULT---/p' | \
            grep -v "RALPH_SUGG_RESULT" | \
            grep -v '```' | \
            tr -d '\r')
    fi

    if [[ -z "$result_json" ]]; then
        log_warn "No RALPH_SUGG_RESULT block found"
        return 1
    fi

    if ! echo "$result_json" | jq empty 2>/dev/null; then
        log_warn "Invalid JSON in result block"
        return 1
    fi

    # Process new suggestions
    local new_sugg=$(echo "$result_json" | jq '.new_suggestions // []')
    if [[ "$new_sugg" != "[]" && "$new_sugg" != "null" ]]; then
        process_new_suggestions "$new_sugg"
    fi

    # Update analyzed files
    local files=$(echo "$result_json" | jq '.files_analyzed // []')
    if [[ "$files" != "[]" && "$files" != "null" ]]; then
        update_analyzed_files "$files"
    fi

    # Update covered areas
    local areas=$(echo "$result_json" | jq '.areas_covered // []')
    if [[ "$areas" != "[]" && "$areas" != "null" ]]; then
        update_covered_areas "$areas"
    fi

    return 0
}

process_new_suggestions() {
    local sugg_json=$1
    local tasks_file="$SCRIPT_DIR/tasks.json"
    local session_file="$SCRIPT_DIR/session.json"

    local known_ids=$(jq -r '.known_sugg_ids[]' "$session_file" 2>/dev/null)

    echo "$sugg_json" | jq -c '.[]' | while read -r sugg; do
        local sugg_id=$(echo "$sugg" | jq -r '.id')

        if [[ "$DEDUPE_ENABLED" == "true" ]] && echo "$known_ids" | grep -q "^$sugg_id$"; then
            log_info "Suggestion $sugg_id already known - skipped"
            continue
        fi

        if [[ -z "$sugg_id" || "$sugg_id" == "null" ]]; then
            local max_num=$(jq '[.suggestions[].id | select(. != null) | capture("SUGG-(?<n>[0-9]+)") | .n | tonumber] | max // 0' "$tasks_file" 2>/dev/null || echo "0")
            sugg_id="SUGG-$(printf '%03d' $((max_num + 1)))"
            sugg=$(echo "$sugg" | jq --arg id "$sugg_id" '.id = $id')
        fi

        sugg=$(echo "$sugg" | jq --arg ts "$(get_iso_timestamp)" '
            .found_at = $ts |
            .source = "sugg-ralph" |
            .implemented = false
        ')

        local tmp_file="$tasks_file.tmp"
        jq --argjson sugg "$sugg" '.suggestions += [$sugg]' "$tasks_file" > "$tmp_file" && mv "$tmp_file" "$tasks_file"

        tmp_file="$session_file.tmp"
        jq --arg id "$sugg_id" '.known_sugg_ids += [$id] | .known_sugg_ids = (.known_sugg_ids | unique)' \
            "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"

        log_success "Suggestion $sugg_id added"
    done
}

update_analyzed_files() {
    local files_json=$1
    local session_file="$SCRIPT_DIR/session.json"

    local tmp_file="$session_file.tmp"
    jq --argjson files "$files_json" '
        .analyzed_files = (.analyzed_files + $files | unique) |
        .analysis_stats.total_files_analyzed = (.analyzed_files | length)
    ' "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"
}

update_covered_areas() {
    local areas_json=$1
    local session_file="$SCRIPT_DIR/session.json"

    local tmp_file="$session_file.tmp"
    jq --argjson areas "$areas_json" '
        .covered_areas = (.covered_areas + $areas | unique)
    ' "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"
}

# ============================================
# Status & Summary
# ============================================
update_sugg_status() {
    local loop_count=$1
    local status=$2

    local sugg_count=$(jq '.suggestions | length' "$SCRIPT_DIR/tasks.json" 2>/dev/null || echo "0")
    local files_count=$(jq '.analyzed_files | length' "$SCRIPT_DIR/session.json" 2>/dev/null || echo "0")

    local extras=$(jq -n \
        --argjson suggestions_found "$sugg_count" \
        --argjson files_analyzed "$files_count" \
        '{
            suggestions_found: $suggestions_found,
            files_analyzed: $files_analyzed
        }')

    write_status_json "sugg" "$status" "$loop_count" "Analysis" "$loop_count" "$MAX_ITERATIONS" "$extras"
}

show_sugg_status() {
    local session_file="$SCRIPT_DIR/session.json"
    local tasks_file="$SCRIPT_DIR/tasks.json"
    local status_file="$LOG_DIR/status.json"

    echo -e "${ORANGE}=== RALPH Sugg Status ===${NC}"
    echo ""

    if [[ -f "$status_file" ]]; then
        local status=$(jq -r '.status' "$status_file" 2>/dev/null || echo "unknown")
        local loop=$(jq -r '.loop' "$status_file" 2>/dev/null || echo "0")
        local started=$(jq -r '.started_at' "$status_file" 2>/dev/null || echo "unknown")

        echo -e "Status:        ${BLUE}$status${NC}"
        echo -e "Loop:          ${BLUE}$loop / $MAX_ITERATIONS${NC}"
        echo -e "Started:       ${BLUE}$started${NC}"
    else
        echo -e "Status:        ${YELLOW}Not started${NC}"
    fi

    echo ""

    if [[ -f "$tasks_file" ]]; then
        local sugg_total=$(jq '.suggestions | length' "$tasks_file" 2>/dev/null || echo "0")
        local sugg_high=$(jq '[.suggestions[] | select(.priority == "high")] | length' "$tasks_file" 2>/dev/null || echo "0")
        local sugg_medium=$(jq '[.suggestions[] | select(.priority == "medium")] | length' "$tasks_file" 2>/dev/null || echo "0")

        echo -e "${CYAN}Suggestions:${NC}"
        echo -e "  Total:       ${BLUE}$sugg_total${NC}"
        echo -e "  High Prio:   ${RED}$sugg_high${NC}"
        echo -e "  Medium Prio: ${YELLOW}$sugg_medium${NC}"
    fi

    echo ""

    if [[ -f "$session_file" ]]; then
        local files=$(jq '.analyzed_files | length' "$session_file" 2>/dev/null || echo "0")
        local areas=$(jq -r '.covered_areas | join(", ")' "$session_file" 2>/dev/null || echo "none")

        echo -e "${PURPLE}Analysis:${NC}"
        echo -e "  Files:       ${BLUE}$files${NC}"
        echo -e "  Areas:       ${BLUE}$areas${NC}"
    fi

    echo ""
}

show_sugg_summary() {
    local tasks_file="$SCRIPT_DIR/tasks.json"

    echo ""
    echo -e "${ORANGE}=== Suggestions Summary ===${NC}"
    echo ""

    if [[ -f "$tasks_file" ]]; then
        local sugg_total=$(jq '.suggestions | length' "$tasks_file" 2>/dev/null || echo "0")

        if [[ $sugg_total -gt 0 ]]; then
            echo -e "${CYAN}Suggestions ($sugg_total):${NC}"
            jq -r '.suggestions[] | "  [\(.priority)] \(.id): \(.title) [\(.type)]"' "$tasks_file" 2>/dev/null
            echo ""

            echo -e "${YELLOW}By type:${NC}"
            jq -r '[.suggestions[].type] | group_by(.) | map({type: .[0], count: length}) | .[] | "  \(.type): \(.count)"' "$tasks_file" 2>/dev/null
            echo ""
        else
            echo -e "${GREEN}No suggestions found yet${NC}"
            echo ""
        fi
    fi

    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "  1. Review suggestions: ${BLUE}cat $tasks_file | jq '.suggestions[]'${NC}"
    echo -e "  2. Implement high-priority: ${BLUE}jq '.suggestions[] | select(.priority == \"high\")' $tasks_file${NC}"
    echo ""
}

# ============================================
# Main Loop
# ============================================

# Pre-flight checks
check_claude
init_session

# Header
echo ""
echo -e "${ORANGE}==========================================${NC}"
echo -e "${ORANGE}       RALPH Sugg Mode${NC}"
echo -e "${ORANGE}==========================================${NC}"
echo ""

sugg_count=$(jq '.suggestions | length' "$SCRIPT_DIR/tasks.json" 2>/dev/null || echo "0")

echo -e "Analyze:       ${BLUE}$ANALYZE_DIRS${NC}"
echo -e "Exclude:       ${BLUE}$ANALYZE_EXCLUDE${NC}"
echo -e "Suggestions:   ${BLUE}$sugg_count${NC}"
echo -e "Max loops:     ${BLUE}$MAX_ITERATIONS${NC}"
echo -e "Timeout:       ${BLUE}$TIMEOUT_MINUTES min${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop early${NC}"
echo ""
echo -e "${ORANGE}==========================================${NC}"
echo ""

# Cleanup on interrupt
cleanup() {
    echo ""
    log_info "RALPH Sugg interrupted. Saving session..."
    save_session
    show_sugg_summary
    exit 0
}
trap cleanup SIGINT SIGTERM

# Main analysis loop
loop_count=0
no_discovery_count=0

while [[ $loop_count -lt $MAX_ITERATIONS ]]; do
    loop_count=$((loop_count + 1))

    log_loop "=== Analysis #$loop_count / $MAX_ITERATIONS ==="

    update_sugg_status "$loop_count" "analyzing"

    sugg_before=$(jq '.suggestions | length' "$SCRIPT_DIR/tasks.json" 2>/dev/null || echo "0")

    execute_analysis "$loop_count"
    exec_result=$?

    sugg_after=$(jq '.suggestions | length' "$SCRIPT_DIR/tasks.json" 2>/dev/null || echo "0")
    new_sugg=$((sugg_after - sugg_before))

    case $exec_result in
        0)
            update_sugg_status "$loop_count" "success"

            if [[ $new_sugg -gt 0 ]]; then
                log_success "New suggestions: $new_sugg"
                no_discovery_count=0
            else
                no_discovery_count=$((no_discovery_count + 1))
                log_info "No new suggestions this iteration"

                if [[ $no_discovery_count -ge $CB_NO_DISCOVERY_THRESHOLD ]]; then
                    log_warn "$CB_NO_DISCOVERY_THRESHOLD iterations without new suggestions"
                    log_info "Codebase may be fully analyzed"
                    break
                fi
            fi
            ;;
        2)
            log_error "Timeout - trying next iteration"
            update_sugg_status "$loop_count" "timeout"
            ;;
        *)
            log_error "Error - trying next iteration"
            update_sugg_status "$loop_count" "error"
            ;;
    esac

    echo -e "${BLUE}Total: $sugg_after suggestions | Loop: $loop_count / $MAX_ITERATIONS${NC}"
    echo ""

    if [[ $loop_count -lt $MAX_ITERATIONS ]]; then
        log_info "Pause for ${SUGG_PAUSE}s..."
        sleep "$SUGG_PAUSE"
    fi
done

# ============================================
# Final Summary
# ============================================
echo ""
echo -e "${ORANGE}==========================================${NC}"
echo -e "${ORANGE}       RALPH Sugg Mode complete${NC}"
echo -e "${ORANGE}==========================================${NC}"
echo ""

save_session
show_sugg_summary
