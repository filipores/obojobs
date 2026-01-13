#!/usr/bin/env bash
# circuit_breaker.sh - Stuck Detection für RALF
# Erkennt und stoppt Infinite Loops

# Source date utilities
CB_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$CB_DIR/date_utils.sh"

# Circuit Breaker States
CB_STATE_CLOSED="CLOSED"        # Normal operation
CB_STATE_HALF_OPEN="HALF_OPEN"  # Monitoring mode
CB_STATE_OPEN="OPEN"            # Failure detected, halted

# State files
CB_STATE_FILE="${SCRIPT_DIR:-.}/.circuit_breaker_state"
CB_HISTORY_FILE="${LOG_DIR:-logs}/iteration_history.json"

# Thresholds (from config or defaults)
CB_NO_PROGRESS_THRESHOLD=${CB_NO_PROGRESS_THRESHOLD:-3}
CB_SAME_ERROR_THRESHOLD=${CB_SAME_ERROR_THRESHOLD:-5}

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Initialize circuit breaker
init_circuit_breaker() {
    if [[ -f "$CB_STATE_FILE" ]]; then
        if ! jq '.' "$CB_STATE_FILE" > /dev/null 2>&1; then
            rm -f "$CB_STATE_FILE"
        fi
    fi

    if [[ ! -f "$CB_STATE_FILE" ]]; then
        cat > "$CB_STATE_FILE" << EOF
{
    "state": "$CB_STATE_CLOSED",
    "last_change": "$(get_iso_timestamp)",
    "consecutive_no_progress": 0,
    "consecutive_same_error": 0,
    "last_progress_loop": 0,
    "total_opens": 0,
    "reason": ""
}
EOF
    fi

    if [[ ! -f "$CB_HISTORY_FILE" ]]; then
        mkdir -p "$(dirname "$CB_HISTORY_FILE")"
        echo '[]' > "$CB_HISTORY_FILE"
    fi
}

# Get current circuit breaker state
get_circuit_state() {
    if [[ ! -f "$CB_STATE_FILE" ]]; then
        echo "$CB_STATE_CLOSED"
        return
    fi

    jq -r '.state' "$CB_STATE_FILE" 2>/dev/null || echo "$CB_STATE_CLOSED"
}

# Check if circuit allows execution
can_execute() {
    local state=$(get_circuit_state)

    if [[ "$state" == "$CB_STATE_OPEN" ]]; then
        return 1
    else
        return 0
    fi
}

