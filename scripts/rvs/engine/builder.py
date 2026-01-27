"""Context assembly for the RVS build engine.

Provides the orchestration layer that merges profile, skills, education,
and resolved content into a single rendering context.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.rvs.engine.context import prepare_context
from scripts.rvs.loader import load_yaml_strict
from scripts.rvs.models.education import Education
from scripts.rvs.models.experience import ExperienceEntry
from scripts.rvs.models.profile import Profile
from scripts.rvs.models.project import ProjectEntry
from scripts.rvs.models.skills import Skills


class BuildError(Exception):
    """Raised when build context assembly fails."""

    def __init__(self, message: str, cause: Exception | None = None):
        self.message = message
        self.cause = cause
        super().__init__(message)


def _get_git_hash() -> str:
    """Retrieve the current git commit hash.

    Returns:
        Short git commit hash or 'unknown' if not in a git repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def _get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format.

    Returns:
        Formatted timestamp string.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sort_skills_alphabetically(skills: Skills) -> dict[str, list[str]]:
    """Sort all skill categories alphabetically for deterministic output.

    Args:
        skills: Validated Skills model instance.

    Returns:
        Dictionary with category names as keys and sorted skill lists as values.
    """
    skills_by_category = skills.get_skills_by_category()
    return {
        category: sorted(items, key=str.lower) for category, items in skills_by_category.items()
    }


def load_static_data(root: Path) -> tuple[Profile, Skills, Education]:
    """Load static data files (profile, skills, education).

    Args:
        root: Project root path containing data/ directory.

    Returns:
        Tuple of (Profile, Skills, Education) validated models.

    Raises:
        BuildError: If any data file cannot be loaded.
    """
    try:
        profile = load_yaml_strict(root / "data" / "profile.yaml", Profile)
        skills = load_yaml_strict(root / "data" / "skills.yaml", Skills)
        education = load_yaml_strict(root / "data" / "education.yaml", Education)
        return profile, skills, education
    except FileNotFoundError as e:
        raise BuildError(f"Required data file not found: {e}") from e
    except Exception as e:
        raise BuildError(f"Failed to load static data: {e}") from e


def assemble_context(
    profile: Profile,
    skills: Skills,
    education: Education,
    experience: list[ExperienceEntry],
    projects: list[ProjectEntry],
    *,
    timestamp_fn: Callable[[], str] | None = None,
    git_hash_fn: Callable[[], str] | None = None,
) -> dict[str, Any]:
    """Assemble the complete rendering context from all data sources.

    Merges profile, skills, education, and resolved content into a single
    dictionary keyed for Jinja2 template access. Skills are sorted alphabetically
    within each category to ensure deterministic output.

    Args:
        profile: Validated Profile model.
        skills: Validated Skills model.
        education: Validated Education model.
        experience: List of resolved ExperienceEntry objects.
        projects: List of resolved ProjectEntry objects.
        timestamp_fn: Optional function to generate timestamp (for testing).
        git_hash_fn: Optional function to get git hash (for testing).

    Returns:
        Read-only dictionary containing all resume data keyed as:
        - profile: Contact and identity information
        - skills: Alphabetically sorted skills by category
        - education: List of education entries
        - experience: List of experience entries with filtered highlights
        - projects: List of project entries with filtered highlights
        - build_meta: Build metadata (timestamp, git_hash)
    """
    timestamp = (timestamp_fn or _get_utc_timestamp)()
    git_hash = (git_hash_fn or _get_git_hash)()

    sorted_skills = _sort_skills_alphabetically(skills)

    context: dict[str, Any] = {
        "profile": prepare_context(profile),
        "skills": sorted_skills,
        "education": [prepare_context(entry) for entry in education.entries],
        "experience": [prepare_context(entry) for entry in experience],
        "projects": [prepare_context(entry) for entry in projects],
        "build_meta": {
            "timestamp": timestamp,
            "git_hash": git_hash,
        },
    }

    return context
