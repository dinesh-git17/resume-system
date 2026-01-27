"""Skills taxonomy model.

Defines the schema for skills.yaml containing categorized technical
and professional skills.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from scripts.rvs.models.base import BaseResumeModel, _TechTagAnnotation


class Skills(BaseResumeModel):
    """Skills data model supporting categorized skill lists.

    Maps to data/skills.yaml structure. Each category contains a list
    of skill items. Validation ensures no duplicate items within categories
    (case-insensitive comparison).

    Example YAML structure:
        languages:
          - python
          - go
          - typescript
        frameworks:
          - django
          - react
        tools:
          - docker
          - kubernetes
    """

    languages: list[Annotated[str, _TechTagAnnotation]] = Field(default_factory=list)
    frameworks: list[Annotated[str, _TechTagAnnotation]] = Field(default_factory=list)
    databases: list[Annotated[str, _TechTagAnnotation]] = Field(default_factory=list)
    tools: list[Annotated[str, _TechTagAnnotation]] = Field(default_factory=list)
    platforms: list[Annotated[str, _TechTagAnnotation]] = Field(default_factory=list)
    methodologies: list[str] = Field(default_factory=list)
    other: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_no_duplicates_within_categories(self) -> Skills:
        """Ensure no duplicate items within each category (case-insensitive)."""
        categories = {
            "languages": self.languages,
            "frameworks": self.frameworks,
            "databases": self.databases,
            "tools": self.tools,
            "platforms": self.platforms,
            "methodologies": self.methodologies,
            "other": self.other,
        }

        for category_name, items in categories.items():
            seen: set[str] = set()
            for item in items:
                item_lower = item.lower()
                if item_lower in seen:
                    raise ValueError(
                        f"Duplicate item '{item}' in category '{category_name}' "
                        f"(case-insensitive comparison)"
                    )
                seen.add(item_lower)

        return self

    def get_all_skills(self) -> list[str]:
        """Return a flat list of all skills across all categories."""
        return (
            list(self.languages)
            + list(self.frameworks)
            + list(self.databases)
            + list(self.tools)
            + list(self.platforms)
            + list(self.methodologies)
            + list(self.other)
        )

    def get_skills_by_category(self) -> dict[str, list[str]]:
        """Return skills organized by category."""
        return {
            "languages": list(self.languages),
            "frameworks": list(self.frameworks),
            "databases": list(self.databases),
            "tools": list(self.tools),
            "platforms": list(self.platforms),
            "methodologies": list(self.methodologies),
            "other": list(self.other),
        }
