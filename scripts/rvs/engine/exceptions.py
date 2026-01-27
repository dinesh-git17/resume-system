"""Custom exceptions for the RVS template engine.

Provides typed exception hierarchy for rendering failures, enabling
structured error handling and clear failure diagnostics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jinja2 import UndefinedError


class RenderingError(Exception):
    """Raised when template rendering fails due to context or template issues.

    Wraps underlying Jinja2 exceptions to provide a consistent error interface
    while preserving the original cause for debugging.
    """

    def __init__(self, message: str, cause: Exception | None = None):
        self.message = message
        self.cause = cause
        super().__init__(message)

    @classmethod
    def from_undefined(cls, error: UndefinedError, template_name: str) -> RenderingError:
        """Create RenderingError from a Jinja2 UndefinedError.

        Args:
            error: The original UndefinedError from Jinja2.
            template_name: Name of the template being rendered.

        Returns:
            RenderingError with descriptive message and preserved cause.
        """
        return cls(
            f"Undefined variable in template '{template_name}': {error}",
            cause=error,
        )


class TemplateNotFoundError(Exception):
    """Raised when a requested template does not exist.

    Indicates that the specified template name could not be resolved
    within the configured template directory.
    """

    def __init__(self, template_name: str):
        self.template_name = template_name
        super().__init__(f"Template not found: '{template_name}'")
