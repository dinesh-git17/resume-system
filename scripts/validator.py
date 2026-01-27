#!/usr/bin/env python3
"""RVS Validation Engine.

Deterministic validation of YAML data files against Pydantic schemas.
Enforces schema compliance, ID uniqueness, and referential integrity.

Exit Codes:
    0: All validations passed
    1: One or more validation errors detected
    2: Internal error (e.g., invalid arguments, missing directories)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.rvs.loader import YAMLLoadError, YAMLValidationError, load_yaml_strict
from scripts.rvs.models import (
    Education,
    ExperienceFile,
    Manifest,
    ProjectFile,
)
from scripts.rvs.validator.core import (
    ValidationContext,
    discover_yaml_files,
    format_errors,
    format_success,
    is_tty,
    validate_yaml_file,
)


def collect_ids_from_experience(
    exp_file: ExperienceFile,
    file_path: Path,
    ctx: ValidationContext,
) -> None:
    """Extract all IDs from an experience file and register in the global index.

    Args:
        exp_file: Parsed experience file.
        file_path: Source file path for error reporting.
        ctx: Validation context with ID index.
    """
    for entry in exp_file.entries:
        _register_id(entry.id, file_path, ctx)
        for highlight in entry.highlights:
            _register_id(highlight.id, file_path, ctx)


def collect_ids_from_projects(
    proj_file: ProjectFile,
    file_path: Path,
    ctx: ValidationContext,
) -> None:
    """Extract all IDs from a project file and register in the global index.

    Args:
        proj_file: Parsed project file.
        file_path: Source file path for error reporting.
        ctx: Validation context with ID index.
    """
    for entry in proj_file.entries:
        _register_id(entry.id, file_path, ctx)
        for highlight in entry.highlights:
            _register_id(highlight.id, file_path, ctx)


def collect_ids_from_education(
    edu: Education,
    file_path: Path,
    ctx: ValidationContext,
) -> None:
    """Extract all IDs from an education file and register in the global index.

    Args:
        edu: Parsed education data.
        file_path: Source file path for error reporting.
        ctx: Validation context with ID index.
    """
    for entry in edu.entries:
        _register_id(entry.id, file_path, ctx)


def _register_id(
    id_value: str,
    file_path: Path,
    ctx: ValidationContext,
) -> None:
    """Register an ID in the global index, detecting duplicates.

    Args:
        id_value: The ID string to register.
        file_path: File where this ID was found.
        ctx: Validation context with ID index.
    """
    if id_value in ctx.id_index:
        existing_file = ctx.id_index[id_value]
        ctx.add_error(
            file_path=file_path,
            error_type="duplicate_id",
            message=(f"Duplicate ID '{id_value}' found in file {existing_file} and {file_path}"),
        )
    else:
        ctx.id_index[id_value] = file_path


def build_global_id_index(root: Path, ctx: ValidationContext) -> None:
    """Build the global ID index from all content files.

    Args:
        root: Root directory of the project.
        ctx: Validation context to populate with IDs.
    """
    data_dir = root / "data"
    content_dir = root / "content"

    if data_dir.exists():
        edu_path = data_dir / "education.yaml"
        if edu_path.exists():
            try:
                edu = load_yaml_strict(edu_path, Education)
                collect_ids_from_education(edu, edu_path, ctx)
            except (YAMLLoadError, YAMLValidationError):
                pass

    if content_dir.exists():
        exp_dir = content_dir / "experience"
        if exp_dir.exists():
            for yaml_file in sorted(exp_dir.glob("*.yaml")):
                try:
                    exp = load_yaml_strict(yaml_file, ExperienceFile)
                    collect_ids_from_experience(exp, yaml_file, ctx)
                except (YAMLLoadError, YAMLValidationError):
                    pass

        proj_dir = content_dir / "projects"
        if proj_dir.exists():
            for yaml_file in sorted(proj_dir.glob("*.yaml")):
                try:
                    proj = load_yaml_strict(yaml_file, ProjectFile)
                    collect_ids_from_projects(proj, yaml_file, ctx)
                except (YAMLLoadError, YAMLValidationError):
                    pass


def validate_manifest_references(
    manifest: Manifest,
    manifest_path: Path,
    root: Path,
    ctx: ValidationContext,
) -> None:
    """Validate that all IDs referenced in a manifest exist in the global index.

    Args:
        manifest: Parsed manifest object.
        manifest_path: Path to the manifest file.
        root: Root directory of the project.
        ctx: Validation context with ID index.
    """
    profile_path = root / "data" / f"{manifest.profile}.yaml"
    if manifest.profile == "default":
        profile_path = root / "data" / "profile.yaml"

    if not profile_path.exists():
        ctx.add_error(
            file_path=manifest_path,
            error_type="broken_reference",
            message=(
                f"Manifest references unknown profile '{manifest.profile}' "
                f"(expected file: {profile_path})"
            ),
        )

    for entry in manifest.include_experience:
        if entry.id not in ctx.id_index:
            ctx.add_error(
                file_path=manifest_path,
                error_type="broken_reference",
                message=f"Manifest references unknown experience ID '{entry.id}'",
            )
        if entry.bullets:
            for bullet_id in entry.bullets:
                if bullet_id not in ctx.id_index:
                    ctx.add_error(
                        file_path=manifest_path,
                        error_type="broken_reference",
                        message=f"Manifest references unknown bullet ID '{bullet_id}'",
                    )

    for entry in manifest.include_projects:
        if entry.id not in ctx.id_index:
            ctx.add_error(
                file_path=manifest_path,
                error_type="broken_reference",
                message=f"Manifest references unknown project ID '{entry.id}'",
            )
        if entry.bullets:
            for bullet_id in entry.bullets:
                if bullet_id not in ctx.id_index:
                    ctx.add_error(
                        file_path=manifest_path,
                        error_type="broken_reference",
                        message=f"Manifest references unknown bullet ID '{bullet_id}'",
                    )


def validate_manifests(root: Path, ctx: ValidationContext) -> None:
    """Validate all manifests in config/ directory.

    Args:
        root: Root directory of the project.
        ctx: Validation context with ID index populated.
    """
    config_dir = root / "config"
    if not config_dir.exists():
        return

    for manifest_path in sorted(config_dir.glob("*.yaml")):
        try:
            manifest = load_yaml_strict(manifest_path, Manifest)
            validate_manifest_references(manifest, manifest_path, root, ctx)
        except (YAMLLoadError, YAMLValidationError):
            pass


def run_validation(target: Path) -> int:
    """Execute full validation pipeline.

    Args:
        target: Root directory to validate.

    Returns:
        Exit code (0 for success, 1 for validation errors, 2 for internal errors).
    """
    colorize = is_tty()
    ctx = ValidationContext()

    if not target.exists():
        red = "\033[31m" if colorize else ""
        reset = "\033[0m" if colorize else ""
        print(
            f"{red}[FAIL]{reset} Target directory does not exist: {target}",
            file=sys.stderr,
        )
        return 2

    if not target.is_dir():
        red = "\033[31m" if colorize else ""
        reset = "\033[0m" if colorize else ""
        print(
            f"{red}[FAIL]{reset} Target must be a directory: {target}",
            file=sys.stderr,
        )
        return 2

    yaml_files = discover_yaml_files(target)

    for yaml_file in yaml_files:
        validate_yaml_file(yaml_file, target, ctx)

    build_global_id_index(target, ctx)

    validate_manifests(target, ctx)

    if ctx.has_errors:
        print(format_errors(ctx, colorize=colorize), file=sys.stderr)
        return 1

    print(format_success(ctx, colorize=colorize))
    return 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate RVS YAML files against Pydantic schemas.",
        epilog="Exit codes: 0=success, 1=validation errors, 2=internal error",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd(),
        help="Root directory to validate (default: current directory)",
    )

    args = parser.parse_args()
    return run_validation(args.target)


if __name__ == "__main__":
    sys.exit(main())
