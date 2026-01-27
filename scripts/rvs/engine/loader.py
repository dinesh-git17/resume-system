"""Manifest loading for the RVS build engine.

Provides strict YAML manifest parsing with Pydantic validation
for build configuration files.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from scripts.rvs.loader import YAMLLoadError, load_yaml_strict
from scripts.rvs.models.manifest import Manifest


class ManifestValidationError(Exception):
    """Raised when manifest loading or validation fails.

    Wraps underlying YAML or Pydantic errors to provide a consistent
    error interface for manifest-specific failures.
    """

    def __init__(self, path: Path, message: str, cause: Exception | None = None):
        self.path = path
        self.message = message
        self.cause = cause
        super().__init__(f"Manifest validation failed for '{path}': {message}")


def load_manifest(path: Path | str) -> Manifest:
    """Load and validate a build manifest from a YAML file.

    Parses the manifest file and validates it against the strict Manifest
    Pydantic schema. Unknown fields are rejected (extra='forbid').

    Args:
        path: Path to the manifest YAML file (typically in config/).

    Returns:
        Validated Manifest instance.

    Raises:
        ManifestValidationError: If the file cannot be read, parsed,
            or fails schema validation.
    """
    path = Path(path) if isinstance(path, str) else path

    if not path.exists():
        raise ManifestValidationError(
            path,
            "File not found",
            cause=FileNotFoundError(f"Manifest file not found: {path}"),
        )

    try:
        return load_yaml_strict(path, Manifest)
    except YAMLLoadError as e:
        raise ManifestValidationError(path, e.message, cause=e) from e
    except ValidationError as e:
        error_summary = _format_validation_errors(e)
        raise ManifestValidationError(path, error_summary, cause=e) from e
    except Exception as e:
        raise ManifestValidationError(
            path,
            f"Unexpected error: {e}",
            cause=e,
        ) from e


def _format_validation_errors(error: ValidationError) -> str:
    """Format Pydantic validation errors into a human-readable string.

    Args:
        error: Pydantic ValidationError instance.

    Returns:
        Formatted error message string.
    """
    messages = []
    for err in error.errors():
        loc = ".".join(str(loc) for loc in err["loc"]) if err["loc"] else "root"
        msg = err["msg"]
        messages.append(f"{loc}: {msg}")
    return "; ".join(messages)
