"""Integration tests for the RVS validation engine.

Tests cover schema validation, ID uniqueness, manifest referential integrity,
and error reporting using both canonical and poisoned test fixtures.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"
POISONED_DIR = FIXTURES_DIR / "poisoned"
CANONICAL_DIR = FIXTURES_DIR / "canonical"


def run_validator(target: Path) -> tuple[int, str, str]:
    """Execute validator.py and capture output.

    Args:
        target: Directory to validate.

    Returns:
        Tuple of (exit_code, stdout, stderr).
    """
    result = subprocess.run(
        [sys.executable, "scripts/validator.py", "--target", str(target)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    return result.returncode, result.stdout, result.stderr


class TestCanonicalData:
    """Tests verifying valid data passes validation."""

    def test_canonical_fixtures_pass(self) -> None:
        """Canonical test fixtures pass validation with exit code 0."""
        exit_code, stdout, stderr = run_validator(CANONICAL_DIR)
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}. stderr: {stderr}"
        assert "0 errors found" in stdout

    def test_main_repository_passes(self) -> None:
        """Main repository data passes validation."""
        repo_root = Path(__file__).parent.parent
        exit_code, stdout, stderr = run_validator(repo_root)
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}. stderr: {stderr}"


class TestSchemaViolation:
    """Tests for schema validation errors."""

    def test_invalid_email_detected(self) -> None:
        """Invalid email format causes validation failure."""
        target = POISONED_DIR / "schema_violation"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "email" in stderr.lower()

    def test_invalid_resume_id_detected(self) -> None:
        """Uppercase ResumeID causes validation failure."""
        target = POISONED_DIR / "schema_violation"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "INVALID_UPPERCASE_ID" in stderr or "lowercase" in stderr.lower()


class TestYAMLSyntax:
    """Tests for YAML syntax error detection."""

    def test_invalid_yaml_syntax_detected(self) -> None:
        """Invalid YAML syntax causes validation failure."""
        target = POISONED_DIR / "yaml_syntax"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "yaml" in stderr.lower() or "syntax" in stderr.lower()


class TestDuplicateID:
    """Tests for duplicate ID detection."""

    def test_duplicate_entry_id_across_files(self) -> None:
        """Duplicate entry IDs across files are detected."""
        target = POISONED_DIR / "duplicate_id"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "duplicate" in stderr.lower()
        assert "duplicate-entry-id" in stderr.lower()

    def test_duplicate_bullet_id_detected(self) -> None:
        """Duplicate bullet IDs within project file are detected."""
        target = POISONED_DIR / "duplicate_id"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "duplicate-bullet-id" in stderr.lower()


class TestBrokenReferences:
    """Tests for manifest referential integrity."""

    def test_nonexistent_profile_detected(self) -> None:
        """Missing profile file reference is detected."""
        target = POISONED_DIR / "broken_reference"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "nonexistent-profile" in stderr.lower()

    def test_nonexistent_experience_id_detected(self) -> None:
        """Missing experience ID reference is detected."""
        target = POISONED_DIR / "broken_reference"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "nonexistent-experience-id" in stderr.lower()

    def test_nonexistent_bullet_id_detected(self) -> None:
        """Missing bullet ID reference is detected."""
        target = POISONED_DIR / "broken_reference"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "nonexistent-bullet-id" in stderr.lower()

    def test_nonexistent_project_id_detected(self) -> None:
        """Missing project ID reference is detected."""
        target = POISONED_DIR / "broken_reference"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "nonexistent-project-id" in stderr.lower()


class TestErrorReporting:
    """Tests for structured error reporting."""

    def test_errors_grouped_by_file(self) -> None:
        """Errors are grouped by filename in output."""
        target = POISONED_DIR / "broken_reference"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "broken-manifest.yaml:" in stderr

    def test_summary_footer_present(self) -> None:
        """Summary footer with file count and error count is present."""
        target = POISONED_DIR / "schema_violation"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "files checked" in stderr.lower()
        assert "errors found" in stderr.lower()

    def test_field_path_in_schema_error(self) -> None:
        """Schema errors include field path."""
        target = POISONED_DIR / "schema_violation"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "entries.0" in stderr or "email" in stderr


class TestExitCodes:
    """Tests for Unix-compliant exit codes."""

    def test_success_exit_code_zero(self) -> None:
        """Successful validation returns exit code 0."""
        exit_code, _, _ = run_validator(CANONICAL_DIR)
        assert exit_code == 0

    def test_validation_error_exit_code_one(self) -> None:
        """Validation errors return exit code 1."""
        exit_code, _, _ = run_validator(POISONED_DIR / "schema_violation")
        assert exit_code == 1

    def test_nonexistent_target_exit_code_two(self) -> None:
        """Nonexistent target directory returns exit code 2."""
        exit_code, _, stderr = run_validator(Path("/nonexistent/path"))
        assert exit_code == 2
        assert "does not exist" in stderr.lower()


class TestCLIInterface:
    """Tests for CLI argument handling."""

    def test_default_target_is_cwd(self) -> None:
        """Default target is current working directory when --target not specified."""
        repo_root = Path(__file__).parent.parent
        result = subprocess.run(
            [sys.executable, "scripts/validator.py"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        assert result.returncode == 0

    def test_help_flag(self) -> None:
        """--help flag displays usage information."""
        repo_root = Path(__file__).parent.parent
        result = subprocess.run(
            [sys.executable, "scripts/validator.py", "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        assert result.returncode == 0
        assert "target" in result.stdout.lower()


class TestValidateShWrapper:
    """Tests for scripts/validate.sh shell wrapper."""

    def test_wrapper_invokes_validator(self) -> None:
        """validate.sh correctly invokes validator.py."""
        repo_root = Path(__file__).parent.parent
        result = subprocess.run(
            ["./scripts/validate.sh"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        assert result.returncode == 0
        assert "files checked" in result.stdout.lower()

    def test_wrapper_passes_arguments(self) -> None:
        """validate.sh passes arguments to validator.py."""
        repo_root = Path(__file__).parent.parent
        result = subprocess.run(
            ["./scripts/validate.sh", "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        assert result.returncode == 0
        assert "target" in result.stdout.lower()

    def test_wrapper_returns_correct_exit_code(self) -> None:
        """validate.sh returns correct exit code from validator.py."""
        repo_root = Path(__file__).parent.parent
        result = subprocess.run(
            ["./scripts/validate.sh", "--target", str(POISONED_DIR / "schema_violation")],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        assert result.returncode == 1


class TestErrorFormat:
    """Tests for structured error format with [FAIL] prefix."""

    def test_fail_prefix_in_error_output(self) -> None:
        """Error output contains [FAIL] prefix."""
        target = POISONED_DIR / "schema_violation"
        exit_code, stdout, stderr = run_validator(target)
        assert exit_code == 1
        assert "[FAIL]" in stderr

    def test_pass_prefix_in_success_output(self) -> None:
        """Success output contains [PASS] prefix."""
        exit_code, stdout, stderr = run_validator(CANONICAL_DIR)
        assert exit_code == 0
        assert "[PASS]" in stdout
