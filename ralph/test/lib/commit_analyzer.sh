#!/usr/bin/env bash
# commit_analyzer.sh - Analyzes Commits for Test Ralph
# Extracts features from commit range or manual list
#
# Prerequisite: date_utils.sh is loaded by ralph.sh

# State files
TASKS_FILE="${SCRIPT_DIR:-.}/tasks.json"
MANUAL_TASKS_FILE="${SCRIPT_DIR:-.}/manual_tasks.json"

# Colors are loaded from lib/colors.sh (via ralph.sh)

# Initialize features file
init_features_file() {
    if [[ ! -f "$TASKS_FILE" ]]; then
        echo '{"features": [], "source": "none", "generated_at": ""}' > "$TASKS_FILE"
    fi
}

# Extract features from commit range
extract_from_commits() {
    local base_branch=${1:-main}
    local features=()

    echo -e "${BLUE}Analyzing commits since $base_branch...${NC}"

    # Get commit list
    local commits=$(git log --oneline "$base_branch"..HEAD 2>/dev/null)

    if [[ -z "$commits" ]]; then
        echo -e "${YELLOW}No new commits since $base_branch${NC}"
        return 1
    fi

    # Parse each commit
    local feature_json="[]"
    local index=0

    while IFS= read -r line; do
        local hash=$(echo "$line" | cut -d' ' -f1)
        local message=$(echo "$line" | cut -d' ' -f2-)

        # Get changed files for this commit
        local changed_files=$(git diff-tree --no-commit-id --name-only -r "$hash" 2>/dev/null | tr '\n' ',' | sed 's/,$//')

        # Detect if frontend or backend change
        local scope="unknown"
        if echo "$changed_files" | grep -q "frontend/"; then
            scope="frontend"
        elif echo "$changed_files" | grep -q "backend/"; then
            scope="backend"
        fi
        if echo "$changed_files" | grep -qE "frontend/.*backend/|backend/.*frontend/"; then
            scope="fullstack"
        fi

        # Extract feature type from commit message
        local feature_type="unknown"
        if echo "$message" | grep -qiE "^feat"; then
            feature_type="feature"
        elif echo "$message" | grep -qiE "^fix"; then
            feature_type="bugfix"
        elif echo "$message" | grep -qiE "^refactor"; then
            feature_type="refactor"
        elif echo "$message" | grep -qiE "^docs"; then
            feature_type="docs"
        elif echo "$message" | grep -qiE "^test"; then
            feature_type="test"
        fi

        # Build feature entry
        local entry=$(jq -n \
            --arg id "COMMIT-$index" \
            --arg hash "$hash" \
            --arg message "$message" \
            --arg scope "$scope" \
            --arg type "$feature_type" \
            --arg files "$changed_files" \
            --arg tested "false" \
            '{
                id: $id,
                commit_hash: $hash,
                message: $message,
                scope: $scope,
                type: $type,
                changed_files: ($files | split(",")),
                tested: false,
                test_result: null
            }')

        # Validate JSON before adding
        if echo "$entry" | jq -e '.' > /dev/null 2>&1; then
            feature_json=$(echo "$feature_json" | jq ". += [$entry]")
            index=$((index + 1))
        else
            echo -e "${YELLOW}Warning: Invalid JSON for commit $hash, skipping${NC}" >&2
        fi

    done <<< "$commits"

    # Filter to only frontend-relevant commits for UI testing
    local frontend_features=$(echo "$feature_json" | jq '[.[] | select(.scope == "frontend" or .scope == "fullstack")]')
    local frontend_count=$(echo "$frontend_features" | jq 'length')

    echo -e "${GREEN}Found: $index commits, $frontend_count frontend-relevant${NC}"

    # Save to file
    jq -n \
        --argjson features "$frontend_features" \
        --arg source "git_commits" \
        --arg base "$base_branch" \
        --arg timestamp "$(get_iso_timestamp)" \
        '{
            features: $features,
            source: $source,
            base_branch: $base,
            generated_at: $timestamp,
            total_commits: ($features | length)
        }' > "$TASKS_FILE"

    return 0
}

