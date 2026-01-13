#!/bin/bash
# RALF Debug Mode - Interaktives Debugging mit Lerneffekt
# Usage: ./ralph.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
MAX_ATTEMPTS=3

cd "$PROJECT_ROOT"

echo "=========================================="
echo "  RALF Debug Mode"
echo "  Interaktives Debugging mit Lerneffekt"
echo "=========================================="
echo ""

# Collect problem description
echo "Beschreibe das Problem (Enter, dann Ctrl+D zum Beenden):"
echo "------------------------------------------"
PROBLEM=$(cat)
echo ""

# Collect error/stacktrace
echo "Füge den Error/Stacktrace ein (Enter, dann Ctrl+D zum Beenden):"
echo "------------------------------------------"
ERROR=$(cat)
echo ""

# Create temp file with context
TEMP_FILE=$(mktemp)
cat > "$TEMP_FILE" << EOF
# Debug Session Input

## Problem-Beschreibung
$PROBLEM

## Error/Stacktrace
\`\`\`
$ERROR
\`\`\`
EOF

echo "=========================================="
echo "  Starte Debug-Analyse..."
echo "=========================================="
echo ""

# Run Claude with debug prompt and input
claude --print "$SCRIPT_DIR/prompt.md" \
    --allowedTools "Bash,Read,Write,Edit,Glob,Grep" \
    --max-turns "$MAX_ATTEMPTS" \
    --input-file "$TEMP_FILE"

# Cleanup
rm -f "$TEMP_FILE"

echo ""
echo "=========================================="
echo "  RALF Debug Mode beendet"
echo "=========================================="
echo ""
echo "Hinweis: Änderungen wurden NICHT committed."
echo "Überprüfe die Änderungen und committe manuell wenn OK."
