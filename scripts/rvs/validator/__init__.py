"""RVS Validator package.

Provides schema validation infrastructure for resume YAML files.
"""

from scripts.rvs.validator.core import (
    ValidationContext,
    ValidationResult,
    discover_yaml_files,
    validate_yaml_file,
)
from scripts.rvs.validator.registry import (
    ModelRegistry,
    UnknownPathError,
    get_model_for_path,
)

__all__ = [
    "ModelRegistry",
    "UnknownPathError",
    "ValidationContext",
    "ValidationResult",
    "discover_yaml_files",
    "get_model_for_path",
    "validate_yaml_file",
]
