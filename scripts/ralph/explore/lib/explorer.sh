#!/usr/bin/env bash
# explorer.sh - Exploration-spezifische Funktionen für RALF Explore Mode
# Handhabt Session-Management, Parsing und Deduplication

# ============================================
# Session Management
# ============================================

init_explore_session() {
    local session_file="$SCRIPT_DIR/session.json"

    if [[ ! -f "$session_file" ]]; then
        cat > "$session_file" << 'EOF'
{
  "started_at": null,
  "last_updated": null,
  "visited_pages": [],
  "known_bug_ids": [],
  "known_sugg_ids": [],
  "login_status": false,
  "test_credentials": {
    "email": "",
    "password": ""
  },
  "exploration_stats": {
    "total_loops": 0,
    "total_interactions": 0,
    "errors_encountered": 0
  }
}
EOF
    fi

    # Update session with start time and credentials
    local tmp_file="$session_file.tmp"
    jq --arg started "$(get_iso_timestamp)" \
       --arg email "$TEST_USER_EMAIL" \
       --arg password "$TEST_USER_PASSWORD" '
        .started_at = (if .started_at == null then $started else .started_at end) |
        .test_credentials.email = $email |
        .test_credentials.password = $password
    ' "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"

    # Sync known IDs from bugs.json and sugg.json
    sync_known_ids

    log_info "Session initialisiert"
}

sync_known_ids() {
    local session_file="$SCRIPT_DIR/session.json"
    local bugs_file="$SCRIPT_DIR/bugs.json"
    local sugg_file="$SCRIPT_DIR/sugg.json"

    # Get existing bug IDs
    local bug_ids="[]"
    if [[ -f "$bugs_file" ]]; then
        bug_ids=$(jq '[.bugs[].id]' "$bugs_file" 2>/dev/null || echo "[]")
    fi

    # Get existing suggestion IDs
    local sugg_ids="[]"
    if [[ -f "$sugg_file" ]]; then
        sugg_ids=$(jq '[.suggestions[].id]' "$sugg_file" 2>/dev/null || echo "[]")
    fi

    # Update session
    local tmp_file="$session_file.tmp"
    jq --argjson bugs "$bug_ids" --argjson sugg "$sugg_ids" '
        .known_bug_ids = $bugs |
        .known_sugg_ids = $sugg
    ' "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"
}

save_session() {
    local session_file="$SCRIPT_DIR/session.json"
    local tmp_file="$session_file.tmp"

    jq --arg updated "$(get_iso_timestamp)" '
        .last_updated = $updated
    ' "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"

    log_info "Session gespeichert"
}

