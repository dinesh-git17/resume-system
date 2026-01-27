# Testing

Test structure, execution, and coverage for the RVS schema layer.

## Test Location

```
tests/
├── __init__.py
└── test_schemas.py
```

## Test Structure

Tests are organized by component in `tests/test_schemas.py`:

### Custom Type Tests

| Class | Tests |
|-------|-------|
| `TestResumeID` | ResumeID format validation |
| `TestTechTag` | TechTag format validation |
| `TestResumeDate` | ResumeDateValue parsing and comparison |
| `TestResumeDateValueEdgeCases` | Hash, repr, operators |

### Model Tests

| Class | Tests |
|-------|-------|
| `TestProfileModel` | Profile validation |
| `TestEducationModel` | Education/EducationEntry validation |
| `TestSkillsModel` | Skills validation with duplicate detection |
| `TestExperienceModel` | Experience/Highlight validation |
| `TestProjectModel` | Project/ProjectHighlight validation |

### Validation Tests

| Class | Tests |
|-------|-------|
| `TestProjectDateValidation` | Project date range validation |
| `TestExperienceDateValidation` | Experience date range validation |
| `TestProjectFileValidation` | ProjectFile ID uniqueness |

### Loader Tests

| Class | Tests |
|-------|-------|
| `TestYAMLLoader` | load_yaml_strict and load_yaml_list_strict |

### Integration Tests

| Class | Tests |
|-------|-------|
| `TestCanonicalFiles` | Validation of canonical YAML files |

## Running Tests

### Full Suite

```bash
.venv/bin/python -m pytest tests/ -v
```

### With Coverage

```bash
.venv/bin/python -m pytest tests/ --cov=scripts.rvs --cov-report=term-missing
```

### Specific Class

```bash
.venv/bin/python -m pytest tests/test_schemas.py::TestResumeID -v
```

### Specific Test

```bash
.venv/bin/python -m pytest tests/test_schemas.py::TestResumeID::test_valid_lowercase_alphanumeric -v
```

### Pattern Matching

```bash
# Run all tests with "valid" in name
.venv/bin/python -m pytest tests/ -k "valid" -v

# Run all tests with "reject" in name
.venv/bin/python -m pytest tests/ -k "reject" -v
```

## Coverage

### Current Coverage

The test suite achieves 96% coverage of the `scripts.rvs` package:

| Module | Coverage |
|--------|----------|
| `scripts/rvs/__init__.py` | 100% |
| `scripts/rvs/loader.py` | 94% |
| `scripts/rvs/models/__init__.py` | 100% |
| `scripts/rvs/models/base.py` | 91% |
| `scripts/rvs/models/education.py` | 100% |
| `scripts/rvs/models/experience.py` | 100% |
| `scripts/rvs/models/profile.py` | 100% |
| `scripts/rvs/models/project.py` | 100% |
| `scripts/rvs/models/skills.py` | 100% |

### Coverage Report

```bash
.venv/bin/python -m pytest tests/ --cov=scripts.rvs --cov-report=term-missing
```

Output shows uncovered lines:

```
Name                               Stmts   Miss  Cover   Missing
----------------------------------------------------------------
scripts/rvs/__init__.py                2      0   100%
scripts/rvs/loader.py                 69      4    94%   73-74, 123-124
...
```

## Test Patterns

### Valid Input Tests

Test that valid input is accepted:

```python
def test_valid_lowercase_alphanumeric(self) -> None:
    """Accept lowercase alphanumeric IDs."""
    assert _validate_resume_id("google") == "google"
    assert _validate_resume_id("experience1") == "experience1"
```

### Invalid Input Tests

Test that invalid input is rejected with appropriate errors:

```python
def test_reject_uppercase(self) -> None:
    """Reject IDs with uppercase letters."""
    with pytest.raises(ValueError, match="lowercase alphanumeric"):
        _validate_resume_id("Google")
```

### Model Validation Tests

Test complete model validation:

```python
def test_valid_full_profile(self) -> None:
    """Accept complete profile data."""
    profile = Profile(
        name="Alex Chen",
        email="alex@example.com",
        phone="+1-555-123-4567",
        location="San Francisco, CA",
        linkedin="https://linkedin.com/in/alexchen",
    )
    assert profile.name == "Alex Chen"
    assert str(profile.email) == "alex@example.com"
```

### Extra Field Tests

Test that extra fields are rejected:

```python
def test_reject_extra_fields(self) -> None:
    """Reject extra fields not in schema."""
    with pytest.raises(ValidationError, match="Extra inputs"):
        Profile(
            name="Alex Chen",
            email="alex@example.com",
            unknown_field="value",
        )
```

### Container Validation Tests

Test container-level validation:

```python
def test_education_unique_ids(self) -> None:
    """Reject duplicate education entry IDs."""
    with pytest.raises(ValidationError, match="Duplicate"):
        Education(
            entries=[
                EducationEntry(id="same-id", ...),
                EducationEntry(id="same-id", ...),
            ]
        )
```

### Loader Tests

Test YAML loading with fixtures:

```python
def test_load_valid_yaml(self, tmp_path: Path) -> None:
    """Load valid YAML file."""
    yaml_content = """
name: Alex Chen
email: alex@example.com
"""
    yaml_file = tmp_path / "profile.yaml"
    yaml_file.write_text(yaml_content, encoding="utf-8")

    profile = load_yaml_strict(yaml_file, Profile)
    assert profile.name == "Alex Chen"
```

### Canonical File Tests

Test that canonical YAML files remain valid:

```python
def test_profile_yaml_valid(self, data_dir: Path) -> None:
    """Canonical profile.yaml passes validation."""
    profile = load_yaml_strict(data_dir / "profile.yaml", Profile)
    assert profile.name
    assert profile.email
```

## Adding Tests

### For New Custom Types

1. Create test class `TestNewType`
2. Add valid input tests
3. Add invalid input tests with error matching
4. Test edge cases (empty, boundary values)

### For New Models

1. Create test class `TestNewModel`
2. Test valid complete input
3. Test valid minimal input
4. Test invalid email/URL formats
5. Test extra field rejection
6. Test constraint violations

### For New Loaders

1. Add to `TestYAMLLoader` or create new class
2. Test valid file loading
3. Test file not found
4. Test non-UTF-8 handling
5. Test YAML syntax errors
6. Test empty files
7. Test validation errors

### For New YAML Files

1. Add to `TestCanonicalFiles`
2. Test file exists and loads
3. Test critical fields are present

## Test Dependencies

| Package | Purpose |
|---------|---------|
| pytest | Test framework |
| pytest-cov | Coverage reporting |

Install with:

```bash
uv sync --group dev
```

## pytest Configuration

Configuration in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

## Continuous Integration

Tests should run on every commit. Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync --group dev

      - name: Run tests
        run: .venv/bin/python -m pytest tests/ -v --cov=scripts.rvs

      - name: Protocol Zero check
        run: ./scripts/protocol-zero.sh
```

## Debugging Test Failures

### Verbose Output

```bash
.venv/bin/python -m pytest tests/ -v --tb=long
```

### Stop on First Failure

```bash
.venv/bin/python -m pytest tests/ -x
```

### Print Statements

```bash
.venv/bin/python -m pytest tests/ -s
```

### Debug with pdb

```bash
.venv/bin/python -m pytest tests/ --pdb
```

Or add breakpoint in test:

```python
def test_something(self) -> None:
    import pdb; pdb.set_trace()
    # ... rest of test
```
