# Resume Versioning System (RVS)

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Pydantic](https://img.shields.io/badge/pydantic-v2-blue)
![Build](https://img.shields.io/badge/build-deterministic-green)
![Local-First](https://img.shields.io/badge/architecture-local--first-purple)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Status](https://img.shields.io/badge/status-stable-green)

A deterministic, local-first resume generation engine that treats resumes as structured data.

## Problem

Traditional resume management suffers from:

1. **Version drift**: Multiple copies diverge across applications
2. **Content sprawl**: Experience bullets scattered across documents
3. **Manual tailoring**: Rewriting for each job description
4. **No validation**: Typos, broken links, inconsistent formatting

RVS solves this by storing resume content as validated YAML, selecting content via manifests, and generating HTML through deterministic builds.

## Key Features

- **YAML-based content store**: All experience, projects, skills, and education stored as structured YAML with unique IDs
- **Manifest-driven builds**: Select which content appears in each resume variant via configuration
- **Pydantic V2 validation**: Strict schema enforcement with referential integrity checks
- **Deterministic output**: Same input produces bit-identical output with `--reproducible` flag
- **Bullet-level selection**: Include specific highlights from each experience or project entry
- **Claude Code integration**: Skill system for job description analysis and content matching

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Build Pipeline                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   data/           content/           config/                    │
│   ├─ profile     ├─ experience/     └─ manifest.yaml            │
│   ├─ education   └─ projects/            │                      │
│   └─ skills           │                  │                      │
│        │              │                  │                      │
│        └──────────────┴──────────────────┘                      │
│                       │                                         │
│                       ▼                                         │
│              ┌─────────────────┐                                │
│              │   validator.py  │  Schema + ID + Ref checks      │
│              └────────┬────────┘                                │
│                       │                                         │
│                       ▼                                         │
│              ┌─────────────────┐                                │
│              │    engine.py    │  Load → Resolve → Render       │
│              └────────┬────────┘                                │
│                       │                                         │
│                       ▼                                         │
│              ┌─────────────────┐                                │
│              │   out/*.html    │  Atomic write                  │
│              └─────────────────┘                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Repository Structure

```
resume-system/
├── data/                     # Atomic facts (singleton YAML)
│   ├── profile.yaml          # Contact information
│   ├── education.yaml        # Academic credentials
│   └── skills.yaml           # Categorized skill lists
│
├── content/                  # Addressable content bricks
│   ├── experience/           # Work history with highlights
│   └── projects/             # Portfolio with highlights
│
├── config/                   # Build manifests
│   └── <FirstName>_<LastName>_<Company>_<Role>_Resume.yaml  # Naming convention
│
├── templates/                # Jinja2 templates (read-only)
│   └── resume.html.j2        # HTML resume template
│
├── scripts/                  # Automation layer
│   ├── engine.py             # Build CLI
│   ├── validator.py          # Validation CLI
│   ├── bootstrap.sh          # Environment setup
│   ├── lint.sh               # Linting wrapper
│   ├── validate.sh           # Validation wrapper
│   ├── protocol-zero.sh      # Attribution scanner
│   └── rvs/                  # Core package
│       ├── models/           # Pydantic V2 schemas
│       ├── engine/           # Build pipeline
│       └── validator/        # Validation subsystem
│
├── .claude/skills/           # Claude Code skill definitions
│   ├── jd-analyzer/          # Job description extraction
│   ├── content-librarian/    # Content search
│   ├── manifest-composer/    # Manifest generation
│   └── integrity-enforcer/   # Validation wrapper
│
├── tests/                    # pytest test suite
├── out/                      # Generated artifacts (gitignored)
└── docs/                     # Documentation
```

## Data Model

### Singleton Data (`data/`)

| File | Schema | Purpose |
|------|--------|---------|
| `profile.yaml` | `Profile` | Name, email, phone, location, links |
| `education.yaml` | `Education` | Degrees with institution, dates, honors |
| `skills.yaml` | `Skills` | Languages, frameworks, databases, tools |

### Content Bricks (`content/`)

| Directory | Schema | Purpose |
|-----------|--------|---------|
| `experience/*.yaml` | `ExperienceFile` | Jobs with role, company, highlights |
| `projects/*.yaml` | `ProjectFile` | Projects with description, tech stack, highlights |

### ID System

All addressable content uses unique IDs following the pattern `^[a-z0-9][a-z0-9_-]*$`.

```yaml
# content/experience/company.yaml
entries:
  - id: company-role-swe        # Entry ID
    role: Software Engineer
    highlights:
      - id: company-role-perf   # Bullet ID
        text: Improved latency by 40%
```

Manifests reference these IDs to select content:

```yaml
# config/<FirstName>_<LastName>_<Company>_<Role>_Resume.yaml
include_experience:
  - id: company-role-swe
    bullets:
      - company-role-perf       # Optional: select specific bullets
```

## Workflow

### Validate

```bash
./scripts/validate.sh
```

Checks:
- YAML syntax
- Pydantic schema compliance
- ID format and uniqueness
- Referential integrity (manifest IDs exist in content)

Exit codes: `0` = pass, `1` = validation errors, `2` = internal error

### Build

```bash
# Manifest naming convention: <FirstName>_<LastName>_<Company>_<Role>_Resume.yaml
python scripts/engine.py --manifest config/Dinesh_Dawonauth_Google_Data_Scientist_Resume.yaml
```

Pipeline stages:
1. `prepare-output`: Create/clean output directory
2. `load-manifest`: Parse and validate manifest
3. `load-static-data`: Load profile, skills, education
4. `resolve-content`: Resolve IDs to content objects
5. `assemble-context`: Build template context
6. `render-template`: Render Jinja2 template
7. `write-output`: Atomic write to `out/`

For bit-identical reproducible builds:

```bash
python scripts/engine.py --manifest config/Dinesh_Dawonauth_Google_Data_Scientist_Resume.yaml --reproducible
```

## Claude Code Integration

RVS includes a skill system for Claude Code agents located in `.claude/skills/`.

### Skills

| Skill | Purpose |
|-------|---------|
| `jd-analyzer` | Extract structured requirements from job descriptions |
| `content-librarian` | Search content store for matching IDs |
| `manifest-composer` | Generate valid manifest files |
| `integrity-enforcer` | Run validation and report results |

### Grounding Rule

Claude agents operate under a closed-world assumption:

- Only data in `data/` and `content/` exists
- No content invention or embellishment
- Missing content triggers a stop, not generation

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Clone repository
git clone https://github.com/dinesh-git17/resume-system.git
cd resume-system

# Run bootstrap (creates venv, installs deps, configures pre-commit)
./scripts/bootstrap.sh

# Activate environment
source .venv/bin/activate
```

### Verify Installation

```bash
./scripts/validate.sh
python scripts/engine.py --manifest config/Dinesh_Dawonauth_Example_Resume.yaml
```

## Usage

### Create a New Resume Variant

1. Create a manifest in `config/` using naming convention `<FirstName>_<LastName>_<Company>_<Role>_Resume.yaml`:

```yaml
# config/Dinesh_Dawonauth_Google_SWE_Resume.yaml
template: resume
profile: default

include_experience:
  - id: company-senior-swe
    bullets:
      - company-senior-arch
      - company-senior-scale
  - id: startup-engineer

include_projects:
  - id: open-source-tool
```

2. Validate:

```bash
./scripts/validate.sh
```

3. Build:

```bash
python scripts/engine.py --manifest config/Dinesh_Dawonauth_Google_SWE_Resume.yaml
```

4. Output: `out/Dinesh_Dawonauth_Google_SWE_Resume.html`

### Add New Content

1. Add entry to `content/experience/experience.yaml` or `content/projects/projects.yaml`
2. Assign unique IDs to entry and each highlight
3. Run `./scripts/validate.sh`
4. Reference new IDs in manifest

## Determinism Guarantees

With `--reproducible` flag:

- Timestamp fixed to `1970-01-01T00:00:00Z`
- Git hash fixed to `0000000`
- Skills sorted alphabetically within categories
- Manifest order preserved in output
- Same input produces identical output bytes

Without flag:
- Build includes current timestamp and git hash
- Content order still deterministic

## Development

### Linting

```bash
./scripts/lint.sh
```

Runs: ruff, mypy, yamllint

### Testing

```bash
.venv/bin/python -m pytest tests/ -v
```

### Pre-commit Hooks

Installed by `bootstrap.sh`. Enforces:
- YAML syntax
- Linting
- Protocol Zero (no attribution markers)

### Adding a New Schema

1. Define Pydantic model in `scripts/rvs/models/`
2. Register path mapping in `scripts/rvs/validator/registry.py`
3. Add test cases in `tests/`

## Validation Commands

| Command | Purpose |
|---------|---------|
| `./scripts/validate.sh` | Schema and referential integrity |
| `./scripts/lint.sh` | Code and YAML linting |
| `./scripts/protocol-zero.sh` | Attribution marker scan |

## Exit Codes

| Script | Code | Meaning |
|--------|------|---------|
| `validate.sh` | 0 | All validations passed |
| `validate.sh` | 1 | Validation errors |
| `validate.sh` | 2 | Internal error |
| `engine.py` | 0 | Build succeeded |
| `engine.py` | 1 | Build failed |

## Notes

### Protocol Zero

This repository enforces a zero-tolerance policy for attribution markers. The `protocol-zero.sh` script scans for forbidden phrases before commits.

### Template Modifications

Templates in `templates/` are treated as read-only. Modifications require explicit override instruction to maintain separation between content and presentation.

### ID Naming Convention

Recommended pattern: `<company>-<role>-<descriptor>`

Examples:
- `google-staff-swe`
- `google-staff-distributed-cache`
- `startup-engineer-ml-pipeline`

## License

MIT
