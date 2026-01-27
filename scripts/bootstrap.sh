#!/usr/bin/env bash
# scripts/bootstrap.sh
# Idempotent Development Environment Bootstrap
#
# Initializes the Python environment using uv, installs dependencies,
# and configures git hooks. Safe to run multiple times.
#
# Usage:
#   ./scripts/bootstrap.sh
#
# Exit Codes:
#   0  Success (environment ready)
#   1  Failure (missing dependency or setup error)

set -euo pipefail

# Resolve script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m'

print_step() {
    echo -e "${BOLD}[STEP]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
}

# Check Python version (requires 3.11+)
check_python_version() {
    print_step "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        print_fail "python3 not found in PATH"
        exit 1
    fi

    local python_version
    python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    local major
    major=$(echo "$python_version" | cut -d. -f1)
    local minor
    minor=$(echo "$python_version" | cut -d. -f2)

    if [[ "$major" -lt 3 ]] || { [[ "$major" -eq 3 ]] && [[ "$minor" -lt 11 ]]; }; then
        print_fail "Python 3.11+ required, found $python_version"
        exit 1
    fi

    print_pass "Python $python_version detected"
}

# Check uv is available
check_uv() {
    print_step "Checking uv package manager..."

    if ! command -v uv &> /dev/null; then
        print_fail "uv not found in PATH. Install via: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    local uv_version
    uv_version=$(uv --version | head -1)
    print_pass "$uv_version detected"
}

# Create or update virtual environment
setup_venv() {
    print_step "Setting up virtual environment..."

    cd "$PROJECT_ROOT"

    # Check if .venv exists and is valid
    if [[ -d ".venv" ]] && [[ -f ".venv/bin/python" ]]; then
        # Verify the venv Python is functional
        if .venv/bin/python --version &> /dev/null; then
            print_skip "Virtual environment already exists and is valid"
        else
            print_step "Recreating corrupted virtual environment..."
            rm -rf .venv
            uv venv --python python3.11
            print_pass "Virtual environment recreated"
        fi
    else
        uv venv --python python3.11
        print_pass "Virtual environment created"
    fi
}

# Install dependencies
install_dependencies() {
    print_step "Installing dependencies..."

    cd "$PROJECT_ROOT"

    # uv sync installs all dependencies including dev
    uv sync --all-groups

    print_pass "Dependencies installed"
}

# Setup pre-commit hooks
setup_precommit() {
    print_step "Configuring pre-commit hooks..."

    cd "$PROJECT_ROOT"

    # Check if pre-commit config exists
    if [[ ! -f ".pre-commit-config.yaml" ]]; then
        print_skip "No .pre-commit-config.yaml found, skipping hooks"
        return 0
    fi

    # Check if hooks are already installed
    if [[ -f ".git/hooks/pre-commit" ]] && grep -q "pre-commit" ".git/hooks/pre-commit" 2>/dev/null; then
        print_skip "Pre-commit hooks already installed"
    else
        # Install hooks using the venv pre-commit
        .venv/bin/pre-commit install
        .venv/bin/pre-commit install --hook-type commit-msg
        print_pass "Pre-commit hooks installed"
    fi
}

# Verify setup
verify_setup() {
    print_step "Verifying setup..."

    cd "$PROJECT_ROOT"

    local errors=0

    # Check venv activation works
    if ! .venv/bin/python -c "import sys; sys.exit(0)" 2>/dev/null; then
        print_fail "Virtual environment Python not functional"
        errors=$((errors + 1))
    fi

    # Check key packages are installed
    for pkg in pydantic yaml jinja2; do
        if ! .venv/bin/python -c "import $pkg" 2>/dev/null; then
            print_fail "Package $pkg not installed"
            errors=$((errors + 1))
        fi
    done

    # Check pre-commit is available
    if ! .venv/bin/pre-commit --version &>/dev/null; then
        print_fail "pre-commit not available"
        errors=$((errors + 1))
    fi

    if [[ $errors -gt 0 ]]; then
        print_fail "Setup verification failed with $errors errors"
        exit 1
    fi

    print_pass "Setup verification complete"
}

main() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "RVS Development Environment Bootstrap"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    check_python_version
    check_uv
    setup_venv
    install_dependencies
    setup_precommit
    verify_setup

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_pass "Bootstrap complete. Environment ready."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Activate with: source .venv/bin/activate"
    echo ""
}

main "$@"
