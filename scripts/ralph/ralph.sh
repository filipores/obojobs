#!/bin/bash
# Ralph - Autonomous AI agent loop for obojobs
# Usage: ./ralph.sh [max_iterations]

set -e

MAX_ITERATIONS=${1:-10}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PRD_FILE="$SCRIPT_DIR/prd.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"

cd "$PROJECT_DIR"

# Archive previous run if branch changed
if [ -f "$PRD_FILE" ] && [ -f "$LAST_BRANCH_FILE" ]; then
  CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || echo "")
  LAST_BRANCH=$(cat "$LAST_BRANCH_FILE" 2>/dev/null || echo "")

  if [ -n "$CURRENT_BRANCH" ] && [ -n "$LAST_BRANCH" ] && [ "$CURRENT_BRANCH" != "$LAST_BRANCH" ]; then
    # Archive the previous run
    DATE=$(date +%Y-%m-%d)
    # Strip "ralph/" prefix from branch name for folder
    FOLDER_NAME=$(echo "$LAST_BRANCH" | sed 's|^ralph/||')
    ARCHIVE_FOLDER="$ARCHIVE_DIR/$DATE-$FOLDER_NAME"

    echo "📦 Archiving previous run: $LAST_BRANCH"
    mkdir -p "$ARCHIVE_FOLDER"
    [ -f "$PRD_FILE" ] && cp "$PRD_FILE" "$ARCHIVE_FOLDER/"
    [ -f "$PROGRESS_FILE" ] && cp "$PROGRESS_FILE" "$ARCHIVE_FOLDER/"
    echo "   Archived to: $ARCHIVE_FOLDER"

    # Reset progress file for new run
    echo "# Ralph Progress Log - obojobs" > "$PROGRESS_FILE"
    echo "Started: $(date)" >> "$PROGRESS_FILE"
    echo "" >> "$PROGRESS_FILE"
    echo "## Codebase Patterns" >> "$PROGRESS_FILE"
    echo "(Patterns werden hier gesammelt)" >> "$PROGRESS_FILE"
    echo "" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
  fi
fi

# Track current branch
if [ -f "$PRD_FILE" ]; then
  CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || echo "")
  if [ -n "$CURRENT_BRANCH" ]; then
    echo "$CURRENT_BRANCH" > "$LAST_BRANCH_FILE"
  fi
fi

# Initialize progress file if it doesn't exist
if [ ! -f "$PROGRESS_FILE" ]; then
  echo "# Ralph Progress Log - obojobs" > "$PROGRESS_FILE"
  echo "Started: $(date)" >> "$PROGRESS_FILE"
  echo "" >> "$PROGRESS_FILE"
  echo "## Codebase Patterns" >> "$PROGRESS_FILE"
  echo "(Patterns werden hier gesammelt)" >> "$PROGRESS_FILE"
  echo "" >> "$PROGRESS_FILE"
  echo "---" >> "$PROGRESS_FILE"
fi

# Function to push and create/update PR
push_and_pr() {
  local branch_name=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null)
  local prd_description=$(jq -r '.description // empty' "$PRD_FILE" 2>/dev/null)

  if [ -z "$branch_name" ]; then
    echo "⚠️  No branch name in prd.json, skipping push"
    return
  fi

  # Check if we have commits to push
  local unpushed=$(git log origin/"$branch_name"..HEAD 2>/dev/null | head -1 || echo "new")

  if [ -z "$unpushed" ]; then
    echo "📤 No new commits to push"
    return
  fi

  echo "📤 Pushing to origin/$branch_name..."
  git push -u origin "$branch_name" 2>/dev/null || git push origin "$branch_name"

  # Check if PR already exists
  local existing_pr=$(gh pr list --head "$branch_name" --state open --json number --jq '.[0].number' 2>/dev/null || echo "")

  if [ -z "$existing_pr" ]; then
    echo "🔀 Creating Pull Request..."

    # Get completed stories for PR body
    local completed_stories=$(jq -r '.userStories[] | select(.passes == true) | "- [x] \(.id): \(.title)"' "$PRD_FILE" 2>/dev/null)
    local pending_stories=$(jq -r '.userStories[] | select(.passes == false) | "- [ ] \(.id): \(.title)"' "$PRD_FILE" 2>/dev/null)

    # Create PR
    gh pr create --base main --head "$branch_name" \
      --title "feat: $prd_description" \
      --body "$(cat <<EOF
## Summary

$prd_description

## Stories

$completed_stories
$pending_stories

## Status

🤖 This PR is being worked on by Ralph (autonomous AI agent).
PR will be updated automatically as stories are completed.

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" || echo "⚠️  PR creation failed (might already exist)"

    local pr_url=$(gh pr list --head "$branch_name" --state open --json url --jq '.[0].url' 2>/dev/null || echo "")
    if [ -n "$pr_url" ]; then
      echo "🔗 PR: $pr_url"
    fi
  else
    echo "🔄 PR #$existing_pr updated with new commits"

    # Update PR body with current status
    local completed_stories=$(jq -r '.userStories[] | select(.passes == true) | "- [x] \(.id): \(.title)"' "$PRD_FILE" 2>/dev/null)
    local pending_stories=$(jq -r '.userStories[] | select(.passes == false) | "- [ ] \(.id): \(.title)"' "$PRD_FILE" 2>/dev/null)

    gh pr edit "$existing_pr" --body "$(cat <<EOF
## Summary

$prd_description

## Stories

$completed_stories
$pending_stories

## Status

🤖 This PR is being worked on by Ralph (autonomous AI agent).
PR will be updated automatically as stories are completed.

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" 2>/dev/null || echo "⚠️  Could not update PR body"
  fi
}

echo ""
echo "🚀 Starting Ralph for obojobs"
echo "📁 Project: $PROJECT_DIR"
echo "🔄 Max iterations: $MAX_ITERATIONS"
echo ""

for i in $(seq 1 $MAX_ITERATIONS); do
  echo ""
  echo "═══════════════════════════════════════════════════════"
  echo "  Ralph Iteration $i of $MAX_ITERATIONS"
  echo "═══════════════════════════════════════════════════════"

  # Run claude with the ralph prompt
  OUTPUT=$(cat "$SCRIPT_DIR/prompt.md" | claude --dangerously-skip-permissions 2>&1 | tee /dev/stderr) || true

  # Push changes and create/update PR after each iteration
  echo ""
  echo "───────────────────────────────────────────────────────"
  push_and_pr
  echo "───────────────────────────────────────────────────────"

  # Check for completion signal
  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo ""
    echo "✅ Ralph completed all tasks!"
    echo "   Completed at iteration $i of $MAX_ITERATIONS"

    # Final push
    push_and_pr

    echo ""
    echo "🎉 All done! PR is ready for review."
    exit 0
  fi

  echo ""
  echo "⏳ Iteration $i complete. Continuing..."
  sleep 2
done

echo ""
echo "⚠️ Ralph reached max iterations ($MAX_ITERATIONS) without completing all tasks."
echo "   Check $PROGRESS_FILE for status."

# Final push even if not complete
push_and_pr

exit 1
