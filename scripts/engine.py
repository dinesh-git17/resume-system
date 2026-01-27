#!/usr/bin/env python3
"""RVS Build Engine CLI.

Command-line interface for building resume artifacts from manifest
configurations. Orchestrates the load-resolve-assemble-render-write pipeline.

Usage:
    python scripts/engine.py --manifest config/Dinesh_Dawonauth_Google_Data_Scientist_Resume.yaml
    python scripts/engine.py --manifest config/Dinesh_Dawonauth_Google_Data_Scientist_Resume.yaml --reproducible

Manifest naming convention: <FirstName>_<LastName>_<Company>_<Role>_Resume.yaml
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from scripts.rvs.engine.builder import BuildError, assemble_context, load_static_data
from scripts.rvs.engine.exceptions import RenderingError, TemplateNotFoundError
from scripts.rvs.engine.loader import ManifestValidationError, load_manifest
from scripts.rvs.engine.renderer import Renderer
from scripts.rvs.engine.resolver import ResolutionError, resolve_manifest_content

REPRODUCIBLE_TIMESTAMP = "1970-01-01T00:00:00Z"
REPRODUCIBLE_GIT_HASH = "0000000"


def _get_project_root() -> Path:
    """Determine the project root directory."""
    return Path(__file__).parent.parent.resolve()


class Timer:
    """Context manager for timing code blocks."""

    def __init__(self, step_name: str):
        self.step_name = step_name
        self.start_time: float = 0
        self.elapsed_ms: float = 0

    def __enter__(self) -> Timer:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000

    def log(self) -> None:
        """Print timing information to stdout."""
        print(f"  [{self.step_name}] {self.elapsed_ms:.1f}ms")


def prepare_output_directory(out_dir: Path) -> None:
    """Create or clean the output directory.

    Args:
        out_dir: Path to the output directory.
    """
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def atomic_write(content: str, target_path: Path) -> None:
    """Write content to a file atomically using temp file and rename.

    Args:
        content: String content to write.
        target_path: Final destination path for the file.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        suffix=".tmp",
        prefix=target_path.stem + "_",
        dir=target_path.parent,
    )
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(temp_path).rename(target_path)
    except Exception:
        Path(temp_path).unlink(missing_ok=True)
        raise


def run_build(
    manifest_path: Path,
    *,
    reproducible: bool = False,
) -> int:
    """Execute the build pipeline.

    Args:
        manifest_path: Path to the manifest YAML file.
        reproducible: If True, use fixed timestamp and git hash for deterministic output.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    root = _get_project_root()
    out_dir = root / "out"

    manifest_name = manifest_path.stem
    output_file = out_dir / f"{manifest_name}.html"

    print(f"Building resume from: {manifest_path}")
    print(f"Output: {output_file}")
    if reproducible:
        print("Mode: reproducible (fixed timestamp and git hash)")
    print()

    total_start = time.perf_counter()

    timestamp_fn: Callable[[], str] | None = None
    git_hash_fn: Callable[[], str] | None = None
    if reproducible:
        timestamp_fn = lambda: REPRODUCIBLE_TIMESTAMP  # noqa: E731
        git_hash_fn = lambda: REPRODUCIBLE_GIT_HASH  # noqa: E731

    try:
        with Timer("prepare-output") as t:
            prepare_output_directory(out_dir)
        t.log()

        with Timer("load-manifest") as t:
            manifest = load_manifest(manifest_path)
        t.log()

        with Timer("load-static-data") as t:
            profile, skills, education = load_static_data(root)
        t.log()

        with Timer("resolve-content") as t:
            experience, projects = resolve_manifest_content(manifest, root)
        t.log()

        with Timer("assemble-context") as t:
            context = assemble_context(
                profile=profile,
                skills=skills,
                education=education,
                experience=experience,
                projects=projects,
                timestamp_fn=timestamp_fn,
                git_hash_fn=git_hash_fn,
            )
        t.log()

        with Timer("render-template") as t:
            renderer = Renderer()
            template_name = f"{manifest.template}.html.j2"
            html_output = renderer.render(template_name, context)
        t.log()

        with Timer("write-output") as t:
            atomic_write(html_output, output_file)
        t.log()

        total_ms = (time.perf_counter() - total_start) * 1000
        print()
        print(f"Build complete: {output_file}")
        print(f"Total time: {total_ms:.1f}ms")
        return 0

    except ManifestValidationError as e:
        print(f"ERROR: Manifest validation failed: {e.message}", file=sys.stderr)
        return 1

    except ResolutionError as e:
        print(f"ERROR: Content resolution failed: {e.message}", file=sys.stderr)
        return 1

    except BuildError as e:
        print(f"ERROR: Build failed: {e.message}", file=sys.stderr)
        return 1

    except TemplateNotFoundError as e:
        print(f"ERROR: Template not found: '{e.template_name}'", file=sys.stderr)
        return 1

    except RenderingError as e:
        print(f"ERROR: Rendering failed: {e.message}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"ERROR: Unexpected failure: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """CLI entry point.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="Build resume artifact from manifest configuration.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to manifest YAML file (e.g., config/Dinesh_Dawonauth_Google_Data_Scientist_Resume.yaml)",
    )
    parser.add_argument(
        "--reproducible",
        action="store_true",
        help="Use fixed timestamp and git hash for bit-identical reproducible builds",
    )

    args = parser.parse_args()

    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = _get_project_root() / manifest_path

    return run_build(manifest_path, reproducible=args.reproducible)


if __name__ == "__main__":
    sys.exit(main())
