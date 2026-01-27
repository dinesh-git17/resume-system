"""Unit tests for the RVS template engine.

Tests cover strict undefined behavior, syntax error handling, context
serialization, and deterministic rendering output.
"""

from __future__ import annotations

import tempfile
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pydantic import BaseModel
from scripts.rvs.engine import (
    Renderer,
    RenderingError,
    TemplateNotFoundError,
    create_env,
    format_date,
    prepare_context,
)


class TestCreateEnv:
    """Tests for Jinja2 environment factory."""

    def test_returns_environment(self) -> None:
        """create_env returns a configured Environment object."""
        env = create_env()
        assert isinstance(env, Environment)

    def test_uses_strict_undefined(self) -> None:
        """Environment uses StrictUndefined for missing variables."""
        env = create_env()
        assert env.undefined is StrictUndefined

    def test_autoescape_enabled(self) -> None:
        """Autoescape is enabled by default."""
        env = create_env()
        assert env.autoescape is True

    def test_trim_blocks_enabled(self) -> None:
        """trim_blocks is enabled for cleaner output."""
        env = create_env()
        assert env.trim_blocks is True

    def test_lstrip_blocks_enabled(self) -> None:
        """lstrip_blocks is enabled for cleaner output."""
        env = create_env()
        assert env.lstrip_blocks is True

    def test_loader_is_filesystem(self) -> None:
        """Loader is a FileSystemLoader."""
        env = create_env()
        assert isinstance(env.loader, FileSystemLoader)

    def test_loader_searchpath_is_templates(self) -> None:
        """Loader searchpath points to templates directory."""
        env = create_env()
        loader = env.loader
        assert isinstance(loader, FileSystemLoader)
        searchpath = loader.searchpath
        assert len(searchpath) == 1
        assert searchpath[0].endswith("templates")

    def test_format_date_filter_registered(self) -> None:
        """format_date filter is registered."""
        env = create_env()
        assert "format_date" in env.filters


