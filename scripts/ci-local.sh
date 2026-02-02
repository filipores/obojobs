#!/bin/bash
#
# Local CI mirror script - runs the same checks as GitHub CI
# Produces JSON results compatible with aggregate-local-results.js
#

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$PROJECT_ROOT/.ci-results"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
SKIP_E2E=false
SKIP_FRONTEND=false
SKIP_BACKEND=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-e2e)
            SKIP_E2E=true
            shift
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        --skip-backend)
            SKIP_BACKEND=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --skip-e2e       Skip E2E tests (faster)"
            echo "  --skip-frontend  Skip frontend checks"
            echo "  --skip-backend   Skip backend checks"
            echo "  --verbose, -v    Show full output"
            echo "  --help, -h       Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Initialize results directory
rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR"

# Initialize overall status
OVERALL_STATUS="success"

# Helper function to record result
record_result() {
    local job=$1
    local step=$2
    local status=$3
    local duration=$4
    local output_file=$5

    local output=""
    if [ -f "$output_file" ]; then
        output=$(cat "$output_file" | head -c 10000)
    fi

    # Create JSON result
    cat > "$RESULTS_DIR/${job}_${step}.json" << EOF
{
    "job": "$job",
    "step": "$step",
    "status": "$status",
    "duration_ms": $duration,
    "timestamp": "$TIMESTAMP",
    "output": $(echo "$output" | jq -Rs .)
}
EOF

    if [ "$status" = "failure" ]; then
        OVERALL_STATUS="failure"
    fi
}

# Get timestamp in milliseconds (portable)
get_timestamp_ms() {
    if command -v gdate &> /dev/null; then
        gdate +%s%3N
    elif date +%s%3N 2>/dev/null | grep -q '^[0-9]*$'; then
        date +%s%3N
    else
        echo $(($(date +%s) * 1000))
    fi
}

# Helper function to run a step
run_step() {
    local job=$1
    local step=$2
    local cmd=$3
    local working_dir=$4

    echo -e "${BLUE}[$job]${NC} Running: $step"

    local output_file="$RESULTS_DIR/${job}_${step}.log"
    local start_time=$(get_timestamp_ms)

    if [ "$VERBOSE" = true ]; then
        (cd "$working_dir" && eval "$cmd" 2>&1 | tee "$output_file")
        local exit_code=${PIPESTATUS[0]}
    else
        (cd "$working_dir" && eval "$cmd" > "$output_file" 2>&1)
        local exit_code=$?
    fi

    local end_time=$(get_timestamp_ms)
    local duration=$((end_time - start_time))

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}  ✓ $step passed${NC} (${duration}ms)"
        record_result "$job" "$step" "success" "$duration" "$output_file"
    else
        echo -e "${RED}  ✗ $step failed${NC} (${duration}ms)"
        if [ "$VERBOSE" = false ]; then
            echo -e "${YELLOW}  Output:${NC}"
            tail -20 "$output_file" | sed 's/^/    /'
        fi
        record_result "$job" "$step" "failure" "$duration" "$output_file"
    fi

    return $exit_code
}

echo ""
echo "=========================================="
echo "  Local CI Mirror"
echo "  $(date)"
echo "=========================================="
echo ""

