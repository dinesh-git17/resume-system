"""Model Registry for RVS Validator.

Maps filesystem paths to Pydantic model classes for validation.
Implements a registry pattern that handles both singleton files
(e.g., profile.yaml) and collection directories (e.g., experience/).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from scripts.rvs.models import (
    Education,
    ExperienceFile,
    Manifest,
    Profile,
    ProjectFile,
    Skills,
)

if TYPE_CHECKING:
    from pydantic import BaseModel


class UnknownPathError(Exception):
    """Raised when a file path cannot be mapped to any known model."""

    def __init__(self, file_path: Path, message: str | None = None) -> None:
        """Initialize with file path and optional custom message.

        Args:
            file_path: The path that could not be mapped.
            message: Optional custom error message.
        """
        self.file_path = file_path
        self.message = message or f"No model registered for path: {file_path}"
        super().__init__(self.message)


class ModelRegistry:
    """Registry mapping filesystem paths to Pydantic model classes.

    Supports two mapping types:
    - Singleton: Exact filename match (e.g., data/profile.yaml -> Profile)
    - Collection: Directory match (e.g., content/experience/*.yaml -> ExperienceFile)
    """

    def __init__(self) -> None:
        """Initialize registry with default RVS model mappings."""
        self._singleton_mappings: dict[tuple[str, ...], type[BaseModel]] = {
            ("data", "profile.yaml"): Profile,
            ("data", "education.yaml"): Education,
            ("data", "skills.yaml"): Skills,
        }

        self._collection_mappings: dict[tuple[str, ...], type[BaseModel]] = {
            ("content", "experience"): ExperienceFile,
            ("content", "projects"): ProjectFile,
            ("config",): Manifest,
        }

    def get_model(self, file_path: Path, root: Path) -> type[BaseModel]:
        """Determine the appropriate Pydantic model for a YAML file.

        Args:
            file_path: Absolute path to the YAML file.
            root: Root directory of the project.

        Returns:
            Pydantic model class for the file.

        Raises:
            UnknownPathError: If file path cannot be mapped to a known model.
        """
        try:
            rel_path = file_path.relative_to(root)
        except ValueError as e:
            raise UnknownPathError(
                file_path,
                f"File path {file_path} is not relative to root {root}",
            ) from e

        parts = rel_path.parts

        if len(parts) < 2:
            raise UnknownPathError(
                file_path,
                f"File must be in a subdirectory of root: {rel_path}",
            )

        singleton_key = tuple(parts)
        if singleton_key in self._singleton_mappings:
            return self._singleton_mappings[singleton_key]

        for prefix_len in range(len(parts) - 1, 0, -1):
            collection_key = parts[:prefix_len]
            if collection_key in self._collection_mappings:
                return self._collection_mappings[collection_key]

        raise UnknownPathError(
            file_path,
            f"No model registered for directory structure: {'/'.join(parts[:-1])}",
        )

    def is_registered_path(self, file_path: Path, root: Path) -> bool:
        """Check if a file path maps to a registered model.

        Args:
            file_path: Absolute path to the YAML file.
            root: Root directory of the project.

        Returns:
            True if the path maps to a registered model, False otherwise.
        """
        try:
            self.get_model(file_path, root)
            return True
        except UnknownPathError:
            return False


_default_registry = ModelRegistry()


def get_model_for_path(
    file_path: Path,
    root: Path,
    *,
    strict: bool = False,
) -> type[BaseModel] | None:
    """Get the Pydantic model class for a file path.

    Convenience function using the default registry.

    Args:
        file_path: Absolute path to the YAML file.
        root: Root directory of the project.
        strict: If True, raise UnknownPathError for unmapped paths.
                If False, return None for unmapped paths.

    Returns:
        Pydantic model class, or None if strict=False and path is unmapped.

    Raises:
        UnknownPathError: If strict=True and path cannot be mapped.
    """
    try:
        return _default_registry.get_model(file_path, root)
    except UnknownPathError:
        if strict:
            raise
        return None
