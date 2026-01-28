# CLAUDE-CONTEXT.md

## One Paragraph Summary

RVS (Resume Versioning System) is a local-first, deterministic resume generation engine. It stores professional experience, education, skills, and projects as structured YAML files with unique IDs. A manifest system selects which content IDs to include in each resume variant. The build pipeline validates YAML against Pydantic V2 schemas, resolves ID references, filters bullets per manifest specifications, assembles a rendering context, and generates HTML via Jinja2 templates. All operations are designed for bit-identical reproducibility. The system enforces Protocol Zero: no AI attribution artifacts may appear in output.

---

## Repository Layout

```
resume-system/
├── CLAUDE.md                 # Governance and rules (supreme authority)
├── CLAUDE-CONTEXT.md         # This file
├── pyproject.toml            # Python 3.11+ dependencies (Pydantic, Jinja2, PyYAML)
├── uv.lock                   # Lockfile for uv package manager
├── setup.sh                  # One-shot environment bootstrap
│
├── data/                     # Atomic facts (singleton YAML files)
│   ├── profile.yaml          # Contact info (Profile schema)
│   ├── education.yaml        # Academic credentials (Education schema)
│   └── skills.yaml           # Categorized skills (Skills schema)
│
├── content/                  # Narrative bricks (addressable by ID)
│   ├── experience/           # Work history (ExperienceFile schema)
│   │   └── google.yaml
│   ├── projects/             # Portfolio (ProjectFile schema)
│   │   └── projects.yaml
│   └── summaries/            # Empty; reserved for future use
│
├── config/                   # Build manifests (Manifest schema)
│   └── <FirstName>_<LastName>_<Company>_<Role>_Resume.yaml  # Naming convention
│
├── templates/                # READ-ONLY Jinja2 templates
│   └── resume.html.j2        # Main resume template with StrictUndefined
│
├── out/                      # Generated artifacts (gitignored)
│   └── <FirstName>_<LastName>_<Company>_<Role>_Resume.html  # Rendered output
│
├── scripts/                  # Trusted automation layer
│   ├── bootstrap.sh          # Environment setup (uv, venv, pre-commit)
│   ├── lint.sh               # Unified linting (ruff, mypy, yamllint)
│   ├── validate.sh           # Schema validation wrapper
│   ├── protocol-zero.sh      # AI attribution scanner
│   ├── engine.py             # Build CLI entry point
│   ├── validator.py          # Validation CLI entry point
│   └── rvs/                   # Core Python package
│       ├── __init__.py
│       ├── loader.py         # Strict YAML loading with Pydantic
│       ├── models/           # Pydantic V2 data models
│       │   ├── base.py       # BaseResumeModel, ResumeID, TechTag, ResumeDateValue
│       │   ├── profile.py    # Profile, Link
│       │   ├── education.py  # Education, EducationEntry
│       │   ├── skills.py     # Skills
│       │   ├── experience.py # ExperienceFile, ExperienceEntry, Highlight
│       │   ├── project.py    # ProjectFile, ProjectEntry, ProjectHighlight
│       │   └── manifest.py   # Manifest, ManifestEntry
│       ├── engine/           # Build pipeline components
│       │   ├── loader.py     # Manifest loading
│       │   ├── resolver.py   # ID resolution and bullet filtering
│       │   ├── builder.py    # Context assembly
│       │   ├── context.py    # Pydantic-to-dict conversion
│       │   ├── renderer.py   # Jinja2 rendering wrapper
│       │   ├── core.py       # Jinja2 environment factory
│       │   └── exceptions.py # Custom exception hierarchy
│       └── validator/        # Validation subsystem
│           ├── core.py       # Validation context and error accumulation
│           └── registry.py   # Path-to-model mapping
│
├── .claude/                  # Agent configuration
│   ├── settings.local.json   # Local Claude settings
│   └── skills/               # Agent skill definitions
│       ├── jd-analyzer/      # Job description extraction
│       ├── content-librarian/# Content search and verification
│       ├── manifest-composer/# Manifest file generation
│       └── integrity-enforcer/# Validation wrapper
│
├── tests/                    # pytest test suite
│   ├── test_schemas.py       # Model validation tests
│   ├── test_engine.py        # Template engine tests
│   ├── test_validator.py     # Validation pipeline tests
│   ├── test_registry.py      # Path registry tests
│   ├── test_traversal.py     # File traversal tests
│   ├── test_build_reproducibility.py # Determinism tests
│   └── fixtures/             # Test data
│       ├── canonical/        # Valid reference files
│       └── poisoned/         # Invalid files for error testing
│
└── docs/                     # Documentation
    ├── architecture.md       # Data model architecture
    ├── workflows.md          # Developer workflows
    ├── models.md             # Model documentation
    ├── cli.md                # CLI documentation
    └── testing.md            # Testing guide
```

