# Resume System

Resume-as-Code monorepo for LLM-orchestrated resume generation.

## Prerequisites

- Python 3.11 or higher
- Git
- [uv](https://github.com/astral-sh/uv) (will be installed by setup script if missing)

## Quick Start

Clone the repository and run the setup script:

```bash
git clone <repository-url>
cd resume-system
./setup.sh
```

The setup script will:
1. Verify or install `uv` package manager
2. Create and configure the Python virtual environment
3. Install all dependencies
4. Set up pre-commit hooks

## Manual Setup

If you prefer manual setup:

```bash
# Install dependencies
uv sync

# Install pre-commit hooks
.venv/bin/pre-commit install
```

## Directory Structure

```
resume-system/
├── .claude/           # Claude Code configuration and rules
├── data/              # Core YAML data (contact, skills, education)
├── content/
│   ├── experience/    # Job experience YAML files
│   ├── projects/      # Project description YAML files
│   └── summaries/     # Professional summary Markdown files
├── templates/         # Jinja2 resume templates
├── config/            # Build and rendering configuration
├── scripts/           # Python utility scripts
├── drafts/            # Temporary working files (git-ignored)
└── out/               # Generated output (git-ignored)
```

## Development

### Activating the Environment

```bash
source .venv/bin/activate
```

### Validating YAML Files

Pre-commit hooks automatically validate YAML files on commit. For manual validation:

```bash
.venv/bin/yamllint data/ content/ config/
```

### Running Pre-commit Manually

```bash
.venv/bin/pre-commit run --all-files
```

## Data Files

All resume content is stored in YAML and Markdown files:

- `data/` - Core data (contact info, skills, education)
- `content/experience/` - Work experience entries
- `content/projects/` - Project descriptions
- `content/summaries/` - Professional summary variations

## Configuration

Build and rendering configuration is stored in `config/`.

## Output

Generated resumes are written to `out/` (git-ignored).

## License

MIT
