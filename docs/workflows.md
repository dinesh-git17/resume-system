# Workflows

Developer workflows for common tasks.

## Initial Setup

### Prerequisites

- Python 3.11 or higher
- Git
- uv package manager (installed automatically by setup script)

### Setup Steps

```bash
# Clone repository
git clone <repository-url>
cd resume-system

# Run automated setup
./setup.sh
```

The setup script:

1. Verifies or installs uv package manager
2. Creates Python virtual environment
3. Installs all dependencies
4. Sets up pre-commit hooks

### Manual Setup

If the setup script fails:

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync --group dev

# Install pre-commit hooks
.venv/bin/pre-commit install
```

### Verify Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify Python version
python --version  # Should be 3.11+

# Verify imports work
python -c "from scripts.rvs.models import Profile; print('OK')"

# Run tests
python -m pytest tests/test_schemas.py -v
```

## Validation Workflow

### Before Committing

1. Run Protocol Zero check:
   ```bash
   ./scripts/protocol-zero.sh
   ```

2. Run YAML linting:
   ```bash
   .venv/bin/yamllint data/ content/
   ```

3. Run tests:
   ```bash
   .venv/bin/python -m pytest tests/ -v
   ```

### Validation Script

Create a single validation script:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Running Protocol Zero check..."
./scripts/protocol-zero.sh

echo "Running YAML lint..."
.venv/bin/yamllint data/ content/

echo "Running tests..."
.venv/bin/python -m pytest tests/ -v

echo "All checks passed!"
```

## Adding New Data

### Adding a Profile Field

1. Update `scripts/rvs/models/profile.py`:
   ```python
   class Profile(BaseResumeModel):
       # existing fields...
       new_field: str | None = Field(default=None, max_length=100)
   ```

2. Update `data/profile.yaml` (optional):
   ```yaml
   name: Alex Chen
   email: alex@example.com
   new_field: value
   ```

3. Add tests in `tests/test_schemas.py`:
   ```python
   def test_profile_with_new_field(self) -> None:
       profile = Profile(
           name="Test",
           email="test@example.com",
           new_field="value",
       )
       assert profile.new_field == "value"
   ```

4. Run validation:
   ```bash
   .venv/bin/python -m pytest tests/test_schemas.py -v
   ```

### Adding an Experience Entry

1. Edit `content/experience/<company>.yaml`:
   ```yaml
   entries:
     - id: company-role-1
       company: Company Name
       role: Job Title
       location: City, State
       start_date: "2024-01"
       end_date: Present
       highlights:
         - id: company-role-1-h1
           text: Achievement description.
           tags:
             - python
             - kubernetes
   ```

2. Validate:
   ```python
   from scripts.rvs.loader import load_yaml_strict
   from scripts.rvs.models import ExperienceFile

   exp = load_yaml_strict("content/experience/<company>.yaml", ExperienceFile)
   print(f"Loaded {len(exp.entries)} entries")
   ```

### Adding a Skill

1. Edit `data/skills.yaml`:
   ```yaml
   languages:
     - python
     - go
     - new-skill  # Add here
   ```

2. Validate:
   ```python
   from scripts.rvs.loader import load_yaml_strict
   from scripts.rvs.models import Skills

   skills = load_yaml_strict("data/skills.yaml", Skills)
   assert "new-skill" in skills.languages
   ```

## Adding New Models

### Step 1: Create Model File

Create `scripts/rvs/models/<name>.py`:

```python
"""<Name> model for <description>.

Defines the schema for <filename>.yaml containing <content description>.
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


class <Name>Entry(BaseResumeModel):
    """Single <name> entry."""

    id: Annotated[str, _ResumeIDAnnotation]
    # Add fields here


class <Name>File(BaseResumeModel):
    """Container for <name> entries."""

    entries: list[<Name>Entry] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_unique_ids(self) -> "<Name>File":
        """Ensure all entry IDs are unique."""
        ids = [entry.id for entry in self.entries]
        duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
        if duplicates:
            raise ValueError(f"Duplicate IDs: {set(duplicates)}")
        return self
```

### Step 2: Export from Package

Edit `scripts/rvs/models/__init__.py`:

```python
from scripts.rvs.models.<name> import <Name>Entry, <Name>File

__all__ = [
    # existing exports...
    "<Name>Entry",
    "<Name>File",
]
```

### Step 3: Add Tests

Edit `tests/test_schemas.py`:

```python
class Test<Name>Model:
    """Tests for <Name> model validation."""

    def test_valid_entry(self) -> None:
        entry = <Name>Entry(
            id="test-entry",
            # fields...
        )
        assert entry.id == "test-entry"

    def test_duplicate_ids_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate"):
            <Name>File(
                entries=[
                    <Name>Entry(id="same-id", ...),
                    <Name>Entry(id="same-id", ...),
                ]
            )
```

### Step 4: Create Sample YAML

Create sample file in appropriate directory:

```yaml
entries:
  - id: sample-entry
    # fields...
```

### Step 5: Validate

```bash
.venv/bin/python -m pytest tests/test_schemas.py -v
```

## Debugging

### Validation Errors

When validation fails, examine the error details:

```python
from pydantic import ValidationError
from scripts.rvs.models import Profile

try:
    Profile(name="", email="invalid")
except ValidationError as e:
    for error in e.errors():
        print(f"Field: {error['loc']}")
        print(f"Type: {error['type']}")
        print(f"Message: {error['msg']}")
        print()
```

### YAML Loading Errors

When YAML loading fails:

```python
from scripts.rvs.loader import load_yaml_strict, YAMLLoadError, YAMLValidationError
from scripts.rvs.models import Profile

try:
    profile = load_yaml_strict("data/profile.yaml", Profile)
except YAMLLoadError as e:
    print(f"Load error: {e.message}")
    print(f"File: {e.path}")
    if e.cause:
        print(f"Cause: {e.cause}")
except YAMLValidationError as e:
    print(f"Validation error in: {e.path}")
    print(f"Model: {e.model_name}")
    print(e.validation_error)
```

### Interactive Testing

Use Python REPL for interactive debugging:

```bash
.venv/bin/python
```

```python
>>> from scripts.rvs.models import Profile
>>> Profile(name="Test", email="test@example.com")
Profile(name='Test', email='test@example.com', ...)

>>> from scripts.rvs.models.base import _parse_resume_date
>>> d = _parse_resume_date("2024-06")
>>> d.value
datetime.date(2024, 6, 1)
>>> d.is_present
False
```

## Running Tests

### Full Test Suite

```bash
.venv/bin/python -m pytest tests/ -v
```

### With Coverage

```bash
.venv/bin/python -m pytest tests/ --cov=scripts.rvs --cov-report=term-missing
```

### Specific Tests

```bash
# Run single test class
.venv/bin/python -m pytest tests/test_schemas.py::TestResumeID -v

# Run single test method
.venv/bin/python -m pytest tests/test_schemas.py::TestResumeID::test_valid_lowercase_alphanumeric -v

# Run tests matching pattern
.venv/bin/python -m pytest tests/ -k "valid" -v
```

## Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`.

### Manual Run

```bash
# Run all hooks on all files
.venv/bin/pre-commit run --all-files

# Run specific hook
.venv/bin/pre-commit run yamllint --all-files
```

### Skip Hooks (Emergency Only)

```bash
git commit --no-verify -m "message"
```

Use only when absolutely necessary and fix issues immediately after.