---

## Key Concepts and Terminology

| Term                | Definition                                                                                                                         |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **ResumeID**        | Unique identifier for addressable content. Pattern: `^[a-z0-9][a-z0-9_-]*$`. Examples: `google-staff-swe`, `distcache-adoption`.   |
| **TechTag**         | Normalized technology identifier. Pattern: `^[a-z0-9][a-z0-9._-]*$`. Auto-lowercased. Examples: `python`, `kubernetes`, `node.js`. |
| **ResumeDateValue** | Date wrapper supporting `YYYY-MM` format and `Present` literal. Implements comparison for sorting.                                 |
| **Content Brick**   | A discrete, addressable piece of resume content stored in `content/`. Each brick has a unique ID.                                  |
| **Highlight**       | A bullet point within an experience or project entry. Each highlight has its own ID.                                               |
| **Manifest**        | A YAML file in `config/` that specifies which content IDs to include in a resume build.                                            |
| **ManifestEntry**   | A reference to an experience or project ID, optionally with a list of specific bullet IDs to include.                              |
| **Profile**         | Singleton data file containing contact information and links.                                                                      |
| **Protocol Zero**   | The zero-tolerance policy forbidding any AI attribution markers in output.                                                         |
| **Grounding Rule**  | The closed-world assumption: only data in `data/` and `content/` exists. No hallucination.                                         |

---

## Data Model Overview

### What Lives in `data/`

Singleton YAML files containing atomic, non-repeating facts.

| File             | Schema      | Purpose                                                                                           |
| ---------------- | ----------- | ------------------------------------------------------------------------------------------------- |
| `profile.yaml`   | `Profile`   | Name, email, phone, location, LinkedIn, GitHub, website, additional links                         |
| `education.yaml` | `Education` | List of `EducationEntry` objects with unique IDs                                                  |
| `skills.yaml`    | `Skills`    | Categorized skill lists: languages, frameworks, databases, tools, platforms, methodologies, other |

### What Lives in `content/`

Collection directories containing experience and project YAML files.

| Directory           | Schema           | Purpose                                                 |
| ------------------- | ---------------- | ------------------------------------------------------- |
| `experience/*.yaml` | `ExperienceFile` | Work history entries with highlights (bullets)          |
| `projects/*.yaml`   | `ProjectFile`    | Portfolio entries with highlights                       |
| `summaries/`        | Reserved         | Currently empty; for future professional summary blocks |

### What Lives in `config/`

Build manifest files that orchestrate resume generation.

| File Pattern | Schema     | Purpose                                                                             |
| ------------ | ---------- | ----------------------------------------------------------------------------------- |
| `*.yaml`     | `Manifest` | Specifies template, profile, and ordered lists of experience/project IDs to include |

### How IDs Are Defined and Referenced

1. **Definition**: IDs are defined inline in content YAML files using the `id` field.

   ```yaml
   entries:
     - id: google-staff-swe # Entry-level ID
       highlights:
         - id: google-staff-arch # Bullet-level ID
   ```

2. **Reference**: Manifests reference IDs to select content for inclusion.

   ```yaml
   include_experience:
     - id: google-staff-swe
       bullets:
         - google-staff-arch # Optional: select specific bullets
   ```

