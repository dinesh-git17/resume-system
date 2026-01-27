"""Unit tests for the RVS Model Registry.

Tests cover path-to-model mapping, singleton vs collection handling,
and error cases for unknown directories.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.rvs.models import (
    Education,
    ExperienceFile,
    Manifest,
    Profile,
    ProjectFile,
    Skills,
)
from scripts.rvs.validator.registry import (
    ModelRegistry,
    UnknownPathError,
    get_model_for_path,
)


class TestModelRegistry:
    """Tests for ModelRegistry class."""

    @pytest.fixture
    def registry(self) -> ModelRegistry:
        """Return a fresh ModelRegistry instance."""
        return ModelRegistry()

    @pytest.fixture
    def root(self, tmp_path: Path) -> Path:
        """Create a temporary project root directory."""
        return tmp_path

    def test_singleton_profile_mapping(self, registry: ModelRegistry, root: Path) -> None:
        """Map data/profile.yaml to Profile model."""
        file_path = root / "data" / "profile.yaml"
        model = registry.get_model(file_path, root)
        assert model is Profile

    def test_singleton_education_mapping(self, registry: ModelRegistry, root: Path) -> None:
        """Map data/education.yaml to Education model."""
        file_path = root / "data" / "education.yaml"
        model = registry.get_model(file_path, root)
        assert model is Education

    def test_singleton_skills_mapping(self, registry: ModelRegistry, root: Path) -> None:
        """Map data/skills.yaml to Skills model."""
        file_path = root / "data" / "skills.yaml"
        model = registry.get_model(file_path, root)
        assert model is Skills

    def test_collection_experience_mapping(self, registry: ModelRegistry, root: Path) -> None:
        """Map content/experience/*.yaml to ExperienceFile model."""
        file_path = root / "content" / "experience" / "google.yaml"
        model = registry.get_model(file_path, root)
        assert model is ExperienceFile

    def test_collection_experience_any_filename(self, registry: ModelRegistry, root: Path) -> None:
        """Any .yaml file in content/experience/ maps to ExperienceFile."""
        file_path = root / "content" / "experience" / "amazon.yaml"
        model = registry.get_model(file_path, root)
        assert model is ExperienceFile

    def test_collection_projects_mapping(self, registry: ModelRegistry, root: Path) -> None:
        """Map content/projects/*.yaml to ProjectFile model."""
        file_path = root / "content" / "projects" / "projects.yaml"
        model = registry.get_model(file_path, root)
        assert model is ProjectFile

    def test_collection_config_mapping(self, registry: ModelRegistry, root: Path) -> None:
        """Map config/*.yaml to Manifest model."""
        file_path = root / "config" / "swe-resume.yaml"
        model = registry.get_model(file_path, root)
        assert model is Manifest

    def test_unknown_directory_raises_error(self, registry: ModelRegistry, root: Path) -> None:
        """Raise UnknownPathError for files in unknown directories."""
        file_path = root / "unknown" / "file.yaml"
        with pytest.raises(UnknownPathError) as exc_info:
            registry.get_model(file_path, root)
        assert file_path == exc_info.value.file_path
        assert "No model registered" in str(exc_info.value)

    def test_unknown_data_file_raises_error(self, registry: ModelRegistry, root: Path) -> None:
        """Raise UnknownPathError for unknown files in data/."""
        file_path = root / "data" / "unknown.yaml"
        with pytest.raises(UnknownPathError) as exc_info:
            registry.get_model(file_path, root)
        assert "No model registered" in str(exc_info.value)

    def test_file_not_relative_to_root_raises_error(
        self, registry: ModelRegistry, root: Path
    ) -> None:
        """Raise UnknownPathError if file is not under root."""
        file_path = Path("/other/path/file.yaml")
        with pytest.raises(UnknownPathError) as exc_info:
            registry.get_model(file_path, root)
        assert "not relative to root" in str(exc_info.value)

    def test_file_at_root_raises_error(self, registry: ModelRegistry, root: Path) -> None:
        """Raise UnknownPathError for files directly at root."""
        file_path = root / "file.yaml"
        with pytest.raises(UnknownPathError) as exc_info:
            registry.get_model(file_path, root)
        assert "must be in a subdirectory" in str(exc_info.value)

    def test_is_registered_path_true(self, registry: ModelRegistry, root: Path) -> None:
        """Return True for registered paths."""
        file_path = root / "data" / "profile.yaml"
        assert registry.is_registered_path(file_path, root) is True

    def test_is_registered_path_false(self, registry: ModelRegistry, root: Path) -> None:
        """Return False for unregistered paths."""
        file_path = root / "unknown" / "file.yaml"
        assert registry.is_registered_path(file_path, root) is False


class TestGetModelForPath:
    """Tests for get_model_for_path convenience function."""

    @pytest.fixture
    def root(self, tmp_path: Path) -> Path:
        """Create a temporary project root directory."""
        return tmp_path

    def test_returns_model_for_known_path(self, root: Path) -> None:
        """Return model class for known path."""
        file_path = root / "data" / "profile.yaml"
        model = get_model_for_path(file_path, root)
        assert model is Profile

    def test_returns_none_for_unknown_path_non_strict(self, root: Path) -> None:
        """Return None for unknown path when strict=False."""
        file_path = root / "unknown" / "file.yaml"
        model = get_model_for_path(file_path, root, strict=False)
        assert model is None

    def test_raises_for_unknown_path_strict(self, root: Path) -> None:
        """Raise UnknownPathError for unknown path when strict=True."""
        file_path = root / "unknown" / "file.yaml"
        with pytest.raises(UnknownPathError):
            get_model_for_path(file_path, root, strict=True)

    def test_default_is_non_strict(self, root: Path) -> None:
        """Default behavior is non-strict (returns None)."""
        file_path = root / "unknown" / "file.yaml"
        model = get_model_for_path(file_path, root)
        assert model is None


class TestUnknownPathError:
    """Tests for UnknownPathError exception."""

    def test_error_contains_file_path(self) -> None:
        """Exception stores the file path."""
        file_path = Path("/test/file.yaml")
        error = UnknownPathError(file_path)
        assert error.file_path == file_path

    def test_default_message(self) -> None:
        """Default message includes file path."""
        file_path = Path("/test/file.yaml")
        error = UnknownPathError(file_path)
        assert str(file_path) in str(error)

    def test_custom_message(self) -> None:
        """Custom message is used when provided."""
        file_path = Path("/test/file.yaml")
        error = UnknownPathError(file_path, "Custom error message")
        assert error.message == "Custom error message"
        assert str(error) == "Custom error message"
