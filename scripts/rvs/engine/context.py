"""Context serialization layer for the RVS template engine.

Provides safe transformation of Pydantic models to dictionaries suitable
for Jinja2 template rendering, with deterministic output.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, cast

from pydantic import BaseModel


def _convert_enums(obj: Any) -> Any:
    """Recursively convert Enum values to their string representations.

    Traverses nested structures (dicts, lists) and converts any Enum
    instances to their value attribute.

    Args:
        obj: Any Python object that may contain Enum values.

    Returns:
        Object with all Enum instances replaced by their values.
    """
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {key: _convert_enums(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_convert_enums(item) for item in obj]
    return obj


def prepare_context(model: BaseModel) -> dict[str, Any]:
    """Transform a Pydantic model into a Jinja2-compatible dictionary.

    Serializes the model while preserving date objects for filter usage
    and converting Enum values to their string representations.

    The output dictionary is deterministic: repeated calls with the same
    model produce identical results, ensuring bit-identical rendering.

    Args:
        model: Any Pydantic BaseModel instance.

    Returns:
        Dictionary suitable for Jinja2 template context. Keys are sorted
        for deterministic iteration order.
    """
    # Use mode='python' to preserve datetime/date objects for filters
    # This allows format_date filter to receive actual date objects
    data = model.model_dump(mode="python")

    # Convert any Enum values to their string representations
    return cast(dict[str, Any], _convert_enums(data))


def prepare_context_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Prepare a raw dictionary for use as Jinja2 context.

    For cases where the context is already a dictionary (e.g., merged
    from multiple models), this function ensures Enum conversion.

    Args:
        data: Dictionary to prepare for template rendering.

    Returns:
        Dictionary with Enum values converted to strings.
    """
    return cast(dict[str, Any], _convert_enums(data))
