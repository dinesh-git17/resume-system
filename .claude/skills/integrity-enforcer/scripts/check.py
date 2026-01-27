#!/usr/bin/env python3
"""
Integrity Enforcer Wrapper
Executes the main validation script and formats output as JSON for the agent.
"""

import json
import os
import subprocess
import sys

VALIDATOR_SCRIPT = "scripts/validate.sh"


def main() -> None:
    """Run validation script and output results as JSON."""
    # Ensure we are at repo root
    if not os.path.exists(VALIDATOR_SCRIPT):
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "errors": [
                        {
                            "file": "SYSTEM",
                            "msg": f"Critical: {VALIDATOR_SCRIPT} not found. Am I at repo root?",
                        }
                    ],
                }
            )
        )
        sys.exit(1)

    try:
        # Run the validator script
        # We capture stdout/stderr to parse them
        result = subprocess.run(
            ["bash", VALIDATOR_SCRIPT], capture_output=True, text=True, check=False
        )

        output_lines = result.stdout.splitlines() + result.stderr.splitlines()

        if result.returncode == 0:
            print(
                json.dumps(
                    {"status": "PASS", "errors": [], "message": "Repository Integrity Verified."},
                    indent=2,
                )
            )
            sys.exit(0)
        else:
            # Parse errors from standard log format
            # Assumes validator output format: [FAIL] <file>: <field> - <msg>
            structured_errors = []
            for line in output_lines:
                if "[FAIL]" in line or "Error:" in line:
                    structured_errors.append({"raw_log": line.strip()})

            # Fallback if no structured logs found but exit code was 1
            if not structured_errors:
                structured_errors.append(
                    {"raw_log": "Unknown validation failure. Check console output."}
                )

            print(
                json.dumps(
                    {"status": "FAIL", "errors": structured_errors, "exit_code": result.returncode},
                    indent=2,
                )
            )
            sys.exit(1)

    except OSError as e:
        print(json.dumps({"status": "FAIL", "errors": [{"file": "script", "msg": str(e)}]}))
        sys.exit(1)


if __name__ == "__main__":
    main()
