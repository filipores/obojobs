#!/usr/bin/env bash
# test_reporter.sh - Generiert Test-Reports für Test-Ralph
# Parst RALPH_TEST_RESULT Block und erstellt strukturierte Reports

# Source date utilities
TR_DIR="$(dirname "${BASH_SOURCE[0]}")"
if [[ -f "$TR_DIR/../../feature/lib/date_utils.sh" ]]; then
    source "$TR_DIR/../../feature/lib/date_utils.sh"
else
    get_iso_timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
fi

# State files
REPORTS_DIR="${SCRIPT_DIR:-.}/reports"
FINAL_REPORT_FILE="$REPORTS_DIR/final_report.json"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

    echo -e "${GREEN}Test-Ergebnis gespeichert: $result_file${NC}"
}

# Generate final report
generate_final_report() {
    local features_file="${SCRIPT_DIR:-.}/features.json"

    if [[ ! -f "$features_file" ]]; then
        echo -e "${RED}Keine features.json gefunden${NC}"
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

    echo -e "${GREEN}Final Report generiert: $FINAL_REPORT_FILE${NC}"

    # Print summary
    echo ""
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}        TEST REPORT SUMMARY${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo -e "Features getestet:  $tested / $total"
    echo -e "Bugs gefunden:      $(echo "$all_bugs" | jq 'length')"
    echo -e "  - Critical:       $critical_bugs"
    echo -e "  - Major:          $major_bugs"
    echo -e "  - Minor:          $minor_bugs"
    echo -e "  - Trivial:        $trivial_bugs"
    echo -e "Vorschläge:         $(echo "$all_suggestions" | jq 'length')"
    echo ""

    if [[ $critical_bugs -gt 0 || $major_bugs -gt 0 ]]; then
        echo -e "${RED}ACHTUNG: $critical_bugs critical und $major_bugs major Bugs gefunden!${NC}"
        echo -e "${YELLOW}Sende Report an Debug-Ralph: ./ralph.sh --mode debug --input $FINAL_REPORT_FILE${NC}"
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
        echo -e "Vorschläge:   $suggestions"
        echo -e "Screenshots:  $screenshots"
        echo -e "${BLUE}===================${NC}"
    else
        echo -e "${YELLOW}Kein RALPH_STATUS Block gefunden${NC}"
    fi
}

# Export functions
export -f init_reports
export -f parse_test_result
export -f parse_status_block
export -f save_test_result
export -f generate_final_report
export -f log_test_summary
