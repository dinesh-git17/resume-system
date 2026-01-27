"""Build Manifest model for resume configuration.

Defines the schema for config/*.yaml manifest files that specify
which experience entries, projects, and profile to include in a
resume build artifact.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from scripts.rvs.models.base import BaseResumeModel, _ResumeIDAnnotation


class ManifestEntry(BaseResumeModel):
    """Reference to an Experience or Project entry with optional bullet selection.

    Allows granular selection of specific highlights/bullets from an entry.
    When bullets is None, all highlights for the entry are included.
    """

    id: Annotated[str, _ResumeIDAnnotation] = Field(
        ..., description="Unique ID of the Experience or Project entry"
    )
    bullets: list[Annotated[str, _ResumeIDAnnotation]] | None = Field(
        default=None,
        description="Specific bullet IDs to include. If None, all highlights included.",
    )

    @model_validator(mode="after")
    def _validate_bullets_not_empty(self) -> ManifestEntry:
        """Ensure bullets list is not empty when provided."""
        if self.bullets is not None and len(self.bullets) == 0:
            raise ValueError(
                "bullets list cannot be empty; use null/None to include all highlights"
            )
        return self


class Manifest(BaseResumeModel):
    """Build manifest defining a resume artifact configuration.

    Specifies template, profile, and ordered lists of experience and
    project entries to include in the generated resume.
    """

    template: str = Field(
        ..., min_length=1, max_length=100, description="Template ID to use for rendering"
    )
    profile: str = Field(
        ..., min_length=1, max_length=100, description="Profile key (e.g., 'default', 'redacted')"
    )
    include_experience: list[ManifestEntry] = Field(
        default_factory=list,
        description="Ordered list of experience entries to include",
    )
    include_projects: list[ManifestEntry] = Field(
        default_factory=list,
        description="Ordered list of project entries to include",
    )

    @model_validator(mode="after")
    def _validate_no_duplicate_entry_ids(self) -> Manifest:
        """Ensure no duplicate entry IDs within each section."""
        exp_ids = [e.id for e in self.include_experience]
        exp_dupes = [id_ for id_ in exp_ids if exp_ids.count(id_) > 1]
        if exp_dupes:
            raise ValueError(f"Duplicate experience entry IDs in manifest: {set(exp_dupes)}")

        proj_ids = [p.id for p in self.include_projects]
        proj_dupes = [id_ for id_ in proj_ids if proj_ids.count(id_) > 1]
        if proj_dupes:
            raise ValueError(f"Duplicate project entry IDs in manifest: {set(proj_dupes)}")

        return self
