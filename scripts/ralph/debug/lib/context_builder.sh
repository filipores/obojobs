#!/usr/bin/env bash
# context_builder.sh - Pre-computed Context für Token-Optimierung
# Ermittelt relevante Dateien VOR dem Claude-Aufruf

CB_DIR="$(dirname "${BASH_SOURCE[0]}")"
PROJECT_ROOT="$(cd "$CB_DIR/../../../.." && pwd)"

# Get relevant files for a story based on keywords and patterns
get_story_context() {
    local story_id=$1
    local prd_file="${SCRIPT_DIR:-$CB_DIR/..}/prd.json"

    if [[ ! -f "$prd_file" ]]; then
        echo ""
        return
    fi

    # Extract story details
    local story=$(jq -r --arg id "$story_id" '.userStories[] | select(.id == $id)' "$prd_file")
    local title=$(echo "$story" | jq -r '.title // ""')
    local description=$(echo "$story" | jq -r '.description // ""')
    local criteria=$(echo "$story" | jq -r '.acceptanceCriteria // [] | join(" ")' 2>/dev/null)

    # Build search patterns from story content
    local search_text="$title $description $criteria"

    # Extract component names (*.vue, *.py files mentioned)
    local components=$(echo "$search_text" | grep -oE '[A-Z][a-zA-Z]+\.(vue|py|ts)' | sort -u | head -5)

    # Extract model names (mentioned in criteria)
    local models=$(echo "$search_text" | grep -oE "Model '[A-Za-z]+'" | sed "s/Model '//g" | sed "s/'//g" | head -3)

    # Extract endpoint patterns
    local endpoints=$(echo "$search_text" | grep -oE '/api/[a-z/_-]+' | sort -u | head -5)

    # Find actual files
    local relevant_files=""

    # Search for component files
    for comp in $components; do
        local found=$(find "$PROJECT_ROOT/frontend/src" "$PROJECT_ROOT/backend" -name "$comp" 2>/dev/null | head -1)
        if [[ -n "$found" ]]; then
            relevant_files="$relevant_files${found#$PROJECT_ROOT/}\n"
        fi
    done

    # Search for model files in backend
    for model in $models; do
        local model_lower=$(echo "$model" | tr '[:upper:]' '[:lower:]')
        local found=$(find "$PROJECT_ROOT/backend" -name "*.py" -exec grep -l "class $model" {} \; 2>/dev/null | head -1)
        if [[ -n "$found" ]]; then
            relevant_files="$relevant_files${found#$PROJECT_ROOT/}\n"
        fi
    done

    # Get recently modified files in relevant directories
    local recent=$(git diff --name-only HEAD~5 2>/dev/null | grep -E '\.(vue|py|ts)$' | head -5)
    if [[ -n "$recent" ]]; then
        relevant_files="$relevant_files$recent\n"
    fi

    # Remove duplicates and format
    echo -e "$relevant_files" | sort -u | grep -v '^$' | head -10
}

# Get bug context from bugs.json
get_bug_context() {
    local bug_id=$1
    local bugs_file="${SCRIPT_DIR:-$CB_DIR/..}/bugs.json"

    if [[ ! -f "$bugs_file" ]]; then
        echo ""
        return
    fi

    # Extract affected files directly from bug
    local affected=$(jq -r --arg id "$bug_id" '.bugs[] | select(.id == $id) | .affectedFiles // [] | .[]' "$bugs_file" 2>/dev/null)

    # Also search for related test files
    local test_files=""
    for file in $affected; do
        local base=$(basename "$file" | sed 's/\.[^.]*$//')
        local test=$(find "$PROJECT_ROOT" -name "*${base}*test*" -o -name "*test*${base}*" 2>/dev/null | head -1)
        if [[ -n "$test" ]]; then
            test_files="$test_files${test#$PROJECT_ROOT/}\n"
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

    echo "RELEVANT_FILES (pre-computed, check these first):"
    echo "$files" | while read -r file; do
        if [[ -n "$file" ]]; then
            echo "  - $file"
        fi
    done
}

# Export functions
export -f get_story_context
export -f get_bug_context
export -f build_context_string
