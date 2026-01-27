"""Jinja2 environment configuration for the RVS template engine.

Provides a strict, deterministic Jinja2 environment with fail-fast behavior
for undefined variables and secure defaults.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, StrictUndefined

if TYPE_CHECKING:
    from scripts.rvs.models.base import ResumeDateValue

# Pattern for YYYY-MM format dates (serialized ResumeDateValue)
_DATE_STRING_PATTERN = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def _get_templates_dir() -> Path:
    """Resolve the absolute path to the templates directory.

    Returns:
        Absolute path to the templates/ directory at project root.
    """
    # Navigate from scripts/rvs/engine/core.py to project root
    engine_dir = Path(__file__).parent
    rvs_dir = engine_dir.parent
    scripts_dir = rvs_dir.parent
    project_root = scripts_dir.parent
    return project_root / "templates"


def format_date(value: date | str | ResumeDateValue, fmt: str = "%b %Y") -> str:
    """Format a date value for display in templates.

    Handles datetime.date objects, the literal string "Present", YYYY-MM format
    strings (from serialized ResumeDateValue), and ResumeDateValue wrapper
    objects. Defaults to "Mon YYYY" format.

    Args:
        value: A date object, "Present" string, "YYYY-MM" string, or ResumeDateValue.
        fmt: strftime format string. Defaults to "%b %Y" (e.g., "Jan 2024").

    Returns:
        Formatted date string or "Present" for ongoing positions.

    Raises:
        ValueError: If value is neither a date, "Present", nor a valid date string.
    """
    if isinstance(value, str):
        if value == "Present":
            return "Present"
        # Handle YYYY-MM format strings from serialized ResumeDateValue
        match = _DATE_STRING_PATTERN.match(value)
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            return date(year, month, 1).strftime(fmt)
        raise ValueError(f"Invalid date string: '{value}'. Expected 'YYYY-MM' or 'Present'.")

    if isinstance(value, date):
        return value.strftime(fmt)

    # Handle ResumeDateValue objects
    if hasattr(value, "is_present") and hasattr(value, "to_date"):
        if value.is_present:
            return "Present"
        inner_date = value.to_date()
        if inner_date is not None:
            return inner_date.strftime(fmt)

    raise ValueError(f"Cannot format value of type {type(value).__name__} as date")


def create_env() -> Environment:
    """Create a strictly configured Jinja2 environment.

    Configures the environment with:
    - FileSystemLoader rooted in templates/ directory
    - StrictUndefined to fail on missing variables
    - Autoescape enabled for XSS protection
    - trim_blocks and lstrip_blocks for cleaner output

    Returns:
        Configured Jinja2 Environment instance.

    Raises:
        FileNotFoundError: If templates directory does not exist.
    """
    templates_dir = _get_templates_dir()

    if not templates_dir.exists():
        raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Register custom filters
    env.filters["format_date"] = format_date

    return env