reset_session() {
    rm -f "$SCRIPT_DIR/session.json"
    rm -f "$SCRIPT_DIR/bugs.json"
    rm -f "$SCRIPT_DIR/sugg.json"
    rm -f "$LOG_DIR"/*.log
    rm -f "$LOG_DIR"/*.json

    log_info "Session zurückgesetzt"
}

get_session_context() {
    local session_file="$SCRIPT_DIR/session.json"

    if [[ ! -f "$session_file" ]]; then
        echo "No session"
        return
    fi

    # Build concise context string
    local visited_count=$(jq '.visited_pages | length' "$session_file" 2>/dev/null || echo "0")
    local known_bugs=$(jq '.known_bug_ids | length' "$session_file" 2>/dev/null || echo "0")
    local known_sugg=$(jq '.known_sugg_ids | length' "$session_file" 2>/dev/null || echo "0")
    local login_status=$(jq -r '.login_status' "$session_file" 2>/dev/null || echo "false")
    local email=$(jq -r '.test_credentials.email' "$session_file" 2>/dev/null || echo "")

    # Get last 5 visited pages
    local recent_pages=$(jq -r '.visited_pages[-5:] | join(", ")' "$session_file" 2>/dev/null || echo "none")

    # Get known bug IDs for deduplication
    local bug_ids=$(jq -r '.known_bug_ids | join(", ")' "$session_file" 2>/dev/null || echo "none")

    echo "Pages visited: $visited_count. Known bugs: $known_bugs (IDs: $bug_ids). Known suggestions: $known_sugg. Login: $login_status. Test email: $email. Recent pages: $recent_pages"
}

# ============================================
# Result Parsing
# ============================================

parse_explore_result() {
    local output_file=$1

    if [[ ! -f "$output_file" ]]; then
        log_warn "Output-Datei nicht gefunden: $output_file"
        return 1
    fi

    # Extract RALPH_EXPLORE_RESULT block
    local result_json=""
    if grep -q "RALPH_EXPLORE_RESULT" "$output_file"; then
        result_json=$(sed -n '/---RALPH_EXPLORE_RESULT---/,/---END_RALPH_EXPLORE_RESULT---/p' "$output_file" | \
            grep -v "RALPH_EXPLORE_RESULT" | \
            tr -d '\r')
    fi

    if [[ -z "$result_json" ]]; then
        log_warn "Kein RALPH_EXPLORE_RESULT Block gefunden"
        return 1
    fi

    # Validate JSON
    if ! echo "$result_json" | jq empty 2>/dev/null; then
        log_warn "Ungültiges JSON im Result-Block"
        return 1
    fi

    # Process new bugs
    local new_bugs=$(echo "$result_json" | jq '.new_bugs // []')
    if [[ "$new_bugs" != "[]" && "$new_bugs" != "null" ]]; then
        process_new_bugs "$new_bugs"
    fi

    # Process new suggestions
    local new_sugg=$(echo "$result_json" | jq '.new_suggestions // []')
    if [[ "$new_sugg" != "[]" && "$new_sugg" != "null" ]]; then
        process_new_suggestions "$new_sugg"
    fi

    # Update visited pages
    local pages=$(echo "$result_json" | jq '.pages_visited // []')
    if [[ "$pages" != "[]" && "$pages" != "null" ]]; then
        update_visited_pages "$pages"
    fi

    # Update session stats
    local interactions=$(echo "$result_json" | jq '.interactions_tested // 0')
    update_session_stats "$interactions"

    return 0
}

process_new_bugs() {
    local bugs_json=$1
    local bugs_file="$SCRIPT_DIR/bugs.json"
    local session_file="$SCRIPT_DIR/session.json"

    # Get known bug IDs for deduplication
    local known_ids=$(jq -r '.known_bug_ids[]' "$session_file" 2>/dev/null)

    # Process each bug
    echo "$bugs_json" | jq -c '.[]' | while read -r bug; do
        local bug_id=$(echo "$bug" | jq -r '.id')

        # Check for duplicates
        if [[ "$DEDUPE_ENABLED" == "true" ]] && echo "$known_ids" | grep -q "^$bug_id$"; then
            log_info "Bug $bug_id bereits bekannt - übersprungen"
            continue
        fi

        # Generate new ID if needed
        if [[ -z "$bug_id" || "$bug_id" == "null" ]]; then
            local max_num=$(jq '[.bugs[].id | select(. != null) | capture("BUG-(?<n>[0-9]+)") | .n | tonumber] | max // 0' "$bugs_file" 2>/dev/null || echo "0")
            bug_id="BUG-$(printf '%03d' $((max_num + 1)))"
            bug=$(echo "$bug" | jq --arg id "$bug_id" '.id = $id')
        fi

        # Add metadata
        bug=$(echo "$bug" | jq --arg ts "$(get_iso_timestamp)" '
            .found_at = $ts |
            .source = "explore-ralph" |
            .fixed = false |
            .fixAttempts = 0
        ')

        # Add to bugs.json
        local tmp_file="$bugs_file.tmp"
        jq --argjson bug "$bug" '.bugs += [$bug]' "$bugs_file" > "$tmp_file" && mv "$tmp_file" "$bugs_file"

        # Add to known IDs
        tmp_file="$session_file.tmp"
        jq --arg id "$bug_id" '.known_bug_ids += [$id] | .known_bug_ids = (.known_bug_ids | unique)' \
            "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"

        log_success "Bug $bug_id hinzugefügt"
    done
}

process_new_suggestions() {
    local sugg_json=$1
    local sugg_file="$SCRIPT_DIR/sugg.json"
    local session_file="$SCRIPT_DIR/session.json"

    # Get known suggestion IDs for deduplication
    local known_ids=$(jq -r '.known_sugg_ids[]' "$session_file" 2>/dev/null)

    # Process each suggestion
    echo "$sugg_json" | jq -c '.[]' | while read -r sugg; do
        local sugg_id=$(echo "$sugg" | jq -r '.id')

        # Check for duplicates
        if [[ "$DEDUPE_ENABLED" == "true" ]] && echo "$known_ids" | grep -q "^$sugg_id$"; then
            log_info "Suggestion $sugg_id bereits bekannt - übersprungen"
            continue
        fi

        # Generate new ID if needed
        if [[ -z "$sugg_id" || "$sugg_id" == "null" ]]; then
            local max_num=$(jq '[.suggestions[].id | select(. != null) | capture("SUG-(?<n>[0-9]+)") | .n | tonumber] | max // 0' "$sugg_file" 2>/dev/null || echo "0")
            sugg_id="SUG-$(printf '%03d' $((max_num + 1)))"
            sugg=$(echo "$sugg" | jq --arg id "$sugg_id" '.id = $id')
        fi

        # Add metadata
        sugg=$(echo "$sugg" | jq --arg ts "$(get_iso_timestamp)" '
            .found_at = $ts |
            .source = "explore-ralph" |
            .implemented = false
        ')

        # Add to sugg.json
        local tmp_file="$sugg_file.tmp"
        jq --argjson sugg "$sugg" '.suggestions += [$sugg]' "$sugg_file" > "$tmp_file" && mv "$tmp_file" "$sugg_file"

        # Add to known IDs
        tmp_file="$session_file.tmp"
        jq --arg id "$sugg_id" '.known_sugg_ids += [$id] | .known_sugg_ids = (.known_sugg_ids | unique)' \
            "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"

        log_success "Suggestion $sugg_id hinzugefügt"
    done
}

update_visited_pages() {
    local pages_json=$1
    local session_file="$SCRIPT_DIR/session.json"

    local tmp_file="$session_file.tmp"
    jq --argjson pages "$pages_json" '
        .visited_pages = (.visited_pages + $pages | unique)
    ' "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"
}

update_session_stats() {
    local interactions=$1
    local session_file="$SCRIPT_DIR/session.json"

    local tmp_file="$session_file.tmp"
    jq --argjson interactions "$interactions" '
        .exploration_stats.total_loops += 1 |
        .exploration_stats.total_interactions += $interactions
    ' "$session_file" > "$tmp_file" && mv "$tmp_file" "$session_file"
}

# ============================================
# Status & Summary
# ============================================

show_explore_status() {
    local session_file="$SCRIPT_DIR/session.json"
    local bugs_file="$SCRIPT_DIR/bugs.json"
    local sugg_file="$SCRIPT_DIR/sugg.json"
    local status_file="$LOG_DIR/status.json"

    echo -e "${ORANGE}=== RALF Explore Status ===${NC}"
    echo ""

    if [[ -f "$status_file" ]]; then
        local status=$(jq -r '.status' "$status_file" 2>/dev/null || echo "unknown")
        local loop=$(jq -r '.loop' "$status_file" 2>/dev/null || echo "0")
        local started=$(jq -r '.started_at' "$status_file" 2>/dev/null || echo "unknown")

        echo -e "Status:        ${BLUE}$status${NC}"
        echo -e "Loop:          ${BLUE}$loop${NC}"
        echo -e "Gestartet:     ${BLUE}$started${NC}"
    else
        echo -e "Status:        ${YELLOW}Nicht gestartet${NC}"
    fi

    echo ""

    if [[ -f "$bugs_file" ]]; then
        local bugs_total=$(jq '.bugs | length' "$bugs_file" 2>/dev/null || echo "0")
        local bugs_critical=$(jq '[.bugs[] | select(.severity == "critical")] | length' "$bugs_file" 2>/dev/null || echo "0")
        local bugs_major=$(jq '[.bugs[] | select(.severity == "major")] | length' "$bugs_file" 2>/dev/null || echo "0")

        echo -e "${RED}Bugs:${NC}"
        echo -e "  Total:       ${BLUE}$bugs_total${NC}"
        echo -e "  Critical:    ${RED}$bugs_critical${NC}"
        echo -e "  Major:       ${YELLOW}$bugs_major${NC}"
    fi

    echo ""

    if [[ -f "$sugg_file" ]]; then
        local sugg_total=$(jq '.suggestions | length' "$sugg_file" 2>/dev/null || echo "0")
        local sugg_high=$(jq '[.suggestions[] | select(.priority == "high")] | length' "$sugg_file" 2>/dev/null || echo "0")

        echo -e "${GREEN}Suggestions:${NC}"
        echo -e "  Total:       ${BLUE}$sugg_total${NC}"
        echo -e "  High Prio:   ${YELLOW}$sugg_high${NC}"
    fi

    echo ""

    if [[ -f "$session_file" ]]; then
        local pages=$(jq '.visited_pages | length' "$session_file" 2>/dev/null || echo "0")
        local interactions=$(jq '.exploration_stats.total_interactions' "$session_file" 2>/dev/null || echo "0")

        echo -e "${CYAN}Exploration:${NC}"
        echo -e "  Seiten:      ${BLUE}$pages${NC}"
        echo -e "  Interaktionen: ${BLUE}$interactions${NC}"
    fi

    echo ""
}

show_findings_summary() {
    local bugs_file="$SCRIPT_DIR/bugs.json"
    local sugg_file="$SCRIPT_DIR/sugg.json"

    echo ""
    echo -e "${ORANGE}=== Findings Summary ===${NC}"
    echo ""

    # Bugs Summary
    if [[ -f "$bugs_file" ]]; then
        local bugs_total=$(jq '.bugs | length' "$bugs_file" 2>/dev/null || echo "0")

        if [[ $bugs_total -gt 0 ]]; then
            echo -e "${RED}Bugs ($bugs_total):${NC}"
            jq -r '.bugs[] | "  [\(.severity)] \(.id): \(.title)"' "$bugs_file" 2>/dev/null
            echo ""
        else
            echo -e "${GREEN}Keine Bugs gefunden${NC}"
            echo ""
        fi
    fi

    # Suggestions Summary
    if [[ -f "$sugg_file" ]]; then
        local sugg_total=$(jq '.suggestions | length' "$sugg_file" 2>/dev/null || echo "0")

        if [[ $sugg_total -gt 0 ]]; then
            echo -e "${CYAN}Suggestions ($sugg_total):${NC}"
            jq -r '.suggestions[] | "  [\(.priority)] \(.id): \(.title)"' "$sugg_file" 2>/dev/null
            echo ""
        else
            echo -e "${GREEN}Keine Suggestions gefunden${NC}"
            echo ""
        fi
    fi

    # Next steps
    local bugs_total=$(jq '.bugs | length' "$bugs_file" 2>/dev/null || echo "0")
    if [[ $bugs_total -gt 0 ]]; then
        echo -e "${YELLOW}Nächste Schritte:${NC}"
        echo -e "  1. Bugs reviewen:  ${BLUE}cat $bugs_file | jq '.bugs[]'${NC}"
        echo -e "  2. Debug starten:  ${BLUE}cp bugs.json ../debug/ && cd ../debug && ./ralph.sh${NC}"
        echo ""
    fi
}

# Export functions
export -f init_explore_session
export -f sync_known_ids
export -f save_session
export -f reset_session
export -f get_session_context
export -f parse_explore_result
export -f process_new_bugs
export -f process_new_suggestions
export -f update_visited_pages
export -f update_session_stats
export -f show_explore_status
export -f show_findings_summary
