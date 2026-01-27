#!/usr/bin/env bash
#
# Resume System Setup Script
# Bootstraps the development environment for the Resume-as-Code system.
# Compatible with macOS and Linux.
#

set -euo pipefail

# Colors for output (disabled if not a terminal)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect operating system
detect_os() {
    case "$(uname -s)" in
        Darwin*)    echo "macos" ;;
        Linux*)     echo "linux" ;;
        *)          echo "unknown" ;;
    esac
}

# Check Python version
check_python() {
    log_info "Checking Python version..."

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

        if [[ "$MAJOR" -ge 3 && "$MINOR" -ge 11 ]]; then
            log_info "Python $PYTHON_VERSION found (>= 3.11 required)"
            return 0
        else
            log_error "Python $PYTHON_VERSION found, but Python 3.11+ is required"
            return 1
        fi
    else
        log_error "Python 3 not found. Please install Python 3.11 or higher."
        return 1
    fi
}

# Check and install uv
check_uv() {
    log_info "Checking for uv package manager..."

    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version | head -n1)
        log_info "Found $UV_VERSION"
        return 0
    fi

    log_warn "uv not found. Installing uv..."

    # Install uv using the official installer
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Source the shell configuration to get uv in PATH
    if [[ -f "$HOME/.cargo/env" ]]; then
        source "$HOME/.cargo/env"
    elif [[ -f "$HOME/.local/bin/uv" ]]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi

    # Verify installation
    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version | head -n1)
        log_info "Successfully installed $UV_VERSION"
        return 0
    else
        log_error "Failed to install uv. Please install manually: https://github.com/astral-sh/uv"
        return 1
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing Python dependencies with uv..."
    uv sync
    log_info "Dependencies installed successfully"
}

# Setup pre-commit hooks
setup_precommit() {
    log_info "Setting up pre-commit hooks..."

    if [[ ! -d ".git" ]]; then
        log_warn "Git repository not initialized. Initializing..."
        git init
    fi

    .venv/bin/pre-commit install --hook-type pre-commit --hook-type commit-msg
    log_info "Pre-commit hooks installed (pre-commit and commit-msg stages)"
}

# Verify setup
verify_setup() {
    log_info "Verifying setup..."

    local errors=0

    # Check virtual environment
    if [[ ! -d ".venv" ]]; then
        log_error "Virtual environment not found"
        ((errors++))
    fi

    # Check Python version in venv
    if [[ -f ".venv/bin/python" ]]; then
        VENV_PYTHON=$(.venv/bin/python --version 2>&1)
        log_info "Virtual environment: $VENV_PYTHON"
    else
        log_error "Python not found in virtual environment"
        ((errors++))
    fi

    # Check pre-commit hook
    if [[ -f ".git/hooks/pre-commit" ]]; then
        log_info "Pre-commit hook installed"
    else
        log_error "Pre-commit hook not found"
        ((errors++))
    fi

    # Check commit-msg hook
    if [[ -f ".git/hooks/commit-msg" ]]; then
        log_info "Commit-msg hook installed"
    else
        log_error "Commit-msg hook not found"
        ((errors++))
    fi

    # Check protocol-zero script
    if [[ -x "scripts/protocol-zero.sh" ]]; then
        log_info "Protocol Zero script present and executable"
    else
        log_error "Protocol Zero script not found or not executable"
        ((errors++))
    fi

    # Check lockfile
    if [[ -f "uv.lock" ]]; then
        log_info "Lockfile present"
    else
        log_error "Lockfile (uv.lock) not found"
        ((errors++))
    fi

    return $errors
}

# Main execution
main() {
    local SCRIPT_DIR
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"

    echo ""
    echo "=========================================="
    echo "  Resume System - Environment Setup"
    echo "=========================================="
    echo ""

    local OS
    OS=$(detect_os)
    log_info "Detected OS: $OS"

    if [[ "$OS" == "unknown" ]]; then
        log_error "Unsupported operating system. This script supports macOS and Linux."
        exit 1
    fi

    # Run setup steps
    check_python || exit 1
    check_uv || exit 1
    install_dependencies || exit 1
    setup_precommit || exit 1

    echo ""
    if verify_setup; then
        echo ""
        echo "=========================================="
        echo -e "  ${GREEN}Setup completed successfully!${NC}"
        echo "=========================================="
        echo ""
        echo "To activate the environment:"
        echo "  source .venv/bin/activate"
        echo ""
        echo "To validate YAML files:"
        echo "  .venv/bin/yamllint data/ content/ config/"
        echo ""
    else
        echo ""
        echo "=========================================="
        echo -e "  ${RED}Setup completed with errors${NC}"
        echo "=========================================="
        exit 1
    fi
}

main "$@"