class TestFormatDateFilter:
    """Tests for the format_date Jinja2 filter."""

    def test_formats_date_as_mon_yyyy(self) -> None:
        """date object formats to 'Mon YYYY' by default."""
        result = format_date(date(2024, 1, 15))
        assert result == "Jan 2024"

    def test_formats_date_december(self) -> None:
        """December date formats correctly."""
        result = format_date(date(2023, 12, 1))
        assert result == "Dec 2023"

    def test_handles_present_string(self) -> None:
        """'Present' string passes through unchanged."""
        result = format_date("Present")
        assert result == "Present"

    def test_custom_format(self) -> None:
        """Custom strftime format is applied."""
        result = format_date(date(2024, 6, 15), fmt="%B %Y")
        assert result == "June 2024"

    def test_invalid_string_raises(self) -> None:
        """Non-'Present' string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date string"):
            format_date("not-a-date")

    def test_handles_yyyy_mm_string(self) -> None:
        """YYYY-MM format string from serialized ResumeDateValue."""
        result = format_date("2024-03")
        assert result == "Mar 2024"

    def test_handles_yyyy_mm_january(self) -> None:
        """YYYY-MM format for January."""
        result = format_date("2025-01")
        assert result == "Jan 2025"

    def test_handles_yyyy_mm_december(self) -> None:
        """YYYY-MM format for December."""
        result = format_date("2023-12")
        assert result == "Dec 2023"

    def test_yyyy_mm_with_custom_format(self) -> None:
        """YYYY-MM format with custom strftime format."""
        result = format_date("2024-06", fmt="%B %Y")
        assert result == "June 2024"

    def test_invalid_yyyy_mm_month_raises(self) -> None:
        """Invalid month in YYYY-MM format raises."""
        with pytest.raises(ValueError, match="Invalid date string"):
            format_date("2024-13")

    def test_invalid_yyyy_mm_format_raises(self) -> None:
        """Malformed YYYY-MM format raises."""
        with pytest.raises(ValueError, match="Invalid date string"):
            format_date("2024-1")


class TestPrepareContext:
    """Tests for context serialization."""

    def test_accepts_pydantic_model(self) -> None:
        """Function accepts any Pydantic model."""

        class SimpleModel(BaseModel):
            name: str
            value: int

        model = SimpleModel(name="test", value=42)
        result = prepare_context(model)
        assert isinstance(result, dict)

    def test_returns_dict(self) -> None:
        """Function returns a standard Python dictionary."""

        class SimpleModel(BaseModel):
            key: str

        model = SimpleModel(key="value")
        result = prepare_context(model)
        assert type(result) is dict

    def test_enum_values_converted(self) -> None:
        """Enum values are converted to their string values."""

        class Status(Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        class ModelWithEnum(BaseModel):
            status: Status

        model = ModelWithEnum(status=Status.ACTIVE)
        result = prepare_context(model)
        assert result["status"] == "active"

    def test_nested_enum_converted(self) -> None:
        """Nested Enum values are converted."""

        class Level(Enum):
            HIGH = "high"
            LOW = "low"

        class Inner(BaseModel):
            level: Level

        class Outer(BaseModel):
            inner: Inner

        model = Outer(inner=Inner(level=Level.HIGH))
        result = prepare_context(model)
        assert result["inner"]["level"] == "high"

    def test_list_enum_converted(self) -> None:
        """Enum values in lists are converted."""

        class Color(Enum):
            RED = "red"
            BLUE = "blue"

        class ModelWithList(BaseModel):
            colors: list[Color]

        model = ModelWithList(colors=[Color.RED, Color.BLUE])
        result = prepare_context(model)
        assert result["colors"] == ["red", "blue"]

    def test_date_preserved(self) -> None:
        """Date objects are preserved for filter usage."""

        class ModelWithDate(BaseModel):
            created: date

        model = ModelWithDate(created=date(2024, 1, 15))
        result = prepare_context(model)
        assert isinstance(result["created"], date)
        assert result["created"] == date(2024, 1, 15)


class TestRenderer:
    """Tests for the Renderer class."""

    @pytest.fixture
    def temp_templates(self) -> Any:
        """Create a temporary templates directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            templates_path = Path(tmpdir)

            # Valid template
            (templates_path / "valid.html").write_text("<h1>{{ title }}</h1><p>{{ content }}</p>")

            # Template with missing variable
            (templates_path / "missing_var.html").write_text(
                "<p>{{ defined_var }} {{ undefined_var }}</p>"
            )

            # Template with syntax error
            (templates_path / "syntax_error.html").write_text("<p>{% if unclosed %}</p>")

            yield templates_path

    @pytest.fixture
    def renderer_with_temp(self, temp_templates: Path) -> Renderer:
        """Create a Renderer with temporary templates directory."""
        env = Environment(
            loader=FileSystemLoader(str(temp_templates)),
            undefined=StrictUndefined,
            autoescape=True,
        )
        return Renderer(env=env)

    def test_render_returns_string(self, renderer_with_temp: Renderer) -> None:
        """render() returns a string."""
        result = renderer_with_temp.render("valid.html", {"title": "Test", "content": "Body"})
        assert isinstance(result, str)

    def test_render_valid_template(self, renderer_with_temp: Renderer) -> None:
        """Valid context produces expected HTML output."""
        result = renderer_with_temp.render("valid.html", {"title": "Hello", "content": "World"})
        assert result == "<h1>Hello</h1><p>World</p>"

    def test_render_escapes_html(self, renderer_with_temp: Renderer) -> None:
        """HTML in context is escaped for XSS protection."""
        result = renderer_with_temp.render("valid.html", {"title": "<script>", "content": "safe"})
        assert "&lt;script&gt;" in result

    def test_missing_template_raises_template_not_found(self, renderer_with_temp: Renderer) -> None:
        """Non-existent template raises TemplateNotFoundError."""
        with pytest.raises(TemplateNotFoundError) as exc_info:
            renderer_with_temp.render("nonexistent.html", {})
        assert "nonexistent.html" in str(exc_info.value)

    def test_missing_variable_raises_rendering_error(self, renderer_with_temp: Renderer) -> None:
        """Missing context variable raises RenderingError."""
        with pytest.raises(RenderingError) as exc_info:
            renderer_with_temp.render("missing_var.html", {"defined_var": "present"})
        assert "undefined_var" in str(exc_info.value).lower() or "Undefined" in str(exc_info.value)

    def test_syntax_error_raises_rendering_error(self, renderer_with_temp: Renderer) -> None:
        """Template syntax error raises RenderingError."""
        with pytest.raises(RenderingError) as exc_info:
            renderer_with_temp.render("syntax_error.html", {})
        assert "syntax" in str(exc_info.value).lower()

    def test_output_deterministic(self, renderer_with_temp: Renderer) -> None:
        """Multiple renders with same input produce identical output."""
        context = {"title": "Deterministic", "content": "Test"}
        results = [renderer_with_temp.render("valid.html", context) for _ in range(10)]
        assert all(r == results[0] for r in results)


