#!/bin/bash
# RALF Plan Mode - PRD Generator, Task Breakdown, Tech Research
# Usage: ./ralph.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "  RALF Plan Mode"
echo "  PRD Generator | Task Breakdown | Tech Research"
echo "=========================================="
echo ""

# Show options
echo "Was möchtest du planen?"
echo ""
echo "  1) PRD generieren - Feature-Beschreibung → vollständige PRD"
echo "  2) Task Breakdown - Großes Feature → kleine Stories"
echo "  3) Tech Research - Technologien recherchieren und vergleichen"
echo ""
read -p "Wähle (1/2/3): " MODE

echo ""

case $MODE in
    1)
        echo "PRD Generator"
        echo "Beschreibe das Feature (Enter, dann Ctrl+D zum Beenden):"
        echo "------------------------------------------"
        INPUT=$(cat)
        TASK="PRD_GENERATOR"
        ;;
    2)
        echo "Task Breakdown"
        echo "Beschreibe das Feature das aufgeteilt werden soll (Enter, dann Ctrl+D zum Beenden):"
        echo "------------------------------------------"
        INPUT=$(cat)
        TASK="TASK_BREAKDOWN"
        ;;
    3)
        echo "Tech Research"
        echo "Was soll recherchiert werden? (Enter, dann Ctrl+D zum Beenden):"
        echo "------------------------------------------"
        INPUT=$(cat)
        TASK="TECH_RESEARCH"
        ;;
    *)
        echo "Ungültige Auswahl"
        exit 1
        ;;
esac

echo ""

# Create temp file with context
TEMP_FILE=$(mktemp)
cat > "$TEMP_FILE" << EOF
# Plan Mode Task: $TASK

$INPUT
EOF

echo "=========================================="
echo "  Starte Planung..."
echo "=========================================="
echo ""

# Run Claude with plan prompt - interactive mode for follow-ups
claude --print "$SCRIPT_DIR/prompt.md" \
    --allowedTools "Read,Glob,Grep,WebFetch,WebSearch" \
    --input-file "$TEMP_FILE"

# Cleanup
rm -f "$TEMP_FILE"