3. **Uniqueness**: IDs MUST be globally unique across all content files. The validator enforces this.

4. **Validation**: The validator builds a global ID index and checks all manifest references.

---

## Validation Pipeline (validator.py)

### What It Validates

1. **YAML Syntax**: Files must be valid YAML 1.2.
2. **UTF-8 Encoding**: All files must be valid UTF-8.
3. **Schema Compliance**: Each file is validated against its Pydantic model based on path.
4. **ID Format**: All IDs must match `^[a-z0-9][a-z0-9_-]*$`.
5. **ID Uniqueness**: No duplicate IDs across the entire repository.
6. **Referential Integrity**: All IDs referenced in manifests must exist in content files.
7. **Date Ordering**: `end_date >= start_date` when both are present.
8. **No Extra Fields**: Unknown fields cause validation failure (`extra='forbid'`).

### Path-to-Model Mapping

The `ModelRegistry` in `scripts/rvs/validator/registry.py` maps paths to schemas:

| Path Pattern                | Model            |
| --------------------------- | ---------------- |
| `data/profile.yaml`         | `Profile`        |
| `data/education.yaml`       | `Education`      |
| `data/skills.yaml`          | `Skills`         |
| `content/experience/*.yaml` | `ExperienceFile` |
| `content/projects/*.yaml`   | `ProjectFile`    |
| `config/*.yaml`             | `Manifest`       |

### Exit Codes

| Code | Meaning                                               |
| ---- | ----------------------------------------------------- |
| 0    | All validations passed                                |
| 1    | One or more validation errors detected                |
| 2    | Internal error (missing directory, invalid arguments) |

### Determinism Guarantees

- File discovery is alphabetically sorted for consistent traversal.
- Error reporting order is deterministic.
- Same input always produces same validation output.

---

## Build Pipeline (engine.py)

### Pipeline Stages

1. **prepare-output**: Clean/create `out/` directory.
2. **load-manifest**: Parse and validate manifest YAML against `Manifest` schema.
3. **load-static-data**: Load `profile.yaml`, `skills.yaml`, `education.yaml`.
4. **resolve-content**: Resolve manifest entry IDs to content objects with bullet filtering.
5. **assemble-context**: Merge all data into a single rendering context dict.
6. **render-template**: Render Jinja2 template with assembled context.
7. **write-output**: Atomically write HTML to `out/<manifest-name>.html`.

### Manifest Processing

The manifest specifies:

- `template`: Which template to use (maps to `templates/<template>.html.j2`)
- `profile`: Which profile to use (currently only `default` supported)
- `include_experience`: Ordered list of experience entries with optional bullet filtering
- `include_projects`: Ordered list of project entries with optional bullet filtering

### ID Resolution

The `ContentResolver` class in `scripts/rvs/engine/resolver.py`:

1. Lazily loads all experience and project files on first access.
2. Builds internal indexes mapping IDs to entry objects.
3. Resolves manifest entries to content objects.
4. Filters highlights based on bullet IDs when specified.
5. Preserves manifest-defined ordering.

### Context Mapping

The `assemble_context()` function in `scripts/rvs/engine/builder.py`:

1. Converts Pydantic models to plain dicts via `prepare_context()`.
2. Sorts skills alphabetically within each category.
3. Adds build metadata (timestamp, git hash).
4. Returns immutable context dict for template rendering.

### Template Rendering

The `Renderer` class in `scripts/rvs/engine/renderer.py`:

1. Uses Jinja2 with `StrictUndefined` for fail-fast behavior.
2. Registered filter: `format_date` for date formatting.
3. Autoescape enabled for XSS protection.
4. Template directory restricted to `templates/`.

### Output Writing

The `atomic_write()` function:

1. Writes to a temporary file in the target directory.
2. Atomically renames to final destination.
3. Prevents partial writes on failure.

### Reproducibility Guarantees

With `--reproducible` flag:

- Timestamp fixed to `1970-01-01T00:00:00Z`
- Git hash fixed to `0000000`
- Skills sorted alphabetically
- Manifest order preserved
- Same input produces bit-identical output