class TestRendererString:
    """Tests for render_string method."""

    def test_render_string_valid(self) -> None:
        """render_string produces expected output."""
        renderer = Renderer()
        result = renderer.render_string("Hello {{ name }}!", {"name": "World"})
        assert result == "Hello World!"

    def test_render_string_missing_variable(self) -> None:
        """render_string raises RenderingError for missing variable."""
        renderer = Renderer()
        with pytest.raises(RenderingError):
            renderer.render_string("{{ missing }}", {})

    def test_render_string_syntax_error(self) -> None:
        """render_string raises RenderingError for syntax error."""
        renderer = Renderer()
        with pytest.raises(RenderingError, match="[Ss]yntax"):
            renderer.render_string("{% if unclosed %}", {})


class TestRenderingErrorChaining:
    """Tests for exception cause preservation."""

    def test_rendering_error_preserves_cause(self) -> None:
        """RenderingError preserves underlying exception."""
        cause = ValueError("original error")
        error = RenderingError("wrapper", cause=cause)
        assert error.cause is cause

    def test_from_undefined_creates_rendering_error(self) -> None:
        """from_undefined factory creates RenderingError."""
        from jinja2 import UndefinedError

        undefined_error = UndefinedError("'missing' is undefined")
        error = RenderingError.from_undefined(undefined_error, "test.html")
        assert isinstance(error, RenderingError)
        assert error.cause is undefined_error
        assert "test.html" in error.message


class TestStrictBehavior:
    """Integration tests for fail-fast behavior."""

    def test_undefined_in_loop_raises(self) -> None:
        """Undefined variable inside loop raises immediately."""
        renderer = Renderer()
        template = "{% for item in items %}{{ item.undefined }}{% endfor %}"
        with pytest.raises(RenderingError):
            renderer.render_string(template, {"items": [{"name": "test"}]})

    def test_undefined_in_conditional_raises(self) -> None:
        """Undefined variable in conditional branch raises."""
        renderer = Renderer()
        template = "{% if show %}{{ missing }}{% endif %}"
        with pytest.raises(RenderingError):
            renderer.render_string(template, {"show": True})

    def test_nested_undefined_raises(self) -> None:
        """Deeply nested undefined access raises."""
        renderer = Renderer()
        template = "{{ a.b.c.d }}"
        with pytest.raises(RenderingError):
            renderer.render_string(template, {"a": {"b": {}}})


class TestFilterIntegration:
    """Tests for filter usage in templates."""

    def test_format_date_in_template(self) -> None:
        """format_date filter works in template context."""
        renderer = Renderer()
        result = renderer.render_string("{{ d | format_date }}", {"d": date(2024, 3, 15)})
        assert result == "Mar 2024"

    def test_format_date_present_in_template(self) -> None:
        """format_date filter handles 'Present' in template."""
        renderer = Renderer()
        result = renderer.render_string("{{ d | format_date }}", {"d": "Present"})
        assert result == "Present"


class TestTemplateDirectoryRestriction:
    """Tests for template directory isolation."""

    def test_cannot_load_outside_templates(self) -> None:
        """Templates outside templates/ directory cannot be loaded."""
        renderer = Renderer()
        with pytest.raises(TemplateNotFoundError):
            renderer.render("../scripts/rvs/__init__.py", {})

    def test_cannot_use_absolute_path(self) -> None:
        """Absolute paths are not resolved."""
        renderer = Renderer()
        with pytest.raises(TemplateNotFoundError):
            renderer.render("/etc/passwd", {})
