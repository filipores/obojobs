#!/usr/bin/env bash
# logger.sh - Structured Logging for RALPH
# Shared library for all Ralph modes
# Writes to $LOG_DIR/ralph.log and $LOG_DIR/status.json

# Source shared libraries from same directory
_LOGGER_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$_LOGGER_DIR/date_utils.sh"
source "$_LOGGER_DIR/colors.sh"

# Log function with timestamps and colors
log_info() {
    local message=$1
    local timestamp=$(get_basic_timestamp)
    echo -e "${BLUE}[$timestamp] [INFO] $message${NC}"
    echo "[$timestamp] [INFO] $message" >> "$LOG_DIR/ralph.log"
}

log_error() {
    local message=$1
    local timestamp=$(get_basic_timestamp)
    echo -e "${RED}[$timestamp] [ERROR] $message${NC}"
    echo "[$timestamp] [ERROR] $message" >> "$LOG_DIR/ralph.log"
}

log_warn() {
    local message=$1
    local timestamp=$(get_basic_timestamp)
    echo -e "${YELLOW}[$timestamp] [WARN] $message${NC}"
    echo "[$timestamp] [WARN] $message" >> "$LOG_DIR/ralph.log"
}

log_success() {
    local message=$1
    local timestamp=$(get_basic_timestamp)
    echo -e "${GREEN}[$timestamp] [SUCCESS] $message${NC}"
    echo "[$timestamp] [SUCCESS] $message" >> "$LOG_DIR/ralph.log"
}

log_loop() {
    local message=$1
    local timestamp=$(get_basic_timestamp)
    echo -e "${PURPLE}[$timestamp] [LOOP] $message${NC}"
    echo "[$timestamp] [LOOP] $message" >> "$LOG_DIR/ralph.log"
}

# Log iteration details
log_iteration() {
    local loop_number=$1
    local story_id=$2
    local status=$3
    local files_changed=$4

    local timestamp=$(get_iso_timestamp)

    # Append to history
    local history_file="$LOG_DIR/history.json"

    if [[ ! -f "$history_file" ]]; then
        echo '[]' > "$history_file"
    fi

    local entry=$(jq -n \
        --arg timestamp "$timestamp" \
        --argjson loop "$loop_number" \
        --arg story_id "$story_id" \
        --arg status "$status" \
        --argjson files_changed "$files_changed" \
        '{
            timestamp: $timestamp,
            loop: $loop,
            story_id: $story_id,
            status: $status,
            files_changed: $files_changed
        }')

    # Keep only last MAX_HISTORY_ENTRIES entries
    local max_entries=${MAX_HISTORY_ENTRIES:-50}
    local history=$(cat "$history_file")
    history=$(echo "$history" | jq ". += [$entry] | .[-${max_entries}:]")
    echo "$history" > "$history_file"
}

# =============================================================================
# Generic Status Function for All Modes
# =============================================================================
# Unified JSON format for monitor compatibility
#
# Required fields (all modes):
#   - mode: feature|debug|test|explore
#   - status: running|complete|error|timeout|circuit_open|interrupted|api_limit
#   - loop: Current loop number
#   - current_task: Current task (Story/Bug/Feature)
#   - progress_completed: Completed tasks
#   - progress_total: Total tasks
#   - started_at: ISO timestamp
#   - updated_at: ISO timestamp
#
# Optional fields (mode-specific):
#   - extras: JSON object with additional fields
# =============================================================================

write_status_json() {
    local mode=$1
    local status=$2
    local loop=$3
    local current_task=$4
    local progress_completed=$5
    local progress_total=$6
    local extras="${7:-{}}"  # Optional: JSON object with extra fields

    mkdir -p "$LOG_DIR"

    # Validate extras as valid JSON, fallback to empty object
    if ! echo "$extras" | jq . >/dev/null 2>&1; then
        extras="{}"
    fi

    jq -n \
        --arg mode "$mode" \
        --arg status "$status" \
        --argjson loop "$loop" \
        --arg current_task "$current_task" \
        --argjson progress_completed "$progress_completed" \
        --argjson progress_total "$progress_total" \
        --arg started_at "${RALPH_STARTED_AT:-$(get_iso_timestamp)}" \
        --arg updated_at "$(get_iso_timestamp)" \
        --argjson extras "$extras" \
        '{
            mode: $mode,
            status: $status,
            loop: $loop,
            current_task: $current_task,
            progress: {
                completed: $progress_completed,
                total: $progress_total
            },
            started_at: $started_at,
            updated_at: $updated_at
        } + $extras' > "$LOG_DIR/status.json"
}

# Legacy update_status for Feature Mode (backwards compatibility)
# Used by feature/ralph.sh
update_status() {
    local loop_count=$1
    local calls_made=$2
    local current_story=$3
    local status=$4
    local last_error="${5:-}"

    mkdir -p "$LOG_DIR"

    # Get progress data if tasks.json exists
    local completed=0
    local total=0
    if [[ -f "$SCRIPT_DIR/tasks.json" ]]; then
        completed=$(jq '[.userStories[] | select(.passes == true)] | length' "$SCRIPT_DIR/tasks.json" 2>/dev/null || echo "0")
        total=$(jq '.userStories | length' "$SCRIPT_DIR/tasks.json" 2>/dev/null || echo "0")
    fi

    # Create extras JSON
    local extras=$(jq -n \
        --argjson calls_made "$calls_made" \
        --argjson max_calls "${MAX_CALLS_PER_HOUR:-50}" \
        --arg last_error "$last_error" \
        --arg next_reset "$(get_next_hour_time)" \
        '{
            calls_made_this_hour: $calls_made,
            max_calls_per_hour: $max_calls,
            last_error: $last_error,
            next_reset: $next_reset
        }')

    write_status_json "feature" "$status" "$loop_count" "$current_story" "$completed" "$total" "$extras"
}

# Export functions
export -f log_info
export -f log_error
export -f log_warn
export -f log_success
export -f log_loop
export -f log_iteration
export -f write_status_json
export -f update_status
