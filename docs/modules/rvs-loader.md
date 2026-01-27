# Module: scripts.rvs.loader

Strict YAML loader with Pydantic validation.

## Purpose

This module provides type-safe YAML loading with:

- UTF-8 encoding enforcement
- YAML 1.2 compliance via PyYAML SafeLoader
- Automatic Pydantic model validation
- Descriptive error handling

## Location

```
scripts/rvs/loader.py
```

## Public Interface

### Functions

#### load_yaml_strict

Load a YAML file and validate against a Pydantic model.

```python
def load_yaml_strict(path: Path | str, model_class: type[T]) -> T:
    """Load a YAML file and validate against a Pydantic model.

    Args:
        path: Path to the YAML file.
        model_class: Pydantic model class to validate against.

    Returns:
        Validated Pydantic model instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        YAMLLoadError: If file cannot be read or parsed as YAML.
        YAMLValidationError: If content fails Pydantic validation.
    """
```

**Usage:**

```python
from pathlib import Path
from scripts.rvs.loader import load_yaml_strict
from scripts.rvs.models import Profile

profile = load_yaml_strict(Path("data/profile.yaml"), Profile)
# or with string path
profile = load_yaml_strict("data/profile.yaml", Profile)
```

#### load_yaml_list_strict

Load a YAML file containing a list and validate each item.

```python
def load_yaml_list_strict(path: Path | str, model_class: type[T]) -> list[T]:
    """Load a YAML file containing a list and validate each item.

    Args:
        path: Path to the YAML file.
        model_class: Pydantic model class to validate each item against.

    Returns:
        List of validated Pydantic model instances.

    Raises:
        FileNotFoundError: If the file does not exist.
        YAMLLoadError: If file cannot be read or parsed as YAML.
        YAMLValidationError: If any item fails Pydantic validation.
    """
```

**Usage:**

```python
from scripts.rvs.loader import load_yaml_list_strict
from scripts.rvs.models import Highlight

# For a YAML file containing a list of highlights
highlights = load_yaml_list_strict("highlights.yaml", Highlight)
```

### Exceptions

#### YAMLLoadError

Raised when YAML loading fails due to encoding or parsing issues.

```python
class YAMLLoadError(Exception):
    def __init__(self, path: Path, message: str, cause: Exception | None = None):
        self.path = path
        self.message = message
        self.cause = cause
```

**Attributes:**
- `path`: Path to the file that failed to load
- `message`: Human-readable error description
- `cause`: Original exception that caused the failure

**Raised for:**
- Non-UTF-8 encoded files
- YAML syntax errors
- Empty files
- Files with wrong root type (list vs mapping)

#### YAMLValidationError

Raised when YAML content fails Pydantic validation.

```python
class YAMLValidationError(Exception):
    def __init__(
        self, path: Path, model_name: str, validation_error: ValidationError
    ):
        self.path = path
        self.model_name = model_name
        self.validation_error = validation_error
```

**Attributes:**
- `path`: Path to the file that failed validation
- `model_name`: Name of the Pydantic model that failed
- `validation_error`: Original Pydantic ValidationError with details

## Validation Steps

The loader performs validation in this order:

1. **File existence**: Raises `FileNotFoundError` if missing
2. **UTF-8 decoding**: Raises `YAMLLoadError` for encoding errors
3. **YAML parsing**: Raises `YAMLLoadError` for syntax errors
4. **Empty check**: Raises `YAMLLoadError` for empty/null content
5. **Root type check**: Raises `YAMLLoadError` for wrong structure
6. **Pydantic validation**: Raises `YAMLValidationError` for schema violations

## Error Handling

### Handling Load Errors

```python
from scripts.rvs.loader import (
    load_yaml_strict,
    YAMLLoadError,
    YAMLValidationError,
)
from scripts.rvs.models import Profile

try:
    profile = load_yaml_strict("data/profile.yaml", Profile)
except FileNotFoundError:
    print("File does not exist")
except YAMLLoadError as e:
    print(f"Failed to load {e.path}: {e.message}")
    if e.cause:
        print(f"Caused by: {e.cause}")
except YAMLValidationError as e:
    print(f"Validation failed for {e.path}")
    print(f"Model: {e.model_name}")
    for error in e.validation_error.errors():
        print(f"  {error['loc']}: {error['msg']}")
```

### Common Error Messages

| Error Type | Message Pattern | Cause |
|------------|-----------------|-------|
| `YAMLLoadError` | "File is not valid UTF-8" | Non-UTF-8 encoding |
| `YAMLLoadError` | "Invalid YAML syntax" | YAML parse error |
| `YAMLLoadError` | "YAML file is empty or contains only null" | Empty file |
| `YAMLLoadError` | "YAML root must be a mapping" | List instead of dict |
| `YAMLLoadError` | "YAML root must be a list" | Dict instead of list |
| `YAMLValidationError` | "Validation failed for..." | Schema violation |

## Invariants

1. **UTF-8 Only**: Files must be valid UTF-8
2. **No Arbitrary Code**: Uses `yaml.safe_load` only
3. **Type Safety**: Returns typed model instances
4. **Fail Fast**: Raises on first error, no partial results
5. **Path Flexibility**: Accepts both `Path` and `str`

## Failure Modes

### File System Errors

| Condition | Exception |
|-----------|-----------|
| File not found | `FileNotFoundError` |
| Permission denied | `YAMLLoadError` with OSError cause |
| Not a file | `YAMLLoadError` with OSError cause |

### Encoding Errors

| Condition | Exception |
|-----------|-----------|
| Non-UTF-8 bytes | `YAMLLoadError` with UnicodeDecodeError cause |
| Invalid UTF-8 sequence | `YAMLLoadError` with UnicodeDecodeError cause |

### YAML Errors

| Condition | Exception |
|-----------|-----------|
| Syntax error | `YAMLLoadError` with YAMLError cause |
| Unclosed quotes | `YAMLLoadError` with YAMLError cause |
| Tab indentation | `YAMLLoadError` with YAMLError cause |

### Validation Errors

| Condition | Exception |
|-----------|-----------|
| Missing required field | `YAMLValidationError` |
| Invalid field type | `YAMLValidationError` |
| Extra field present | `YAMLValidationError` |
| Constraint violation | `YAMLValidationError` |

## Extension Guidelines

### Adding Custom Loaders

For specialized loading needs, wrap the existing functions:

```python
from pathlib import Path
from scripts.rvs.loader import load_yaml_strict
from scripts.rvs.models import ExperienceFile

def load_experience(company: str) -> ExperienceFile:
    """Load experience file for a specific company."""
    path = Path("content/experience") / f"{company}.yaml"
    return load_yaml_strict(path, ExperienceFile)
```

### Adding Pre-Processing

For files requiring transformation before validation:

```python
import yaml
from pathlib import Path
from scripts.rvs.models import Skills

def load_skills_with_defaults(path: Path) -> Skills:
    """Load skills with default empty categories."""
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content) or {}

    # Ensure all categories exist
    for category in ["languages", "frameworks", "databases", "tools"]:
        data.setdefault(category, [])

    return Skills.model_validate(data)
```

## Testing

The loader is tested in `tests/test_schemas.py`:

- `TestYAMLLoader`: Unit tests for loader functions
- `TestCanonicalFiles`: Integration tests with real YAML files
