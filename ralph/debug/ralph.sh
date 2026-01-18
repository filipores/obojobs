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
# Safe Library Loading
# ============================================
source_or_fail() {
    local file=$1
    if [[ ! -f "$file" ]]; then
        echo "FATAL: Required library not found: $file" >&2
        exit 1
    fi
    # shellcheck source=/dev/null
    source "$file"
}

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
source_or_fail "$SHARED_LIB/date_utils.sh"
source_or_fail "$SHARED_LIB/logger.sh"
source_or_fail "$SHARED_LIB/circuit_breaker.sh"
source_or_fail "$SHARED_LIB/context_builder.sh"

# Override paths
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# ============================================
# Hilfsfunktionen (DRY)
# ============================================

# JSON-Manipulation mit atomarem Update (vereint beide alten Funktionen)
# Verwendung: update_bugs_json '.filter' oder update_bugs_json --arg x y '.filter'
update_bugs_json() {
    local tmp_file="$SCRIPT_DIR/tasks.json.tmp"
    # Alle Argumente werden an jq weitergegeben
    if jq "$@" "$SCRIPT_DIR/tasks.json" > "$tmp_file"; then
        mv "$tmp_file" "$SCRIPT_DIR/tasks.json"
        return 0
    else
        rm -f "$tmp_file"
        log_error "Fehler beim Aktualisieren von tasks.json"
        return 1
    fi
}

# Zentrale Funktion für Bug-Feld-Abfragen (vermeidet Duplikation)
get_bug_field() {
    local bug_id=$1
    local field=$2
    local default=${3:-0}
    jq -r --arg id "$bug_id" --arg field "$field" --arg default "$default" \
        '.bugs[] | select(.id == $id) | .[$field] // $default' \
        "$SCRIPT_DIR/tasks.json" 2>/dev/null || echo "$default"
}

# Validierung der tasks.json Struktur
validate_bugs_json() {
    local bugs_file="$SCRIPT_DIR/tasks.json"

    if ! jq empty "$bugs_file" 2>/dev/null; then
        log_error "tasks.json ist kein valides JSON"
        return 1
    fi

    if [[ $(jq '.bugs | type' "$bugs_file") != '"array"' ]]; then
        log_error "tasks.json hat kein 'bugs' Array"
        return 1
    fi

    return 0
}

# Effiziente Bug-Statistik (alle Werte in einem jq-Aufruf)
get_bug_stats() {
    jq -r '[
        (.bugs | length),
        ([.bugs[] | select(.fixed == true)] | length),
        ([.bugs[] | select(.fixed == false)] | length)
    ] | @tsv' "$SCRIPT_DIR/tasks.json"
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
    -m, --max-attempts N    Max Fix-Versuche pro Bug (default: $MAX_ITERATIONS)
    --split                 Split-Screen: links Ralph, rechts Claude (benötigt tmux)
    --status                Zeige aktuellen Bug-Status
    --reset                 Reset Debug-State und starte neu
    --add-bug               Interaktiv neuen Bug hinzufügen
    --circuit-status        Zeige Circuit Breaker Status
    --reset-circuit         Reset Circuit Breaker zu CLOSED

Beispiele:
    ./ralph.sh                      # Standard-Ausführung
    ./ralph.sh --split              # Split-Screen mit tmux
    ./ralph.sh --status             # Status anzeigen
    ./ralph.sh --circuit-status     # Circuit Breaker Status

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
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        --split)
            SPLIT_MODE=true
            shift
            ;;
        --status)
            if [[ -f "$SCRIPT_DIR/tasks.json" ]]; then
                echo -e "${BLUE}=== Bug Status ===${NC}"
                read -r total fixed remaining < <(get_bug_stats)
                echo -e "Total:     $total"
                echo -e "Fixed:     ${GREEN}$fixed${NC}"
                echo -e "Remaining: ${YELLOW}$remaining${NC}"
                echo ""
                echo -e "${BLUE}=== Offene Bugs ===${NC}"
                jq -r '.bugs[] | select(.fixed == false) | "[\(.severity)] \(.id): \(.title)"' "$SCRIPT_DIR/tasks.json"
            else
                echo "Keine tasks.json gefunden."
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
        --circuit-status)
            init_circuit_breaker
            show_circuit_status
            exit 0
            ;;
        --reset-circuit)
            reset_circuit_breaker "Manual reset via CLI"
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

            # Add bug to tasks.json
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

            update_bugs_json --argjson bug "$new_bug" '.bugs += [$bug]'
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
    [[ "$MAX_ITERATIONS" != "3" ]] && ralph_cmd+=" --max-attempts $MAX_ITERATIONS"

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

