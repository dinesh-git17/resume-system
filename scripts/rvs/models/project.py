"""Project model for portfolio and side projects.

Defines the schema for project YAML files containing project entries,
descriptions, highlights, and associated technologies.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, HttpUrl, model_validator

from scripts.rvs.models.base import (
    BaseResumeModel,
    ResumeDateValue,
    _ResumeIDAnnotation,
    _TechTagAnnotation,
)


class ProjectHighlight(BaseResumeModel):
    """Single highlight/bullet point within a project entry.

    Each highlight requires a unique ID for addressability.
    """

    id: Annotated[str, _ResumeIDAnnotation]
    text: str = Field(..., min_length=1, max_length=1000)
    tags: list[Annotated[str, _TechTagAnnotation]] = Field(default_factory=list)


class ProjectEntry(BaseResumeModel):
    """Single project entry representing one portfolio item.

    Contains project metadata, description, highlights,
    and technology stack information.
    """

    id: Annotated[str, _ResumeIDAnnotation]
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    start_date: ResumeDateValue | None = None
    end_date: ResumeDateValue | None = None
    url: HttpUrl | None = None
    repository: HttpUrl | None = None
    technologies: list[Annotated[str, _TechTagAnnotation]] = Field(default_factory=list)
    highlights: list[ProjectHighlight] = Field(default_factory=list)
    role: str | None = Field(default=None, max_length=200)
    organization: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _validate_date_range(self) -> ProjectEntry:
        """Ensure end_date is not before start_date when both are provided."""
        if self.start_date is not None and self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError(
                    f"end_date ({self.end_date}) cannot be before start_date ({self.start_date})"
                )
        return self

    @model_validator(mode="after")
    def _validate_unique_highlight_ids(self) -> ProjectEntry:
        """Ensure all highlight IDs are unique within this project."""
        if not self.highlights:
            return self
        ids = [h.id for h in self.highlights]
        duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate highlight IDs within project '{self.id}': {set(duplicates)}"
            )
        return self


class ProjectFile(BaseResumeModel):
    """Container for project file content.

    Represents the root structure of a project YAML file
    which may contain one or more project entries.
    """

    entries: list[ProjectEntry] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_unique_entry_ids(self) -> ProjectFile:
        """Ensure all project entry IDs are unique within the file."""
        ids = [entry.id for entry in self.entries]
        duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
        if duplicates:
            raise ValueError(f"Duplicate project entry IDs detected: {set(duplicates)}")
        return self
