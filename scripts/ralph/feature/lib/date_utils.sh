#!/usr/bin/env bash
# date_utils.sh - Cross-platform date utility functions
# Provides consistent date formatting across GNU (Linux) and BSD (macOS) systems

# Get current timestamp in ISO 8601 format
get_iso_timestamp() {
    local os_type
    os_type=$(uname)

    if [[ "$os_type" == "Darwin" ]]; then
        # macOS (BSD date)
        date -u +"%Y-%m-%dT%H:%M:%S%z" | sed 's/\(..\)$/:\1/'
    else
        # Linux (GNU date)
        date -u -Iseconds
    fi
}

# Get time component (HH:MM:SS) for one hour from now
get_next_hour_time() {
    local os_type
    os_type=$(uname)

    if [[ "$os_type" == "Darwin" ]]; then
        date -v+1H '+%H:%M:%S'
    else
        date -d '+1 hour' '+%H:%M:%S'
    fi
}

# Get current timestamp in a basic format
get_basic_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# Get current Unix epoch time in seconds
get_epoch_seconds() {
    date +%s
}

# Export functions
export -f get_iso_timestamp
export -f get_next_hour_time
export -f get_basic_timestamp
export -f get_epoch_seconds