if [[ ! -f "$SCRIPT_DIR/tasks.json" ]]; then
    log_error "Keine tasks.json gefunden in $SCRIPT_DIR"
    echo "Erstelle zuerst eine tasks.json oder nutze --add-bug"
    exit 1
fi

# Validiere tasks.json Struktur
if ! validate_bugs_json; then
    echo "Bitte korrigiere die tasks.json und versuche es erneut"
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
# Circuit Breaker initialisieren
# ============================================
init_circuit_breaker

# ============================================
# Header
# ============================================
echo ""
echo -e "${RED}==========================================${NC}"
echo -e "${RED}       RALF Debug Mode${NC}"
echo -e "${RED}==========================================${NC}"
echo ""
echo -e "Bugs:          ${BLUE}$FIXED_BUGS/$TOTAL_BUGS fixed${NC}"
echo -e "Max Attempts:  ${BLUE}$MAX_ITERATIONS${NC}"
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
    ' "$SCRIPT_DIR/tasks.json"
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
# Gibt "model|true/false" zurück (Pipe-Syntax vermeidet Anti-Pattern)
select_model() {
    local current_bug=$1
    local fix_attempts
    fix_attempts=$(get_bug_field "$current_bug" "fixAttempts" "0")

    if [[ $fix_attempts -ge $FALLBACK_THRESHOLD ]]; then
        echo "${CLAUDE_MODEL_FALLBACK}|true"
    else
        echo "${CLAUDE_MODEL}|false"
    fi
}

