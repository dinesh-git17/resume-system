# Skill: Integrity Enforcer (integrity-enforcer)

**Version:** 1.0.0
**Type:** Deterministic Verification
**Enforcement Level:** STRICT / BLOCKING

## Purpose

To serve as the final gateway before any build or commit. This skill executes the repository's validation pipeline (`scripts/validate.sh`) and translates raw CLI output into structured, actionable JSON reports. It enforces the "Verify" step of the agent's workflow.

## Responsibilities

1.  **Execute:** Run the canonical `scripts/validate.sh` validation suite.
2.  **Parse:** Capture `stdout` and `stderr`.
3.  **Analyze:** Categorize errors (Schema Violation, Missing ID, Duplicate ID, Profile Error).
4.  **Report:** Output a strictly formatted JSON object indicating Pass/Fail status and specific error locations.

## Boundaries (Strict Prohibitions)

- **NO Bypass:** You MUST NOT ignore a non-zero exit code. If this skill reports failure, you MUST stop and fix the issue.
- **NO Auto-Fix:** This skill only _reports_ errors. It does not attempt to patch files.
- **NO Hallucinated Success:** If the underlying script fails, this skill MUST report "FAIL".

## Input

- None (Runs on the current state of the repository).

## Output

- A JSON object with `status` ("PASS" | "FAIL") and a list of `errors`.

## Instructions

1.  Execute `python3 .claude/skills/integrity-enforcer/scripts/check.py`.
2.  Read the JSON output.
3.  If `status` is "FAIL", iterate through the `errors` list and fix the underlying YAML files.
4.  If `status` is "PASS", proceed to the next step (Build or Commit).
