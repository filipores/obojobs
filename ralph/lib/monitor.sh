#!/usr/bin/env bash
# =============================================================================
# RALPH Monitor - Generic Live Monitoring for All Modes
# =============================================================================
# Shows status, current task, progress and errors in real-time
# Works with all Ralph modes (feature, debug, test, explore)
#
# Usage:
#   ./monitor.sh [MODE] [REFRESH_INTERVAL]
#
# Examples:
#   ./monitor.sh                  # Auto-detect mode, 5s refresh
#   ./monitor.sh feature          # Feature mode monitor
#   ./monitor.sh debug 3          # Debug mode, 3s refresh
#   ./monitor.sh --all            # All modes simultaneously
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RALPH_ROOT="$SCRIPT_DIR/.."

# Load colors
source "$SCRIPT_DIR/colors.sh"

# =============================================================================
# Configuration
# =============================================================================
REFRESH_INTERVAL=5
MONITOR_MODE=""
SHOW_ALL=false

# Modes and their display names
declare -A MODE_NAMES=(
    ["feature"]="Feature Mode"
    ["debug"]="Debug Mode"
    ["test"]="Test Mode"
    ["explore"]="Explore Mode"
)

declare -A MODE_COLORS=(
    ["feature"]="$CYAN"
    ["debug"]="$RED"
    ["test"]="$GREEN"
    ["explore"]="$PURPLE"
)

# =============================================================================
# Argument Parsing
# =============================================================================
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --all)
                SHOW_ALL=true
                shift
                ;;
            feature|debug|test|explore)
                MONITOR_MODE="$1"
                shift
                ;;
            [0-9]*)
                REFRESH_INTERVAL="$1"
                shift
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
RALPH Monitor - Live Monitoring for All Modes

Usage: ./monitor.sh [MODE] [REFRESH_INTERVAL]

Modes:
  feature     Feature mode (implement user stories)
  debug       Debug mode (fix bugs)
  test        Test mode (exploratory UI tests)
  explore     Explore mode (explore app)

Options:
  --all       Show all modes simultaneously
  -h, --help  Show this help
  [NUMBER]    Refresh interval in seconds (default: 5)

Examples:
  ./monitor.sh                  # Auto-detect active mode
  ./monitor.sh feature          # Only feature mode
  ./monitor.sh debug 3          # Debug mode, 3s refresh
  ./monitor.sh --all            # All modes
EOF
}

# =============================================================================
# Helper Functions
# =============================================================================
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

get_status_icon() {
    local status=$1
    case $status in
        "running") echo "▶" ;;
        "success"|"complete") echo "✓" ;;
        "error") echo "✗" ;;
        "timeout") echo "⏱" ;;
        "circuit_open") echo "⚡" ;;
        "api_limit") echo "⚠" ;;
        "interrupted") echo "⏸" ;;
        *) echo "●" ;;
    esac
}

# Draw progress bar
# Returns false if no progress bar can be drawn
draw_progress_bar() {
    local completed=$1
    local total=$2
    local width=${3:-30}
    local label=${4:-"Progress"}

    # For total=0 no progress bar (e.g. Explore mode)
    if [[ $total -eq 0 ]]; then
        printf "${BOLD}%-12s${NC} %d (endless)\n" "$label:" "$completed"
        return 1
    fi

    local percent=$((completed * 100 / total))
    local filled=$((percent * width / 100))
    local empty=$((width - filled))

    local bar_color="${GREEN}"
    if [[ $percent -lt 30 ]]; then
        bar_color="${RED}"
    elif [[ $percent -lt 70 ]]; then
        bar_color="${YELLOW}"
    fi

    printf "${BOLD}%-12s${NC} [${bar_color}" "$label:"
    printf "%${filled}s" | tr ' ' '█'
    printf "${NC}"
    printf "%${empty}s" | tr ' ' '░'
    printf "] %d/%d (%d%%)\n" "$completed" "$total" "$percent"
    return 0
}

# Rate limit bar (inverted - shows usage)
draw_rate_limit_bar() {
    local used=$1
    local max=$2
    local width=${3:-30}

    if [[ $max -eq 0 ]]; then
        max=1
    fi

    local percent=$((used * 100 / max))
    local filled=$((percent * width / 100))
    local empty=$((width - filled))

    local bar_color="${GREEN}"
    if [[ $percent -gt 80 ]]; then
        bar_color="${RED}"
    elif [[ $percent -gt 50 ]]; then
        bar_color="${YELLOW}"
    fi

    printf "${BOLD}%-12s${NC} [${bar_color}" "API Calls:"
    printf "%${filled}s" | tr ' ' '█'
    printf "${NC}"
    printf "%${empty}s" | tr ' ' '░'
    printf "] %d/%d (%d%%)\n" "$used" "$max" "$percent"
}

