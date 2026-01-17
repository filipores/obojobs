#!/bin/bash
# RALF Explore Mode - Autonome explorative Tests
# Läuft kontinuierlich bis manuell unterbrochen (Ctrl+C)

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

# Source explore-specific libraries
source "$SCRIPT_DIR/lib/explorer.sh"

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
RALF Explore Mode - Autonome explorative Tests

Usage: ./ralph.sh [OPTIONS]

Optionen:
    -h, --help      Zeige diese Hilfe
    --status        Zeige aktuellen Explore-Status
    --reset         Reset Session und starte neu
    --summary       Zeige Zusammenfassung aller Findings

Beispiele:
    ./ralph.sh              # Starte Exploration (läuft bis Ctrl+C)
    ./ralph.sh --status     # Status anzeigen
    ./ralph.sh --summary    # Findings-Zusammenfassung

Hinweis: Drücke Ctrl+C zum Beenden. Findings werden automatisch gespeichert.

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
        --status)
            show_explore_status
            exit 0
            ;;
        --reset)
            log_info "Reset Explore-Session..."
            reset_session
            log_success "Reset abgeschlossen"
            exit 0
            ;;
        --summary)
            show_findings_summary
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

    local mcp_list=$(claude mcp list 2>/dev/null || echo "")

    if ! echo "$mcp_list" | grep -qi "playwright"; then
        log_warn "MCP Playwright nicht konfiguriert!"
        echo ""
        echo -e "${YELLOW}Bitte MCP Playwright hinzufügen:${NC}"
        echo ""
        echo "  claude mcp add playwright -- npx @anthropic/mcp-playwright"
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

# Check if servers are running
check_servers() {
    log_info "Prüfe Server..."

    # Frontend
    if curl -s --head "$FRONTEND_URL" > /dev/null 2>&1; then
        log_success "Frontend erreichbar unter $FRONTEND_URL"
    else
        log_warn "Frontend nicht erreichbar unter $FRONTEND_URL"
        if [[ "$AUTO_START_SERVERS" == "true" ]]; then
            log_info "Starte Frontend-Server..."
            cd "$PROJECT_ROOT/frontend" && npm run dev &
            sleep 5
        else
            echo -e "${YELLOW}Bitte starte den Frontend-Server:${NC}"
            echo "  cd frontend && npm run dev"
            read -p "Warte auf Server-Start und drücke Enter..."
        fi
    fi

    # Backend
    if curl -s "$BACKEND_URL/api/health" > /dev/null 2>&1; then
        log_success "Backend erreichbar unter $BACKEND_URL"
    else
        log_warn "Backend nicht erreichbar unter $BACKEND_URL"
        if [[ "$AUTO_START_SERVERS" == "true" ]]; then
            log_info "Starte Backend-Server..."
            cd "$PROJECT_ROOT/backend" && source venv/bin/activate && python app.py &
            sleep 5
        else
            echo -e "${YELLOW}Bitte starte den Backend-Server:${NC}"
            echo "  cd backend && source venv/bin/activate && python app.py"
            read -p "Warte auf Server-Start und drücke Enter..."
        fi
    fi
}

# ============================================
# Initialize Session
# ============================================
init_session() {
    log_info "Initialisiere Explore-Session..."

    # Initialize bugs.json if not exists
    if [[ ! -f "$SCRIPT_DIR/bugs.json" ]]; then
        cat > "$SCRIPT_DIR/bugs.json" << 'EOF'
{
  "project": "obojobs",
  "mode": "explore",
  "description": "Bugs gefunden durch Explore-Ralph - autonome explorative Tests",
  "bugs": []
}
EOF
        log_info "bugs.json erstellt"
    fi

    # Initialize sugg.json if not exists
    if [[ ! -f "$SCRIPT_DIR/sugg.json" ]]; then
        cat > "$SCRIPT_DIR/sugg.json" << 'EOF'
{
  "project": "obojobs",
  "mode": "explore",
  "description": "Suggestions gefunden durch Explore-Ralph - autonome explorative Tests",
  "suggestions": []
}
EOF
        log_info "sugg.json erstellt"
    fi

    # Initialize or load session
    init_explore_session
}

# ============================================
# Execute Exploration
# ============================================
execute_exploration() {
    local loop_count=$1

    local timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local output_file="$LOG_DIR/explore_output_${timestamp}.log"

    log_loop "Starte Exploration #$loop_count"

    local timeout_seconds=$((TIMEOUT_MINUTES * 60))

    # Build session context for Claude
    local session_context=$(get_session_context)
    local context="RALF Explore Mode - Loop #${loop_count}. Frontend: ${FRONTEND_URL}. Backend: ${BACKEND_URL}.
Session Info: ${session_context}"

    # Build timeout prefix
    local timeout_prefix=""
    if [[ -n "$TIMEOUT_CMD" ]]; then
        timeout_prefix="$TIMEOUT_CMD ${timeout_seconds}s"
    fi

    # Execute Claude
    local exec_result=0

    if $timeout_prefix claude \
        --model "$CLAUDE_MODEL_EXPLORE" \
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
        log_success "Exploration abgeschlossen"

        # Parse and save results
        parse_explore_result "$output_file"

        return 0
    else
        if [[ $exec_result -eq 124 ]]; then
            log_error "Timeout nach $TIMEOUT_MINUTES Minuten"
            return 2
        fi

        log_error "Exploration fehlgeschlagen"
        return 1
    fi
}

