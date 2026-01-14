#!/bin/bash
# RALF Debug Mode - Bug-basiertes Debugging
# Analog zu Feature-Ralph, aber für Bug-Fixing

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
source "$SHARED_LIB/context_builder.sh"

# Override paths
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Session tracking
RALPH_STARTED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
export RALPH_STARTED_AT

# ============================================
# Help Function
# ============================================
show_help() {
    cat << EOF
RALF Debug Mode - Bug-basiertes Debugging

Usage: ./ralph.sh [OPTIONS]

Optionen:
    -h, --help              Zeige diese Hilfe
    -t, --timeout MIN       Claude Timeout in Minuten (default: $TIMEOUT_MINUTES)
    -m, --max-attempts N    Max Fix-Versuche pro Bug (default: $MAX_FIX_ATTEMPTS)
    --status                Zeige aktuellen Bug-Status
    --reset                 Reset Debug-State und starte neu
    --add-bug               Interaktiv neuen Bug hinzufügen

Beispiele:
    ./ralph.sh                      # Standard-Ausführung
    ./ralph.sh --timeout 20         # 20 Minuten Timeout
    ./ralph.sh --status             # Status anzeigen

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
        -t|--timeout)
            TIMEOUT_MINUTES="$2"
            shift 2
            ;;
        -m|--max-attempts)
            MAX_FIX_ATTEMPTS="$2"
            shift 2
            ;;
        --status)
            if [[ -f "$SCRIPT_DIR/bugs.json" ]]; then
                echo -e "${BLUE}=== Bug Status ===${NC}"
                total=$(jq '.bugs | length' "$SCRIPT_DIR/bugs.json")
                fixed=$(jq '[.bugs[] | select(.fixed == true)] | length' "$SCRIPT_DIR/bugs.json")
                remaining=$(jq '[.bugs[] | select(.fixed == false)] | length' "$SCRIPT_DIR/bugs.json")
                echo -e "Total:     $total"
                echo -e "Fixed:     ${GREEN}$fixed${NC}"
                echo -e "Remaining: ${YELLOW}$remaining${NC}"
                echo ""
                echo -e "${BLUE}=== Offene Bugs ===${NC}"
                jq -r '.bugs[] | select(.fixed == false) | "[\(.severity)] \(.id): \(.title)"' "$SCRIPT_DIR/bugs.json"
            else
                echo "Keine bugs.json gefunden."
            fi
            exit 0
            ;;
        --reset)
            log_info "Reset Debug-State..."
            jq '.bugs = [.bugs[] | .fixed = false | .fixAttempts = 0]' "$SCRIPT_DIR/bugs.json" > "$SCRIPT_DIR/bugs.json.tmp"
            mv "$SCRIPT_DIR/bugs.json.tmp" "$SCRIPT_DIR/bugs.json"
            rm -f "$SCRIPT_DIR/.circuit_breaker_state"
            rm -f "$LOG_DIR"/*.log
            log_success "Reset abgeschlossen"
            exit 0
            ;;
        --add-bug)
            echo "Bug hinzufügen (interaktiv):"
            echo ""
            read -p "Bug ID (z.B. BUG-006): " bug_id
            read -p "Title: " title
            read -p "Severity (critical/major/minor/trivial): " severity
            read -p "Description: " description
            read -p "Affected Files (comma-separated): " files

            # Add bug to bugs.json
            new_bug=$(jq -n \
                --arg id "$bug_id" \
                --arg title "$title" \
                --arg severity "$severity" \
                --arg desc "$description" \
                --arg files "$files" \
                '{
                    id: $id,
                    title: $title,
                    severity: $severity,
                    description: $desc,
                    stepsToReproduce: [],
                    expected: "",
                    actual: "",
                    rootCause: "",
                    affectedFiles: ($files | split(",")),
                    suggestedFix: "",
                    fixed: false,
                    fixAttempts: 0,
                    source: "manual"
                }')

            jq --argjson bug "$new_bug" '.bugs += [$bug]' "$SCRIPT_DIR/bugs.json" > "$SCRIPT_DIR/bugs.json.tmp"
            mv "$SCRIPT_DIR/bugs.json.tmp" "$SCRIPT_DIR/bugs.json"
            log_success "Bug $bug_id hinzugefügt"
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

if [[ ! -f "$SCRIPT_DIR/bugs.json" ]]; then
    log_error "Keine bugs.json gefunden in $SCRIPT_DIR"
    echo "Erstelle zuerst eine bugs.json oder nutze --add-bug"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/prompt.md" ]]; then
    log_error "Keine prompt.md gefunden in $SCRIPT_DIR"
    exit 1
fi

# ============================================
# Bug Info
# ============================================
TOTAL_BUGS=$(jq '.bugs | length' "$SCRIPT_DIR/bugs.json")
FIXED_BUGS=$(jq '[.bugs[] | select(.fixed == true)] | length' "$SCRIPT_DIR/bugs.json")

# ============================================
# Header
# ============================================
echo ""
echo -e "${RED}==========================================${NC}"
echo -e "${RED}       RALF Debug Mode${NC}"
echo -e "${RED}==========================================${NC}"
echo ""
echo -e "Bugs:          ${BLUE}$FIXED_BUGS/$TOTAL_BUGS fixed${NC}"
echo -e "Max Attempts:  ${BLUE}$MAX_FIX_ATTEMPTS${NC}"
echo -e "Timeout:       ${BLUE}$TIMEOUT_MINUTES minutes${NC}"
echo ""
echo -e "${RED}==========================================${NC}"
echo ""

# ============================================
# Get Current Bug
# ============================================
get_current_bug() {
    # Find first bug with fixed: false, ordered by severity (critical > major > minor > trivial)
    jq -r '
        .bugs
        | map(select(.fixed == false))
        | sort_by(
            if .severity == "critical" then 0
            elif .severity == "major" then 1
            elif .severity == "minor" then 2
            else 3 end
        )
        | .[0].id // "NONE"
    ' "$SCRIPT_DIR/bugs.json"
}

# ============================================
# Execute QA Phase (Haiku - Token-optimiert)
# ============================================
execute_qa_phase() {
    if [[ "$ENABLE_QA_PHASE" != "true" ]]; then
        return 0
    fi

    log_info "QA-Phase mit Haiku..."

    local timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local qa_output="$LOG_DIR/qa_output_${timestamp}.log"

    if ${TIMEOUT_CMD:+$TIMEOUT_CMD 120s} claude \
        --model "$CLAUDE_MODEL_QA" \
        --output-format json \
        --allowedTools "Bash,Read" \
        -p "$(cat "$SCRIPT_DIR/qa_prompt.md")" \
        > "$qa_output" 2>&1; then

        local qa_result=$(jq -r '.result // ""' "$qa_output" 2>/dev/null)
        if echo "$qa_result" | grep -q "SUMMARY: ALL_PASS"; then
            log_success "QA-Phase: Alle Checks bestanden"
            return 0
        elif echo "$qa_result" | grep -q "SUMMARY: HAS_FAILURES"; then
            log_warn "QA-Phase: Hat Fehler"
            return 1
        fi
    fi
    return 0
}

# ============================================
# Execute Claude
# ============================================
execute_claude() {
    local loop_count=$1
    local current_bug=$2

    local timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local output_file="$LOG_DIR/debug_output_${current_bug}_${timestamp}.log"

    log_loop "Starte Claude Code für Bug: $current_bug (${CLAUDE_MODEL_IMPL##*-})"

    local timeout_seconds=$((TIMEOUT_MINUTES * 60))

    # Get bug details
    local bug_details=$(jq -r --arg id "$current_bug" '.bugs[] | select(.id == $id)' "$SCRIPT_DIR/bugs.json")
    local bug_title=$(echo "$bug_details" | jq -r '.title')
    local bug_severity=$(echo "$bug_details" | jq -r '.severity')

    # Pre-compute relevant files (Token-Optimierung)
    local relevant_files=$(get_bug_context "$current_bug")
    local file_context=$(build_context_string "$relevant_files")

    # Build context
    local context="RALF Debug Mode - Loop #${loop_count}. Fixing Bug: ${current_bug} (${bug_severity}): ${bug_title}
${file_context}"

    # Build timeout prefix
    local timeout_prefix=""
    if [[ -n "$TIMEOUT_CMD" ]]; then
        timeout_prefix="$TIMEOUT_CMD ${timeout_seconds}s"
    fi

    # Execute Claude with model selection
    if $timeout_prefix claude \
        --model "$CLAUDE_MODEL_IMPL" \
        --output-format json \
        --allowedTools "$CLAUDE_ALLOWED_TOOLS" \
        --append-system-prompt "$context" \
        -p "$(cat "$SCRIPT_DIR/prompt.md")" \
        > "$output_file" 2>&1; then

        log_success "Claude Code Ausführung abgeschlossen"

        # Check if bug was fixed (parse RALPH_STATUS)
        if grep -q "FIX_SUCCESSFUL: true" "$output_file" 2>/dev/null; then
            log_success "Bug $current_bug erfolgreich gefixt!"
            return 0
        elif grep -q "STATUS: BLOCKED" "$output_file" 2>/dev/null; then
            log_warn "Bug $current_bug blockiert"
            return 3
        else
            log_warn "Bug $current_bug noch nicht gefixt"
            # Increment fix attempts
            jq --arg id "$current_bug" '
                .bugs = [.bugs[] |
                    if .id == $id then .fixAttempts += 1 else . end
                ]' "$SCRIPT_DIR/bugs.json" > "$SCRIPT_DIR/bugs.json.tmp"
            mv "$SCRIPT_DIR/bugs.json.tmp" "$SCRIPT_DIR/bugs.json"
            return 1
        fi
    else
        local exit_code=$?

        if [[ $exit_code -eq 124 ]]; then
            log_error "Timeout nach $TIMEOUT_MINUTES Minuten!"
            return 2
        fi

        log_error "Claude Code Ausführung fehlgeschlagen"
        return 1
    fi
}

# ============================================
# Update Status
# ============================================
update_status() {
    local loop_count=$1
    local current_bug=$2
    local status=$3

    FIXED_BUGS=$(jq '[.bugs[] | select(.fixed == true)] | length' "$SCRIPT_DIR/bugs.json")

    cat > "$LOG_DIR/status.json" << EOF
{
    "mode": "debug",
    "status": "$status",
    "loop": $loop_count,
    "current_bug": "$current_bug",
    "bugs_fixed": $FIXED_BUGS,
    "bugs_total": $TOTAL_BUGS,
    "started_at": "$RALPH_STARTED_AT",
    "updated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
}

# ============================================
# Main Loop
# ============================================
loop_count=0

# Cleanup on interrupt
cleanup() {
    log_info "RALF Debug unterbrochen. Cleanup..."
    update_status "$loop_count" "" "interrupted"
    exit 0
}
trap cleanup SIGINT SIGTERM

log_success "Starte RALF Debug Mode Loop..."

while true; do
    loop_count=$((loop_count + 1))

    # Get current bug
    current_bug=$(get_current_bug)

    if [[ "$current_bug" == "NONE" ]]; then
        log_success "Alle Bugs gefixt!"
        update_status "$loop_count" "" "complete"
        break
    fi

    # Check fix attempts
    attempts=$(jq -r --arg id "$current_bug" '.bugs[] | select(.id == $id) | .fixAttempts' "$SCRIPT_DIR/bugs.json")
    if [[ $attempts -ge $MAX_FIX_ATTEMPTS ]]; then
        log_error "Bug $current_bug: Max Versuche ($MAX_FIX_ATTEMPTS) erreicht - überspringe"
        # Mark as blocked
        jq --arg id "$current_bug" '
            .bugs = [.bugs[] |
                if .id == $id then .blocked = true else . end
            ]' "$SCRIPT_DIR/bugs.json" > "$SCRIPT_DIR/bugs.json.tmp"
        mv "$SCRIPT_DIR/bugs.json.tmp" "$SCRIPT_DIR/bugs.json"
        continue
    fi

    log_loop "=== Loop #$loop_count - Bug: $current_bug (Versuch $((attempts + 1))/$MAX_FIX_ATTEMPTS) ==="

    # Update status
    update_status "$loop_count" "$current_bug" "running"

    # Execute Claude
    execute_claude "$loop_count" "$current_bug"
    exec_result=$?

    case $exec_result in
        0)
            # Run QA phase with Haiku
            execute_qa_phase

            log_success "Bug $current_bug gefixt"
            update_status "$loop_count" "$current_bug" "success"
            FIXED_BUGS=$((FIXED_BUGS + 1))
            log_info "Bugs fixed: $FIXED_BUGS/$TOTAL_BUGS"
            sleep 3
            ;;
        2)
            log_error "Timeout - versuche erneut"
            update_status "$loop_count" "$current_bug" "timeout"
            sleep 10
            ;;
        3)
            log_warn "Bug blockiert - überspringe"
            update_status "$loop_count" "$current_bug" "blocked"
            sleep 5
            ;;
        *)
            log_warn "Fix nicht erfolgreich - versuche erneut"
            update_status "$loop_count" "$current_bug" "retry"
            sleep 5
            ;;
    esac

    log_loop "=== Loop #$loop_count abgeschlossen ==="
    echo ""
done

# ============================================
# Final Summary
# ============================================
echo ""
echo -e "${RED}==========================================${NC}"
echo -e "${RED}       RALF Debug Mode beendet${NC}"
echo -e "${RED}==========================================${NC}"
echo ""
echo -e "Total Loops:   ${BLUE}$loop_count${NC}"
echo -e "Bugs Fixed:    ${GREEN}$FIXED_BUGS/$TOTAL_BUGS${NC}"
echo -e "Logs:          ${BLUE}$LOG_DIR/${NC}"
echo ""

# Show remaining bugs if any
remaining=$(jq '[.bugs[] | select(.fixed == false and .blocked != true)] | length' "$SCRIPT_DIR/bugs.json")
if [[ $remaining -gt 0 ]]; then
    echo -e "${YELLOW}Offene Bugs:${NC}"
    jq -r '.bugs[] | select(.fixed == false and .blocked != true) | "  - \(.id): \(.title)"' "$SCRIPT_DIR/bugs.json"
    echo ""
fi

blocked=$(jq '[.bugs[] | select(.blocked == true)] | length' "$SCRIPT_DIR/bugs.json")
if [[ $blocked -gt 0 ]]; then
    echo -e "${RED}Blockierte Bugs (brauchen manuelle Hilfe):${NC}"
    jq -r '.bugs[] | select(.blocked == true) | "  - \(.id): \(.title)"' "$SCRIPT_DIR/bugs.json"
    echo ""
fi