# =============================================================================
# Status Reading
# =============================================================================
read_status() {
    local mode=$1
    local status_file="$RALPH_ROOT/$mode/logs/status.json"

    if [[ ! -f "$status_file" ]]; then
        echo "{}"
        return
    fi

    cat "$status_file" 2>/dev/null || echo "{}"
}

read_circuit_breaker() {
    local mode=$1
    local cb_file="$RALPH_ROOT/$mode/logs/.circuit_breaker_state"

    if [[ ! -f "$cb_file" ]]; then
        echo '{"state": "CLOSED"}'
        return
    fi

    cat "$cb_file" 2>/dev/null || echo '{"state": "CLOSED"}'
}

read_history() {
    local mode=$1
    local history_file="$RALPH_ROOT/$mode/logs/history.json"

    if [[ ! -f "$history_file" ]]; then
        echo "[]"
        return
    fi

    cat "$history_file" 2>/dev/null || echo "[]"
}

# =============================================================================
# Drawing Functions
# =============================================================================
clear_screen() {
    printf "\033[2J\033[H"
}

draw_header() {
    local mode=$1
    local color=${MODE_COLORS[$mode]:-$CYAN}
    local name=${MODE_NAMES[$mode]:-"Unknown Mode"}

    echo -e "${BOLD}${color}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${color}║             RALPH $name - Live Monitor                ║${NC}"
    echo -e "${BOLD}${color}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

draw_multi_header() {
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║               RALPH Monitor - All Modes                        ║${NC}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

draw_mode_status() {
    local mode=$1
    local status_data=$(read_status "$mode")
    local color=${MODE_COLORS[$mode]:-$NC}
    local name=${MODE_NAMES[$mode]:-"Unknown"}

    # Check if status exists
    if [[ "$status_data" == "{}" ]]; then
        echo -e "${color}━━━ $name ━━━${NC}"
        echo -e "  ${YELLOW}⚠ Not active${NC}"
        echo ""
        return
    fi

    # Parse status
    local status=$(echo "$status_data" | jq -r '.status // "unknown"')
    local loop=$(echo "$status_data" | jq -r '.loop // 0')
    local current_task=$(echo "$status_data" | jq -r '.current_task // "N/A"')
    local progress_completed=$(echo "$status_data" | jq -r '.progress.completed // 0')
    local progress_total=$(echo "$status_data" | jq -r '.progress.total // 0')
    local started_at=$(echo "$status_data" | jq -r '.started_at // "N/A"')
    local updated_at=$(echo "$status_data" | jq -r '.updated_at // "N/A"')

    local status_color=$(get_status_color "$status")
    local status_icon=$(get_status_icon "$status")

    # Header for this mode
    echo -e "${color}━━━ $name ━━━${NC}"

    # Basic info
    echo -e "  ${BOLD}Status:${NC}       ${status_color}${status_icon} ${status^^}${NC}"
    echo -e "  ${BOLD}Loop:${NC}         #$loop"
    echo -e "  ${BOLD}Task:${NC}         ${BLUE}$current_task${NC}"

    # Progress bar
    printf "  "
    draw_progress_bar "$progress_completed" "$progress_total" 25 "Progress"

    # Mode-specific extras
    case $mode in
        feature)
            local calls_made=$(echo "$status_data" | jq -r '.calls_made_this_hour // 0')
            local max_calls=$(echo "$status_data" | jq -r '.max_calls_per_hour // 50')
            local next_reset=$(echo "$status_data" | jq -r '.next_reset // "N/A"')
            printf "  "
            draw_rate_limit_bar "$calls_made" "$max_calls" 25
            echo -e "  ${BOLD}Reset:${NC}        $next_reset"
            ;;
        debug)
            local model=$(echo "$status_data" | jq -r '.model // "N/A"')
            local fallback=$(echo "$status_data" | jq -r '.using_fallback // false')
            echo -e "  ${BOLD}Model:${NC}        $model"
            if [[ "$fallback" == "true" ]]; then
                echo -e "  ${BOLD}Fallback:${NC}     ${YELLOW}Active${NC}"
            fi
            ;;
        explore)
            local bugs=$(echo "$status_data" | jq -r '.bugs_found // 0')
            local sugg=$(echo "$status_data" | jq -r '.suggestions_found // 0')
            local pages=$(echo "$status_data" | jq -r '.pages_explored // 0')
            echo -e "  ${BOLD}Bugs:${NC}         ${RED}$bugs${NC} | ${BOLD}Suggestions:${NC} ${GREEN}$sugg${NC} | ${BOLD}Pages:${NC} $pages"
            ;;
        test)
            # Test-specific infos are already in progress
            ;;
    esac

    echo -e "  ${BOLD}Started:${NC}      $started_at"
    echo ""
}

