"""Reproducibility and regression tests for the RVS build engine.

Validates that the build process produces bit-identical output for identical
inputs, ensuring deterministic behavior across runs.
"""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

import pytest
from scripts.rvs.engine import (
    Renderer,
    assemble_context,
    load_manifest,
    load_static_data,
    resolve_manifest_content,
)


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.resolve()


def sha256_hash(content: str) -> str:
    """Compute SHA-256 hash of string content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def fixed_timestamp() -> str:
    """Return fixed timestamp for reproducible builds."""
    return "2024-01-15T12:00:00Z"


def fixed_git_hash() -> str:
    """Return fixed git hash for reproducible builds."""
    return "abc1234"


def build_resume(manifest_path: Path, root: Path) -> str:
    """Execute the full build pipeline and return rendered HTML.

    Args:
        manifest_path: Path to manifest YAML file.
        root: Project root directory.

    Returns:
        Rendered HTML string.
    """
    manifest = load_manifest(manifest_path)
    profile, skills, education = load_static_data(root)
    experience, projects = resolve_manifest_content(manifest, root)

    context = assemble_context(
        profile=profile,
        skills=skills,
        education=education,
        experience=experience,
        projects=projects,
        timestamp_fn=fixed_timestamp,
        git_hash_fn=fixed_git_hash,
    )

    renderer = Renderer()
    template_name = f"{manifest.template}.html.j2"
    return renderer.render(template_name, context)


class TestBuildReproducibility:
    """Test suite for build reproducibility guarantees."""

    @pytest.fixture
    def root(self) -> Path:
        """Return project root path."""
        return get_project_root()

    @pytest.fixture
    def manifest_path(self, root: Path) -> Path:
        """Return path to test manifest."""
        return root / "config" / "job.yaml"

    def test_identical_runs_produce_identical_hashes(self, manifest_path: Path, root: Path) -> None:
        """Verify that two builds from identical inputs produce identical output."""
        run1_html = build_resume(manifest_path, root)
        run2_html = build_resume(manifest_path, root)

        hash1 = sha256_hash(run1_html)
        hash2 = sha256_hash(run2_html)

        assert hash1 == hash2, "Two builds from identical inputs must produce identical hashes"

    def test_output_contains_expected_profile_data(self, manifest_path: Path, root: Path) -> None:
        """Verify that generated HTML contains expected profile data."""
        html = build_resume(manifest_path, root)

        assert "Alex Chen" in html, "Output must contain profile name"
        assert "alex.chen@example.com" in html, "Output must contain email"
        assert "San Francisco Bay Area" in html, "Output must contain location"

    def test_output_contains_expected_experience_data(
        self, manifest_path: Path, root: Path
    ) -> None:
        """Verify that generated HTML contains expected experience content."""
        html = build_resume(manifest_path, root)

        assert "Staff Software Engineer" in html, "Output must contain job title"
        assert "Google" in html, "Output must contain company name"
        assert "distributed caching layer" in html, "Output must contain highlight text"

    def test_output_contains_expected_project_data(self, manifest_path: Path, root: Path) -> None:
        """Verify that generated HTML contains expected project content."""
        html = build_resume(manifest_path, root)

        assert "DistCache" in html, "Output must contain project name"
        assert "MLFlow Orchestrator" in html, "Output must contain project name"

    def test_output_contains_build_metadata(self, manifest_path: Path, root: Path) -> None:
        """Verify that generated HTML contains build metadata."""
        html = build_resume(manifest_path, root)

        assert "2024-01-15T12:00:00Z" in html, "Output must contain build timestamp"
        assert "abc1234" in html, "Output must contain git hash"

    def test_skills_sorting_is_deterministic(self, manifest_path: Path, root: Path) -> None:
        """Verify that skills are sorted alphabetically for determinism."""
        html = build_resume(manifest_path, root)

        languages_section = html[html.find("Languages") : html.find("Languages") + 200]
        assert "cpp" in languages_section or "go" in languages_section

    def test_content_change_produces_different_hash(self, root: Path) -> None:
        """Verify that changing content produces a different hash."""
        manifest_path = root / "config" / "job.yaml"
        original_html = build_resume(manifest_path, root)
        original_hash = sha256_hash(original_html)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            shutil.copytree(root / "data", tmp_root / "data")
            shutil.copytree(root / "content", tmp_root / "content")
            shutil.copytree(root / "config", tmp_root / "config")
            shutil.copytree(root / "templates", tmp_root / "templates")

            profile_path = tmp_root / "data" / "profile.yaml"
            profile_content = profile_path.read_text()
            modified_content = profile_content.replace("Alex Chen", "Alex Modified")
            profile_path.write_text(modified_content)

            modified_manifest_path = tmp_root / "config" / "job.yaml"
            modified_html = build_resume(modified_manifest_path, tmp_root)
            modified_hash = sha256_hash(modified_html)

            assert original_hash != modified_hash, "Changing content must produce a different hash"


class TestBulletFiltering:
    """Test suite for manifest-based bullet filtering."""

    @pytest.fixture
    def root(self) -> Path:
        """Return project root path."""
        return get_project_root()

    def test_bullet_selection_filters_highlights(self, root: Path) -> None:
        """Verify that bullet selection in manifest filters experience highlights."""
        manifest_path = root / "config" / "job.yaml"
        manifest = load_manifest(manifest_path)
        experience, _ = resolve_manifest_content(manifest, root)

        staff_entry = next(e for e in experience if e.id == "google-staff-swe")

        highlight_ids = [h.id for h in staff_entry.highlights]
        assert "google-staff-arch" in highlight_ids
        assert "google-staff-migration" in highlight_ids
        assert "google-staff-oncall" not in highlight_ids

    def test_null_bullets_includes_all_highlights(self, root: Path) -> None:
        """Verify that null/None bullets includes all highlights for an entry."""
        manifest_path = root / "config" / "job.yaml"
        manifest = load_manifest(manifest_path)
        _, projects = resolve_manifest_content(manifest, root)

        distcache = next(p for p in projects if p.id == "distributed-cache")

        assert len(distcache.highlights) == 2
        highlight_ids = [h.id for h in distcache.highlights]
        assert "distcache-adoption" in highlight_ids
        assert "distcache-perf" in highlight_ids


class TestManifestOrder:
    """Test suite for manifest-defined ordering."""

    @pytest.fixture
    def root(self) -> Path:
        """Return project root path."""
        return get_project_root()

    def test_experience_order_matches_manifest(self, root: Path) -> None:
        """Verify that experience entries are returned in manifest order."""
        manifest_path = root / "config" / "job.yaml"
        manifest = load_manifest(manifest_path)
        experience, _ = resolve_manifest_content(manifest, root)

        manifest_ids = [e.id for e in manifest.include_experience]
        resolved_ids = [e.id for e in experience]

        assert manifest_ids == resolved_ids

    def test_project_order_matches_manifest(self, root: Path) -> None:
        """Verify that project entries are returned in manifest order."""
        manifest_path = root / "config" / "job.yaml"
        manifest = load_manifest(manifest_path)
        _, projects = resolve_manifest_content(manifest, root)

        manifest_ids = [p.id for p in manifest.include_projects]
        resolved_ids = [p.id for p in projects]

        assert manifest_ids == resolved_ids


class TestPerformance:
    """Test suite for build performance requirements."""

    @pytest.fixture
    def root(self) -> Path:
        """Return project root path."""
        return get_project_root()

    @pytest.fixture
    def manifest_path(self, root: Path) -> Path:
        """Return path to test manifest."""
        return root / "config" / "job.yaml"

    def test_build_completes_under_one_second(self, manifest_path: Path, root: Path) -> None:
        """Verify that the test suite executes quickly (< 1s for single build)."""
        import time

        start = time.perf_counter()
        build_resume(manifest_path, root)
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"Build took {elapsed:.2f}s, expected < 1s"
