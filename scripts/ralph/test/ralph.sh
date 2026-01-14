#!/bin/bash
# RALF Test Mode - Explorative UI Tests mit MCP Playwright
# Testet Features aus Commit-Range oder manueller Liste

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
    TIMEOUT_CMD=""
fi

# Source configuration
source "$SCRIPT_DIR/config.sh"

# Source shared libraries (from parent lib/)
SHARED_LIB="$SCRIPT_DIR/../lib"
source "$SHARED_LIB/date_utils.sh"
source "$SHARED_LIB/logger.sh"
source "$SHARED_LIB/circuit_breaker.sh"

# Source mode-specific libraries
source "$SCRIPT_DIR/lib/commit_analyzer.sh"
source "$SCRIPT_DIR/lib/test_reporter.sh"

# Override paths to be absolute
LOG_DIR="$SCRIPT_DIR/logs"
REPORTS_DIR="$SCRIPT_DIR/reports"
mkdir -p "$LOG_DIR" "$REPORTS_DIR"

# Session tracking
RALPH_STARTED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
export RALPH_STARTED_AT

# ============================================
# Help Function
# ============================================
show_help() {
    cat << EOF
RALF Test Mode - Explorative UI Tests mit MCP Playwright

Usage: ./ralph.sh [OPTIONS]

Optionen:
    -h, --help              Zeige diese Hilfe
    -b, --base BRANCH       Base-Branch für Commit-Range (default: main)
    -t, --timeout MIN       Claude Timeout in Minuten (default: $TIMEOUT_MINUTES)
    -m, --max-iterations N  Max Anzahl Test-Iterationen (default: $MAX_TEST_ITERATIONS)
    --url URL               Frontend URL (default: $FRONTEND_URL)
    --headless              Browser im Headless-Modus (default)
    --headed                Browser mit UI anzeigen
    --status                Zeige aktuellen Test-Status
    --report                Generiere finalen Report
    --reset                 Reset Test-State und starte neu

Beispiele:
    ./ralph.sh                          # Standard-Ausführung
    ./ralph.sh --base develop           # Commits seit develop
    ./ralph.sh --headed                 # Browser sichtbar
    ./ralph.sh --report                 # Nur Report generieren

EOF
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
        -b|--base)
            COMMIT_RANGE_BASE="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT_MINUTES="$2"
            shift 2
            ;;
        -m|--max-iterations)
            MAX_TEST_ITERATIONS="$2"
            shift 2
            ;;
        --url)
            FRONTEND_URL="$2"
            shift 2
            ;;
        --headless)
            HEADLESS=true
            shift
            ;;
        --headed)
            HEADLESS=false
            shift
            ;;
        --status)
            if [[ -f "$SCRIPT_DIR/features.json" ]]; then
                echo -e "${BLUE}=== Test Progress ===${NC}"
                get_test_progress | jq '.'
                echo ""
                echo -e "${BLUE}=== Features ===${NC}"
                jq '.features[] | {id, message, tested, has_bugs: .test_result.has_bugs}' "$SCRIPT_DIR/features.json"
            else
                echo "Keine Features geladen. Starte erst ./ralph.sh"
            fi
            exit 0
            ;;
        --report)
            generate_final_report
            exit 0
            ;;
        --reset)
            log_info "Reset Test-State..."
            rm -f "$SCRIPT_DIR/features.json"
            rm -f "$SCRIPT_DIR/.circuit_breaker_state"
            rm -f "$REPORTS_DIR"/*.json
            log_success "Reset abgeschlossen"
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
# Pre-flight Checks
# ============================================
cd "$PROJECT_ROOT"

# Check if MCP Playwright is configured
check_mcp_playwright() {
    log_info "Prüfe MCP Playwright Konfiguration..."

    if ! command -v claude &>/dev/null; then
        log_error "Claude CLI nicht gefunden"
        exit 1
    fi

    # Check if playwright MCP server is configured
    local mcp_list=$(claude mcp list 2>/dev/null || echo "")

    if ! echo "$mcp_list" | grep -qi "playwright"; then
        log_warn "MCP Playwright nicht konfiguriert!"
        echo ""
        echo -e "${YELLOW}Bitte MCP Playwright hinzufügen:${NC}"
        echo ""
        echo "  claude mcp add playwright -- npx @anthropic/mcp-playwright"
        echo ""
        echo "Oder mit spezifischen Optionen:"
        echo "  claude mcp add -e HEADLESS=$HEADLESS playwright -- npx @anthropic/mcp-playwright"
        echo ""

        read -p "Soll ich versuchen, MCP Playwright jetzt hinzuzufügen? (y/n): " choice
        if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
            log_info "Füge MCP Playwright hinzu..."
            if claude mcp add playwright -- npx @anthropic/mcp-playwright 2>/dev/null; then
                log_success "MCP Playwright hinzugefügt"
            else
                log_error "Konnte MCP Playwright nicht hinzufügen"
                exit 1
            fi
        else
            exit 1
        fi
    else
        log_success "MCP Playwright ist konfiguriert"
    fi
}

# Check if frontend server is running
check_frontend_server() {
    log_info "Prüfe Frontend-Server..."

    if curl -s --head "$FRONTEND_URL" > /dev/null 2>&1; then
        log_success "Frontend erreichbar unter $FRONTEND_URL"
        return 0
    else
        log_warn "Frontend nicht erreichbar unter $FRONTEND_URL"
        echo ""

        if [[ "$AUTO_START_SERVERS" == "true" ]]; then
            log_info "Starte Frontend-Server..."
            cd "$PROJECT_ROOT/frontend" && npm run dev &
            sleep 5
        else
            echo -e "${YELLOW}Bitte starte den Frontend-Server:${NC}"
            echo "  cd frontend && npm run dev"
            echo ""
            read -p "Warte auf Server-Start und drücke Enter..."
        fi

        # Retry
        if curl -s --head "$FRONTEND_URL" > /dev/null 2>&1; then
            log_success "Frontend jetzt erreichbar"
            return 0
        else
            log_error "Frontend immer noch nicht erreichbar"
            return 1
        fi
    fi
}

# ============================================
# Feature Loading
# ============================================
load_features() {
    log_info "Lade Features zum Testen..."

    init_features_file

    # Try manual features first (priority)
    if load_manual_features; then
        log_info "Manuelle Features geladen (haben Priorität)"
    fi

    # Extract from commits
    if ! extract_from_commits "$COMMIT_RANGE_BASE"; then
        # Check if we have manual features
        local feature_count=$(jq '.features | length' "$SCRIPT_DIR/features.json" 2>/dev/null || echo "0")
        if [[ "$feature_count" == "0" ]]; then
            log_error "Keine Features zum Testen gefunden"
            echo ""
            echo "Optionen:"
            echo "  1. Commits auf Branch machen"
            echo "  2. manual_features.json erstellen"
            echo "  3. Anderen Base-Branch wählen: ./ralph.sh --base develop"
            exit 1
        fi
    fi

    # Show loaded features
    local progress=$(get_test_progress)
    local total=$(echo "$progress" | jq '.total')
    local remaining=$(echo "$progress" | jq '.remaining')

    log_success "$total Features geladen, $remaining zu testen"
}

# ============================================
# Execute Claude Test
# ============================================
execute_test() {
    local loop_count=$1
    local feature=$2
    local feature_id=$(echo "$feature" | jq -r '.id')

    local timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local output_file="$LOG_DIR/test_output_${feature_id}_${timestamp}.log"

    log_loop "Starte Test für Feature: $feature_id"

    local timeout_seconds=$((TIMEOUT_MINUTES * 60))

    # Build context for Claude
    local context="RALF Test Mode - Loop #${loop_count}. Testing Feature: ${feature_id}. Frontend URL: ${FRONTEND_URL}."

    # Build feature context
    local feature_context=$(echo "$feature" | jq -r '"Feature to test:\n- Commit: \(.commit_hash)\n- Message: \(.message)\n- Scope: \(.scope)\n- Changed Files: \(.changed_files | join(", "))"')

    # Build timeout prefix
    local timeout_prefix=""
    if [[ -n "$TIMEOUT_CMD" ]]; then
        timeout_prefix="$TIMEOUT_CMD ${timeout_seconds}s"
    fi

    # Execute Claude with MCP Playwright
    local full_prompt="$feature_context

$(cat "$SCRIPT_DIR/prompt.md")"

    if $timeout_prefix claude \
        --output-format json \
        --allowedTools "$CLAUDE_ALLOWED_TOOLS" \
        --append-system-prompt "$context" \
        -p "$full_prompt" \
        > "$output_file" 2>&1; then

        log_success "Test-Ausführung abgeschlossen"

        # Parse test result
        local test_result=$(parse_test_result "$output_file")
        local found=$(echo "$test_result" | jq -r '.found')

        if [[ "$found" == "true" ]]; then
            # Save individual result
            save_test_result "$feature_id" "$test_result"

            # Mark feature as tested
            mark_feature_tested "$feature_id" "$test_result"

            # Log summary
            log_test_summary "$output_file"

            return 0
        else
            log_warn "Kein RALPH_TEST_RESULT Block gefunden"

            # Mark as tested but with empty result
            local empty_result='{"has_bugs": false, "bugs": [], "suggestions": [], "notes": "No structured result returned"}'
            mark_feature_tested "$feature_id" "$empty_result"

            return 0
        fi
    else
        local exit_code=$?

        if [[ $exit_code -eq 124 ]]; then
            log_error "Timeout nach $TIMEOUT_MINUTES Minuten"
            return 2
        fi

        log_error "Test-Ausführung fehlgeschlagen"
        return 1
    fi
}

# ============================================
# Update Status File
# ============================================
update_status() {
    local loop_count=$1
    local current_feature=$2
    local status=$3

    local progress=$(get_test_progress)

    jq -n \
        --argjson progress "$progress" \
        --arg current_feature "$current_feature" \
        --arg status "$status" \
        --arg loop "$loop_count" \
        --arg started_at "$RALPH_STARTED_AT" \
        --arg updated_at "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        '{
            mode: "test",
            status: $status,
            loop: $loop,
            current_feature: $current_feature,
            progress: $progress,
            started_at: $started_at,
            updated_at: $updated_at
        }' > "$LOG_DIR/status.json"
}

# ============================================
# Main Loop
# ============================================

# Pre-flight checks
check_mcp_playwright
check_frontend_server
load_features

# Header
echo ""
echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}       RALF Test Mode${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""

progress=$(get_test_progress)
echo -e "Features:      ${BLUE}$(echo "$progress" | jq -r '.remaining')/$(echo "$progress" | jq -r '.total') zu testen${NC}"
echo -e "Frontend:      ${BLUE}$FRONTEND_URL${NC}"
echo -e "Base Branch:   ${BLUE}$COMMIT_RANGE_BASE${NC}"
echo -e "Max Loops:     ${BLUE}$MAX_TEST_ITERATIONS${NC}"
echo ""
echo -e "${CYAN}==========================================${NC}"
echo ""

# Cleanup on interrupt
cleanup() {
    log_info "RALF Test unterbrochen. Generiere Report..."
    generate_final_report
    exit 0
}
trap cleanup SIGINT SIGTERM

# Main test loop
loop_count=0

while true; do
    loop_count=$((loop_count + 1))

    # Check max iterations
    if [[ $loop_count -gt $MAX_TEST_ITERATIONS ]]; then
        log_warn "Max Iterationen ($MAX_TEST_ITERATIONS) erreicht"
        break
    fi

    # Get next feature to test
    feature=$(get_next_feature)

    if [[ -z "$feature" ]]; then
        log_success "Alle Features getestet!"
        break
    fi

    feature_id=$(echo "$feature" | jq -r '.id')
    log_loop "=== Loop #$loop_count - Feature: $feature_id ==="

    # Update status
    update_status "$loop_count" "$feature_id" "running"

    # Execute test
    execute_test "$loop_count" "$feature"
    exec_result=$?

    case $exec_result in
        0)
            log_success "Test für $feature_id abgeschlossen"
            update_status "$loop_count" "$feature_id" "success"
            sleep 3
            ;;
        2)
            log_error "Timeout - überspringe Feature"
            update_status "$loop_count" "$feature_id" "timeout"
            sleep 5
            ;;
        *)
            log_error "Fehler - versuche erneut"
            update_status "$loop_count" "$feature_id" "error"
            sleep 10
            ;;
    esac

    # Show progress
    progress=$(get_test_progress)
    echo -e "${BLUE}Progress: $(echo "$progress" | jq -r '.tested')/$(echo "$progress" | jq -r '.total') | Bugs: $(echo "$progress" | jq -r '.bugs')${NC}"
    echo ""
done

# ============================================
# Final Report
# ============================================
echo ""
echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}       RALF Test Mode beendet${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""

generate_final_report

echo ""
echo -e "Loops:         ${BLUE}$loop_count${NC}"
echo -e "Reports:       ${BLUE}$REPORTS_DIR/${NC}"
echo ""

# Suggest next steps
final_report=$(cat "$REPORTS_DIR/final_report.json" 2>/dev/null)
if [[ -n "$final_report" ]]; then
    critical_bugs=$(echo "$final_report" | jq '.bugs.by_severity.critical')
    major_bugs=$(echo "$final_report" | jq '.bugs.by_severity.major')

    if [[ $critical_bugs -gt 0 || $major_bugs -gt 0 ]]; then
        echo -e "${RED}Nächster Schritt: Bugs an Debug-Ralph senden${NC}"
        echo "  Kopiere 'for_debug_ralph' aus dem Report"
    fi

    high_suggestions=$(echo "$final_report" | jq '.for_feature_ralph.features_to_add | length')
    if [[ $high_suggestions -gt 0 ]]; then
        echo -e "${YELLOW}Optionaler Schritt: Feature-Vorschläge an Feature-Ralph${NC}"
        echo "  Kopiere 'for_feature_ralph' aus dem Report"
    fi
fi
