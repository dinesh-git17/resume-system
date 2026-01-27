# Module: scripts.rvs.models

Pydantic V2 data models for resume content validation.

## Purpose

This package defines the schema layer for all resume data. It provides:

- Strict type validation for YAML content
- Custom field types with format enforcement
- Container models with ID uniqueness validation
- Cross-field validation (date ranges)

## Location

```
scripts/rvs/models/
├── __init__.py      # Package exports
├── base.py          # Base model and custom types
├── profile.py       # Profile model
├── education.py     # Education models
├── skills.py        # Skills model
├── experience.py    # Experience models
└── project.py       # Project models
```

## Public Interface

### Imports

```python
from scripts.rvs.models import (
    # Base
    BaseResumeModel,
    ResumeID,
    TechTag,
    ResumeDate,
    ResumeDateValue,
    PresentLiteral,

    # Profile
    Profile,
    Link,

    # Education
    Education,
    EducationEntry,

    # Skills
    Skills,

    # Experience
    ExperienceFile,
    ExperienceEntry,
    Highlight,

    # Project
    ProjectFile,
    ProjectEntry,
    ProjectHighlight,
)
```

### Validation Functions (Internal)

```python
from scripts.rvs.models.base import (
    _validate_resume_id,   # ResumeID validation
    _validate_tech_tag,    # TechTag validation
    _parse_resume_date,    # ResumeDate parsing
)
```

## Key Classes

### BaseResumeModel

Base class for all resume models.

```python
class BaseResumeModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
    )
```

**Configuration:**
- `extra="forbid"`: Rejects unknown fields
- `str_strip_whitespace=True`: Strips whitespace from strings
- `validate_default=True`: Validates default values

### ResumeDateValue

Wrapper for dates supporting "Present" literal.

**Properties:**
- `is_present: bool`: True if date is "Present"
- `value: date | Literal["Present"]`: Underlying value

**Methods:**
- `to_date() -> date | None`: Returns date or None for Present

**Comparison:**
- Implements `__lt__`, `__le__`, `__gt__`, `__ge__`, `__eq__`
- "Present" is greater than any concrete date
- Two "Present" values are equal

### Container Models

`Education`, `ExperienceFile`, and `ProjectFile` enforce ID uniqueness:

```python
@model_validator(mode="after")
def _validate_unique_ids(self) -> Self:
    ids = [entry.id for entry in self.entries]
    duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
    if duplicates:
        raise ValueError(f"Duplicate IDs: {set(duplicates)}")
    return self
```

## Invariants

1. **ID Format**: All `ResumeID` fields match `^[a-z0-9][a-z0-9_-]*$`
2. **ID Uniqueness**: IDs are unique within their container
3. **Date Order**: `end_date >= start_date` when both present
4. **Required Fields**: Missing required fields raise `ValidationError`
5. **No Extra Fields**: Unknown fields raise `ValidationError`
6. **TechTag Format**: All tags match `^[a-z0-9][a-z0-9._-]*$`

## Failure Modes

### ValidationError

Raised by Pydantic when validation fails.

**Common causes:**
- Missing required field
- Invalid field type
- Pattern mismatch (ResumeID, TechTag)
- Constraint violation (min_length, max_length)
- Extra field present
- Date range violation (end < start)
- Duplicate IDs

**Example:**
```python
from pydantic import ValidationError
from scripts.rvs.models import Profile

try:
    Profile(name="Test", email="invalid")
except ValidationError as e:
    print(e.errors())
    # [{'type': 'value_error', 'loc': ('email',), ...}]
```

### ValueError

Raised by custom validators for format violations.

**Common causes:**
- ResumeID with uppercase characters
- ResumeID starting with hyphen/underscore
- TechTag with invalid characters
- ResumeDate with invalid format

## Extension Guidelines

### Adding a New Model

1. Create new file in `scripts/rvs/models/`
2. Import `BaseResumeModel` from `base`
3. Define model class inheriting from `BaseResumeModel`
4. Use appropriate field types:
   - `Annotated[str, _ResumeIDAnnotation]` for IDs
   - `Annotated[str, _TechTagAnnotation]` for tech tags
   - `ResumeDateValue` for dates
5. Add model validators for cross-field constraints
6. Export from `__init__.py`
7. Add tests

**Example:**
```python
from typing import Annotated
from pydantic import Field, model_validator
from scripts.rvs.models.base import (
    BaseResumeModel,
    ResumeDateValue,
    _ResumeIDAnnotation,
)

class CertificationEntry(BaseResumeModel):
    id: Annotated[str, _ResumeIDAnnotation]
    name: str = Field(..., min_length=1, max_length=200)
    issuer: str = Field(..., min_length=1, max_length=200)
    date_earned: ResumeDateValue
    expiry_date: ResumeDateValue | None = None

    @model_validator(mode="after")
    def _validate_date_range(self) -> "CertificationEntry":
        if self.expiry_date is not None:
            if self.expiry_date < self.date_earned:
                raise ValueError("expiry_date cannot be before date_earned")
        return self
```

### Adding a Container Model

Follow the pattern from `Education`, `ExperienceFile`, or `ProjectFile`:

```python
class CertificationFile(BaseResumeModel):
    entries: list[CertificationEntry] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_unique_ids(self) -> "CertificationFile":
        ids = [entry.id for entry in self.entries]
        duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
        if duplicates:
            raise ValueError(f"Duplicate IDs: {set(duplicates)}")
        return self
```

## Testing

All models are tested in `tests/test_schemas.py`:

- Valid input acceptance
- Invalid input rejection
- Edge cases (empty strings, boundary values)
- Custom type validation
- Model validator behavior
