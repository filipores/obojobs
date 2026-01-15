#!/usr/bin/env bash
# rate_limiter.sh - Rate Limiting für RALF
# Begrenzt API-Calls pro Stunde

# Source date utilities from shared lib
RATE_LIMITER_DIR="$(dirname "${BASH_SOURCE[0]}")"
SHARED_LIB_DIR="$RATE_LIMITER_DIR/../../lib"
source "$SHARED_LIB_DIR/date_utils.sh"

# Get rate limit file path (must be called after LOG_DIR is set)
get_rate_limit_file() {
    echo "${LOG_DIR:-$(dirname "${BASH_SOURCE[0]}")/..}/logs/rate_limit.json"
}

# Initialize rate limit tracking
init_rate_limiter() {
    local RATE_LIMIT_FILE=$(get_rate_limit_file)
    mkdir -p "$(dirname "$RATE_LIMIT_FILE")"
    if [[ ! -f "$RATE_LIMIT_FILE" ]]; then
        cat > "$RATE_LIMIT_FILE" << EOF
{
    "calls": 0,
    "hour_started": "$(get_iso_timestamp)"
}
EOF
    fi
}

# Reset if hour passed
reset_if_hour_passed() {
    local RATE_LIMIT_FILE=$(get_rate_limit_file)
    if [[ ! -f "$RATE_LIMIT_FILE" ]]; then
        init_rate_limiter
        return
    fi

    local hour_started=$(jq -r '.hour_started' "$RATE_LIMIT_FILE" 2>/dev/null)

    if [[ -z "$hour_started" || "$hour_started" == "null" ]]; then
        init_rate_limiter
        return
    fi

    # Get current hour (YYYYMMDDHH)
    local current_hour=$(date +%Y%m%d%H)

    # Parse hour_started to same format
    local started_hour=$(echo "$hour_started" | cut -d'T' -f1 | tr -d '-')$(echo "$hour_started" | cut -d'T' -f2 | cut -d':' -f1)

    if [[ "$current_hour" != "$started_hour" ]]; then
        # New hour, reset counter
        cat > "$RATE_LIMIT_FILE" << EOF
{
    "calls": 0,
    "hour_started": "$(get_iso_timestamp)"
}
EOF
        echo "Rate limit counter reset for new hour"
    fi
}

# Check if rate limit is reached
check_rate_limit() {
    local RATE_LIMIT_FILE=$(get_rate_limit_file)
    reset_if_hour_passed

    local calls=$(jq -r '.calls' "$RATE_LIMIT_FILE" 2>/dev/null)
    calls=${calls:-0}

    local max_calls=${MAX_CALLS_PER_HOUR:-50}

    if [[ $calls -ge $max_calls ]]; then
        return 1  # Limit reached
    else
        return 0  # OK to proceed
    fi
}

# Increment call count
increment_call_count() {
    local RATE_LIMIT_FILE=$(get_rate_limit_file)
    reset_if_hour_passed

    local calls=$(jq -r '.calls' "$RATE_LIMIT_FILE" 2>/dev/null)
    calls=${calls:-0}
    calls=$((calls + 1))

    local hour_started=$(jq -r '.hour_started' "$RATE_LIMIT_FILE" 2>/dev/null)

    cat > "$RATE_LIMIT_FILE" << EOF
{
    "calls": $calls,
    "hour_started": "$hour_started"
}
EOF

    echo $calls
}

# Get remaining calls
get_remaining_calls() {
    local RATE_LIMIT_FILE=$(get_rate_limit_file)
    reset_if_hour_passed

    local calls=$(jq -r '.calls' "$RATE_LIMIT_FILE" 2>/dev/null)
    calls=${calls:-0}

    local max_calls=${MAX_CALLS_PER_HOUR:-50}
    echo $((max_calls - calls))
}

# Wait for rate limit reset with countdown
wait_for_reset() {
    local RATE_LIMIT_FILE=$(get_rate_limit_file)
    local calls=$(jq -r '.calls' "$RATE_LIMIT_FILE" 2>/dev/null)
    echo -e "${YELLOW}Rate limit reached ($calls/${MAX_CALLS_PER_HOUR:-50}). Waiting for reset...${NC}"

    # Calculate time until next hour
    local current_minute=$(date +%M)
    local current_second=$(date +%S)
    local wait_time=$(((60 - current_minute - 1) * 60 + (60 - current_second)))

    echo "Sleeping for $wait_time seconds until next hour..."

    # Countdown display
    while [[ $wait_time -gt 0 ]]; do
        local minutes=$((wait_time / 60))
        local seconds=$((wait_time % 60))
        printf "\r${YELLOW}Time until reset: %02d:%02d${NC}" $minutes $seconds
        sleep 1
        ((wait_time--))
    done
    printf "\n"

    # Reset counter
    init_rate_limiter
    echo -e "${GREEN}Rate limit reset! Ready for new calls.${NC}"
}

# Export functions
export -f get_rate_limit_file
export -f init_rate_limiter
export -f reset_if_hour_passed
export -f check_rate_limit
export -f increment_call_count
export -f get_remaining_calls
export -f wait_for_reset