# ============================================
# Update Status File
# ============================================
update_explore_status() {
    local loop_count=$1
    local status=$2

    local bugs_count=$(jq '.bugs | length' "$SCRIPT_DIR/bugs.json" 2>/dev/null || echo "0")
    local sugg_count=$(jq '.suggestions | length' "$SCRIPT_DIR/sugg.json" 2>/dev/null || echo "0")
    local pages_count=$(jq '.visited_pages | length' "$SCRIPT_DIR/session.json" 2>/dev/null || echo "0")

    cat > "$LOG_DIR/status.json" << EOF
{
    "mode": "explore",
    "status": "$status",
    "loop": $loop_count,
    "bugs_found": $bugs_count,
    "suggestions_found": $sugg_count,
    "pages_explored": $pages_count,
    "started_at": "$RALPH_STARTED_AT",
    "updated_at": "$(get_iso_timestamp)"
}
EOF
}

# ============================================
# Main Loop
# ============================================

# Pre-flight checks
check_mcp_playwright
check_servers
init_session

# Header
echo ""
echo -e "${ORANGE}==========================================${NC}"
echo -e "${ORANGE}       RALF Explore Mode${NC}"
echo -e "${ORANGE}==========================================${NC}"
echo ""

bugs_count=$(jq '.bugs | length' "$SCRIPT_DIR/bugs.json" 2>/dev/null || echo "0")
sugg_count=$(jq '.suggestions | length' "$SCRIPT_DIR/sugg.json" 2>/dev/null || echo "0")

echo -e "Frontend:      ${BLUE}$FRONTEND_URL${NC}"
echo -e "Backend:       ${BLUE}$BACKEND_URL${NC}"
echo -e "Bugs bisher:   ${BLUE}$bugs_count${NC}"
echo -e "Suggestions:   ${BLUE}$sugg_count${NC}"
echo -e "Timeout:       ${BLUE}$TIMEOUT_MINUTES min${NC}"
echo ""
echo -e "${YELLOW}Drücke Ctrl+C zum Beenden${NC}"
echo ""
echo -e "${ORANGE}==========================================${NC}"
echo ""

# Cleanup on interrupt
cleanup() {
    echo ""
    log_info "RALF Explore unterbrochen. Speichere Session..."
    save_session
    show_findings_summary
    exit 0
}
trap cleanup SIGINT SIGTERM

# Main explore loop
loop_count=0
no_discovery_count=0

while true; do
    loop_count=$((loop_count + 1))

    # Safety check (should never hit in normal use)
    if [[ $loop_count -gt $MAX_EXPLORE_ITERATIONS ]]; then
        log_warn "Max Iterationen erreicht (Safety-Limit)"
        break
    fi

    log_loop "=== Exploration #$loop_count ==="

    # Update status
    update_explore_status "$loop_count" "exploring"

    # Track findings before
    bugs_before=$(jq '.bugs | length' "$SCRIPT_DIR/bugs.json" 2>/dev/null || echo "0")
    sugg_before=$(jq '.suggestions | length' "$SCRIPT_DIR/sugg.json" 2>/dev/null || echo "0")

    # Execute exploration
    execute_exploration "$loop_count"
    exec_result=$?

    # Track findings after
    bugs_after=$(jq '.bugs | length' "$SCRIPT_DIR/bugs.json" 2>/dev/null || echo "0")
    sugg_after=$(jq '.suggestions | length' "$SCRIPT_DIR/sugg.json" 2>/dev/null || echo "0")

    new_bugs=$((bugs_after - bugs_before))
    new_sugg=$((sugg_after - sugg_before))

    case $exec_result in
        0)
            update_explore_status "$loop_count" "success"

            if [[ $new_bugs -gt 0 || $new_sugg -gt 0 ]]; then
                log_success "Neue Findings: $new_bugs Bugs, $new_sugg Suggestions"
                no_discovery_count=0
            else
                no_discovery_count=$((no_discovery_count + 1))
                log_info "Keine neuen Findings in dieser Iteration"

                if [[ $no_discovery_count -ge $CB_NO_DISCOVERY_THRESHOLD ]]; then
                    log_warn "$CB_NO_DISCOVERY_THRESHOLD Iterationen ohne neue Findings"
                    log_info "Tipp: App könnte vollständig exploriert sein, oder Claude braucht neue Anweisungen"
                fi
            fi
            ;;
        2)
            log_error "Timeout - versuche erneut"
            update_explore_status "$loop_count" "timeout"
            ;;
        *)
            log_error "Fehler - versuche erneut"
            update_explore_status "$loop_count" "error"
            ;;
    esac

    # Show progress
    echo -e "${BLUE}Total: $bugs_after Bugs, $sugg_after Suggestions | Loop: $loop_count${NC}"
    echo ""

    # Pause between explorations
    log_info "Pause für ${EXPLORE_PAUSE}s..."
    sleep "$EXPLORE_PAUSE"
done

# ============================================
# Final Summary
# ============================================
echo ""
echo -e "${ORANGE}==========================================${NC}"
echo -e "${ORANGE}       RALF Explore Mode beendet${NC}"
echo -e "${ORANGE}==========================================${NC}"
echo ""

show_findings_summary
