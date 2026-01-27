"""Strict YAML loader with Pydantic validation.

Provides type-safe YAML loading with UTF-8 enforcement, YAML 1.2 compliance,
and automatic Pydantic model validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel, ValidationError
from yaml import YAMLError

T = TypeVar("T", bound=BaseModel)


class YAMLLoadError(Exception):
    """Raised when YAML loading fails."""

    def __init__(self, path: Path, message: str, cause: Exception | None = None):
        self.path = path
        self.message = message
        self.cause = cause
        super().__init__(f"Failed to load '{path}': {message}")


class YAMLValidationError(Exception):
    """Raised when YAML content fails Pydantic validation."""

    def __init__(self, path: Path, model_name: str, validation_error: ValidationError):
        self.path = path
        self.model_name = model_name
        self.validation_error = validation_error
        error_details = str(validation_error)
        super().__init__(f"Validation failed for '{path}' against {model_name}:\n{error_details}")


def load_yaml_strict(path: Path | str, model_class: type[T]) -> T:
    """Load a YAML file and validate against a Pydantic model.

    Enforces YAML 1.2 compliance, UTF-8 encoding, and strict schema validation
    through Pydantic model parsing.

    Args:
        path: Path to the YAML file.
        model_class: Pydantic model class to validate against.

    Returns:
        Validated Pydantic model instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        YAMLLoadError: If file cannot be read or parsed as YAML.
        YAMLValidationError: If content fails Pydantic validation.
    """
    path = Path(path) if isinstance(path, str) else path

    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise YAMLLoadError(path, f"File is not valid UTF-8: {e}", cause=e) from e
    except OSError as e:
        raise YAMLLoadError(path, f"Cannot read file: {e}", cause=e) from e

    try:
        data = yaml.safe_load(content)
    except YAMLError as e:
        raise YAMLLoadError(path, f"Invalid YAML syntax: {e}", cause=e) from e

    if data is None:
        raise YAMLLoadError(path, "YAML file is empty or contains only null")

    if not isinstance(data, dict):
        raise YAMLLoadError(path, f"YAML root must be a mapping, got: {type(data).__name__}")

    try:
        return model_class.model_validate(data)
    except ValidationError as e:
        raise YAMLValidationError(path, model_class.__name__, e) from e


def load_yaml_list_strict(path: Path | str, model_class: type[T]) -> list[T]:
    """Load a YAML file containing a list and validate each item.

    Args:
        path: Path to the YAML file.
        model_class: Pydantic model class to validate each item against.

    Returns:
        List of validated Pydantic model instances.

    Raises:
        FileNotFoundError: If the file does not exist.
        YAMLLoadError: If file cannot be read or parsed as YAML.
        YAMLValidationError: If any item fails Pydantic validation.
    """
    path = Path(path) if isinstance(path, str) else path

    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise YAMLLoadError(path, f"File is not valid UTF-8: {e}", cause=e) from e
    except OSError as e:
        raise YAMLLoadError(path, f"Cannot read file: {e}", cause=e) from e

    try:
        data = yaml.safe_load(content)
    except YAMLError as e:
        raise YAMLLoadError(path, f"Invalid YAML syntax: {e}", cause=e) from e

    if data is None:
        raise YAMLLoadError(path, "YAML file is empty or contains only null")

    if not isinstance(data, list):
        raise YAMLLoadError(path, f"YAML root must be a list, got: {type(data).__name__}")

    results: list[T] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise YAMLLoadError(
                path,
                f"Item at index {idx} must be a mapping, got: {type(item).__name__}",
            )
        try:
            results.append(model_class.model_validate(item))
        except ValidationError as e:
            raise YAMLValidationError(path, f"{model_class.__name__}[{idx}]", e) from e

    return results
