"""Profile model for resume contact information.

Defines the schema for profile.yaml containing identity, contact details,
and professional links.
"""

from __future__ import annotations

from pydantic import EmailStr, Field, HttpUrl

from scripts.rvs.models.base import BaseResumeModel


class Link(BaseResumeModel):
    """Professional link with label and URL."""

    label: str = Field(..., min_length=1, max_length=50)
    url: HttpUrl


class Profile(BaseResumeModel):
    """Profile data model for contact information.

    Maps to data/profile.yaml structure containing identity,
    contact details, and professional links.
    """

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=100)
    linkedin: HttpUrl | None = None
    github: HttpUrl | None = None
    website: HttpUrl | None = None
    links: list[Link] = Field(default_factory=list)
