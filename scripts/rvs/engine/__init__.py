"""RVS Template Engine package.

Provides strict Jinja2-based template rendering with fail-fast behavior
for undefined variables and deterministic output. Includes build orchestration
components for manifest loading, content resolution, and context assembly.
"""

from scripts.rvs.engine.builder import BuildError, assemble_context, load_static_data
from scripts.rvs.engine.context import prepare_context, prepare_context_dict
from scripts.rvs.engine.core import create_env, format_date
from scripts.rvs.engine.exceptions import RenderingError, TemplateNotFoundError
from scripts.rvs.engine.loader import ManifestValidationError, load_manifest
from scripts.rvs.engine.renderer import Renderer
from scripts.rvs.engine.resolver import ContentResolver, ResolutionError, resolve_manifest_content

__all__ = [
    "BuildError",
    "ContentResolver",
    "ManifestValidationError",
    "Renderer",
    "RenderingError",
    "ResolutionError",
    "TemplateNotFoundError",
    "assemble_context",
    "create_env",
    "format_date",
    "load_manifest",
    "load_static_data",
    "prepare_context",
    "prepare_context_dict",
    "resolve_manifest_content",
]
