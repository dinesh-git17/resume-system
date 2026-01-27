"""Core rendering logic for the RVS template engine.

Provides the Renderer class that transforms context data into HTML output
using Jinja2 templates with strict validation.
"""

from __future__ import annotations

from typing import Any

from jinja2 import Environment, TemplateSyntaxError, UndefinedError
from jinja2.exceptions import TemplateNotFound

from scripts.rvs.engine.core import create_env
from scripts.rvs.engine.exceptions import RenderingError, TemplateNotFoundError


class Renderer:
    """Template renderer with strict error handling.

    Wraps Jinja2 template rendering with fail-fast behavior for missing
    variables and templates. Guarantees deterministic output for identical
    inputs.

    Attributes:
        env: The configured Jinja2 Environment instance.
    """

    def __init__(self, env: Environment | None = None):
        """Initialize the renderer with a Jinja2 environment.

        Args:
            env: Optional pre-configured Environment. If not provided,
                creates a new strict environment via create_env().
        """
        self.env = env if env is not None else create_env()

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file relative to templates/.
            context: Dictionary of variables to pass to the template.

        Returns:
            Rendered template as a string.

        Raises:
            TemplateNotFoundError: If the template does not exist.
            RenderingError: If rendering fails due to undefined variables
                or other template errors.
        """
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound as e:
            raise TemplateNotFoundError(template_name) from e
        except TemplateSyntaxError as e:
            raise RenderingError(
                f"Syntax error in template '{template_name}': {e}",
                cause=e,
            ) from e

        try:
            return template.render(context)
        except UndefinedError as e:
            raise RenderingError.from_undefined(e, template_name) from e
        except Exception as e:
            raise RenderingError(
                f"Unexpected error rendering '{template_name}': {e}",
                cause=e,
            ) from e

    def render_string(self, template_string: str, context: dict[str, Any]) -> str:
        """Render a template from a string.

        Useful for testing or dynamic template generation. Subject to the
        same strict undefined variable checking as file-based templates.

        Args:
            template_string: Jinja2 template as a string.
            context: Dictionary of variables to pass to the template.

        Returns:
            Rendered template as a string.

        Raises:
            RenderingError: If rendering fails due to undefined variables
                or syntax errors.
        """
        try:
            template = self.env.from_string(template_string)
        except TemplateSyntaxError as e:
            raise RenderingError(
                f"Syntax error in template string: {e}",
                cause=e,
            ) from e

        try:
            return template.render(context)
        except UndefinedError as e:
            raise RenderingError(
                f"Undefined variable in template string: {e}",
                cause=e,
            ) from e
        except Exception as e:
            raise RenderingError(
                f"Unexpected error rendering template string: {e}",
                cause=e,
            ) from e
