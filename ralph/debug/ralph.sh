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

# ============================================
# Konstanten (Magic Strings vermeiden)
# ============================================
readonly STATUS_NONE="NONE"
readonly STATUS_FIX_SUCCESSFUL="FIX_SUCCESSFUL: true"
readonly STATUS_BLOCKED="STATUS: BLOCKED"

# Exit-Codes für execute_claude
readonly EXIT_SUCCESS=0
readonly EXIT_FIX_FAILED=1
readonly EXIT_TIMEOUT=2
readonly EXIT_BLOCKED=3

# Source shared libraries (from parent lib/)
SHARED_LIB="$SCRIPT_DIR/../lib"
source "$SHARED_LIB/date_utils.sh"
source "$SHARED_LIB/logger.sh"
source "$SHARED_LIB/circuit_breaker.sh"
source "$SHARED_LIB/context_builder.sh"

# Override paths
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# ============================================
# Hilfsfunktionen (DRY)
# ============================================

# JSON-Manipulation mit atomarem Update
update_bugs_json() {
    local jq_filter="$1"
    local tmp_file="$SCRIPT_DIR/bugs.json.tmp"
    if jq "$jq_filter" "$SCRIPT_DIR/bugs.json" > "$tmp_file"; then
        mv "$tmp_file" "$SCRIPT_DIR/bugs.json"
        return 0
    else
        rm -f "$tmp_file"
        log_error "Fehler beim Aktualisieren von bugs.json"
        return 1
    fi
}

# JSON-Manipulation mit Argumenten
update_bugs_json_with_args() {
    local tmp_file="$SCRIPT_DIR/bugs.json.tmp"
    # Alle Argumente werden an jq weitergegeben
    if jq "$@" "$SCRIPT_DIR/bugs.json" > "$tmp_file"; then
        mv "$tmp_file" "$SCRIPT_DIR/bugs.json"
        return 0
    else
        rm -f "$tmp_file"
        log_error "Fehler beim Aktualisieren von bugs.json"
        return 1
    fi
}

# Effiziente Bug-Statistik (alle Werte in einem jq-Aufruf)
get_bug_stats() {
    jq -r '[
        (.bugs | length),
        ([.bugs[] | select(.fixed == true)] | length),
        ([.bugs[] | select(.fixed == false)] | length)
    ] | @tsv' "$SCRIPT_DIR/bugs.json"
}

# Session tracking
RALPH_STARTED_AT=$(get_iso_timestamp)
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
    --split                 Split-Screen: links Ralph, rechts Claude (benötigt tmux)
    --status                Zeige aktuellen Bug-Status
    --reset                 Reset Debug-State und starte neu
    --add-bug               Interaktiv neuen Bug hinzufügen

Beispiele:
    ./ralph.sh                      # Standard-Ausführung
    ./ralph.sh --split              # Split-Screen mit tmux
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
        --split)
            SPLIT_MODE=true
            shift
            ;;
        --status)
            if [[ -f "$SCRIPT_DIR/bugs.json" ]]; then
                echo -e "${BLUE}=== Bug Status ===${NC}"
                read -r total fixed remaining < <(get_bug_stats)
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
            update_bugs_json '.bugs = [.bugs[] | .fixed = false | .fixAttempts = 0]'
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

            update_bugs_json_with_args --argjson bug "$new_bug" '.bugs += [$bug]'
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
# Split Mode (tmux)
# ============================================
launch_split_mode() {
    if ! command -v tmux &>/dev/null; then
        echo -e "${RED}Error: tmux ist nicht installiert${NC}"
        echo "Installation: brew install tmux (macOS) oder sudo apt install tmux (Ubuntu)"
        exit 1
    fi

    mkdir -p "$SCRIPT_DIR/logs"
    LIVE_LOG_FILE="$SCRIPT_DIR/logs/claude_live.log"
    > "$LIVE_LOG_FILE"

    local session_name="ralph-debug-$$"
    local ralph_cmd="$SCRIPT_DIR/ralph.sh"
    [[ "$TIMEOUT_MINUTES" != "15" ]] && ralph_cmd+=" --timeout $TIMEOUT_MINUTES"
    [[ "$MAX_FIX_ATTEMPTS" != "3" ]] && ralph_cmd+=" --max-attempts $MAX_FIX_ATTEMPTS"

    export RALPH_LIVE_LOG="$LIVE_LOG_FILE"
    export RALPH_IN_SPLIT_MODE=true

    echo -e "${CYAN}Starte Split-Screen Mode...${NC}"

    tmux new-session -d -s "$session_name" -x 200 -y 50
    tmux send-keys -t "$session_name" "cd '$PROJECT_ROOT' && RALPH_LIVE_LOG='$LIVE_LOG_FILE' RALPH_IN_SPLIT_MODE=true $ralph_cmd" C-m
    tmux split-window -h -t "$session_name"
    tmux send-keys -t "$session_name" "echo -e '${RED}═══════════════════════════════════════${NC}' && echo -e '${RED}       Claude Live Output${NC}' && echo -e '${RED}═══════════════════════════════════════${NC}' && echo '' && tail -f '$LIVE_LOG_FILE'" C-m
    tmux attach-session -t "$session_name"
    exit 0
}

