#!/usr/bin/env bash
# response_analyzer.sh - Analyzes Claude Output
# Parses RALPH_STATUS block and exit signals

# Source shared libraries
RA_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$RA_DIR/../../lib/date_utils.sh"
source "$RA_DIR/../../lib/colors.sh"

# State files (in logs/ for consistency)
RESPONSE_ANALYSIS_FILE="${LOG_DIR:-${SCRIPT_DIR:-.}/logs}/.response_analysis"
EXIT_SIGNALS_FILE="${LOG_DIR:-${SCRIPT_DIR:-.}/logs}/.exit_signals"

# Parse RALPH_STATUS block from Claude output
parse_status_block() {
    local output_file=$1

    if [[ ! -f "$output_file" ]]; then
        echo "Error: Output file not found: $output_file"
        return 1
    fi

    # Extract RALPH_STATUS block
    local status_block=$(sed -n '/---RALPH_STATUS---/,/---END_RALPH_STATUS---/p' "$output_file" 2>/dev/null)

    if [[ -z "$status_block" ]]; then
        # No status block found - might be JSON output
        # Try to parse from JSON
        if jq -e '.result' "$output_file" > /dev/null 2>&1; then
            local result_text=$(jq -r '.result // ""' "$output_file" 2>/dev/null)
            # Use printf to properly handle newlines from jq output
            status_block=$(printf '%s\n' "$result_text" | sed -n '/---RALPH_STATUS---/,/---END_RALPH_STATUS---/p')
        fi
    fi

    if [[ -z "$status_block" ]]; then
        echo '{"found": false}'
        return 1
    fi

    # Parse individual fields using printf for proper newline handling
    # Also handle potential whitespace/carriage returns
    local status=$(printf '%s\n' "$status_block" | grep -E '^STATUS:' | sed 's/^STATUS:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local tasks_completed=$(printf '%s\n' "$status_block" | grep -E '^TASKS_COMPLETED' | sed 's/^TASKS_COMPLETED[^:]*:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local files_modified=$(printf '%s\n' "$status_block" | grep -E '^FILES_MODIFIED:' | sed 's/^FILES_MODIFIED:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local tests_status=$(printf '%s\n' "$status_block" | grep -E '^TESTS_STATUS:' | sed 's/^TESTS_STATUS:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local work_type=$(printf '%s\n' "$status_block" | grep -E '^WORK_TYPE:' | sed 's/^WORK_TYPE:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local exit_signal=$(printf '%s\n' "$status_block" | grep -E '^EXIT_SIGNAL:' | sed 's/^EXIT_SIGNAL:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local recommendation=$(printf '%s\n' "$status_block" | grep -E '^RECOMMENDATION:' | sed 's/^RECOMMENDATION:[[:space:]]*//' | tr -d '\r')

    # Convert exit_signal to boolean
    if [[ "$exit_signal" == "true" ]]; then
        exit_signal="true"
    else
        exit_signal="false"
    fi

    # Build JSON output
    cat << EOF
{
    "found": true,
    "status": "${status:-UNKNOWN}",
    "tasks_completed": ${tasks_completed:-0},
    "files_modified": ${files_modified:-0},
    "tests_status": "${tests_status:-NOT_RUN}",
    "work_type": "${work_type:-UNKNOWN}",
    "exit_signal": $exit_signal,
    "recommendation": "${recommendation:-}"
}
EOF

    return 0
}

# Check if EXIT_SIGNAL is true
check_exit_signal() {
    local output_file=$1

    local status=$(parse_status_block "$output_file")
    local exit_signal=$(echo "$status" | jq -r '.exit_signal' 2>/dev/null)

    if [[ "$exit_signal" == "true" ]]; then
        return 0  # Exit signal is true
    else
        return 1  # Exit signal is false or not found
    fi
}

# Analyze full response and save results
analyze_response() {
    local output_file=$1
    local loop_number=$2

    if [[ ! -f "$output_file" ]]; then
        echo "Error: Output file not found"
        return 1
    fi

    # Parse status block
    local status_data=$(parse_status_block "$output_file")
    local found=$(echo "$status_data" | jq -r '.found' 2>/dev/null)

    # Detect API rate limit errors
    local api_limit_hit=false
    if grep -qiE '(rate.?limit|usage.?limit|5.?hour.?limit|limit.?reached)' "$output_file" 2>/dev/null; then
        api_limit_hit=true
    fi

    # Detect errors
    local has_errors=false
    local error_summary=""
    if grep -qE '(^Error:|^ERROR:|Exception|Fatal|FATAL|failed)' "$output_file" 2>/dev/null; then
        has_errors=true
        error_summary=$(grep -E '(^Error:|^ERROR:|Exception|Fatal|FATAL|failed)' "$output_file" | head -3 | tr '\n' ' ')
    fi

    # Detect test-only work
    local is_test_only=false
    if [[ "$found" == "true" ]]; then
        local work_type=$(echo "$status_data" | jq -r '.work_type' 2>/dev/null)
        local files_modified=$(echo "$status_data" | jq -r '.files_modified' 2>/dev/null)

        if [[ "$work_type" == "TESTING" && "$files_modified" == "0" ]]; then
            is_test_only=true
        fi
    fi

    # Save analysis result
    cat > "$RESPONSE_ANALYSIS_FILE" << EOF
{
    "timestamp": "$(get_iso_timestamp)",
    "loop_number": $loop_number,
    "status_block_found": $found,
    "analysis": $status_data,
    "api_limit_hit": $api_limit_hit,
    "has_errors": $has_errors,
    "error_summary": "${error_summary}",
    "is_test_only": $is_test_only
}
EOF

    return 0
}

# Update exit signals tracking
update_exit_signals() {
    if [[ ! -f "$RESPONSE_ANALYSIS_FILE" ]]; then
        return 0
    fi

    local analysis=$(cat "$RESPONSE_ANALYSIS_FILE")

    # Initialize exit signals file if needed
    if [[ ! -f "$EXIT_SIGNALS_FILE" ]]; then
        echo '{"test_only_loops": [], "done_signals": [], "completion_indicators": []}' > "$EXIT_SIGNALS_FILE"
    fi

    local signals=$(cat "$EXIT_SIGNALS_FILE")
    local loop_number=$(echo "$analysis" | jq -r '.loop_number')
    local is_test_only=$(echo "$analysis" | jq -r '.is_test_only')
    local exit_signal=$(echo "$analysis" | jq -r '.analysis.exit_signal')
    local status=$(echo "$analysis" | jq -r '.analysis.status')

    # Update test_only_loops
    if [[ "$is_test_only" == "true" ]]; then
        signals=$(echo "$signals" | jq ".test_only_loops += [$loop_number] | .test_only_loops = .test_only_loops[-5:]")
    else
        # Clear test_only_loops if we did real work
        signals=$(echo "$signals" | jq ".test_only_loops = []")
    fi

    # Update done_signals
    if [[ "$exit_signal" == "true" ]]; then
        signals=$(echo "$signals" | jq ".done_signals += [$loop_number] | .done_signals = .done_signals[-5:]")
    fi

    # Update completion_indicators
    if [[ "$status" == "COMPLETE" ]]; then
        signals=$(echo "$signals" | jq ".completion_indicators += [$loop_number] | .completion_indicators = .completion_indicators[-5:]")
    fi

    echo "$signals" > "$EXIT_SIGNALS_FILE"
}

# Log analysis summary
log_analysis_summary() {
    if [[ ! -f "$RESPONSE_ANALYSIS_FILE" ]]; then
        return 0
    fi

    local analysis=$(cat "$RESPONSE_ANALYSIS_FILE")
    local found=$(echo "$analysis" | jq -r '.status_block_found')

    if [[ "$found" == "true" ]]; then
        local status=$(echo "$analysis" | jq -r '.analysis.status')
        local exit_signal=$(echo "$analysis" | jq -r '.analysis.exit_signal')
        local tasks=$(echo "$analysis" | jq -r '.analysis.tasks_completed')
        local files=$(echo "$analysis" | jq -r '.analysis.files_modified')
        local tests=$(echo "$analysis" | jq -r '.analysis.tests_status')
        local recommendation=$(echo "$analysis" | jq -r '.analysis.recommendation')

        echo -e "${BLUE}=== RALPH_STATUS ===${NC}"
        echo -e "Status: $status"
        echo -e "Tasks Completed: $tasks"
        echo -e "Files Modified: $files"
        echo -e "Tests: $tests"
        echo -e "Exit Signal: $exit_signal"
        if [[ -n "$recommendation" ]]; then
            echo -e "Recommendation: $recommendation"
        fi
        echo -e "${BLUE}===================${NC}"
    else
        echo -e "${YELLOW}No RALPH_STATUS block found in output${NC}"
    fi
}

# Check if should exit gracefully
should_exit_gracefully() {
    if [[ ! -f "$EXIT_SIGNALS_FILE" ]]; then
        echo ""
        return
    fi

    local signals=$(cat "$EXIT_SIGNALS_FILE")

    # Check test-only saturation
    local test_only_count=$(echo "$signals" | jq '.test_only_loops | length')
    if [[ $test_only_count -ge ${MAX_CONSECUTIVE_TEST_LOOPS:-3} ]]; then
        echo "test_saturation"
        return
    fi

    # Check done signals
    local done_count=$(echo "$signals" | jq '.done_signals | length')
    if [[ $done_count -ge ${MAX_CONSECUTIVE_DONE_SIGNALS:-2} ]]; then
        echo "completion_signals"
        return
    fi

    # Check completion with EXIT_SIGNAL
    local completion_count=$(echo "$signals" | jq '.completion_indicators | length')
    if [[ -f "$RESPONSE_ANALYSIS_FILE" ]]; then
        local exit_signal=$(jq -r '.analysis.exit_signal' "$RESPONSE_ANALYSIS_FILE" 2>/dev/null)
        if [[ $completion_count -ge 2 && "$exit_signal" == "true" ]]; then
            echo "project_complete"
            return
        fi
    fi

    # Check PRD completion
    local prd_file="${SCRIPT_DIR:-ralph/feature}/tasks.json"
    if [[ -f "$prd_file" ]]; then
        local total_stories=$(jq '.userStories | length' "$prd_file" 2>/dev/null)
        local passed_stories=$(jq '[.userStories[] | select(.passes == true)] | length' "$prd_file" 2>/dev/null)

        if [[ $total_stories -gt 0 && $passed_stories -eq $total_stories ]]; then
            echo "prd_complete"
            return
        fi
    fi

    echo ""
}

# Detect API 5-hour limit
detect_api_limit() {
    local output_file=$1

    if grep -qiE '(5.?hour.?limit|usage.?limit.?reached|rate.?limit.?exceeded)' "$output_file" 2>/dev/null; then
        echo -e "${RED}Claude API 5-hour limit detected!${NC}"
        echo ""
        echo "Options:"
        echo "  1) Wait and auto-continue (approx. 1 hour)"
        echo "  2) Cancel and start manually later"
        echo ""
        return 0  # Limit detected
    fi

    return 1  # No limit
}

# Export functions
export -f parse_status_block
export -f check_exit_signal
export -f analyze_response
export -f update_exit_signals
export -f log_analysis_summary
export -f should_exit_gracefully
export -f detect_api_limit