# Record loop result and check for stuck patterns
check_stuck_pattern() {
    local loop_number=$1
    local story_id=$2
    local error_message=$3
    local files_changed=$4

    init_circuit_breaker

    # Read current state
    local state_data=$(cat "$CB_STATE_FILE")
    local current_state=$(echo "$state_data" | jq -r '.state')
    local consecutive_no_progress=$(echo "$state_data" | jq -r '.consecutive_no_progress' | tr -d '[:space:]')
    local consecutive_same_error=$(echo "$state_data" | jq -r '.consecutive_same_error' | tr -d '[:space:]')
    local last_progress_loop=$(echo "$state_data" | jq -r '.last_progress_loop' | tr -d '[:space:]')
    local last_error=$(echo "$state_data" | jq -r '.last_error // ""')

    # Ensure integers
    consecutive_no_progress=$((consecutive_no_progress + 0))
    consecutive_same_error=$((consecutive_same_error + 0))
    last_progress_loop=$((last_progress_loop + 0))

    # Check for progress (file changes)
    local has_progress=false
    if [[ $files_changed -gt 0 ]]; then
        has_progress=true
        consecutive_no_progress=0
        last_progress_loop=$loop_number
    else
        consecutive_no_progress=$((consecutive_no_progress + 1))
    fi

    # Check for same error repetition
    if [[ -n "$error_message" && "$error_message" == "$last_error" ]]; then
        consecutive_same_error=$((consecutive_same_error + 1))
    elif [[ -n "$error_message" ]]; then
        consecutive_same_error=1
    else
        consecutive_same_error=0
    fi

    # Record in history
    local history=$(cat "$CB_HISTORY_FILE" 2>/dev/null || echo '[]')
    local entry=$(jq -n \
        --argjson loop "$loop_number" \
        --arg story_id "$story_id" \
        --arg error_message "${error_message:-}" \
        --argjson files_changed "$files_changed" \
        --arg timestamp "$(get_iso_timestamp)" \
        '{
            loop: $loop,
            story_id: $story_id,
            error_message: $error_message,
            files_changed: $files_changed,
            timestamp: $timestamp
        }')
    history=$(echo "$history" | jq ". += [$entry] | .[-50:]")
    echo "$history" > "$CB_HISTORY_FILE"

    # Determine new state
    local new_state="$current_state"
    local reason=""

    case $current_state in
        "$CB_STATE_CLOSED")
            if [[ $consecutive_no_progress -ge $CB_NO_PROGRESS_THRESHOLD ]]; then
                new_state="$CB_STATE_OPEN"
                reason="Kein Fortschritt in $consecutive_no_progress Iterationen"
            elif [[ $consecutive_same_error -ge $CB_SAME_ERROR_THRESHOLD ]]; then
                new_state="$CB_STATE_OPEN"
                reason="Gleicher Fehler $consecutive_same_error mal hintereinander"
            elif [[ $consecutive_no_progress -ge 2 ]]; then
                new_state="$CB_STATE_HALF_OPEN"
                reason="Monitoring: $consecutive_no_progress Loops ohne Fortschritt"
            fi
            ;;

        "$CB_STATE_HALF_OPEN")
            if [[ "$has_progress" == "true" ]]; then
                new_state="$CB_STATE_CLOSED"
                reason="Fortschritt erkannt, Circuit recovered"
            elif [[ $consecutive_no_progress -ge $CB_NO_PROGRESS_THRESHOLD ]]; then
                new_state="$CB_STATE_OPEN"
                reason="Keine Recovery, öffne Circuit nach $consecutive_no_progress Loops"
            fi
            ;;

        "$CB_STATE_OPEN")
            reason="Circuit Breaker ist offen, Ausführung gestoppt"
            ;;
    esac

    # Update state file
    local total_opens=$(echo "$state_data" | jq -r '.total_opens' | tr -d '[:space:]')
    total_opens=$((total_opens + 0))
    if [[ "$new_state" == "$CB_STATE_OPEN" && "$current_state" != "$CB_STATE_OPEN" ]]; then
        total_opens=$((total_opens + 1))
    fi

    cat > "$CB_STATE_FILE" << EOF
{
    "state": "$new_state",
    "last_change": "$(get_iso_timestamp)",
    "consecutive_no_progress": $consecutive_no_progress,
    "consecutive_same_error": $consecutive_same_error,
    "last_progress_loop": $last_progress_loop,
    "total_opens": $total_opens,
    "reason": "$reason",
    "last_error": "$error_message",
    "current_loop": $loop_number
}
EOF

    # Log state transition
    if [[ "$new_state" != "$current_state" ]]; then
        case $new_state in
            "$CB_STATE_OPEN")
                echo -e "${RED}CIRCUIT BREAKER OPENED${NC}"
                echo -e "${RED}Reason: $reason${NC}"
                ;;
            "$CB_STATE_HALF_OPEN")
                echo -e "${YELLOW}CIRCUIT BREAKER: Monitoring Mode${NC}"
                echo -e "${YELLOW}Reason: $reason${NC}"
                ;;
            "$CB_STATE_CLOSED")
                echo -e "${GREEN}CIRCUIT BREAKER: Normal Operation${NC}"
                echo -e "${GREEN}Reason: $reason${NC}"
                ;;
        esac
    fi

    # Return exit code
    if [[ "$new_state" == "$CB_STATE_OPEN" ]]; then
        return 1
    else
        return 0
    fi
}

