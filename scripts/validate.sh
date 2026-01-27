#!/usr/bin/env bash
# scripts/validate.sh
# Schema Validation Wrapper
#
# Standard interface for RVS schema validation (RVS-P1-004).
# Wraps validator.py to provide deterministic execution path.
#
# Usage:
#   ./scripts/validate.sh                    # Validate all YAML files
#   ./scripts/validate.sh --target data/     # Validate specific target
#   ./scripts/validate.sh --help             # Show validator help
#
# Exit Codes:
#   0  All schemas valid
#   1  Schema violation or execution error

set -euo pipefail

# Resolve script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Verify venv exists
if [[ ! -f ".venv/bin/python" ]]; then
    echo "[ERROR] Virtual environment not found. Run: ./scripts/bootstrap.sh" >&2
    exit 1
fi

# Verify validator.py exists
if [[ ! -f "scripts/validator.py" ]]; then
    echo "[ERROR] scripts/validator.py not found. Schema validation unavailable." >&2
    exit 1
fi

# Execute validator with all passed arguments
exec .venv/bin/python scripts/validator.py "$@"