if [[ "$SPLIT_MODE" == "true" && "$RALPH_IN_SPLIT_MODE" != "true" ]]; then
    launch_split_mode
fi

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
# Bug Info (effizient mit einem jq-Aufruf)
# ============================================
read -r TOTAL_BUGS FIXED_BUGS _remaining < <(get_bug_stats)

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
if [[ "$RALPH_IN_SPLIT_MODE" == "true" ]]; then
    echo -e "Split-Mode:    ${PURPLE}AKTIV - Claude Output im rechten Pane${NC}"
fi
echo ""
echo -e "${RED}==========================================${NC}"
echo ""

# ============================================
# Get Current Bug
# ============================================
get_current_bug() {
    # Find first bug with fixed: false, ordered by severity (critical > major > minor > trivial)
    jq -r --arg none "$STATUS_NONE" '
        .bugs
        | map(select(.fixed == false))
        | sort_by(
            if .severity == "critical" then 0
            elif .severity == "major" then 1
            elif .severity == "minor" then 2
            else 3 end
        )
        | .[0].id // $none
    ' "$SCRIPT_DIR/bugs.json"
}

# ============================================
# Code Simplifier (bei großen Änderungen)
# ============================================
check_overengineering() {
    local bug_id=$1

    # Skip if disabled
    if [[ "$OVERENGINEERING_CHECK_ENABLED" != "true" ]]; then
        return 0
    fi

    # Get lines changed
    local lines_changed=$(git diff --numstat 2>/dev/null | awk '{sum += $1 + $2} END {print sum+0}')

    if [[ $lines_changed -le $OVERENGINEERING_THRESHOLD ]]; then
        log_info "Änderungen: ${lines_changed} Zeilen (OK)"
        return 0
    fi

    log_warn "Änderungen: ${lines_changed} Zeilen - starte Code-Simplifier"

    local review_output="$LOG_DIR/simplifier_${bug_id}.log"

    # Run code simplifier with direct prompt
    if claude --model "$CLAUDE_MODEL_FALLBACK" \
        -p "Analysiere und ggf. vereinfache den zuletzt geänderten Code mit dem code-simplifier Agenten." \
        > "$review_output" 2>&1; then
        log_success "Code-Simplifier abgeschlossen"
    else
        log_warn "Code-Simplifier fehlgeschlagen"
    fi

    return 0
}

# ============================================
# Execute Claude - Aufgeteilt in Hilfsfunktionen
# ============================================

# Model-Auswahl basierend auf Fehlversuchen
select_model() {
    local current_bug=$1
    local fix_attempts
    fix_attempts=$(jq -r --arg id "$current_bug" \
        '[.bugs[] | select(.id == $id) | .fixAttempts // 0] | first // 0' \
        "$SCRIPT_DIR/bugs.json") || fix_attempts=0

    if [[ $fix_attempts -ge $FALLBACK_THRESHOLD ]]; then
        echo "$CLAUDE_MODEL_FALLBACK"
        return 1  # Signal: Fallback verwendet
    else
        echo "$CLAUDE_MODEL_IMPL"
        return 0  # Signal: Standard-Model
    fi
}

# Bug-Details laden (effizient in einem jq-Aufruf)
get_bug_details() {
    local current_bug=$1
    jq -r --arg id "$current_bug" \
        '.bugs[] | select(.id == $id) | "\(.title)\t\(.severity)"' \
        "$SCRIPT_DIR/bugs.json"
}