draw_circuit_breaker() {
    local mode=$1
    local cb_data=$(read_circuit_breaker "$mode")

    local state=$(echo "$cb_data" | jq -r '.state // "CLOSED"')
    local no_progress=$(echo "$cb_data" | jq -r '.consecutive_no_progress // 0')
    local same_error=$(echo "$cb_data" | jq -r '.consecutive_same_error // 0')
    local reason=$(echo "$cb_data" | jq -r '.reason // ""')

    local state_color="${GREEN}"
    case $state in
        "OPEN") state_color="${RED}" ;;
        "HALF_OPEN") state_color="${YELLOW}" ;;
    esac

    echo -e "${BOLD}${PURPLE}Circuit Breaker${NC}"
    echo -e "${PURPLE}────────────────${NC}"
    echo -e "Status:         ${state_color}$state${NC}"
    echo -e "No Progress:    $no_progress loops"
    echo -e "Same Error:     $same_error times"

    if [[ -n "$reason" && "$reason" != "null" ]]; then
        echo -e "Reason:         $reason"
    fi
}

draw_history() {
    local mode=$1
    local history=$(read_history "$mode")

    echo ""
    echo -e "${BOLD}${BLUE}Recent Iterations${NC}"
    echo -e "${BLUE}──────────────────${NC}"

    if [[ "$history" == "[]" ]]; then
        echo "No history available."
        return
    fi

    # Show last 5 entries
    echo "$history" | jq -r '.[-5:] | reverse | .[] | "Loop \(.loop): \(.story_id // .task_id // "N/A") - \(.files_changed // 0) files (\(.status // "?"))"' 2>/dev/null || echo "No history available."
}

draw_footer() {
    echo ""
    echo -e "${CYAN}────────────────────────────────────────────────────────────────${NC}"
    echo -e "Updated: $(date '+%H:%M:%S') | Refresh: ${REFRESH_INTERVAL}s | ${YELLOW}Ctrl+C${NC} to exit"
}

# =============================================================================
# Auto-Detect Active Mode
# =============================================================================
detect_active_mode() {
    local most_recent=""
    local most_recent_time=0

    for mode in feature debug test explore; do
        local status_file="$RALPH_ROOT/$mode/logs/status.json"
        if [[ -f "$status_file" ]]; then
            local updated=$(stat -f %m "$status_file" 2>/dev/null || stat -c %Y "$status_file" 2>/dev/null || echo "0")
            if [[ $updated -gt $most_recent_time ]]; then
                most_recent_time=$updated
                most_recent=$mode
            fi
        fi
    done

    echo "$most_recent"
}

# =============================================================================
# Main Monitor Loops
# =============================================================================
monitor_single_mode() {
    local mode=$1

    while true; do
        clear_screen
        draw_header "$mode"
        draw_mode_status "$mode"
        draw_circuit_breaker "$mode"
        draw_history "$mode"
        draw_footer
        sleep "$REFRESH_INTERVAL"
    done
}

monitor_all_modes() {
    while true; do
        clear_screen
        draw_multi_header

        for mode in feature debug test explore; do
            draw_mode_status "$mode"
        done

        draw_footer
        sleep "$REFRESH_INTERVAL"
    done
}

# =============================================================================
# Main
# =============================================================================
main() {
    parse_args "$@"

    echo "RALPH Monitor started (refresh every ${REFRESH_INTERVAL}s)"
    echo "Press Ctrl+C to exit"
    sleep 1

    if [[ "$SHOW_ALL" == "true" ]]; then
        monitor_all_modes
    elif [[ -n "$MONITOR_MODE" ]]; then
        monitor_single_mode "$MONITOR_MODE"
    else
        # Auto-detect
        local detected=$(detect_active_mode)
        if [[ -n "$detected" ]]; then
            echo "Auto-detected active mode: $detected"
            sleep 1
            monitor_single_mode "$detected"
        else
            echo "No active mode found. Showing all modes..."
            sleep 1
            monitor_all_modes
        fi
    fi
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${GREEN}Monitor stopped.${NC}"; exit 0' SIGINT SIGTERM

main "$@"
