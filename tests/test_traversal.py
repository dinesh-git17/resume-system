"""Unit tests for RVS Validator file traversal.

Tests cover deterministic ordering, hidden file filtering,
and directory structure handling.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.rvs.validator.core import (
    ValidationContext,
    ValidationResult,
    _is_hidden,
    discover_yaml_files,
    format_errors,
    format_success,
    is_tty,
)


class TestDiscoverYamlFiles:
    """Tests for discover_yaml_files function."""

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        """Create a temporary project structure with YAML files."""
        data_dir = tmp_path / "data"
        content_dir = tmp_path / "content"
        config_dir = tmp_path / "config"
        experience_dir = content_dir / "experience"
        projects_dir = content_dir / "projects"

        data_dir.mkdir()
        content_dir.mkdir()
        config_dir.mkdir()
        experience_dir.mkdir(parents=True)
        projects_dir.mkdir(parents=True)

        (data_dir / "profile.yaml").write_text("name: Test\n")
        (data_dir / "education.yaml").write_text("entries: []\n")
        (data_dir / "skills.yaml").write_text("languages: []\n")

        (experience_dir / "company-a.yaml").write_text("entries: []\n")
        (experience_dir / "company-b.yaml").write_text("entries: []\n")

        (projects_dir / "projects.yaml").write_text("entries: []\n")

        (config_dir / "manifest.yaml").write_text("template: default\n")

        return tmp_path

    def test_discovers_yaml_files(self, project_root: Path) -> None:
        """Discover all YAML files in data/, content/, config/."""
        files = discover_yaml_files(project_root)
        assert len(files) == 7

    def test_alphabetical_order(self, project_root: Path) -> None:
        """Files are returned in strict alphabetical order."""
        files = discover_yaml_files(project_root)
        sorted_files = sorted(files)
        assert files == sorted_files

    def test_deterministic_order_across_runs(self, project_root: Path) -> None:
        """Multiple runs produce identical ordering."""
        files1 = discover_yaml_files(project_root)
        files2 = discover_yaml_files(project_root)
        files3 = discover_yaml_files(project_root)
        assert files1 == files2 == files3

    def test_ignores_hidden_files(self, project_root: Path) -> None:
        """Hidden files (.DS_Store, etc.) are ignored."""
        (project_root / "data" / ".DS_Store").write_text("binary garbage\n")
        (project_root / "data" / ".hidden.yaml").write_text("hidden: true\n")

        files = discover_yaml_files(project_root)
        filenames = [f.name for f in files]

        assert ".DS_Store" not in filenames
        assert ".hidden.yaml" not in filenames

    def test_ignores_hidden_directories(self, project_root: Path) -> None:
        """Files in hidden directories are ignored."""
        hidden_dir = project_root / "content" / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "secret.yaml").write_text("secret: true\n")

        files = discover_yaml_files(project_root)
        hidden_files = [f for f in files if ".hidden" in str(f)]

        assert len(hidden_files) == 0

    def test_ignores_non_yaml_extensions(self, project_root: Path) -> None:
        """Non-YAML files are ignored."""
        (project_root / "data" / "readme.txt").write_text("readme\n")
        (project_root / "data" / "config.json").write_text("{}\n")
        (project_root / "data" / "script.py").write_text("print()\n")

        files = discover_yaml_files(project_root)
        extensions = [f.suffix for f in files]

        assert all(ext in [".yaml", ".yml"] for ext in extensions)

    def test_supports_yml_extension(self, project_root: Path) -> None:
        """Both .yaml and .yml extensions are discovered."""
        (project_root / "data" / "extra.yml").write_text("data: true\n")

        files = discover_yaml_files(project_root)
        yml_files = [f for f in files if f.suffix == ".yml"]

        assert len(yml_files) == 1

    def test_missing_directories_handled(self, tmp_path: Path) -> None:
        """Missing data/, content/, config/ directories are handled gracefully."""
        files = discover_yaml_files(tmp_path)
        assert files == []

    def test_empty_directories_handled(self, tmp_path: Path) -> None:
        """Empty directories produce empty file list."""
        (tmp_path / "data").mkdir()
        (tmp_path / "content").mkdir()
        (tmp_path / "config").mkdir()

        files = discover_yaml_files(tmp_path)
        assert files == []

    def test_nested_content_directories(self, project_root: Path) -> None:
        """Files in nested content directories are discovered."""
        deep_dir = project_root / "content" / "experience" / "nested"
        deep_dir.mkdir()
        (deep_dir / "deep.yaml").write_text("deep: true\n")

        files = discover_yaml_files(project_root)
        deep_files = [f for f in files if f.name == "deep.yaml"]

        assert len(deep_files) == 1
        assert deep_files[0].parent.name == "nested"


class TestIsHidden:
    """Tests for _is_hidden helper function."""

    def test_hidden_file(self) -> None:
        """Detect hidden files (starting with dot)."""
        assert _is_hidden(Path(".hidden"))
        assert _is_hidden(Path(".DS_Store"))

    def test_hidden_directory_in_path(self) -> None:
        """Detect hidden directories in path."""
        assert _is_hidden(Path(".hidden/file.yaml"))
        assert _is_hidden(Path("data/.secret/config.yaml"))

    def test_not_hidden(self) -> None:
        """Non-hidden paths return False."""
        assert not _is_hidden(Path("file.yaml"))
        assert not _is_hidden(Path("data/profile.yaml"))
        assert not _is_hidden(Path("content/experience/google.yaml"))


class TestValidationContext:
    """Tests for ValidationContext dataclass."""

    def test_initial_state(self) -> None:
        """Initial context has zero errors and files."""
        ctx = ValidationContext()
        assert ctx.error_count == 0
        assert ctx.files_checked == 0
        assert ctx.has_errors is False

    def test_add_error(self) -> None:
        """Add error increments count."""
        ctx = ValidationContext()
        ctx.add_error(
            file_path=Path("test.yaml"),
            error_type="schema",
            message="Test error",
        )
        assert ctx.error_count == 1
        assert ctx.has_errors is True

    def test_add_error_with_field_path(self) -> None:
        """Add error with field path."""
        ctx = ValidationContext()
        ctx.add_error(
            file_path=Path("test.yaml"),
            error_type="schema",
            message="Invalid value",
            field_path="entries.0.id",
        )
        assert ctx.errors[0].field_path == "entries.0.id"

    def test_add_error_with_line_number(self) -> None:
        """Add error with line number."""
        ctx = ValidationContext()
        ctx.add_error(
            file_path=Path("test.yaml"),
            error_type="yaml_syntax",
            message="Syntax error",
            line=42,
        )
        assert ctx.errors[0].line == 42

    def test_files_checked_counter(self) -> None:
        """Files checked counter can be incremented."""
        ctx = ValidationContext()
        ctx.files_checked = 5
        assert ctx.files_checked == 5


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_format_without_field_path(self) -> None:
        """Format error without field path."""
        result = ValidationResult(
            file_path=Path("test.yaml"),
            error_type="yaml_syntax",
            message="Invalid YAML",
        )
        formatted = result.format(colorize=False)
        assert "[FAIL]" in formatted
        assert "test.yaml" in formatted
        assert "Invalid YAML" in formatted

    def test_format_with_field_path(self) -> None:
        """Format error with field path."""
        result = ValidationResult(
            file_path=Path("test.yaml"),
            error_type="schema",
            message="Required field missing",
            field_path="entries.0.id",
        )
        formatted = result.format(colorize=False)
        assert "entries.0.id" in formatted
        assert "Required field missing" in formatted

    def test_format_with_color(self) -> None:
        """Format error with ANSI colors."""
        result = ValidationResult(
            file_path=Path("test.yaml"),
            error_type="schema",
            message="Error",
        )
        formatted = result.format(colorize=True)
        assert "\033[31m" in formatted  # Red
        assert "\033[0m" in formatted  # Reset


class TestFormatErrors:
    """Tests for format_errors function."""

    def test_empty_context(self) -> None:
        """Empty context produces empty string."""
        ctx = ValidationContext()
        assert format_errors(ctx) == ""

    def test_groups_by_file(self) -> None:
        """Errors are grouped by file path."""
        ctx = ValidationContext()
        ctx.files_checked = 2
        ctx.add_error(Path("a.yaml"), "schema", "Error 1")
        ctx.add_error(Path("b.yaml"), "schema", "Error 2")
        ctx.add_error(Path("a.yaml"), "schema", "Error 3")

        formatted = format_errors(ctx, colorize=False)
        a_index = formatted.index("a.yaml")
        b_index = formatted.index("b.yaml")
        assert a_index < b_index

    def test_includes_summary(self) -> None:
        """Output includes summary with file and error counts."""
        ctx = ValidationContext()
        ctx.files_checked = 3
        ctx.add_error(Path("test.yaml"), "schema", "Error")

        formatted = format_errors(ctx, colorize=False)
        assert "3 files checked" in formatted
        assert "1 errors found" in formatted


class TestFormatSuccess:
    """Tests for format_success function."""

    def test_includes_pass_marker(self) -> None:
        """Success output includes [PASS] marker."""
        ctx = ValidationContext()
        ctx.files_checked = 5
        formatted = format_success(ctx, colorize=False)
        assert "[PASS]" in formatted

    def test_includes_file_count(self) -> None:
        """Success output includes file count."""
        ctx = ValidationContext()
        ctx.files_checked = 10
        formatted = format_success(ctx, colorize=False)
        assert "10 files checked" in formatted

    def test_with_color(self) -> None:
        """Success output with color includes green ANSI code."""
        ctx = ValidationContext()
        ctx.files_checked = 5
        formatted = format_success(ctx, colorize=True)
        assert "\033[32m" in formatted  # Green


class TestIsTty:
    """Tests for is_tty function."""

    def test_returns_bool(self) -> None:
        """is_tty returns a boolean value."""
        result = is_tty()
        assert isinstance(result, bool)