# Claude-Kommando ausführen (mit sicherem Array für Timeout)
run_claude_command() {
    local current_model=$1
    local context=$2
    local output_file=$3
    local output_format=$4
    local timeout_seconds=$((TIMEOUT_MINUTES * 60))

    # Sichere Array-basierte Timeout-Behandlung
    local timeout_cmd=()
    if [[ -n "$TIMEOUT_CMD" ]]; then
        timeout_cmd=("$TIMEOUT_CMD" "${timeout_seconds}s")
    fi

    "${timeout_cmd[@]}" claude \
        --model "$current_model" \
        --output-format "$output_format" \
        --allowedTools "$CLAUDE_ALLOWED_TOOLS" \
        --append-system-prompt "$context" \
        -p "$(cat "$SCRIPT_DIR/prompt.md")"
}

# Ergebnis der Claude-Ausführung analysieren
parse_claude_result() {
    local output_file=$1
    local current_bug=$2

    if grep -q "$STATUS_FIX_SUCCESSFUL" "$output_file" 2>/dev/null; then
        log_success "Bug $current_bug erfolgreich gefixt!"
        return $EXIT_SUCCESS
    elif grep -q "$STATUS_BLOCKED" "$output_file" 2>/dev/null; then
        log_warn "Bug $current_bug blockiert"
        return $EXIT_BLOCKED
    else
        log_warn "Bug $current_bug noch nicht gefixt"
        # Increment fix attempts
        update_bugs_json_with_args --arg id "$current_bug" '
            .bugs = [.bugs[] |
                if .id == $id then .fixAttempts += 1 else . end
            ]'
        return $EXIT_FIX_FAILED
    fi
}