# Check PRD for same story stuck
check_story_stuck() {
    local prd_file=$1
    local current_story=$2

    if [[ ! -f "$CB_HISTORY_FILE" ]]; then
        return 0
    fi

    # Count how many times same story appears in last 5 iterations
    local count=$(jq "[.[-5:][].story_id] | map(select(. == \"$current_story\")) | length" "$CB_HISTORY_FILE" 2>/dev/null)

    if [[ $count -ge 5 ]]; then
        echo -e "${RED}Story $current_story stuck - 5 Iterationen ohne passes:true${NC}"
        return 1
    fi

    return 0
}

# Display circuit breaker status
show_circuit_status() {
    init_circuit_breaker

    local state_data=$(cat "$CB_STATE_FILE")
    local state=$(echo "$state_data" | jq -r '.state')
    local reason=$(echo "$state_data" | jq -r '.reason')
    local no_progress=$(echo "$state_data" | jq -r '.consecutive_no_progress')
    local same_error=$(echo "$state_data" | jq -r '.consecutive_same_error')
    local last_progress=$(echo "$state_data" | jq -r '.last_progress_loop')
    local current_loop=$(echo "$state_data" | jq -r '.current_loop')
    local total_opens=$(echo "$state_data" | jq -r '.total_opens')

    local color=""
    case $state in
        "$CB_STATE_CLOSED") color=$GREEN ;;
        "$CB_STATE_HALF_OPEN") color=$YELLOW ;;
        "$CB_STATE_OPEN") color=$RED ;;
    esac

    echo -e "${color}======================================${NC}"
    echo -e "${color}     Circuit Breaker Status${NC}"
    echo -e "${color}======================================${NC}"
    echo -e "State:                 $state"
    echo -e "Reason:                $reason"
    echo -e "Loops ohne Progress:   $no_progress"
    echo -e "Gleicher Error:        $same_error mal"
    echo -e "Letzter Progress:      Loop #$last_progress"
    echo -e "Aktueller Loop:        #$current_loop"
    echo -e "Total Opens:           $total_opens"
    echo ""
}

# Reset circuit breaker
reset_circuit_breaker() {
    local reason=${1:-"Manual reset"}

    cat > "$CB_STATE_FILE" << EOF
{
    "state": "$CB_STATE_CLOSED",
    "last_change": "$(get_iso_timestamp)",
    "consecutive_no_progress": 0,
    "consecutive_same_error": 0,
    "last_progress_loop": 0,
    "total_opens": 0,
    "reason": "$reason"
}
EOF

    echo -e "${GREEN}Circuit Breaker reset to CLOSED state${NC}"
}

# Check if should halt execution
should_halt_execution() {
    local state=$(get_circuit_state)

    if [[ "$state" == "$CB_STATE_OPEN" ]]; then
        show_circuit_status
        echo ""
        echo -e "${RED}EXECUTION HALTED: Circuit Breaker Opened${NC}"
        echo ""
        echo -e "${YELLOW}Mögliche Gründe:${NC}"
        echo "  - Projekt ist vielleicht fertig (check prd.json)"
        echo "  - Claude steckt bei einem Fehler fest"
        echo "  - prompt.md braucht Klarstellung"
        echo ""
        echo -e "${YELLOW}Um fortzufahren:${NC}"
        echo "  1. Logs prüfen: tail -20 logs/ralph.log"
        echo "  2. Claude Output: ls -lt logs/claude_output_*.log | head -1"
        echo "  3. prd.json und prompt.md aktualisieren"
        echo "  4. Circuit reset: ./ralph.sh --reset-circuit"
        echo ""
        return 0  # Signal to halt
    else
        return 1  # Can continue
    fi
}

# Export functions
export -f init_circuit_breaker
export -f get_circuit_state
export -f can_execute
export -f check_stuck_pattern
export -f check_story_stuck
export -f show_circuit_status
export -f reset_circuit_breaker
export -f should_halt_execution
