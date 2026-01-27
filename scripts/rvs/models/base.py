"""Base model and custom types for RVS.

Provides foundational Pydantic model configuration and custom field types
for resume data validation.
"""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

if TYPE_CHECKING:
    from pydantic import GetJsonSchemaHandler
    from pydantic.json_schema import JsonSchemaValue


class BaseResumeModel(BaseModel):
    """Base model for all resume data structures.

    Enforces strict schema validation by forbidding extra fields,
    preventing schema drift in YAML source files.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
    )


# ResumeID pattern: lowercase alphanumeric with hyphens and underscores
RESUME_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _validate_resume_id(value: Any) -> str:
    """Validate ResumeID format."""
    if not isinstance(value, str):
        raise ValueError("ResumeID must be a string")
    if not value:
        raise ValueError("ResumeID cannot be empty")
    if not RESUME_ID_PATTERN.match(value):
        raise ValueError(
            f"ResumeID must be lowercase alphanumeric with hyphens/underscores, "
            f"starting with alphanumeric. Got: '{value}'"
        )
    return value


class _ResumeIDAnnotation:
    """Pydantic annotation for ResumeID validation."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            _validate_resume_id,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string", "pattern": r"^[a-z0-9][a-z0-9_-]*$"}


ResumeID = _ResumeIDAnnotation


# TechTag pattern: lowercase alphanumeric with hyphens and dots
TECH_TAG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def _validate_tech_tag(value: Any) -> str:
    """Validate TechTag format."""
    if not isinstance(value, str):
        raise ValueError("TechTag must be a string")
    normalized: str = value.lower().strip()
    if not normalized:
        raise ValueError("TechTag cannot be empty")
    if not TECH_TAG_PATTERN.match(normalized):
        raise ValueError(
            f"TechTag must be lowercase alphanumeric with hyphens, underscores, "
            f"or dots, starting with alphanumeric. Got: '{normalized}'"
        )
    return normalized


class _TechTagAnnotation:
    """Pydantic annotation for TechTag validation."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            _validate_tech_tag,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string", "pattern": r"^[a-z0-9][a-z0-9._-]*$"}


TechTag = _TechTagAnnotation


# ResumeDate types
PresentLiteral = Literal["Present"]
DATE_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class ResumeDateValue:
    """Wrapper for resume dates supporting YYYY-MM format and 'Present' literal.

    Implements comparison operations for sorting, where 'Present' is always
    considered greater than any concrete date.
    """

    __slots__ = ("_value", "_is_present")

    def __init__(self, value: date | PresentLiteral) -> None:
        if isinstance(value, str) and value == "Present":
            self._value: date | None = None
            self._is_present = True
        elif isinstance(value, date):
            self._value = value
            self._is_present = False
        else:
            raise ValueError(f"Invalid ResumeDateValue: {value}")

    @property
    def is_present(self) -> bool:
        """Check if this date represents 'Present'."""
        return self._is_present

    @property
    def value(self) -> date | PresentLiteral:
        """Get the underlying date or 'Present' literal."""
        if self._is_present:
            return "Present"
        return self._value  # type: ignore[return-value]

    def to_date(self) -> date | None:
        """Get the date value, or None if Present."""
        return self._value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ResumeDateValue):
            return NotImplemented
        if self._is_present and other._is_present:
            return True
        if self._is_present or other._is_present:
            return False
        return self._value == other._value

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ResumeDateValue):
            return NotImplemented
        if self._is_present:
            return False
        if other._is_present:
            return True
        return self._value < other._value  # type: ignore[operator]

    def __le__(self, other: object) -> bool:
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, ResumeDateValue):
            return NotImplemented
        if other._is_present:
            return False
        if self._is_present:
            return True
        return self._value > other._value  # type: ignore[operator]

    def __ge__(self, other: object) -> bool:
        return self == other or self > other

    def __hash__(self) -> int:
        if self._is_present:
            return hash("Present")
        return hash(self._value)

    def __repr__(self) -> str:
        if self._is_present:
            return "ResumeDateValue('Present')"
        return f"ResumeDateValue({self._value!r})"

    def __str__(self) -> str:
        if self._is_present:
            return "Present"
        return self._value.strftime("%Y-%m")  # type: ignore[union-attr]

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Define Pydantic core schema for ResumeDateValue."""
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize, info_arg=False, return_schema=core_schema.str_schema()
            ),
        )

    @classmethod
    def _validate(cls, value: Any) -> ResumeDateValue:
        """Parse a resume date from string, date, or existing ResumeDateValue."""
        if isinstance(value, ResumeDateValue):
            return value

        if isinstance(value, date):
            return cls(value)

        if not isinstance(value, str):
            raise ValueError(f"ResumeDate must be a string or date, got: {type(value).__name__}")

        value = value.strip()

        if value == "Present":
            return cls("Present")

        if not DATE_PATTERN.match(value):
            raise ValueError(f"ResumeDate must be in 'YYYY-MM' format or 'Present'. Got: '{value}'")

        year, month = value.split("-")
        return cls(date(int(year), int(month), 1))

    @staticmethod
    def _serialize(value: ResumeDateValue) -> str:
        """Serialize ResumeDateValue to string."""
        return str(value)


def _parse_resume_date(
    value: str | date | ResumeDateValue,
) -> ResumeDateValue:
    """Parse a resume date from string, date, or existing ResumeDateValue."""
    return ResumeDateValue._validate(value)


ResumeDate = ResumeDateValue
