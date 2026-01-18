#!/usr/bin/env bash
# test_reporter.sh - Generates Test Reports for Test Ralph
# Parses RALPH_TEST_RESULT block and creates structured reports
#
# Prerequisite: date_utils.sh is loaded by ralph.sh

# State files
REPORTS_DIR="${SCRIPT_DIR:-.}/reports"
FINAL_REPORT_FILE="$REPORTS_DIR/final_report.json"

# Colors are loaded from lib/colors.sh (via ralph.sh)

# Initialize reports directory
init_reports() {
    mkdir -p "$REPORTS_DIR"
    mkdir -p "$REPORTS_DIR/screenshots"
}

# Parse RALPH_TEST_RESULT block from Claude output
parse_test_result() {
    local output_file=$1

    if [[ ! -f "$output_file" ]]; then
        echo '{"found": false}'
        return 1
    fi

    # Extract RALPH_TEST_RESULT block
    local result_block=""

    # Try plain text first
    result_block=$(sed -n '/---RALPH_TEST_RESULT---/,/---END_RALPH_TEST_RESULT---/p' "$output_file" 2>/dev/null | sed '1d;$d')

    if [[ -z "$result_block" ]]; then
        # Try JSON output format
        if jq -e '.result' "$output_file" > /dev/null 2>&1; then
            local result_text=$(jq -r '.result // ""' "$output_file" 2>/dev/null)
            # Use printf for proper newline handling
            result_block=$(printf '%s\n' "$result_text" | sed -n '/---RALPH_TEST_RESULT---/,/---END_RALPH_TEST_RESULT---/p' | sed '1d;$d')
        fi
    fi

    if [[ -z "$result_block" ]]; then
        echo '{"found": false}'
        return 1
    fi

    # Validate JSON
    if echo "$result_block" | jq '.' > /dev/null 2>&1; then
        local parsed=$(echo "$result_block" | jq '. + {found: true}')
        echo "$parsed"
        return 0
    else
        echo '{"found": false, "error": "Invalid JSON in test result"}'
        return 1
    fi
}

