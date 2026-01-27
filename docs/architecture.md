# Architecture

This document describes the system architecture for the RVS data schema layer.

## System Boundaries

### In Scope (Epic RVS-P1-002)

- Pydantic V2 data models for all resume entities
- Custom field types (ResumeID, TechTag, ResumeDate)
- Strict YAML loader with UTF-8 enforcement
- Canonical reference YAML files
- Unit tests with coverage

### Out of Scope

- Cross-file ID validation (RVS-P1-004)
- Resume rendering/HTML generation
- Build manifests and orchestration
- Template engine integration

## Module Responsibilities

### scripts/rvs/models/base.py

Provides foundational infrastructure:

- `BaseResumeModel`: Pydantic base class with `extra='forbid'`
- `ResumeID`: Custom type for entity identifiers
- `TechTag`: Custom type for technology tags
- `ResumeDateValue`: Comparable date wrapper supporting "Present"

### scripts/rvs/models/profile.py

Defines contact information schema:

- `Profile`: Name, email, phone, location, social links
- `Link`: Generic labeled URL

### scripts/rvs/models/education.py

Defines academic credential schemas:

- `EducationEntry`: Single degree/credential
- `Education`: Container with unique ID enforcement

### scripts/rvs/models/skills.py

Defines skills taxonomy schema:

- `Skills`: Categorized skill lists with duplicate detection

### scripts/rvs/models/experience.py

Defines work history schemas:

- `Highlight`: Addressable bullet point
- `ExperienceEntry`: Single position with highlights
- `ExperienceFile`: Container with unique ID enforcement

### scripts/rvs/models/project.py

Defines project portfolio schemas:

- `ProjectHighlight`: Addressable bullet point
- `ProjectEntry`: Single project with metadata
- `ProjectFile`: Container with unique ID enforcement

### scripts/rvs/loader.py

Provides validated YAML loading:

- `load_yaml_strict()`: Load single object from YAML
- `load_yaml_list_strict()`: Load list of objects from YAML
- `YAMLLoadError`: Parsing/encoding errors
- `YAMLValidationError`: Schema validation errors

## Data Flow

```
                    ┌─────────────────┐
                    │   YAML File     │
                    │  (UTF-8 text)   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌──────────────────────┐
                    │  load_yaml_strict()  │
                    └────────┬─────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────────┐
        │ UTF-8    │  │  YAML    │  │   Pydantic   │
        │ Decode   │  │  Parse   │  │   Validate   │
        └────┬─────┘  └────┬─────┘  └──────┬───────┘
             │              │               │
             ▼              ▼               ▼
        ┌──────────┐  ┌──────────┐  ┌──────────────┐
        │ YAMLLoad │  │ YAMLLoad │  │ YAMLValidation│
        │   Error  │  │   Error  │  │     Error    │
        └──────────┘  └──────────┘  └──────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Typed Model    │
                    │   Instance      │
                    └─────────────────┘
```

## Validation Flow

Each model enforces validation at multiple levels:

### Level 1: Field Type Validation

Pydantic validates each field against its declared type:

```python
name: str = Field(..., min_length=1, max_length=100)
email: EmailStr
linkedin: HttpUrl | None = None
```

### Level 2: Custom Type Validation

Custom types apply regex patterns and transformations:

```python
# ResumeID: Must match ^[a-z0-9][a-z0-9_-]*$
id: Annotated[str, _ResumeIDAnnotation]

# TechTag: Auto-lowercased, must match ^[a-z0-9][a-z0-9._-]*$
tags: list[Annotated[str, _TechTagAnnotation]]

# ResumeDate: Parsed to ResumeDateValue with comparison support
start_date: ResumeDateValue
```

### Level 3: Model Validation

Model validators enforce cross-field constraints:

```python
@model_validator(mode="after")
def _validate_date_range(self) -> "ExperienceEntry":
    if self.end_date is not None:
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
    return self
```

### Level 4: Container Validation

Container models enforce ID uniqueness:

```python
@model_validator(mode="after")
def _validate_unique_ids(self) -> "Education":
    ids = [entry.id for entry in self.entries]
    duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
    if duplicates:
        raise ValueError(f"Duplicate IDs: {set(duplicates)}")
    return self
```

## File Ownership

| Directory                   | Owner    | Schema           |
| --------------------------- | -------- | ---------------- |
| `data/profile.yaml`         | data/    | `Profile`        |
| `data/education.yaml`       | data/    | `Education`      |
| `data/skills.yaml`          | data/    | `Skills`         |
| `content/experience/*.yaml` | content/ | `ExperienceFile` |
| `content/projects/*.yaml`   | content/ | `ProjectFile`    |

## Dependency Graph

```
scripts/rvs/
├── __init__.py
│   └── imports from: models
├── loader.py
│   └── imports from: pydantic, yaml
└── models/
    ├── __init__.py
    │   └── re-exports all models
    ├── base.py
    │   └── imports from: pydantic, pydantic_core
    ├── profile.py
    │   └── imports from: base
    ├── education.py
    │   └── imports from: base
    ├── skills.py
    │   └── imports from: base
    ├── experience.py
    │   └── imports from: base
    └── project.py
        └── imports from: base
```

## Error Handling Strategy

### Exception Hierarchy

```
Exception
├── FileNotFoundError      # File does not exist
├── YAMLLoadError          # Encoding or parsing failure
│   ├── UTF-8 decode error
│   ├── YAML syntax error
│   ├── Empty file
│   └── Wrong root type
└── YAMLValidationError    # Pydantic validation failure
    └── Contains full ValidationError details
```

### Error Propagation

Errors are raised immediately upon detection. The loader does not attempt recovery or partial parsing. Callers must handle exceptions explicitly.

## Invariants

The following invariants are enforced by the schema:

1. **ID Format**: All IDs match `^[a-z0-9][a-z0-9_-]*$`
2. **ID Uniqueness**: IDs are unique within their container scope
3. **Date Ordering**: `end_date >= start_date` when both present
4. **Required Fields**: All required fields must be present
5. **No Extra Fields**: Unknown fields cause validation failure
6. **UTF-8 Encoding**: All YAML files must be valid UTF-8
7. **YAML 1.2**: Files must be valid YAML 1.2

## Extension Points

### Adding a New Model

1. Create `scripts/rvs/models/<name>.py`
2. Inherit from `BaseResumeModel`
3. Define fields with appropriate types
4. Add model validators as needed
5. Export from `scripts/rvs/models/__init__.py`
6. Add tests to `tests/test_schemas.py`

### Adding a New Custom Type

1. Define validation function in `base.py`
2. Create annotation class with `__get_pydantic_core_schema__`
3. Export type alias
4. Add unit tests for valid/invalid cases

## Performance Considerations

- YAML parsing uses `yaml.safe_load` (no arbitrary code execution)
- Pydantic V2 uses compiled validators for performance
- No lazy loading; entire file is validated on load
- ResumeDateValue uses `__slots__` for memory efficiency
