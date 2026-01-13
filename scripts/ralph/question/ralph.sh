#!/bin/bash
# RALF Question Mode - Codebase Q&A
# Usage: ./ralph.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "  RALF Question Mode"
echo "  Codebase Q&A"
echo "=========================================="
echo ""

# Collect question
echo "Stelle deine Frage (Enter, dann Ctrl+D zum Beenden):"
echo "------------------------------------------"
QUESTION=$(cat)
echo ""

# Create temp file with context
TEMP_FILE=$(mktemp)
cat > "$TEMP_FILE" << EOF
# Frage zur Codebase

$QUESTION
EOF

echo "=========================================="
echo "  Analysiere Codebase..."
echo "=========================================="
echo ""

# Run Claude with question prompt - interactive mode for follow-ups
claude --print "$SCRIPT_DIR/prompt.md" \
    --allowedTools "Read,Glob,Grep" \
    --input-file "$TEMP_FILE"

# Cleanup
rm -f "$TEMP_FILE"