# Parse RALPH_STATUS block
parse_status_block() {
    local output_file=$1

    if [[ ! -f "$output_file" ]]; then
        echo '{"found": false}'
        return 1
    fi

    local status_block=$(sed -n '/---RALPH_STATUS---/,/---END_RALPH_STATUS---/p' "$output_file" 2>/dev/null)

    if [[ -z "$status_block" ]]; then
        if jq -e '.result' "$output_file" > /dev/null 2>&1; then
            local result_text=$(jq -r '.result // ""' "$output_file" 2>/dev/null)
            # Use printf for proper newline handling
            status_block=$(printf '%s\n' "$result_text" | sed -n '/---RALPH_STATUS---/,/---END_RALPH_STATUS---/p')
        fi
    fi

    if [[ -z "$status_block" ]]; then
        echo '{"found": false}'
        return 1
    fi

    # Parse fields using printf for proper newline handling
    local status=$(printf '%s\n' "$status_block" | grep -E '^STATUS:' | sed 's/^STATUS:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local feature_tested=$(printf '%s\n' "$status_block" | grep -E '^FEATURE_TESTED:' | sed 's/^FEATURE_TESTED:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local bugs_found=$(printf '%s\n' "$status_block" | grep -E '^BUGS_FOUND:' | sed 's/^BUGS_FOUND:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local suggestions_found=$(printf '%s\n' "$status_block" | grep -E '^SUGGESTIONS_FOUND:' | sed 's/^SUGGESTIONS_FOUND:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local screenshots_taken=$(printf '%s\n' "$status_block" | grep -E '^SCREENSHOTS_TAKEN:' | sed 's/^SCREENSHOTS_TAKEN:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local exit_signal=$(printf '%s\n' "$status_block" | grep -E '^EXIT_SIGNAL:' | sed 's/^EXIT_SIGNAL:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local recommendation=$(printf '%s\n' "$status_block" | grep -E '^RECOMMENDATION:' | sed 's/^RECOMMENDATION:[[:space:]]*//' | tr -d '\r')

    if [[ "$exit_signal" == "true" ]]; then
        exit_signal="true"
    else
        exit_signal="false"
    fi

    cat << EOF
{
    "found": true,
    "status": "${status:-UNKNOWN}",
    "feature_tested": "${feature_tested:-}",
    "bugs_found": ${bugs_found:-0},
    "suggestions_found": ${suggestions_found:-0},
    "screenshots_taken": ${screenshots_taken:-0},
    "exit_signal": $exit_signal,
    "recommendation": "${recommendation:-}"
}
EOF
}

# Save individual test result
save_test_result() {
    local feature_id=$1
    local test_result=$2

    local result_file="$REPORTS_DIR/test_${feature_id}.json"
    echo "$test_result" | jq '.' > "$result_file"

    echo -e "${GREEN}Test result saved: $result_file${NC}"
}

# Generate final report
generate_final_report() {
    local features_file="${SCRIPT_DIR:-.}/tasks.json"

    if [[ ! -f "$features_file" ]]; then
        echo -e "${RED}No tasks.json found${NC}"
        return 1
    fi

    local features=$(cat "$features_file")

    # Collect all bugs
    local all_bugs=$(echo "$features" | jq '[.features[] | select(.test_result.bugs != null) | .test_result.bugs[]]')

    # Collect all suggestions
    local all_suggestions=$(echo "$features" | jq '[.features[] | select(.test_result.suggestions != null) | .test_result.suggestions[]]')

    # Count by severity
    local critical_bugs=$(echo "$all_bugs" | jq '[.[] | select(.severity == "critical")] | length')
    local major_bugs=$(echo "$all_bugs" | jq '[.[] | select(.severity == "major")] | length')
    local minor_bugs=$(echo "$all_bugs" | jq '[.[] | select(.severity == "minor")] | length')
    local trivial_bugs=$(echo "$all_bugs" | jq '[.[] | select(.severity == "trivial")] | length')

    # Count suggestions by type
    local ux_suggestions=$(echo "$all_suggestions" | jq '[.[] | select(.type == "ux")] | length')
    local perf_suggestions=$(echo "$all_suggestions" | jq '[.[] | select(.type == "performance")] | length')
    local a11y_suggestions=$(echo "$all_suggestions" | jq '[.[] | select(.type == "accessibility")] | length')
    local feature_suggestions=$(echo "$all_suggestions" | jq '[.[] | select(.type == "feature")] | length')

    # Get progress
    local total=$(echo "$features" | jq '.features | length')
    local tested=$(echo "$features" | jq '[.features[] | select(.tested == true)] | length')

    # Build final report
    local report=$(jq -n \
        --arg generated_at "$(get_iso_timestamp)" \
        --argjson total_features "$total" \
        --argjson tested_features "$tested" \
        --argjson total_bugs "$(echo "$all_bugs" | jq 'length')" \
        --argjson critical_bugs "$critical_bugs" \
        --argjson major_bugs "$major_bugs" \
        --argjson minor_bugs "$minor_bugs" \
        --argjson trivial_bugs "$trivial_bugs" \
        --argjson total_suggestions "$(echo "$all_suggestions" | jq 'length')" \
        --argjson ux_suggestions "$ux_suggestions" \
        --argjson perf_suggestions "$perf_suggestions" \
        --argjson a11y_suggestions "$a11y_suggestions" \
        --argjson feature_suggestions "$feature_suggestions" \
        --argjson bugs "$all_bugs" \
        --argjson suggestions "$all_suggestions" \
        '{
            report_type: "ralph_test_report",
            generated_at: $generated_at,
            summary: {
                total_features: $total_features,
                tested_features: $tested_features,
                coverage_percent: (if $total_features > 0 then (($tested_features / $total_features) * 100 | floor) else 0 end)
            },
            bugs: {
                total: $total_bugs,
                by_severity: {
                    critical: $critical_bugs,
                    major: $major_bugs,
                    minor: $minor_bugs,
                    trivial: $trivial_bugs
                },
                items: $bugs
            },
            suggestions: {
                total: $total_suggestions,
                by_type: {
                    ux: $ux_suggestions,
                    performance: $perf_suggestions,
                    accessibility: $a11y_suggestions,
                    feature: $feature_suggestions
                },
                items: $suggestions
            },
            for_debug_ralph: {
                bugs_to_fix: [$bugs[] | select(.severity == "critical" or .severity == "major") | {
                    id: .id,
                    title: .title,
                    severity: .severity,
                    component: .affected_component,
                    steps: .steps_to_reproduce
                }]
            },
            for_feature_ralph: {
                features_to_add: [$suggestions[] | select(.priority == "high") | {
                    id: .id,
                    title: .title,
                    type: .type,
                    description: .description
                }]
            }
        }')

    echo "$report" | jq '.' > "$FINAL_REPORT_FILE"

    echo -e "${GREEN}Final report generated: $FINAL_REPORT_FILE${NC}"

    # Print summary
    echo ""
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}        TEST REPORT SUMMARY${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo -e "Features tested:  $tested / $total"
    echo -e "Bugs found:       $(echo "$all_bugs" | jq 'length')"
    echo -e "  - Critical:     $critical_bugs"
    echo -e "  - Major:        $major_bugs"
    echo -e "  - Minor:        $minor_bugs"
    echo -e "  - Trivial:      $trivial_bugs"
    echo -e "Suggestions:      $(echo "$all_suggestions" | jq 'length')"
    echo ""

    if [[ $critical_bugs -gt 0 || $major_bugs -gt 0 ]]; then
        echo -e "${RED}WARNING: $critical_bugs critical and $major_bugs major bugs found!${NC}"
        echo -e "${YELLOW}Send report to Debug Ralph: ./ralph.sh --mode debug --input $FINAL_REPORT_FILE${NC}"
    fi

    echo ""
}

# Log test summary for current iteration
log_test_summary() {
    local output_file=$1

    local status=$(parse_status_block "$output_file")
    local found=$(echo "$status" | jq -r '.found')

    if [[ "$found" == "true" ]]; then
        local feature=$(echo "$status" | jq -r '.feature_tested')
        local bugs=$(echo "$status" | jq -r '.bugs_found')
        local suggestions=$(echo "$status" | jq -r '.suggestions_found')
        local screenshots=$(echo "$status" | jq -r '.screenshots_taken')

        echo -e "${BLUE}=== TEST SUMMARY ===${NC}"
        echo -e "Feature:      $feature"
        echo -e "Bugs:         $bugs"
        echo -e "Suggestions:  $suggestions"
        echo -e "Screenshots:  $screenshots"
        echo -e "${BLUE}===================${NC}"
    else
        echo -e "${YELLOW}No RALPH_STATUS block found${NC}"
    fi
}

# ============================================
# Helper functions for log_iteration_summary
# ============================================

# Extracts JSON from output file (NDJSON or Single-JSON)
_extract_json_from_output() {
    local output_file=$1
    local json_content

    if head -1 "$output_file" | jq -e '.type' > /dev/null 2>&1; then
        # NDJSON format - get last result line
        json_content=$(grep -E '^\{"type":"result"' "$output_file" | tail -1)
        if [[ -z "$json_content" ]]; then
            json_content=$(tail -1 "$output_file")
        fi
    else
        json_content=$(cat "$output_file")
    fi

    if echo "$json_content" | jq -e '.' > /dev/null 2>&1; then
        echo "$json_content"
        return 0
    fi
    return 1
}

# Loads feature details from tasks.json
_get_feature_details() {
    local feature_id=$1
    local features_file="${SCRIPT_DIR:-$(dirname "$0")}/tasks.json"

    if [[ -f "$features_file" ]]; then
        jq -r --arg id "$feature_id" '.features[] | select(.id == $id)' "$features_file" 2>/dev/null
    fi
}

# Extracts execution metrics from JSON
_extract_execution_metrics() {
    local output_json=$1

    local duration_ms=$(echo "$output_json" | jq -r '.duration_ms // 0')
    local duration_s=$(echo "scale=1; $duration_ms / 1000" | bc 2>/dev/null || echo "0")
    local cost=$(echo "$output_json" | jq -r '.total_cost_usd // 0')
    local num_turns=$(echo "$output_json" | jq -r '.num_turns // 0')
    local input_tokens=$(echo "$output_json" | jq -r '.usage.input_tokens // 0')
    local output_tokens=$(echo "$output_json" | jq -r '.usage.output_tokens // 0')
    local cache_read=$(echo "$output_json" | jq -r '.usage.cache_read_input_tokens // 0')
    local is_error=$(echo "$output_json" | jq -r '.is_error // false')

    jq -n \
        --arg duration_s "$duration_s" \
        --arg cost "$(printf "%.2f" "$cost" 2>/dev/null || echo "$cost")" \
        --arg num_turns "$num_turns" \
        --arg input_tokens "$(printf "%'d" "$input_tokens" 2>/dev/null || echo "$input_tokens")" \
        --arg output_tokens "$(printf "%'d" "$output_tokens" 2>/dev/null || echo "$output_tokens")" \
        --arg cache_read "$(printf "%'d" "$cache_read" 2>/dev/null || echo "$cache_read")" \
        --arg is_error "$is_error" \
        '{duration_s: $duration_s, cost: $cost, num_turns: $num_turns, input_tokens: $input_tokens, output_tokens: $output_tokens, cache_read: $cache_read, is_error: $is_error}'
}

# Extracts test results (Bugs, Suggestions)
_extract_test_results() {
    local output_json=$1

    local temp_output=$(mktemp)
    echo "$output_json" > "$temp_output"
    local test_result=$(parse_test_result "$temp_output")
    rm -f "$temp_output"

    echo "$test_result"
}

# Formats and outputs the iteration summary
_print_iteration_summary() {
    local feature_id=$1
    local feature_data=$2
    local metrics=$3
    local test_result=$4

    # Feature Details
    local feature_title=$(echo "$feature_data" | jq -r '.message // ""' 2>/dev/null)
    local feature_type=$(echo "$feature_data" | jq -r '.type // ""' 2>/dev/null)
    local feature_focus=$(echo "$feature_data" | jq -r '.test_focus // ""' 2>/dev/null | head -c 80)
    local feature_pages=$(echo "$feature_data" | jq -r '.pages // [] | join(", ")' 2>/dev/null | head -c 50)

    # Metrics
    local duration_s=$(echo "$metrics" | jq -r '.duration_s')
    local cost=$(echo "$metrics" | jq -r '.cost')
    local num_turns=$(echo "$metrics" | jq -r '.num_turns')
    local input_fmt=$(echo "$metrics" | jq -r '.input_tokens')
    local output_fmt=$(echo "$metrics" | jq -r '.output_tokens')
    local cache_fmt=$(echo "$metrics" | jq -r '.cache_read')
    local is_error=$(echo "$metrics" | jq -r '.is_error')

    # Status colors
    local status_color=$GREEN status_text="SUCCESS"
    [[ "$is_error" == "true" ]] && { status_color=$RED; status_text="ERROR"; }

    # Type color
    local type_color=$BLUE
    case "$feature_type" in
        critical) type_color=$RED ;; setup) type_color=$YELLOW ;; core) type_color=$GREEN ;;
    esac

    # Test results
    local result_found=$(echo "$test_result" | jq -r '.found // false')
    local bugs_count=0 suggestions_count=0 scenarios_count=0 bugs_list="" suggestions_list=""

    if [[ "$result_found" == "true" ]]; then
        bugs_count=$(echo "$test_result" | jq -r '.bugs | length // 0')
        suggestions_count=$(echo "$test_result" | jq -r '.suggestions | length // 0')
        scenarios_count=$(echo "$test_result" | jq -r '.tested_scenarios | length // 0')
        [[ $bugs_count -gt 0 ]] && bugs_list=$(echo "$test_result" | jq -r '.bugs[] | "     - [\(.severity // "unknown")] \(.title // "No title")"' 2>/dev/null)
        [[ $suggestions_count -gt 0 ]] && suggestions_list=$(echo "$test_result" | jq -r '.suggestions[] | "     - [\(.type // "unknown")] \(.title // "No title")"' 2>/dev/null)
    fi

    local bugs_color=$GREEN sugg_color=$GREEN
    [[ $bugs_count -gt 0 ]] && bugs_color=$RED
    [[ $suggestions_count -gt 0 ]] && sugg_color=$YELLOW

    # Output
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}                     ITERATION SUMMARY                            ${BLUE}║${NC}"
    echo -e "${BLUE}╠══════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║${NC}  ${YELLOW}FEATURE${NC}                                                         ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}  ID:        ${YELLOW}${feature_id:-unknown}${NC}"
    [[ -n "$feature_title" ]] && echo -e "${BLUE}║${NC}  Title:     ${feature_title}"
    [[ -n "$feature_type" ]] && echo -e "${BLUE}║${NC}  Type:      ${type_color}${feature_type}${NC}"
    [[ -n "$feature_focus" ]] && echo -e "${BLUE}║${NC}  Focus:     ${feature_focus}..."
    [[ -n "$feature_pages" ]] && echo -e "${BLUE}║${NC}  Pages:     ${feature_pages}"
    echo -e "${BLUE}╠══════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║${NC}  ${YELLOW}EXECUTION${NC}                                                        ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}  Status:    ${status_color}${status_text}${NC}"
    echo -e "${BLUE}║${NC}  Duration:  ${duration_s}s"
    echo -e "${BLUE}║${NC}  Cost:      \$${cost}"
    echo -e "${BLUE}║${NC}  Turns:     ${num_turns}"
    echo -e "${BLUE}║${NC}  Tokens:    In: ${input_fmt} | Out: ${output_fmt} | Cache: ${cache_fmt}"
    echo -e "${BLUE}╠══════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║${NC}  ${YELLOW}TEST RESULTS${NC}                                                     ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}  Scenarios: ${scenarios_count} tested"
    echo -e "${BLUE}║${NC}  Bugs:      ${bugs_color}${bugs_count}${NC}"
    [[ -n "$bugs_list" ]] && echo -e "$bugs_list"
    echo -e "${BLUE}║${NC}  Suggestions:${sugg_color}${suggestions_count}${NC}"
    [[ -n "$suggestions_list" ]] && echo -e "$suggestions_list"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ============================================
# Main function: Log iteration summary
# ============================================
log_iteration_summary() {
    local output_file=$1
    local feature_id=$2

    # Validation
    if [[ ! -f "$output_file" ]]; then
        echo -e "${YELLOW}No output file found${NC}"
        return 1
    fi
    if [[ ! -s "$output_file" ]]; then
        echo -e "${YELLOW}Output file is empty${NC}"
        return 1
    fi

    # Extract JSON
    local output_json
    output_json=$(_extract_json_from_output "$output_file")
    if [[ $? -ne 0 ]]; then
        echo -e "${YELLOW}Output is not valid JSON${NC}"
        return 1
    fi

    # Collect data
    local feature_data=$(_get_feature_details "$feature_id")
    local metrics=$(_extract_execution_metrics "$output_json")
    local test_result=$(_extract_test_results "$output_json")

    # Output
    _print_iteration_summary "$feature_id" "$feature_data" "$metrics" "$test_result"
}

# Export functions
export -f init_reports
export -f parse_test_result
export -f parse_status_block
export -f save_test_result
export -f generate_final_report
export -f log_test_summary
export -f log_iteration_summary
