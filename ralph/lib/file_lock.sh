#!/usr/bin/env bash
# file_lock.sh - File Locking for RALPH State Files
# Prevents race conditions during concurrent access

# Lock timeout in seconds
LOCK_TIMEOUT=${LOCK_TIMEOUT:-5}

# Acquire a lock on a file
# Usage: acquire_lock "/path/to/file"
# Returns: 0 if lock acquired, 1 if timeout
acquire_lock() {
    local file="$1"
    local lock_file="${file}.lock"
    local timeout=${2:-$LOCK_TIMEOUT}

    # Create lock directory if needed
    mkdir -p "$(dirname "$lock_file")" 2>/dev/null

    # Try to acquire lock with timeout
    local start_time=$(date +%s)
    while true; do
        # Try to create lock file exclusively
        if (set -o noclobber; echo $$ > "$lock_file") 2>/dev/null; then
            return 0
        fi

        # Check timeout
        local current_time=$(date +%s)
        if [[ $((current_time - start_time)) -ge $timeout ]]; then
            return 1
        fi

        # Wait briefly before retry
        sleep 0.1
    done
}

# Release a lock on a file
# Usage: release_lock "/path/to/file"
release_lock() {
    local file="$1"
    local lock_file="${file}.lock"

    # Only remove if we own the lock
    if [[ -f "$lock_file" && "$(cat "$lock_file" 2>/dev/null)" == "$$" ]]; then
        rm -f "$lock_file"
    fi
}

# Execute a command with file lock
# Usage: with_lock "/path/to/file" command [args...]
with_lock() {
    local file="$1"
    shift

    if acquire_lock "$file"; then
        # Execute command
        "$@"
        local result=$?
        release_lock "$file"
        return $result
    else
        echo "Warning: Could not acquire lock for $file" >&2
        # Execute anyway without lock
        "$@"
        return $?
    fi
}

# Atomic file update with lock
# Usage: atomic_update "/path/to/file" "new content"
atomic_update() {
    local file="$1"
    local content="$2"
    local tmp_file="${file}.tmp.$$"

    if acquire_lock "$file"; then
        echo "$content" > "$tmp_file"
        mv "$tmp_file" "$file"
        release_lock "$file"
        return 0
    else
        echo "Warning: Could not acquire lock for $file" >&2
        echo "$content" > "$tmp_file"
        mv "$tmp_file" "$file"
        return 1
    fi
}

# Export functions
export -f acquire_lock
export -f release_lock
export -f with_lock
export -f atomic_update
