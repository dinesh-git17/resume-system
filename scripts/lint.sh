#!/usr/bin/env bash
# scripts/lint.sh
# Unified Linting Entry Point
#
# Orchestrates ruff (lint/format), mypy (types), and yamllint in sequence.
# Fails fast on first tool failure. Preserves color output.
#
# Usage:
#   ./scripts/lint.sh           # Run all linters
#   ./scripts/lint.sh --fix     # Run ruff with auto-fix
#
# Exit Codes:
#   0  All checks passed
#   1  Lint/type/format violation detected

set -euo pipefail

# Resolve script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
BOLD='\033[1m'
NC='\033[0m'

print_step() {
    echo -e "${BOLD}[LINT]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Parse arguments
FIX_MODE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE="--fix"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Verify venv exists
if [[ ! -f ".venv/bin/python" ]]; then
    print_fail "Virtual environment not found. Run: ./scripts/bootstrap.sh"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RVS Unified Linting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Ruff linting
print_step "Running ruff check..."
if ! .venv/bin/ruff check scripts/ tests/ $FIX_MODE; then
    print_fail "ruff check failed"
    exit 1
fi
print_pass "ruff check passed"
echo ""

# Step 2: Ruff formatting check
print_step "Running ruff format check..."
if ! .venv/bin/ruff format --check scripts/ tests/; then
    print_fail "ruff format check failed (run with --fix to auto-format)"
    exit 1
fi
print_pass "ruff format passed"
echo ""

# Step 3: Mypy type checking
print_step "Running mypy..."
if ! .venv/bin/mypy scripts/; then
    print_fail "mypy failed"
    exit 1
fi
print_pass "mypy passed"
echo ""

# Step 4: Yamllint
print_step "Running yamllint..."
YAML_TARGETS=""
for dir in data content config; do
    if [[ -d "$dir" ]]; then
        YAML_TARGETS="$YAML_TARGETS $dir"
    fi
done

if [[ -n "$YAML_TARGETS" ]]; then
    if ! .venv/bin/yamllint -c .yamllint.yaml $YAML_TARGETS; then
        print_fail "yamllint failed"
        exit 1
    fi
    print_pass "yamllint passed"
else
    print_pass "yamllint skipped (no YAML directories found)"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_pass "All lint checks passed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
