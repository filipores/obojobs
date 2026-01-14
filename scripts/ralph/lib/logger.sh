#!/usr/bin/env bash
# logger.sh - Strukturiertes Logging für RALF
# Gemeinsame Library für alle Ralph-Modi
# Schreibt in $LOG_DIR/ralph.log und $LOG_DIR/status.json

# Source date utilities from same directory
_LOGGER_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "$_LOGGER_DIR/date_utils.sh"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Log function mit Timestamps und Farben
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

    # Keep only last 50 entries
    local history=$(cat "$history_file")
    history=$(echo "$history" | jq ". += [$entry] | .[-50:]")
    echo "$history" > "$history_file"
}

# Update status JSON for external monitoring
update_status() {
    local loop_count=$1
    local calls_made=$2
    local current_story=$3
    local status=$4
    local last_error=${5:-""}

    mkdir -p "$LOG_DIR"

    cat > "$LOG_DIR/status.json" << EOF
{
    "timestamp": "$(get_iso_timestamp)",
    "loop_count": $loop_count,
    "calls_made_this_hour": $calls_made,
    "max_calls_per_hour": ${MAX_CALLS_PER_HOUR:-50},
    "current_story": "$current_story",
    "status": "$status",
    "last_error": "$last_error",
    "started_at": "${RALPH_STARTED_AT:-$(get_iso_timestamp)}",
    "next_reset": "$(get_next_hour_time)"
}
EOF
}

# Export functions
export -f log_info
export -f log_error
export -f log_warn
export -f log_success
export -f log_loop
export -f log_iteration
export -f update_status
