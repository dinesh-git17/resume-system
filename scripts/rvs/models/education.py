"""Education model for academic credentials.

Defines the schema for education.yaml containing degree information,
institutions, and academic achievements.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from scripts.rvs.models.base import (
    BaseResumeModel,
    ResumeDateValue,
    _ResumeIDAnnotation,
)


class EducationEntry(BaseResumeModel):
    """Single education entry representing one academic credential."""

    id: Annotated[str, _ResumeIDAnnotation]
    institution: str = Field(..., min_length=1, max_length=200)
    degree: str = Field(..., min_length=1, max_length=200)
    field_of_study: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=100)
    start_date: ResumeDateValue
    end_date: ResumeDateValue | None = None
    gpa: str | None = Field(default=None, max_length=20)
    honors: list[str] = Field(default_factory=list)
    coursework: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_date_range(self) -> EducationEntry:
        """Ensure end_date is not before start_date when both are provided."""
        if self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError(
                    f"end_date ({self.end_date}) cannot be before start_date ({self.start_date})"
                )
        return self


class Education(BaseResumeModel):
    """Education data model containing all academic credentials.

    Maps to data/education.yaml structure.
    """

    entries: list[EducationEntry] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_unique_ids(self) -> Education:
        """Ensure all education entry IDs are unique."""
        ids = [entry.id for entry in self.entries]
        duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
        if duplicates:
            raise ValueError(f"Duplicate education entry IDs detected: {set(duplicates)}")
        return self
