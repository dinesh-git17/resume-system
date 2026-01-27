"""Content resolution and bullet filtering for the RVS build engine.

Provides ID-based lookup of experience and project entries with
optional bullet/highlight filtering based on manifest specifications.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from scripts.rvs.loader import YAMLLoadError, load_yaml_strict
from scripts.rvs.models.experience import ExperienceEntry, ExperienceFile, Highlight
from scripts.rvs.models.project import ProjectEntry, ProjectFile, ProjectHighlight

if TYPE_CHECKING:
    from scripts.rvs.models.manifest import Manifest, ManifestEntry


class ResolutionError(Exception):
    """Raised when content resolution fails.

    Indicates that a requested ID could not be found or a bullet
    filtering operation failed.
    """

    def __init__(self, message: str, entry_id: str | None = None, bullet_id: str | None = None):
        self.message = message
        self.entry_id = entry_id
        self.bullet_id = bullet_id
        super().__init__(message)


class ContentResolver:
    """Resolves manifest entry IDs to validated content objects.

    Loads experience and project files, indexes them by ID, and provides
    lookup with optional bullet filtering.
    """

    def __init__(self, root: Path):
        """Initialize resolver with project root directory.

        Args:
            root: Project root path containing content/ directory.
        """
        self.root = Path(root)
        self._experience_index: dict[str, ExperienceEntry] = {}
        self._project_index: dict[str, ProjectEntry] = {}
        self._loaded = False

    def _load_content(self) -> None:
        """Load and index all experience and project files.

        Builds internal indexes mapping entry IDs to their objects.
        Called lazily on first resolution attempt.
        """
        if self._loaded:
            return

        self._load_experience_files()
        self._load_project_files()
        self._loaded = True

    def _load_experience_files(self) -> None:
        """Load all experience YAML files and index entries by ID."""
        experience_dir = self.root / "content" / "experience"
        if not experience_dir.exists():
            return

        yaml_files = sorted(experience_dir.glob("*.yaml"))
        for file_path in yaml_files:
            try:
                exp_file = load_yaml_strict(file_path, ExperienceFile)
                for entry in exp_file.entries:
                    if entry.id in self._experience_index:
                        raise ResolutionError(
                            f"Duplicate experience entry ID '{entry.id}' found in {file_path}",
                            entry_id=entry.id,
                        )
                    self._experience_index[entry.id] = entry
            except YAMLLoadError as e:
                raise ResolutionError(f"Failed to load experience file: {e.message}") from e

    def _load_project_files(self) -> None:
        """Load all project YAML files and index entries by ID."""
        project_dir = self.root / "content" / "projects"
        if not project_dir.exists():
            return

        yaml_files = sorted(project_dir.glob("*.yaml"))
        for file_path in yaml_files:
            try:
                proj_file = load_yaml_strict(file_path, ProjectFile)
                for entry in proj_file.entries:
                    if entry.id in self._project_index:
                        raise ResolutionError(
                            f"Duplicate project entry ID '{entry.id}' found in {file_path}",
                            entry_id=entry.id,
                        )
                    self._project_index[entry.id] = entry
            except YAMLLoadError as e:
                raise ResolutionError(f"Failed to load project file: {e.message}") from e

    def resolve_experience(self, manifest_entry: ManifestEntry) -> ExperienceEntry:
        """Resolve a manifest entry to an experience entry with filtered bullets.

        Args:
            manifest_entry: Manifest entry specifying ID and optional bullet filter.

        Returns:
            ExperienceEntry with highlights filtered to match manifest bullets
            (if specified) or all highlights (if bullets is None).

        Raises:
            ResolutionError: If entry ID not found or bullet ID doesn't exist.
        """
        self._load_content()

        entry_id = manifest_entry.id
        if entry_id not in self._experience_index:
            raise ResolutionError(
                f"Experience entry '{entry_id}' not found in content",
                entry_id=entry_id,
            )

        original = self._experience_index[entry_id]

        if manifest_entry.bullets is None:
            return original

        filtered_highlights = self._filter_highlights(
            original.highlights,
            manifest_entry.bullets,
            entry_id,
        )

        return ExperienceEntry(
            id=original.id,
            company=original.company,
            role=original.role,
            location=original.location,
            start_date=original.start_date,
            end_date=original.end_date,
            highlights=filtered_highlights,
            team=original.team,
            department=original.department,
        )

    def resolve_project(self, manifest_entry: ManifestEntry) -> ProjectEntry:
        """Resolve a manifest entry to a project entry with filtered highlights.

        Args:
            manifest_entry: Manifest entry specifying ID and optional bullet filter.

        Returns:
            ProjectEntry with highlights filtered to match manifest bullets
            (if specified) or all highlights (if bullets is None).

        Raises:
            ResolutionError: If entry ID not found or bullet ID doesn't exist.
        """
        self._load_content()

        entry_id = manifest_entry.id
        if entry_id not in self._project_index:
            raise ResolutionError(
                f"Project entry '{entry_id}' not found in content",
                entry_id=entry_id,
            )

        original = self._project_index[entry_id]

        if manifest_entry.bullets is None:
            return original

        filtered_highlights = self._filter_project_highlights(
            original.highlights,
            manifest_entry.bullets,
            entry_id,
        )

        return ProjectEntry(
            id=original.id,
            name=original.name,
            description=original.description,
            start_date=original.start_date,
            end_date=original.end_date,
            url=original.url,
            repository=original.repository,
            technologies=original.technologies,
            highlights=filtered_highlights,
            role=original.role,
            organization=original.organization,
        )

    def _filter_highlights(
        self,
        highlights: list[Highlight],
        bullet_ids: list[str],
        entry_id: str,
    ) -> list[Highlight]:
        """Filter and reorder highlights based on requested bullet IDs.

        Args:
            highlights: Original list of Highlight objects.
            bullet_ids: List of bullet IDs to include (defines order).
            entry_id: Parent entry ID for error context.

        Returns:
            Filtered list of Highlight objects in bullet_ids order.

        Raises:
            ResolutionError: If any bullet ID is not found.
        """
        highlight_map = {h.id: h for h in highlights}
        result: list[Highlight] = []

        for bullet_id in bullet_ids:
            if bullet_id not in highlight_map:
                available = list(highlight_map.keys())
                raise ResolutionError(
                    f"Bullet '{bullet_id}' not found in experience entry '{entry_id}'. "
                    f"Available bullets: {available}",
                    entry_id=entry_id,
                    bullet_id=bullet_id,
                )
            result.append(highlight_map[bullet_id])

        return result

    def _filter_project_highlights(
        self,
        highlights: list[ProjectHighlight],
        bullet_ids: list[str],
        entry_id: str,
    ) -> list[ProjectHighlight]:
        """Filter and reorder project highlights based on requested bullet IDs.

        Args:
            highlights: Original list of ProjectHighlight objects.
            bullet_ids: List of bullet IDs to include (defines order).
            entry_id: Parent project ID for error context.

        Returns:
            Filtered list of ProjectHighlight objects in bullet_ids order.

        Raises:
            ResolutionError: If any bullet ID is not found.
        """
        highlight_map = {h.id: h for h in highlights}
        result: list[ProjectHighlight] = []

        for bullet_id in bullet_ids:
            if bullet_id not in highlight_map:
                available = list(highlight_map.keys())
                raise ResolutionError(
                    f"Bullet '{bullet_id}' not found in project '{entry_id}'. "
                    f"Available bullets: {available}",
                    entry_id=entry_id,
                    bullet_id=bullet_id,
                )
            result.append(highlight_map[bullet_id])

        return result


def resolve_manifest_content(
    manifest: Manifest,
    root: Path,
) -> tuple[list[ExperienceEntry], list[ProjectEntry]]:
    """Resolve all manifest entries to content objects.

    Processes include_experience and include_projects from the manifest,
    resolving each entry and filtering bullets as specified. Preserves
    the order defined in the manifest.

    Args:
        manifest: Validated Manifest instance.
        root: Project root path containing content/ directory.

    Returns:
        Tuple of (experience_entries, project_entries) in manifest order.

    Raises:
        ResolutionError: If any entry or bullet ID cannot be resolved.
    """
    resolver = ContentResolver(root)

    experience_entries: list[ExperienceEntry] = []
    for manifest_entry in manifest.include_experience:
        experience_entries.append(resolver.resolve_experience(manifest_entry))

    project_entries: list[ProjectEntry] = []
    for manifest_entry in manifest.include_projects:
        project_entries.append(resolver.resolve_project(manifest_entry))

    return experience_entries, project_entries