# Haupt-Ausführungsfunktion (jetzt schlanker)
execute_claude() {
    local loop_count=$1
    local current_bug=$2

    local timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local output_file="$LOG_DIR/debug_output_${current_bug}_${timestamp}.log"

    # Model-Auswahl
    local current_model
    current_model=$(select_model "$current_bug")
    local using_fallback=$([[ $? -eq 1 ]] && echo "true" || echo "false")

    if [[ "$using_fallback" == "true" ]]; then
        local fix_attempts
        fix_attempts=$(jq -r --arg id "$current_bug" \
            '[.bugs[] | select(.id == $id) | .fixAttempts // 0] | first // 0' \
            "$SCRIPT_DIR/bugs.json")
        log_warn "Wechsle zu Opus (Fallback nach $fix_attempts Fehlversuchen)"
    fi

    # Export für Status-Tracking
    export CURRENT_MODEL="$current_model"
    export USING_FALLBACK="$using_fallback"

    log_loop "Starte Claude Code für Bug: $current_bug (${current_model##*-})"

    # Bug-Details laden
    local bug_details bug_title bug_severity
    IFS=$'\t' read -r bug_title bug_severity < <(get_bug_details "$current_bug")

    # Kontext aufbauen
    local relevant_files file_context
    relevant_files=$(get_bug_context "$current_bug")
    file_context=$(build_context_string "$relevant_files")

    local context="RALF Debug Mode - Loop #${loop_count}. Fixing Bug: ${current_bug} (${bug_severity}): ${bug_title}
${file_context}"

    # Ausführung basierend auf Modus
    local exec_result=0

    if [[ "$RALPH_IN_SPLIT_MODE" == "true" && -n "$RALPH_LIVE_LOG" ]]; then
        # Split-Modus: Header für Live-Log
        {
            echo ""
            echo "═══════════════════════════════════════"
            echo " Bug: $current_bug ($bug_severity)"
            echo " $(date '+%H:%M:%S')"
            echo "═══════════════════════════════════════"
            echo ""
        } >> "$RALPH_LIVE_LOG"

        if run_claude_command "$current_model" "$context" "$output_file" "stream-json" \
            2>&1 | tee -a "$RALPH_LIVE_LOG" > "$output_file"; then
            exec_result=0
        else
            exec_result=$?
        fi

        echo -e "\n─────────────────────────────────────────" >> "$RALPH_LIVE_LOG"
    else
        # Normal-Modus
        if run_claude_command "$current_model" "$context" "$output_file" "json" \
            > "$output_file" 2>&1; then
            exec_result=0
        else
            exec_result=$?
        fi
    fi

    # Ergebnis auswerten
    if [[ $exec_result -eq 0 ]]; then
        log_success "Claude Code Ausführung abgeschlossen"
        parse_claude_result "$output_file" "$current_bug"
        return $?
    else
        if [[ $exec_result -eq 124 ]]; then
            log_error "Timeout nach $TIMEOUT_MINUTES Minuten!"
            return $EXIT_TIMEOUT
        fi
        log_error "Claude Code Ausführung fehlgeschlagen"
        return $EXIT_FIX_FAILED
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

    # Get current model info (set by execute_claude)
    local model_name="${CURRENT_MODEL:-$CLAUDE_MODEL_IMPL}"
    local is_fallback="${USING_FALLBACK:-false}"

    cat > "$LOG_DIR/status.json" << EOF
{
    "mode": "debug",
    "status": "$status",
    "loop": $loop_count,
    "current_bug": "$current_bug",
    "bugs_fixed": $FIXED_BUGS,
    "bugs_total": $TOTAL_BUGS,
    "model": "$model_name",
    "using_fallback": $is_fallback,
    "started_at": "$RALPH_STARTED_AT",
    "updated_at": "$(get_iso_timestamp)"
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

    if [[ "$current_bug" == "$STATUS_NONE" ]]; then
        log_success "Alle Bugs gefixt!"
        update_status "$loop_count" "" "complete"
        break
    fi

    # Check fix attempts (use first match to avoid duplicates)
    attempts=$(jq -r --arg id "$current_bug" '[.bugs[] | select(.id == $id) | .fixAttempts] | first // 0' "$SCRIPT_DIR/bugs.json")
    if [[ $attempts -ge $MAX_FIX_ATTEMPTS ]]; then
        log_error "Bug $current_bug: Max Versuche ($MAX_FIX_ATTEMPTS) erreicht - überspringe"
        # Mark as blocked
        update_bugs_json_with_args --arg id "$current_bug" '
            .bugs = [.bugs[] |
                if .id == $id then .blocked = true else . end
            ]'
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
            # Success - mark bug as fixed and record model used
            if [[ "$USING_FALLBACK" == "true" ]]; then
                log_success "Bug $current_bug gefixt (mit Opus Fallback)"
            else
                log_success "Bug $current_bug gefixt"
            fi

            # Run Over-Engineering Check before committing
            check_overengineering "$current_bug"
            oe_result=$?
            oe_flagged="false"
            [[ $oe_result -ne 0 ]] && oe_flagged="true"

            # Update bugs.json with fix info
            update_bugs_json_with_args \
                --arg id "$current_bug" \
                --arg model "$CURRENT_MODEL" \
                --argjson fallback "$USING_FALLBACK" \
                --argjson oe_flagged "$oe_flagged" \
                '.bugs = [.bugs[] |
                    if .id == $id then
                        .fixed = true |
                        .fixedAt = now |
                        .fixedWithModel = $model |
                        .usedFallback = $fallback |
                        .overEngineeringFlagged = $oe_flagged
                    else . end
                ]'

            if [[ $oe_result -ne 0 ]]; then
                log_warn "Fix wurde als Over-Engineered markiert - bitte manuell prüfen"
            fi

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

# Show over-engineered fixes that need review
overengineered=$(jq '[.bugs[] | select(.overEngineeringFlagged == true)] | length' "$SCRIPT_DIR/bugs.json")
if [[ $overengineered -gt 0 ]]; then
    echo -e "${YELLOW}Over-Engineered Fixes (Review empfohlen):${NC}"
    jq -r '.bugs[] | select(.overEngineeringFlagged == true) | "  - \(.id): \(.title)"' "$SCRIPT_DIR/bugs.json"
    echo -e "  ${CYAN}→ Logs: $LOG_DIR/overengineering_review_*.log${NC}"
    echo ""
fi

# Show Opus fallback usage stats
opus_used=$(jq '[.bugs[] | select(.usedFallback == true)] | length' "$SCRIPT_DIR/bugs.json")
if [[ $opus_used -gt 0 ]]; then
    echo -e "${PURPLE}Opus-Fallback verwendet:${NC}"
    jq -r '.bugs[] | select(.usedFallback == true) | "  - \(.id): \(.title)"' "$SCRIPT_DIR/bugs.json"
    echo ""
fi
