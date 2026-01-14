#!/usr/bin/env bash
# context_builder.sh - Pre-computed Context für Token-Optimierung
# Gemeinsame Library für alle Ralph-Modi

# Get script directory dynamically based on caller
_get_project_root() {
    local script_dir="${SCRIPT_DIR:-$(pwd)}"
    cd "$script_dir/../../.." 2>/dev/null && pwd || pwd
}

# Get relevant files for a story based on keywords and patterns (Feature-Ralph)
get_story_context() {
    local story_id=$1
    local prd_file="${SCRIPT_DIR:-$(pwd)}/prd.json"
    local project_root=$(_get_project_root)

    if [[ ! -f "$prd_file" ]]; then
        echo ""
        return
    fi

    # Extract story details
    local story=$(jq -r --arg id "$story_id" '.userStories[] | select(.id == $id)' "$prd_file" 2>/dev/null)
    local title=$(echo "$story" | jq -r '.title // ""')
    local description=$(echo "$story" | jq -r '.description // ""')
    local criteria=$(echo "$story" | jq -r '.acceptanceCriteria // [] | join(" ")' 2>/dev/null)

    # Build search patterns from story content
    local search_text="$title $description $criteria"

    # Extract component names (*.vue, *.py files mentioned)
    local components=$(echo "$search_text" | grep -oE '[A-Z][a-zA-Z]+\.(vue|py|ts)' | sort -u | head -5)

    # Find actual files
    local relevant_files=""
    for comp in $components; do
        local found=$(find "$project_root/frontend/src" "$project_root/backend" -name "$comp" 2>/dev/null | head -1)
        if [[ -n "$found" ]]; then
            relevant_files="$relevant_files${found#$project_root/}\n"
        fi
    done

    # Get recently modified files
    local recent=$(cd "$project_root" && git diff --name-only HEAD~5 2>/dev/null | grep -E '\.(vue|py|ts)$' | head -5)
    if [[ -n "$recent" ]]; then
        relevant_files="$relevant_files$recent\n"
    fi

    echo -e "$relevant_files" | sort -u | grep -v '^$' | head -10
}

# Get bug context from bugs.json (Debug-Ralph)
get_bug_context() {
    local bug_id=$1
    local bugs_file="${SCRIPT_DIR:-$(pwd)}/bugs.json"
    local project_root=$(_get_project_root)

    if [[ ! -f "$bugs_file" ]]; then
        echo ""
        return
    fi

    # Extract affected files directly from bug
    local affected=$(jq -r --arg id "$bug_id" '.bugs[] | select(.id == $id) | .affectedFiles // [] | .[]' "$bugs_file" 2>/dev/null)

    # Also search for related test files
    local test_files=""
    for file in $affected; do
        local base=$(basename "$file" | sed 's/\.[^.]*$//' | sed 's/:[0-9]*$//')
        local test=$(find "$project_root" -name "*${base}*test*" -o -name "*test*${base}*" 2>/dev/null | head -1)
        if [[ -n "$test" ]]; then
            test_files="$test_files${test#$project_root/}\n"
        fi
    done

    echo -e "$affected\n$test_files" | sort -u | grep -v '^$'
}

# Build context string for prompt
build_context_string() {
    local files=$1

    if [[ -z "$files" ]]; then
        echo ""
        return
    fi

    echo "RELEVANT_FILES (pre-computed):"
    echo "$files" | while read -r file; do
        if [[ -n "$file" ]]; then
            echo "  - $file"
        fi
    done
}

# Export functions
export -f _get_project_root
export -f get_story_context
export -f get_bug_context
export -f build_context_string