---

## Templates and Boundaries

### Where Templates Live

`templates/` directory at project root. Currently contains:

- `resume.html.j2`: Main resume template

### Template Restrictions

1. **READ-ONLY**: Templates MUST NOT be modified without explicit override instruction.
2. **StrictUndefined**: Missing variables cause immediate failure.
3. **No Arbitrary Paths**: Templates cannot load files outside `templates/` directory.
4. **Autoescape On**: HTML in context values is escaped.

### Available Context Variables

| Variable     | Type       | Description                                          |
| ------------ | ---------- | ---------------------------------------------------- |
| `profile`    | dict       | Contact info from `data/profile.yaml`                |
| `skills`     | dict       | Categorized skill lists, sorted alphabetically       |
| `education`  | list[dict] | Education entries                                    |
| `experience` | list[dict] | Resolved experience entries with filtered highlights |
| `projects`   | list[dict] | Resolved project entries with filtered highlights    |
| `build_meta` | dict       | `{timestamp, git_hash}`                              |

### Available Filters

| Filter        | Usage                       | Description                                                                |
| ------------- | --------------------------- | -------------------------------------------------------------------------- |
| `format_date` | `{{ date \| format_date }}` | Formats `YYYY-MM` or date objects to `Mon YYYY`. Passes through `Present`. |

---

## Operational Workflow (End-to-End)

### Initial Setup

```bash
# 1. Clone repository
git clone <url>
cd resume-system

# 2. Run bootstrap (creates venv, installs deps, sets up hooks)
./scripts/bootstrap.sh

# 3. Activate environment
source .venv/bin/activate
```

### Building a Resume

```bash
# Run the build engine with a manifest (naming convention: <FirstName>_<LastName>_<Company>_<Role>_Resume)
python scripts/engine.py --manifest config/Dinesh_Dawonauth_Google_Data_Scientist_Resume.yaml

# For reproducible builds (fixed timestamp/hash)
python scripts/engine.py --manifest config/Dinesh_Dawonauth_Google_Data_Scientist_Resume.yaml --reproducible
```

Output is written to `out/<manifest-name>.html`.

### Validation Before Commit

```bash
# 1. Run schema validation
./scripts/validate.sh

# 2. Run linting
./scripts/lint.sh

# 3. Run Protocol Zero check
./scripts/protocol-zero.sh

# 4. Run tests
.venv/bin/python -m pytest tests/ -v
```

### Adding New Content

1. Edit YAML file in `content/experience/` or `content/projects/`.
2. Ensure all IDs are unique and match the pattern.
3. Run `./scripts/validate.sh` to verify.
4. Update manifest in `config/` to reference new IDs.
5. Rebuild: `python scripts/engine.py --manifest config/<manifest>.yaml`

---

## Claude Code Skill System

Skills are located in `.claude/skills/`. Each skill has a `SKILL.md` defining its purpose and boundaries.

### jd-analyzer

**Purpose**: Extract structured requirements from Job Description text.

**Invocation**: Agent analyzes JD text and outputs JSON matching `.claude/skills/jd-analyzer/assets/schema.json`.

**Output Fields**: `role_title`, `experience_level`, `domain_tags`, `skills.required`, `skills.preferred`, `keywords`.

**Boundaries**:

- MUST NOT match JD to resume content (that is content-librarian's job).
- MUST NOT infer skills not explicitly mentioned.

### content-librarian

**Purpose**: Read-only search against `content/` and `data/` to find grounded content.

**Invocation**: `python3 .claude/skills/content-librarian/scripts/search.py --query "<keywords>"`

**Output**: JSON list of matching IDs with `id`, `file`, `score`, `snippet`.

**Boundaries**:

- MUST NOT modify files.
- MUST report "Zero Results" if content not found.
- MUST NOT invent or hallucinate content.

### manifest-composer

**Purpose**: Generate valid `config/*.yaml` manifest files.

**Invocation**: Agent renders `.claude/skills/manifest-composer/templates/manifest.j2` with provided variables.

**Input Variables**: `target_filename`, `profile`, `experience_ids`, `project_ids`.

**Boundaries**:

- MUST NOT add IDs not provided in input.
- MUST NOT add extra fields to manifest.

### integrity-enforcer

**Purpose**: Execute validation and report results as structured JSON.

**Invocation**: `python3 .claude/skills/integrity-enforcer/scripts/check.py`

**Output**: JSON with `status` ("PASS" or "FAIL") and `errors` list.

**Boundaries**:

- MUST NOT bypass validation.
- MUST report FAIL if scripts/validate.sh returns non-zero.
- Does not auto-fix; only reports.

---

## Determinism and Safety Rules

### Grounding Rule (Anti-Hallucination)

1. The ONLY valid sources of professional data are YAML files in `data/` and `content/`.
2. Claude MUST NOT invent, infer, or embellish content not in source files.
3. If asked to add content that does not exist, Claude MUST refuse and ask for raw data first.

### Protocol Zero Enforcement

1. Forbidden phrases: "Generated by Claude", "AI assisted", "I hope this helps", etc.
2. Forbidden metadata: `Co-authored-by` headers referencing AI.
3. Commit messages MUST be indistinguishable from a senior human engineer.
4. Run `./scripts/protocol-zero.sh` before any commit or output presentation.

### Determinism Requirements

1. Same manifest + content = identical HTML output (with `--reproducible`).
2. File traversal is alphabetically sorted.
3. Skills are sorted alphabetically within categories.
4. Manifest order defines output order.
5. No timestamps or variable data in builds (when reproducible mode enabled).

---

## Common Failure Modes and Debugging

### Symptom: Validation fails with "Duplicate ID"

**Cause**: Same ID used in multiple entries across files.

**Where to look**: Error message specifies both files containing the duplicate.

**Fix**: Rename one of the IDs to be unique. Pattern: `<company>-<role>-<descriptor>`.

### Symptom: "broken_reference" error

**Cause**: Manifest references an ID that does not exist in content files.

**Where to look**: Check `config/<manifest>.yaml` for the referenced ID, then search `content/` for its definition.

**Fix**: Either add the missing content or remove the reference from manifest.

### Symptom: "Schema validation failed" with field path

**Cause**: YAML content violates Pydantic model constraints.

**Where to look**: Error shows field path (e.g., `entries.0.highlights.2.id`).

**Fix**: Check the specific field against model definition in `scripts/rvs/models/`.

### Symptom: RenderingError with "undefined"

**Cause**: Template references a variable not in context.

**Where to look**: Template file at the line indicated. Check if context assembly includes the variable.

**Fix**: Either add the variable to context or fix template to handle missing values.

### Symptom: Build produces different output each run

**Cause**: Non-deterministic elements (timestamp, git hash) in non-reproducible mode.

**Fix**: Use `--reproducible` flag for bit-identical output.

### Symptom: Protocol Zero violation detected

**Cause**: AI attribution markers present in code or content.

**Where to look**: `./scripts/protocol-zero.sh` output shows file and line.

**Fix**: Remove the flagged phrases. Rewrite in human engineer voice.

### Symptom: Bootstrap fails with "uv not found"

**Cause**: uv package manager not installed.

**Fix**: `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## If You Only Read One Section

1. **Source of Truth**: All resume data lives in `data/` and `content/` as YAML.
2. **Entry Point**: `python scripts/engine.py --manifest config/<FirstName>_<LastName>_<Company>_<Role>_Resume.yaml`
3. **Validation**: Run `./scripts/validate.sh` before commits (exit 0 = pass).
4. **No Hallucination**: Never invent content. Use `content-librarian` skill to search.
5. **Skills Required**: Use `jd-analyzer`, `content-librarian`, `manifest-composer`, `integrity-enforcer` for their respective domains. Do not perform these tasks manually.
6. **Protocol Zero**: No AI attribution. Run `./scripts/protocol-zero.sh` before output.
7. **Manifest Controls Output**: Edit `config/*.yaml` to select which IDs appear in resume.

---

## Appendix: Source Map

### Core Scripts

| File                       | Purpose                                  |
| -------------------------- | ---------------------------------------- |
| `scripts/engine.py`        | CLI entry point for build pipeline       |
| `scripts/validator.py`     | CLI entry point for validation           |
| `scripts/bootstrap.sh`     | Environment setup (uv, venv, pre-commit) |
| `scripts/lint.sh`          | Unified linting (ruff, mypy, yamllint)   |
| `scripts/validate.sh`      | Wrapper for validator.py                 |
| `scripts/protocol-zero.sh` | AI attribution scanner                   |

### Data Models

| File                               | Purpose                                             |
| ---------------------------------- | --------------------------------------------------- |
| `scripts/rvs/models/base.py`       | Base model, ResumeID, TechTag, ResumeDateValue      |
| `scripts/rvs/models/profile.py`    | Profile and Link schemas                            |
| `scripts/rvs/models/education.py`  | Education and EducationEntry schemas                |
| `scripts/rvs/models/skills.py`     | Skills schema                                       |
| `scripts/rvs/models/experience.py` | ExperienceFile, ExperienceEntry, Highlight schemas  |
| `scripts/rvs/models/project.py`    | ProjectFile, ProjectEntry, ProjectHighlight schemas |
| `scripts/rvs/models/manifest.py`   | Manifest and ManifestEntry schemas                  |

### Build Engine

| File                               | Purpose                                        |
| ---------------------------------- | ---------------------------------------------- |
| `scripts/rvs/engine/loader.py`     | Manifest loading and validation                |
| `scripts/rvs/engine/resolver.py`   | ID resolution and bullet filtering             |
| `scripts/rvs/engine/builder.py`    | Context assembly                               |
| `scripts/rvs/engine/context.py`    | Pydantic-to-dict conversion                    |
| `scripts/rvs/engine/renderer.py`   | Jinja2 rendering                               |
| `scripts/rvs/engine/core.py`       | Jinja2 environment factory, format_date filter |
| `scripts/rvs/engine/exceptions.py` | Exception classes                              |

### Validation

| File                                | Purpose                                              |
| ----------------------------------- | ---------------------------------------------------- |
| `scripts/rvs/loader.py`             | Strict YAML loading with Pydantic validation         |
| `scripts/rvs/validator/core.py`     | Validation context, file discovery, error formatting |
| `scripts/rvs/validator/registry.py` | Path-to-model mapping                                |

### Skills

| File                                                     | Purpose                                     |
| -------------------------------------------------------- | ------------------------------------------- |
| `.claude/skills/jd-analyzer/SKILL.md`                    | Job description extraction skill definition |
| `.claude/skills/jd-analyzer/assets/schema.json`          | Output schema for JD extraction             |
| `.claude/skills/content-librarian/SKILL.md`              | Content search skill definition             |
| `.claude/skills/content-librarian/scripts/search.py`     | Content search implementation               |
| `.claude/skills/manifest-composer/SKILL.md`              | Manifest generation skill definition        |
| `.claude/skills/manifest-composer/templates/manifest.j2` | Manifest template                           |
| `.claude/skills/integrity-enforcer/SKILL.md`             | Validation wrapper skill definition         |
| `.claude/skills/integrity-enforcer/scripts/check.py`     | Validation wrapper implementation           |

### Data Files

| File                                 | Purpose                                                                         |
| ------------------------------------ | ------------------------------------------------------------------------------- |
| `data/profile.yaml`                  | Contact information (Profile schema)                                            |
| `data/education.yaml`                | Academic credentials (Education schema)                                         |
| `data/skills.yaml`                   | Categorized skill lists (Skills schema)                                         |
| `content/experience/experience.yaml` | Work history (ExperienceFile schema)                                            |
| `content/projects/projects.yaml`     | Portfolio (ProjectFile schema)                                                  |
| `config/*.yaml`                      | Build manifests (naming: `<FirstName>_<LastName>_<Company>_<Role>_Resume.yaml`) |
| `templates/resume.html.j2`           | Resume HTML template                                                            |