# Backend tests
if [ "$SKIP_BACKEND" = false ]; then
    echo -e "${BLUE}=== Backend Tests ===${NC}"

    BACKEND_DIR="$PROJECT_ROOT/backend"

    if [ -d "$BACKEND_DIR" ]; then
        # Check for Python
        if command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
        elif command -v python &> /dev/null; then
            PYTHON_CMD="python"
        else
            echo -e "${RED}  ✗ Python not found${NC}"
            record_result "backend-tests" "python-check" "failure" 0 /dev/null
        fi

        if [ -n "$PYTHON_CMD" ]; then
            # Ruff linter
            if command -v ruff &> /dev/null; then
                run_step "backend-tests" "ruff-lint" "ruff check ." "$BACKEND_DIR"
            else
                echo -e "${YELLOW}  ⚠ ruff not installed, skipping lint${NC}"
            fi

            # Mypy type checking
            if command -v mypy &> /dev/null; then
                run_step "backend-tests" "mypy" "mypy . --config-file mypy.ini" "$BACKEND_DIR"
            else
                echo -e "${YELLOW}  ⚠ mypy not installed, skipping type check${NC}"
            fi

            # Pytest
            if $PYTHON_CMD -c "import pytest" 2>/dev/null; then
                run_step "backend-tests" "pytest" "$PYTHON_CMD -m pytest --cov=. --cov-report=term-missing --cov-fail-under=55 -q" "$BACKEND_DIR"
            else
                echo -e "${YELLOW}  ⚠ pytest not installed, skipping tests${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}  ⚠ Backend directory not found${NC}"
    fi

    echo ""
fi

# Frontend tests
if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "${BLUE}=== Frontend Tests ===${NC}"

    FRONTEND_DIR="$PROJECT_ROOT/frontend"

    if [ -d "$FRONTEND_DIR" ]; then
        # Check for Node.js
        if command -v npm &> /dev/null; then
            # Install dependencies if needed
            if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
                echo -e "${YELLOW}  Installing dependencies...${NC}"
                (cd "$FRONTEND_DIR" && npm ci --silent)
            fi

            # ESLint
            run_step "frontend-tests" "eslint" "npm run lint -- --max-warnings=100" "$FRONTEND_DIR"

            # Vitest
            run_step "frontend-tests" "vitest" "npm run test:coverage" "$FRONTEND_DIR"

            # Build
            run_step "frontend-tests" "build" "npm run build" "$FRONTEND_DIR"
        else
            echo -e "${YELLOW}  ⚠ npm not found, skipping frontend tests${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠ Frontend directory not found${NC}"
    fi

    echo ""
fi

# E2E tests
if [ "$SKIP_E2E" = false ] && [ "$SKIP_FRONTEND" = false ]; then
    echo -e "${BLUE}=== E2E Tests ===${NC}"

    FRONTEND_DIR="$PROJECT_ROOT/frontend"

    if [ -d "$FRONTEND_DIR" ] && command -v npm &> /dev/null; then
        # Check if Playwright is installed
        if [ -d "$FRONTEND_DIR/node_modules/@playwright" ]; then
            run_step "e2e-tests" "playwright" "npm run test:e2e" "$FRONTEND_DIR"
        else
            echo -e "${YELLOW}  ⚠ Playwright not installed, run 'npx playwright install' first${NC}"
        fi
    fi

    echo ""
fi

# Aggregate results
echo -e "${BLUE}=== Aggregating Results ===${NC}"
if command -v node &> /dev/null; then
    node "$SCRIPT_DIR/aggregate-local-results.js" "$RESULTS_DIR"
else
    echo -e "${YELLOW}  Node.js not available, creating basic summary...${NC}"
    # Create a basic JSON summary without node
    cat > "$RESULTS_DIR/ci-results.json" << EOF
{
    "workflow_run": {
        "id": "local-$(date +%s)",
        "name": "CI (Local)",
        "status": "completed",
        "conclusion": "$OVERALL_STATUS",
        "run_started_at": "$TIMESTAMP",
        "event": "local"
    },
    "summary": {
        "conclusion": "$OVERALL_STATUS"
    }
}
EOF
fi

# Final summary
echo ""
echo "=========================================="
if [ "$OVERALL_STATUS" = "success" ]; then
    echo -e "  ${GREEN}All checks passed!${NC}"
else
    echo -e "  ${RED}Some checks failed${NC}"
fi
echo "=========================================="
echo ""
echo "Results saved to: $RESULTS_DIR/ci-results.json"

# Exit with appropriate code
if [ "$OVERALL_STATUS" = "success" ]; then
    exit 0
else
    exit 1
fi