# Bug-Details laden (effizient in einem jq-Aufruf)
get_bug_details() {
    local current_bug=$1
    jq -r --arg id "$current_bug" \
        '.bugs[] | select(.id == $id) | "\(.title)\t\(.severity)"' \
        "$SCRIPT_DIR/tasks.json"
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
        update_bugs_json --arg id "$current_bug" '
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

    # Model-Auswahl (Pipe-Syntax: model|using_fallback)
    local current_model using_fallback
    IFS='|' read -r current_model using_fallback < <(select_model "$current_bug")

    if [[ "$using_fallback" == "true" ]]; then
        local fix_attempts
        fix_attempts=$(get_bug_field "$current_bug" "fixAttempts" "0")
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
# Update Status (nutzt generische write_status_json)
# ============================================
update_debug_status() {
    local loop_count=$1
    local current_bug=$2
    local status=$3

    local fixed_bugs=$(jq '[.bugs[] | select(.fixed == true)] | length' "$SCRIPT_DIR/tasks.json" 2>/dev/null || echo "0")

    # Get current model info (set by execute_claude)
    local model_name="${CURRENT_MODEL:-$CLAUDE_MODEL}"
    local is_fallback="${USING_FALLBACK:-false}"

    # Extras für Debug-Mode
    local extras=$(jq -n \
        --arg model "$model_name" \
        --argjson using_fallback "$is_fallback" \
        '{
            model: $model,
            using_fallback: $using_fallback
        }')

    write_status_json "debug" "$status" "$loop_count" "$current_bug" "$fixed_bugs" "$TOTAL_BUGS" "$extras"
}

# ============================================
# Main Loop
# ============================================
loop_count=0

# Cleanup on interrupt
cleanup() {
    log_info "RALF Debug unterbrochen. Cleanup..."
    update_debug_status "$loop_count" "" "interrupted"
    exit 0
}
trap cleanup SIGINT SIGTERM

log_success "Starte RALF Debug Mode Loop..."

while true; do
    loop_count=$((loop_count + 1))

    # Circuit Breaker Check am Anfang jedes Loops
    if should_halt_execution; then
        log_error "Circuit Breaker hat Ausführung gestoppt"
        update_debug_status "$loop_count" "" "circuit_breaker_open"
        break
    fi

    # Get current bug
    current_bug=$(get_current_bug)

    if [[ "$current_bug" == "$STATUS_NONE" ]]; then
        log_success "Alle Bugs gefixt!"
        update_debug_status "$loop_count" "" "complete"
        break
    fi

    # Check fix attempts
    attempts=$(get_bug_field "$current_bug" "fixAttempts" "0")
    if [[ $attempts -ge $MAX_ITERATIONS ]]; then
        log_error "Bug $current_bug: Max Versuche ($MAX_ITERATIONS) erreicht - überspringe"
        # Mark as blocked
        update_bugs_json --arg id "$current_bug" '
            .bugs = [.bugs[] |
                if .id == $id then .blocked = true else . end
            ]'
        continue
    fi

    log_loop "=== Loop #$loop_count - Bug: $current_bug (Versuch $((attempts + 1))/$MAX_ITERATIONS) ==="

    # Update status
    update_debug_status "$loop_count" "$current_bug" "running"

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

            # Update tasks.json with fix info
            update_bugs_json \
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

            update_debug_status "$loop_count" "$current_bug" "success"
            FIXED_BUGS=$((FIXED_BUGS + 1))
            log_info "Bugs fixed: $FIXED_BUGS/$TOTAL_BUGS"
            sleep 3
            ;;
        2)
            log_error "Timeout - versuche erneut"
            update_debug_status "$loop_count" "$current_bug" "timeout"
            sleep 10
            ;;
        3)
            log_warn "Bug blockiert - überspringe"
            update_debug_status "$loop_count" "$current_bug" "blocked"
            sleep 5
            ;;
        *)
            log_warn "Fix nicht erfolgreich - versuche erneut"
            update_debug_status "$loop_count" "$current_bug" "retry"
            sleep 5
            ;;
    esac

    # Circuit Breaker: Stuck Pattern Detection
    # Zähle geänderte Dateien seit letztem Commit
    files_changed=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
    error_msg=""
    [[ $exec_result -ne 0 ]] && error_msg="Exit code: $exec_result"

    check_stuck_pattern "$loop_count" "$current_bug" "$error_msg" "$files_changed"

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
remaining=$(jq '[.bugs[] | select(.fixed == false and .blocked != true)] | length' "$SCRIPT_DIR/tasks.json")
if [[ $remaining -gt 0 ]]; then
    echo -e "${YELLOW}Offene Bugs:${NC}"
    jq -r '.bugs[] | select(.fixed == false and .blocked != true) | "  - \(.id): \(.title)"' "$SCRIPT_DIR/tasks.json"
    echo ""
fi

blocked=$(jq '[.bugs[] | select(.blocked == true)] | length' "$SCRIPT_DIR/tasks.json")
if [[ $blocked -gt 0 ]]; then
    echo -e "${RED}Blockierte Bugs (brauchen manuelle Hilfe):${NC}"
    jq -r '.bugs[] | select(.blocked == true) | "  - \(.id): \(.title)"' "$SCRIPT_DIR/tasks.json"
    echo ""
fi

# Show over-engineered fixes that need review
overengineered=$(jq '[.bugs[] | select(.overEngineeringFlagged == true)] | length' "$SCRIPT_DIR/tasks.json")
if [[ $overengineered -gt 0 ]]; then
    echo -e "${YELLOW}Over-Engineered Fixes (Review empfohlen):${NC}"
    jq -r '.bugs[] | select(.overEngineeringFlagged == true) | "  - \(.id): \(.title)"' "$SCRIPT_DIR/tasks.json"
    echo -e "  ${CYAN}→ Logs: $LOG_DIR/overengineering_review_*.log${NC}"
    echo ""
fi

# Show Opus fallback usage stats
opus_used=$(jq '[.bugs[] | select(.usedFallback == true)] | length' "$SCRIPT_DIR/tasks.json")
if [[ $opus_used -gt 0 ]]; then
    echo -e "${PURPLE}Opus-Fallback verwendet:${NC}"
    jq -r '.bugs[] | select(.usedFallback == true) | "  - \(.id): \(.title)"' "$SCRIPT_DIR/tasks.json"
    echo ""
fi
