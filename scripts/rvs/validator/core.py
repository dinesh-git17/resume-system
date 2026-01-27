"""Core validation logic for RVS Validator.

Provides deterministic file traversal, YAML validation, and error accumulation.
Traversal is strictly alphabetical to ensure consistent behavior across OS.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import ValidationError

from scripts.rvs.loader import YAMLLoadError, YAMLValidationError, load_yaml_strict
from scripts.rvs.validator.registry import UnknownPathError, get_model_for_path


@dataclass
class ValidationResult:
    """Structured validation error for reporting."""

    file_path: Path
    error_type: str
    message: str
    field_path: str | None = None
    line: int | None = None

    def format(self, colorize: bool = False) -> str:
        """Format error for human-readable output.

        Args:
            colorize: If True, use ANSI color codes.

        Returns:
            Formatted error string.
        """
        red = "\033[31m" if colorize else ""
        reset = "\033[0m" if colorize else ""

        filename = self.file_path.name
        if self.field_path:
            return f"{red}[FAIL]{reset} {filename}: {self.field_path} - {self.message}"
        return f"{red}[FAIL]{reset} {filename}: {self.message}"


@dataclass
class ValidationContext:
    """Accumulates validation state across multiple files."""

    errors: list[ValidationResult] = field(default_factory=list)
    files_checked: int = 0
    id_index: dict[str, Path] = field(default_factory=dict)

    def add_error(
        self,
        file_path: Path,
        error_type: str,
        message: str,
        field_path: str | None = None,
        line: int | None = None,
    ) -> None:
        """Record a validation error.

        Args:
            file_path: Path to the file that failed validation.
            error_type: Category of error (yaml_syntax, schema, etc.).
            message: Human-readable error description.
            field_path: Dot-separated path to the failing field.
            line: Line number in YAML file where error occurred.
        """
        self.errors.append(
            ValidationResult(
                file_path=file_path,
                error_type=error_type,
                message=message,
                field_path=field_path,
                line=line,
            )
        )

    @property
    def error_count(self) -> int:
        """Total number of errors recorded."""
        return len(self.errors)

    @property
    def has_errors(self) -> bool:
        """Check if any errors were recorded."""
        return len(self.errors) > 0


def _is_hidden(path: Path) -> bool:
    """Check if a file or any parent directory is hidden.

    Args:
        path: Path to check.

    Returns:
        True if path contains a hidden component.
    """
    return any(part.startswith(".") for part in path.parts)


def discover_yaml_files(root: Path) -> list[Path]:
    """Find all YAML files in data/, content/, and config/ directories.

    Traversal is deterministic (alphabetically sorted) to ensure consistent
    behavior across Linux and macOS. Hidden files and directories are ignored.

    Args:
        root: Root directory of the project.

    Returns:
        Sorted list of YAML file paths.
    """
    yaml_files: list[Path] = []

    for subdir in sorted(["config", "content", "data"]):
        dir_path = root / subdir
        if not dir_path.exists() or not dir_path.is_dir():
            continue

        for extension in ["*.yaml", "*.yml"]:
            for yaml_file in dir_path.rglob(extension):
                if not _is_hidden(yaml_file.relative_to(root)):
                    yaml_files.append(yaml_file)

    return sorted(yaml_files)


def extract_pydantic_errors(
    validation_error: ValidationError,
    file_path: Path,
) -> list[ValidationResult]:
    """Convert Pydantic ValidationError to structured error list.

    Args:
        validation_error: Pydantic validation exception.
        file_path: Path to the file that failed validation.

    Returns:
        List of structured validation errors with field paths.
    """
    errors: list[ValidationResult] = []
    for error in validation_error.errors():
        loc_parts = [str(p) for p in error["loc"]]
        field_path = ".".join(loc_parts) if loc_parts else None
        errors.append(
            ValidationResult(
                file_path=file_path,
                error_type="schema",
                message=error["msg"],
                field_path=field_path,
            )
        )
    return errors


def extract_yaml_line_number(yaml_error: yaml.YAMLError) -> int | None:
    """Extract line number from YAML parsing error.

    Args:
        yaml_error: YAML parsing exception.

    Returns:
        Line number where error occurred, or None if unavailable.
    """
    if hasattr(yaml_error, "problem_mark") and yaml_error.problem_mark is not None:
        return int(yaml_error.problem_mark.line) + 1
    return None


def validate_yaml_file(
    file_path: Path,
    root: Path,
    ctx: ValidationContext,
) -> bool:
    """Validate a single YAML file against its schema.

    Args:
        file_path: Path to the YAML file.
        root: Root directory of the project.
        ctx: Validation context for accumulating results.

    Returns:
        True if validation passed, False otherwise.
    """
    ctx.files_checked += 1

    try:
        model_class = get_model_for_path(file_path, root, strict=False)
    except UnknownPathError as e:
        ctx.add_error(
            file_path=file_path,
            error_type="registry",
            message=str(e),
        )
        return False

    if model_class is None:
        return True

    try:
        with open(file_path, encoding="utf-8") as f:
            yaml.safe_load(f)
    except yaml.YAMLError as e:
        line_num = extract_yaml_line_number(e)
        ctx.add_error(
            file_path=file_path,
            error_type="yaml_syntax",
            message=f"Invalid YAML syntax: {e}",
            line=line_num,
        )
        return False

    try:
        load_yaml_strict(file_path, model_class)
        return True
    except YAMLLoadError as e:
        ctx.add_error(
            file_path=file_path,
            error_type="yaml_load",
            message=e.message,
        )
        return False
    except YAMLValidationError as e:
        for err in extract_pydantic_errors(e.validation_error, file_path):
            ctx.errors.append(err)
        return False


def format_errors(ctx: ValidationContext, colorize: bool = False) -> str:
    """Format validation errors for human-readable output.

    Groups errors by file path and formats with field paths where available.

    Args:
        ctx: Validation context with accumulated errors.
        colorize: If True, use ANSI color codes.

    Returns:
        Formatted error string.
    """
    if not ctx.has_errors:
        return ""

    red = "\033[31m" if colorize else ""
    reset = "\033[0m" if colorize else ""

    errors_by_file: dict[Path, list[ValidationResult]] = {}
    for error in ctx.errors:
        if error.file_path not in errors_by_file:
            errors_by_file[error.file_path] = []
        errors_by_file[error.file_path].append(error)

    lines: list[str] = []
    for file_path in sorted(errors_by_file.keys()):
        lines.append(f"\n{file_path}:")
        for error in errors_by_file[file_path]:
            if error.field_path:
                lines.append(f"  {red}[FAIL]{reset} {error.field_path} - {error.message}")
            else:
                lines.append(f"  {red}[FAIL]{reset} {error.message}")

    lines.append(f"\n{ctx.files_checked} files checked, {ctx.error_count} errors found.")
    return "\n".join(lines)


def format_success(ctx: ValidationContext, colorize: bool = False) -> str:
    """Format success message for output.

    Args:
        ctx: Validation context with file count.
        colorize: If True, use ANSI color codes.

    Returns:
        Formatted success string.
    """
    green = "\033[32m" if colorize else ""
    reset = "\033[0m" if colorize else ""
    return (
        f"{green}[PASS]{reset} {ctx.files_checked} files checked, {ctx.error_count} errors found."
    )


def is_tty() -> bool:
    """Check if stdout is connected to a TTY.

    Returns:
        True if stdout is a TTY, False otherwise.
    """
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
