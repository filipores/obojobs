#!/bin/bash
# RALF Monitor - Live-Überwachung der RALF-Ausführung
# Zeigt Status, Story, Iteration und Fehler in Echtzeit

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
STATUS_FILE="$LOG_DIR/status.json"
HISTORY_FILE="$LOG_DIR/iteration_history.json"
RATE_LIMIT_FILE="$LOG_DIR/rate_limit.json"
CB_STATE_FILE="$SCRIPT_DIR/.circuit_breaker_state"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Refresh interval in seconds
REFRESH_INTERVAL=${1:-5}

# Clear screen and move cursor to top
clear_screen() {
    printf "\033[2J\033[H"
}

# Draw header
draw_header() {
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║               RALF Feature Mode - Live Monitor                ║${NC}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Get status color
get_status_color() {
    local status=$1
    case $status in
        "running"|"success") echo "${GREEN}" ;;
        "error"|"timeout"|"circuit_open") echo "${RED}" ;;
        "api_limit"|"interrupted") echo "${YELLOW}" ;;
        "complete") echo "${CYAN}" ;;
        *) echo "${NC}" ;;
    esac
}

# Draw main status
draw_status() {
    if [[ ! -f "$STATUS_FILE" ]]; then
        echo -e "${YELLOW}⚠ Kein Status gefunden. RALF läuft nicht.${NC}"
        echo ""
        echo "Starte RALF mit: ./ralph.sh"
        return
    fi

    local status_data=$(cat "$STATUS_FILE" 2>/dev/null)

    local timestamp=$(echo "$status_data" | jq -r '.timestamp // "N/A"')
    local loop_count=$(echo "$status_data" | jq -r '.loop_count // 0')
    local calls_made=$(echo "$status_data" | jq -r '.calls_made_this_hour // 0')
    local max_calls=$(echo "$status_data" | jq -r '.max_calls_per_hour // 50')
    local current_story=$(echo "$status_data" | jq -r '.current_story // "N/A"')
    local status=$(echo "$status_data" | jq -r '.status // "unknown"')
    local started_at=$(echo "$status_data" | jq -r '.started_at // "N/A"')
    local next_reset=$(echo "$status_data" | jq -r '.next_reset // "N/A"')

    local status_color=$(get_status_color "$status")

    echo -e "${BOLD}Status:${NC}         ${status_color}●${NC} ${status^^}"
    echo -e "${BOLD}Aktuelle Story:${NC} ${BLUE}$current_story${NC}"
    echo -e "${BOLD}Loop:${NC}           #$loop_count"
    echo ""

    # Progress bar for rate limit
    local percent=$((calls_made * 100 / max_calls))
    local bar_width=30
    local filled=$((percent * bar_width / 100))
    local empty=$((bar_width - filled))

    local bar_color="${GREEN}"
    if [[ $percent -gt 80 ]]; then
        bar_color="${RED}"
    elif [[ $percent -gt 50 ]]; then
        bar_color="${YELLOW}"
    fi

    echo -e "${BOLD}API Calls:${NC}      $calls_made/$max_calls"
    printf "                [${bar_color}"
    printf "%${filled}s" | tr ' ' '█'
    printf "${NC}"
    printf "%${empty}s" | tr ' ' '░'
    printf "] %d%%\n" $percent

    echo ""
    echo -e "${BOLD}Gestartet:${NC}      $started_at"
    echo -e "${BOLD}Nächster Reset:${NC} $next_reset"
}

# Draw circuit breaker status
draw_circuit_breaker() {
    echo ""
    echo -e "${BOLD}${PURPLE}Circuit Breaker${NC}"
    echo -e "${PURPLE}────────────────${NC}"

    if [[ ! -f "$CB_STATE_FILE" ]]; then
        echo -e "Status: ${GREEN}CLOSED${NC} (Normal)"
        return
    fi

    local cb_data=$(cat "$CB_STATE_FILE" 2>/dev/null)
    local state=$(echo "$cb_data" | jq -r '.state // "CLOSED"')
    local no_progress=$(echo "$cb_data" | jq -r '.consecutive_no_progress // 0')
    local same_error=$(echo "$cb_data" | jq -r '.consecutive_same_error // 0')
    local reason=$(echo "$cb_data" | jq -r '.reason // ""')

    local state_color="${GREEN}"
    case $state in
        "OPEN") state_color="${RED}" ;;
        "HALF_OPEN") state_color="${YELLOW}" ;;
    esac

    echo -e "Status:         ${state_color}$state${NC}"
    echo -e "Ohne Progress:  $no_progress Loops"
    echo -e "Gleicher Error: $same_error mal"

    if [[ -n "$reason" && "$reason" != "null" ]]; then
        echo -e "Grund:          $reason"
    fi
}

# Draw recent history
draw_history() {
    echo ""
    echo -e "${BOLD}${BLUE}Letzte Iterationen${NC}"
    echo -e "${BLUE}──────────────────${NC}"

    if [[ ! -f "$HISTORY_FILE" ]]; then
        echo "Keine History vorhanden."
        return
    fi

    # Show last 5 iterations
    local history=$(jq -r '.[-5:] | reverse | .[] | "\(.loop): \(.story_id) - \(.files_changed) files"' "$HISTORY_FILE" 2>/dev/null)

    if [[ -z "$history" ]]; then
        echo "Keine History vorhanden."
    else
        echo "$history"
    fi
}

# Draw footer
draw_footer() {
    echo ""
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"
    echo -e "Aktualisiert: $(date '+%H:%M:%S') | Refresh: ${REFRESH_INTERVAL}s | ${YELLOW}Ctrl+C${NC} zum Beenden"
}

# Main monitor loop
main() {
    echo "RALF Monitor gestartet (Refresh alle ${REFRESH_INTERVAL}s)"
    echo "Drücke Ctrl+C zum Beenden"
    sleep 1

    while true; do
        clear_screen
        draw_header
        draw_status
        draw_circuit_breaker
        draw_history
        draw_footer

        sleep $REFRESH_INTERVAL
    done
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${GREEN}Monitor beendet.${NC}"; exit 0' SIGINT SIGTERM

# Run main
main
