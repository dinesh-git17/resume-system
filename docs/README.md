# RVS Documentation

Resume Versioning System (RVS) is a Resume-as-Code infrastructure that provides strongly typed, machine-readable schemas for professional resume data. This documentation covers the core data schema layer implemented in Epic RVS-P1-002.

## Purpose

RVS enables deterministic, validated resume generation by enforcing strict Pydantic V2 schemas on all YAML source files. The system prevents schema drift, ensures ID uniqueness, and provides type-safe data loading.

## Architecture Overview

```
resume-system/
├── data/                    # Atomic facts (Profile, Education, Skills)
│   ├── profile.yaml
│   ├── education.yaml
│   └── skills.yaml
├── content/                 # Narrative bricks (Experience, Projects)
│   ├── experience/
│   │   └── google.yaml
│   └── projects/
│       └── projects.yaml
├── scripts/
│   └── rvs/                 # Core validation package
│       ├── __init__.py
│       ├── loader.py        # YAML loading with validation
│       └── models/          # Pydantic schema definitions
│           ├── __init__.py
│           ├── base.py      # Custom types and base model
│           ├── profile.py
│           ├── education.py
│           ├── skills.py
│           ├── experience.py
│           └── project.py
├── tests/
│   └── test_schemas.py      # Schema validation tests
└── docs/                    # This documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- uv package manager

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd resume-system
./setup.sh

# Or manual setup
uv sync --group dev
```

### Validate YAML Files

```python
from scripts.rvs.loader import load_yaml_strict
from scripts.rvs.models import Profile, Education, Skills

# Load and validate profile
profile = load_yaml_strict("data/profile.yaml", Profile)

# Load and validate education
education = load_yaml_strict("data/education.yaml", Education)

# Load and validate skills
skills = load_yaml_strict("data/skills.yaml", Skills)
```

### Run Tests

```bash
.venv/bin/python -m pytest tests/test_schemas.py -v
```

### Run Protocol Zero Check

```bash
./scripts/protocol-zero.sh
```

## Key Concepts

### Custom Types

| Type         | Pattern                  | Example              |
| ------------ | ------------------------ | -------------------- |
| `ResumeID`   | `^[a-z0-9][a-z0-9_-]*$`  | `google-staff-swe`   |
| `TechTag`    | `^[a-z0-9][a-z0-9._-]*$` | `node.js`, `grpc`    |
| `ResumeDate` | `YYYY-MM` or `Present`   | `2024-01`, `Present` |

### Data Tiers

1. **Atomic Facts** (`data/`): Contact, education, skills. Single source of truth.
2. **Narrative Bricks** (`content/`): Experience and project entries. Addressable by ID.
3. **Templates** (`templates/`): Presentation layer. No data logic.
4. **Config** (`config/`): Build manifests. Orchestration only.

### Validation Flow

```
YAML File → UTF-8 Check → YAML Parse → Pydantic Validation → Typed Model
```

## Common Workflows

| Task                | Command                                        |
| ------------------- | ---------------------------------------------- |
| Run all tests       | `.venv/bin/python -m pytest tests/ -v`         |
| Run with coverage   | `.venv/bin/python -m pytest --cov=scripts.rvs` |
| Lint YAML           | `.venv/bin/yamllint data/ content/`            |
| Protocol Zero check | `./scripts/protocol-zero.sh`                   |

## Documentation Index

- [Architecture](architecture.md): System boundaries, data flow, validation
- [Models Reference](models.md): Complete schema documentation
- [Workflows](workflows.md): Developer setup and common tasks
- [Testing](testing.md): Test structure and coverage
- [CLI Tools](cli.md): Protocol Zero and validation scripts

### Module Documentation

- [rvs.models](modules/rvs-models.md): Pydantic schema definitions
- [rvs.loader](modules/rvs-loader.md): YAML loading with validation

## Governance

All code and data in this repository is governed by `CLAUDE.md`. Key rules:

1. All YAML files must pass Pydantic validation
2. Every entry requires a unique, immutable ID
3. Extra fields are forbidden (strict schema enforcement)
4. UTF-8 encoding is mandatory
5. YAML 1.2 with 2-space indentation

## Dependencies

| Package    | Version    | Purpose           |
| ---------- | ---------- | ----------------- |
| pydantic   | >=2.0,<3.0 | Schema validation |
| pyyaml     | >=6.0,<7.0 | YAML parsing      |
| pytest     | >=8.0,<9.0 | Testing (dev)     |
| pytest-cov | >=4.0,<5.0 | Coverage (dev)    |