# Load manual features from prompt.md or manual_tasks.json
load_manual_features() {
    local prompt_file="${SCRIPT_DIR:-.}/prompt.md"

    # Check for manual_tasks.json first (highest priority)
    if [[ -f "$MANUAL_TASKS_FILE" ]]; then
        echo -e "${BLUE}Loading manual features from manual_tasks.json...${NC}"

        local manual_features=$(jq '.features // []' "$MANUAL_TASKS_FILE" 2>/dev/null)
        local manual_count=$(echo "$manual_features" | jq 'length')

        if [[ $manual_count -gt 0 ]]; then
            echo -e "${GREEN}$manual_count manual features found${NC}"

            # Merge with existing features (manual takes priority)
            if [[ -f "$TASKS_FILE" ]]; then
                local existing=$(cat "$TASKS_FILE")
                local existing_features=$(echo "$existing" | jq '.features // []')

                # Manual features override commits with same hash
                local merged=$(jq -n \
                    --argjson manual "$manual_features" \
                    --argjson existing "$existing_features" \
                    '$manual + [$existing[] | select(.commit_hash as $h | $manual | map(.commit_hash) | index($h) | not)]')

                jq -n \
                    --argjson features "$merged" \
                    --arg source "manual_override" \
                    --arg timestamp "$(get_iso_timestamp)" \
                    '{
                        features: $features,
                        source: $source,
                        generated_at: $timestamp,
                        total_commits: ($features | length)
                    }' > "$TASKS_FILE"
            fi

            return 0
        fi
    fi

    return 1
}

# Get next untested feature
get_next_feature() {
    if [[ ! -f "$TASKS_FILE" ]]; then
        echo ""
        return 1
    fi

    local next=$(jq -r '.features | map(select(.tested == false)) | .[0] // empty' "$TASKS_FILE")

    if [[ -z "$next" || "$next" == "null" ]]; then
        echo ""
        return 1
    fi

    echo "$next"
    return 0
}

# Get feature by ID
get_feature_by_id() {
    local feature_id=$1

    if [[ ! -f "$TASKS_FILE" ]]; then
        echo ""
        return 1
    fi

    jq -r --arg id "$feature_id" '.features | map(select(.id == $id)) | .[0] // empty' "$TASKS_FILE"
}

# Mark feature as tested
mark_feature_tested() {
    local feature_id=$1
    local test_result=$2  # JSON object with test results

    if [[ ! -f "$TASKS_FILE" ]]; then
        return 1
    fi

    local updated=$(jq --arg id "$feature_id" --argjson result "$test_result" '
        .features = [.features[] |
            if .id == $id then
                .tested = true | .test_result = $result
            else
                .
            end
        ]' "$TASKS_FILE")

    echo "$updated" > "$TASKS_FILE"
}

# Get testing progress
get_test_progress() {
    if [[ ! -f "$TASKS_FILE" ]]; then
        echo '{"total": 0, "tested": 0, "remaining": 0, "bugs": 0, "passed": 0}'
        return
    fi

    jq '{
        total: (.features | length),
        tested: ([.features[] | select(.tested == true)] | length),
        remaining: ([.features[] | select(.tested == false)] | length),
        bugs: ([.features[] | select(.test_result.has_bugs == true)] | length),
        passed: ([.features[] | select(.test_result.has_bugs == false and .tested == true)] | length)
    }' "$TASKS_FILE"
}

# Get all bugs found
get_all_bugs() {
    if [[ ! -f "$TASKS_FILE" ]]; then
        echo '[]'
        return
    fi

    jq '[.features[] | select(.test_result.bugs != null) | .test_result.bugs[]] | flatten' "$TASKS_FILE"
}

# Get all feature suggestions
get_all_suggestions() {
    if [[ ! -f "$TASKS_FILE" ]]; then
        echo '[]'
        return
    fi

    jq '[.features[] | select(.test_result.suggestions != null) | .test_result.suggestions[]] | flatten' "$TASKS_FILE"
}

# Export functions
export -f init_features_file
export -f extract_from_commits
export -f load_manual_features
export -f get_next_feature
export -f get_feature_by_id
export -f mark_feature_tested
export -f get_test_progress
export -f get_all_bugs
export -f get_all_suggestions
