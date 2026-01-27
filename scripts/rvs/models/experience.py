"""Experience model for professional work history.

Defines the schema for experience YAML files containing job entries,
highlights (bullets), and associated tags.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from scripts.rvs.models.base import (
    BaseResumeModel,
    ResumeDateValue,
    _ResumeIDAnnotation,
    _TechTagAnnotation,
)


class Highlight(BaseResumeModel):
    """Single highlight/bullet point within an experience entry.

    Each highlight requires a unique ID for addressability and
    selective inclusion in manifests.
    """

    id: Annotated[str, _ResumeIDAnnotation]
    text: str = Field(..., min_length=1, max_length=1000)
    tags: list[Annotated[str, _TechTagAnnotation]] = Field(default_factory=list)
    impact: str | None = Field(default=None, max_length=500)


class ExperienceEntry(BaseResumeModel):
    """Single work experience entry representing one position.

    Contains company information, role details, date range,
    and a list of highlight bullets.
    """

    id: Annotated[str, _ResumeIDAnnotation]
    company: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=200)
    location: str = Field(..., min_length=1, max_length=100)
    start_date: ResumeDateValue
    end_date: ResumeDateValue | None = None
    highlights: list[Highlight] = Field(..., min_length=1)
    team: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _validate_date_range(self) -> ExperienceEntry:
        """Ensure end_date is not before start_date when provided."""
        if self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError(
                    f"end_date ({self.end_date}) cannot be before start_date ({self.start_date})"
                )
        return self

    @model_validator(mode="after")
    def _validate_unique_highlight_ids(self) -> ExperienceEntry:
        """Ensure all highlight IDs are unique within this entry."""
        ids = [h.id for h in self.highlights]
        duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate highlight IDs within experience entry '{self.id}': {set(duplicates)}"
            )
        return self


class ExperienceFile(BaseResumeModel):
    """Container for experience file content.

    Represents the root structure of an experience YAML file
    which may contain one or more experience entries.
    """

    entries: list[ExperienceEntry] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_unique_entry_ids(self) -> ExperienceFile:
        """Ensure all experience entry IDs are unique within the file."""
        ids = [entry.id for entry in self.entries]
        duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
        if duplicates:
            raise ValueError(f"Duplicate experience entry IDs detected: {set(duplicates)}")
        return self
