#!/usr/bin/env bash
# commit_analyzer.sh - Analysiert Commits für Test-Ralph
# Extrahiert Features aus Commit-Range oder manueller Liste

# Source date utilities from feature mode
CA_DIR="$(dirname "${BASH_SOURCE[0]}")"
if [[ -f "$CA_DIR/../../feature/lib/date_utils.sh" ]]; then
    source "$CA_DIR/../../feature/lib/date_utils.sh"
else
    get_iso_timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
fi

# State files
FEATURES_FILE="${SCRIPT_DIR:-.}/features.json"
MANUAL_FEATURES_FILE="${SCRIPT_DIR:-.}/manual_features.json"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Initialize features file
init_features_file() {
    if [[ ! -f "$FEATURES_FILE" ]]; then
        echo '{"features": [], "source": "none", "generated_at": ""}' > "$FEATURES_FILE"
    fi
}

# Extract features from commit range
extract_from_commits() {
    local base_branch=${1:-main}
    local features=()

    echo -e "${BLUE}Analysiere Commits seit $base_branch...${NC}"

    # Get commit list
    local commits=$(git log --oneline "$base_branch"..HEAD 2>/dev/null)

    if [[ -z "$commits" ]]; then
        echo -e "${YELLOW}Keine neuen Commits seit $base_branch${NC}"
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

        feature_json=$(echo "$feature_json" | jq ". += [$entry]")
        index=$((index + 1))

    done <<< "$commits"

    # Filter to only frontend-relevant commits for UI testing
    local frontend_features=$(echo "$feature_json" | jq '[.[] | select(.scope == "frontend" or .scope == "fullstack")]')
    local frontend_count=$(echo "$frontend_features" | jq 'length')

    echo -e "${GREEN}Gefunden: $index Commits, davon $frontend_count frontend-relevant${NC}"

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
        }' > "$FEATURES_FILE"

    return 0
}

# Load manual features from prompt.md or manual_features.json
load_manual_features() {
    local prompt_file="${SCRIPT_DIR:-.}/prompt.md"

    # Check for manual_features.json first (highest priority)
    if [[ -f "$MANUAL_FEATURES_FILE" ]]; then
        echo -e "${BLUE}Lade manuelle Features aus manual_features.json...${NC}"

        local manual_features=$(jq '.features // []' "$MANUAL_FEATURES_FILE" 2>/dev/null)
        local manual_count=$(echo "$manual_features" | jq 'length')

        if [[ $manual_count -gt 0 ]]; then
            echo -e "${GREEN}$manual_count manuelle Features gefunden${NC}"

            # Merge with existing features (manual takes priority)
            if [[ -f "$FEATURES_FILE" ]]; then
                local existing=$(cat "$FEATURES_FILE")
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
                    }' > "$FEATURES_FILE"
            fi

            return 0
        fi
    fi

    return 1
}

# Get next untested feature
get_next_feature() {
    if [[ ! -f "$FEATURES_FILE" ]]; then
        echo ""
        return 1
    fi

    local next=$(jq -r '.features | map(select(.tested == false)) | .[0] // empty' "$FEATURES_FILE")

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

    if [[ ! -f "$FEATURES_FILE" ]]; then
        echo ""
        return 1
    fi

    jq -r --arg id "$feature_id" '.features | map(select(.id == $id)) | .[0] // empty' "$FEATURES_FILE"
}

# Mark feature as tested
mark_feature_tested() {
    local feature_id=$1
    local test_result=$2  # JSON object with test results

    if [[ ! -f "$FEATURES_FILE" ]]; then
        return 1
    fi

    local updated=$(jq --arg id "$feature_id" --argjson result "$test_result" '
        .features = [.features[] |
            if .id == $id then
                .tested = true | .test_result = $result
            else
                .
            end
        ]' "$FEATURES_FILE")

    echo "$updated" > "$FEATURES_FILE"
}

# Get testing progress
get_test_progress() {
    if [[ ! -f "$FEATURES_FILE" ]]; then
        echo '{"total": 0, "tested": 0, "remaining": 0, "bugs": 0, "passed": 0}'
        return
    fi

    jq '{
        total: (.features | length),
        tested: ([.features[] | select(.tested == true)] | length),
        remaining: ([.features[] | select(.tested == false)] | length),
        bugs: ([.features[] | select(.test_result.has_bugs == true)] | length),
        passed: ([.features[] | select(.test_result.has_bugs == false and .tested == true)] | length)
    }' "$FEATURES_FILE"
}

# Get all bugs found
get_all_bugs() {
    if [[ ! -f "$FEATURES_FILE" ]]; then
        echo '[]'
        return
    fi

    jq '[.features[] | select(.test_result.bugs != null) | .test_result.bugs[]] | flatten' "$FEATURES_FILE"
}

# Get all feature suggestions
get_all_suggestions() {
    if [[ ! -f "$FEATURES_FILE" ]]; then
        echo '[]'
        return
    fi

    jq '[.features[] | select(.test_result.suggestions != null) | .test_result.suggestions[]] | flatten' "$FEATURES_FILE"
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
