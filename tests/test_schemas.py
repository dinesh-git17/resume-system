"""Schema validation tests for RVS models.

Tests cover custom types, model validation, and canonical YAML file parsing.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError
from scripts.rvs.loader import (
    YAMLLoadError,
    YAMLValidationError,
    load_yaml_list_strict,
    load_yaml_strict,
)
from scripts.rvs.models import (
    Education,
    EducationEntry,
    ExperienceEntry,
    ExperienceFile,
    Highlight,
    Profile,
    ProjectEntry,
    ProjectFile,
    ProjectHighlight,
    ResumeDateValue,
    Skills,
)
from scripts.rvs.models.base import (
    _parse_resume_date,
    _validate_resume_id,
    _validate_tech_tag,
)

# =============================================================================
# ResumeID Tests
# =============================================================================


class TestResumeID:
    """Tests for ResumeID validation."""

    def test_valid_lowercase_alphanumeric(self) -> None:
        """Accept lowercase alphanumeric IDs."""
        assert _validate_resume_id("google") == "google"
        assert _validate_resume_id("experience1") == "experience1"

    def test_valid_with_hyphens(self) -> None:
        """Accept IDs with hyphens."""
        assert _validate_resume_id("google-senior-swe") == "google-senior-swe"

    def test_valid_with_underscores(self) -> None:
        """Accept IDs with underscores."""
        assert _validate_resume_id("google_senior_swe") == "google_senior_swe"

    def test_valid_mixed_separators(self) -> None:
        """Accept IDs with mixed hyphens and underscores."""
        assert _validate_resume_id("exp-01_highlight") == "exp-01_highlight"

    def test_reject_uppercase(self) -> None:
        """Reject IDs with uppercase letters."""
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            _validate_resume_id("Google")

    def test_reject_spaces(self) -> None:
        """Reject IDs with spaces."""
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            _validate_resume_id("google swe")

    def test_reject_special_characters(self) -> None:
        """Reject IDs with special characters."""
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            _validate_resume_id("google@swe")

    def test_reject_empty(self) -> None:
        """Reject empty IDs."""
        with pytest.raises(ValueError, match="cannot be empty"):
            _validate_resume_id("")

    def test_reject_starting_with_hyphen(self) -> None:
        """Reject IDs starting with hyphen."""
        with pytest.raises(ValueError, match="starting with alphanumeric"):
            _validate_resume_id("-google")

    def test_reject_starting_with_underscore(self) -> None:
        """Reject IDs starting with underscore."""
        with pytest.raises(ValueError, match="starting with alphanumeric"):
            _validate_resume_id("_google")


# =============================================================================
# TechTag Tests
# =============================================================================


class TestTechTag:
    """Tests for TechTag validation."""

    def test_valid_lowercase(self) -> None:
        """Accept lowercase tags."""
        assert _validate_tech_tag("python") == "python"
        assert _validate_tech_tag("go") == "go"

    def test_valid_with_hyphens(self) -> None:
        """Accept tags with hyphens."""
        assert _validate_tech_tag("react-native") == "react-native"

    def test_valid_with_dots(self) -> None:
        """Accept tags with dots."""
        assert _validate_tech_tag("node.js") == "node.js"
        assert _validate_tech_tag("asp.net") == "asp.net"

    def test_valid_with_numbers(self) -> None:
        """Accept tags with numbers."""
        assert _validate_tech_tag("python3") == "python3"
        assert _validate_tech_tag("vue3") == "vue3"

    def test_auto_lowercase(self) -> None:
        """Auto-convert uppercase to lowercase."""
        assert _validate_tech_tag("Python") == "python"
        assert _validate_tech_tag("REACT") == "react"

    def test_strip_whitespace(self) -> None:
        """Strip leading/trailing whitespace."""
        assert _validate_tech_tag("  python  ") == "python"

    def test_reject_empty(self) -> None:
        """Reject empty tags."""
        with pytest.raises(ValueError, match="cannot be empty"):
            _validate_tech_tag("")

    def test_reject_spaces(self) -> None:
        """Reject tags with internal spaces."""
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            _validate_tech_tag("react native")

    def test_reject_starting_with_dot(self) -> None:
        """Reject tags starting with dot."""
        with pytest.raises(ValueError, match="starting with alphanumeric"):
            _validate_tech_tag(".net")


# =============================================================================
# ResumeDate Tests
# =============================================================================


class TestResumeDate:
    """Tests for ResumeDate validation and comparison."""

    def test_parse_valid_date(self) -> None:
        """Parse YYYY-MM format to date object."""
        result = _parse_resume_date("2024-01")
        assert isinstance(result, ResumeDateValue)
        assert result.value == date(2024, 1, 1)

    def test_parse_present_literal(self) -> None:
        """Accept 'Present' literal."""
        result = _parse_resume_date("Present")
        assert result.is_present
        assert result.value == "Present"

    def test_parse_date_object(self) -> None:
        """Accept date object directly."""
        d = date(2024, 6, 15)
        result = _parse_resume_date(d)
        assert result.value == d

    def test_reject_invalid_format(self) -> None:
        """Reject invalid date formats."""
        with pytest.raises(ValueError, match="YYYY-MM"):
            _parse_resume_date("2024/01")
        with pytest.raises(ValueError, match="YYYY-MM"):
            _parse_resume_date("24-01")
        with pytest.raises(ValueError, match="YYYY-MM"):
            _parse_resume_date("2024-1")

    def test_reject_invalid_month(self) -> None:
        """Reject invalid month values."""
        with pytest.raises(ValueError, match="YYYY-MM"):
            _parse_resume_date("2024-13")
        with pytest.raises(ValueError, match="YYYY-MM"):
            _parse_resume_date("2024-00")

    def test_comparison_date_vs_date(self) -> None:
        """Compare two concrete dates."""
        d1 = _parse_resume_date("2020-01")
        d2 = _parse_resume_date("2021-06")
        assert d1 < d2
        assert d2 > d1
        assert d1 != d2

    def test_comparison_date_vs_present(self) -> None:
        """Present is always greater than concrete dates."""
        d = _parse_resume_date("2024-12")
        p = _parse_resume_date("Present")
        assert d < p
        assert p > d
        assert not p < d

    def test_comparison_present_vs_present(self) -> None:
        """Two Present values are equal."""
        p1 = _parse_resume_date("Present")
        p2 = _parse_resume_date("Present")
        assert p1 == p2
        assert not p1 < p2
        assert not p1 > p2

    def test_str_representation(self) -> None:
        """String representation matches expected format."""
        d = _parse_resume_date("2024-06")
        assert str(d) == "2024-06"
        p = _parse_resume_date("Present")
        assert str(p) == "Present"


# =============================================================================
# Profile Model Tests
# =============================================================================


class TestProfileModel:
    """Tests for Profile model validation."""

    def test_valid_full_profile(self) -> None:
        """Accept complete profile data."""
        profile = Profile(
            name="Alex Chen",
            email="alex@example.com",
            phone="+1-555-123-4567",
            location="San Francisco, CA",
            linkedin="https://linkedin.com/in/alexchen",
            github="https://github.com/alexchen",
            website="https://alexchen.dev",
        )
        assert profile.name == "Alex Chen"
        assert str(profile.email) == "alex@example.com"

    def test_valid_minimal_profile(self) -> None:
        """Accept minimal required fields only."""
        profile = Profile(name="Alex Chen", email="alex@example.com")
        assert profile.phone is None
        assert profile.location is None

    def test_reject_invalid_email(self) -> None:
        """Reject invalid email format."""
        with pytest.raises(ValidationError, match="email"):
            Profile(name="Alex Chen", email="not-an-email")

    def test_reject_invalid_url(self) -> None:
        """Reject invalid URL format."""
        with pytest.raises(ValidationError):
            Profile(
                name="Alex Chen",
                email="alex@example.com",
                linkedin="not-a-url",
            )

    def test_reject_extra_fields(self) -> None:
        """Reject extra fields not in schema."""
        with pytest.raises(ValidationError, match="Extra inputs"):
            Profile(
                name="Alex Chen",
                email="alex@example.com",
                unknown_field="value",  # type: ignore[call-arg]
            )


# =============================================================================
# Education Model Tests
# =============================================================================


class TestEducationModel:
    """Tests for Education model validation."""

    def test_valid_education_entry(self) -> None:
        """Accept valid education entry."""
        entry = EducationEntry(
            id="stanford-mscs",
            institution="Stanford University",
            degree="Master of Science",
            field_of_study="Computer Science",
            location="Stanford, CA",
            start_date="2015-09",
            end_date="2017-06",
            gpa="3.92/4.0",
        )
        assert entry.id == "stanford-mscs"
        assert entry.institution == "Stanford University"

    def test_valid_education_with_present(self) -> None:
        """Accept education entry with Present end date."""
        entry = EducationEntry(
            id="current-phd",
            institution="MIT",
            degree="Doctor of Philosophy",
            start_date="2022-09",
            end_date="Present",
        )
        assert entry.end_date is not None
        assert entry.end_date.is_present

    def test_valid_education_no_end_date(self) -> None:
        """Accept education entry without end date."""
        entry = EducationEntry(
            id="current-study",
            institution="MIT",
            degree="PhD",
            start_date="2022-09",
        )
        assert entry.end_date is None

    def test_reject_end_before_start(self) -> None:
        """Reject end date before start date."""
        with pytest.raises(ValidationError, match="cannot be before"):
            EducationEntry(
                id="invalid-dates",
                institution="University",
                degree="BS",
                start_date="2020-01",
                end_date="2019-01",
            )

    def test_education_unique_ids(self) -> None:
        """Reject duplicate education entry IDs."""
        with pytest.raises(ValidationError, match="Duplicate"):
            Education(
                entries=[
                    EducationEntry(
                        id="same-id",
                        institution="Uni A",
                        degree="BS",
                        start_date="2015-09",
                    ),
                    EducationEntry(
                        id="same-id",
                        institution="Uni B",
                        degree="MS",
                        start_date="2019-09",
                    ),
                ]
            )


# =============================================================================
# Skills Model Tests
# =============================================================================


class TestSkillsModel:
    """Tests for Skills model validation."""

    def test_valid_skills(self) -> None:
        """Accept valid skills data."""
        skills = Skills(
            languages=["python", "go", "java"],
            frameworks=["django", "react"],
            tools=["docker", "kubernetes"],
        )
        assert "python" in skills.languages
        assert len(skills.get_all_skills()) == 7

    def test_empty_categories_allowed(self) -> None:
        """Allow empty skill categories."""
        skills = Skills(languages=["python"])
        assert skills.frameworks == []
        assert skills.tools == []

    def test_reject_duplicate_in_category(self) -> None:
        """Reject duplicate items within a category."""
        with pytest.raises(ValidationError, match="Duplicate"):
            Skills(languages=["python", "python"])

    def test_reject_case_insensitive_duplicate(self) -> None:
        """Reject duplicates with different casing."""
        with pytest.raises(ValidationError, match="Duplicate"):
            Skills(languages=["Python", "python"])

    def test_get_skills_by_category(self) -> None:
        """Return skills organized by category."""
        skills = Skills(
            languages=["python"],
            frameworks=["django"],
        )
        by_cat = skills.get_skills_by_category()
        assert by_cat["languages"] == ["python"]
        assert by_cat["frameworks"] == ["django"]


# =============================================================================
# Experience Model Tests
# =============================================================================


class TestExperienceModel:
    """Tests for Experience model validation."""

    def test_valid_highlight(self) -> None:
        """Accept valid highlight."""
        h = Highlight(
            id="exp-01",
            text="Built distributed system serving 1M QPS.",
            tags=["go", "grpc"],
        )
        assert h.id == "exp-01"
        assert "go" in h.tags

    def test_highlight_requires_id(self) -> None:
        """Highlight must have ID."""
        with pytest.raises(ValidationError):
            Highlight(text="Some achievement")  # type: ignore[call-arg]

    def test_valid_experience_entry(self) -> None:
        """Accept valid experience entry."""
        entry = ExperienceEntry(
            id="google-swe",
            company="Google",
            role="Software Engineer",
            location="Mountain View, CA",
            start_date="2020-01",
            end_date="Present",
            highlights=[
                Highlight(id="h1", text="Designed distributed system."),
            ],
        )
        assert entry.company == "Google"
        assert entry.end_date is not None
        assert entry.end_date.is_present

    def test_reject_duplicate_highlight_ids(self) -> None:
        """Reject duplicate highlight IDs within entry."""
        with pytest.raises(ValidationError, match="Duplicate highlight"):
            ExperienceEntry(
                id="exp-1",
                company="Company",
                role="Role",
                location="Location",
                start_date="2020-01",
                highlights=[
                    Highlight(id="same-id", text="First."),
                    Highlight(id="same-id", text="Second."),
                ],
            )

    def test_experience_file_unique_entry_ids(self) -> None:
        """Reject duplicate entry IDs within file."""
        with pytest.raises(ValidationError, match="Duplicate experience"):
            ExperienceFile(
                entries=[
                    ExperienceEntry(
                        id="same-id",
                        company="A",
                        role="R",
                        location="L",
                        start_date="2020-01",
                        highlights=[Highlight(id="h1", text="T")],
                    ),
                    ExperienceEntry(
                        id="same-id",
                        company="B",
                        role="R",
                        location="L",
                        start_date="2021-01",
                        highlights=[Highlight(id="h2", text="T")],
                    ),
                ]
            )


# =============================================================================
# Project Model Tests
# =============================================================================


class TestProjectModel:
    """Tests for Project model validation."""

    def test_valid_project(self) -> None:
        """Accept valid project entry."""
        project = ProjectEntry(
            id="distcache",
            name="DistCache",
            description="Distributed caching library.",
            technologies=["go", "grpc"],
        )
        assert project.id == "distcache"

    def test_valid_project_with_highlights(self) -> None:
        """Accept project with highlights."""
        project = ProjectEntry(
            id="proj-1",
            name="Project",
            description="Description.",
            highlights=[
                ProjectHighlight(id="ph1", text="Achievement 1."),
                ProjectHighlight(id="ph2", text="Achievement 2."),
            ],
        )
        assert len(project.highlights) == 2

    def test_reject_duplicate_project_highlight_ids(self) -> None:
        """Reject duplicate highlight IDs within project."""
        with pytest.raises(ValidationError, match="Duplicate highlight"):
            ProjectEntry(
                id="proj",
                name="Project",
                description="Desc.",
                highlights=[
                    ProjectHighlight(id="same", text="A."),
                    ProjectHighlight(id="same", text="B."),
                ],
            )


# =============================================================================
# YAML Loader Tests
# =============================================================================


class TestYAMLLoader:
    """Tests for strict YAML loader."""

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

    def test_file_not_found(self) -> None:
        """Raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_yaml_strict(Path("/nonexistent/file.yaml"), Profile)

    def test_non_utf8_file(self, tmp_path: Path) -> None:
        """Raise YAMLLoadError for non-UTF-8 file."""
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_bytes(b"\xff\xfe")

        with pytest.raises(YAMLLoadError, match="UTF-8"):
            load_yaml_strict(yaml_file, Profile)

    def test_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """Raise YAMLLoadError for invalid YAML syntax."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("key: [unclosed bracket", encoding="utf-8")

        with pytest.raises(YAMLLoadError, match="YAML syntax"):
            load_yaml_strict(yaml_file, Profile)

    def test_empty_yaml(self, tmp_path: Path) -> None:
        """Raise YAMLLoadError for empty YAML file."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("", encoding="utf-8")

        with pytest.raises(YAMLLoadError, match="empty"):
            load_yaml_strict(yaml_file, Profile)

    def test_validation_error(self, tmp_path: Path) -> None:
        """Raise YAMLValidationError for schema violations."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("name: X\nemail: not-an-email\n", encoding="utf-8")

        with pytest.raises(YAMLValidationError, match="Validation failed"):
            load_yaml_strict(yaml_file, Profile)

    def test_non_dict_root(self, tmp_path: Path) -> None:
        """Raise YAMLLoadError for non-dict YAML root."""
        yaml_file = tmp_path / "list.yaml"
        yaml_file.write_text("- item1\n- item2\n", encoding="utf-8")

        with pytest.raises(YAMLLoadError, match="must be a mapping"):
            load_yaml_strict(yaml_file, Profile)

    def test_load_with_string_path(self, tmp_path: Path) -> None:
        """Accept string path in addition to Path object."""
        yaml_content = "name: Test\nemail: test@example.com\n"
        yaml_file = tmp_path / "profile.yaml"
        yaml_file.write_text(yaml_content, encoding="utf-8")

        profile = load_yaml_strict(str(yaml_file), Profile)
        assert profile.name == "Test"

    def test_load_list_strict_valid(self, tmp_path: Path) -> None:
        """Load valid YAML list file."""
        yaml_content = """
- id: item-1
  text: First item.
- id: item-2
  text: Second item.
"""
        yaml_file = tmp_path / "highlights.yaml"
        yaml_file.write_text(yaml_content, encoding="utf-8")

        highlights = load_yaml_list_strict(yaml_file, Highlight)
        assert len(highlights) == 2
        assert highlights[0].id == "item-1"

    def test_load_list_strict_file_not_found(self) -> None:
        """Raise FileNotFoundError for missing file in list loader."""
        with pytest.raises(FileNotFoundError):
            load_yaml_list_strict(Path("/nonexistent/file.yaml"), Highlight)

    def test_load_list_strict_non_list_root(self, tmp_path: Path) -> None:
        """Raise YAMLLoadError for non-list YAML root in list loader."""
        yaml_file = tmp_path / "dict.yaml"
        yaml_file.write_text("key: value\n", encoding="utf-8")

        with pytest.raises(YAMLLoadError, match="must be a list"):
            load_yaml_list_strict(yaml_file, Highlight)

    def test_load_list_strict_non_dict_item(self, tmp_path: Path) -> None:
        """Raise YAMLLoadError for non-dict item in list."""
        yaml_file = tmp_path / "bad_list.yaml"
        yaml_file.write_text("- string_item\n- another_string\n", encoding="utf-8")

        with pytest.raises(YAMLLoadError, match="must be a mapping"):
            load_yaml_list_strict(yaml_file, Highlight)

    def test_load_list_strict_validation_error(self, tmp_path: Path) -> None:
        """Raise YAMLValidationError for invalid item in list."""
        yaml_content = """
- id: valid-id
  text: Valid text.
- id: INVALID-ID
  text: This has invalid ID.
"""
        yaml_file = tmp_path / "highlights.yaml"
        yaml_file.write_text(yaml_content, encoding="utf-8")

        with pytest.raises(YAMLValidationError):
            load_yaml_list_strict(yaml_file, Highlight)

    def test_load_list_strict_empty(self, tmp_path: Path) -> None:
        """Raise YAMLLoadError for empty YAML list file."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("", encoding="utf-8")

        with pytest.raises(YAMLLoadError, match="empty"):
            load_yaml_list_strict(yaml_file, Highlight)

    def test_load_list_strict_non_utf8(self, tmp_path: Path) -> None:
        """Raise YAMLLoadError for non-UTF-8 file in list loader."""
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_bytes(b"\xff\xfe")

        with pytest.raises(YAMLLoadError, match="UTF-8"):
            load_yaml_list_strict(yaml_file, Highlight)

    def test_load_list_strict_invalid_yaml(self, tmp_path: Path) -> None:
        """Raise YAMLLoadError for invalid YAML syntax in list loader."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("- [unclosed bracket", encoding="utf-8")

        with pytest.raises(YAMLLoadError, match="YAML syntax"):
            load_yaml_list_strict(yaml_file, Highlight)


# =============================================================================
# Additional Edge Case Tests
# =============================================================================


class TestResumeDateValueEdgeCases:
    """Additional tests for ResumeDateValue edge cases."""

    def test_hash_date(self) -> None:
        """ResumeDateValue is hashable for dates."""
        d = _parse_resume_date("2024-06")
        assert hash(d) == hash(date(2024, 6, 1))

    def test_hash_present(self) -> None:
        """ResumeDateValue is hashable for Present."""
        p = _parse_resume_date("Present")
        assert hash(p) == hash("Present")

    def test_repr_date(self) -> None:
        """ResumeDateValue repr for dates."""
        d = _parse_resume_date("2024-06")
        assert "2024" in repr(d)

    def test_repr_present(self) -> None:
        """ResumeDateValue repr for Present."""
        p = _parse_resume_date("Present")
        assert "Present" in repr(p)

    def test_le_operator(self) -> None:
        """Less-than-or-equal comparison."""
        d1 = _parse_resume_date("2024-01")
        d2 = _parse_resume_date("2024-01")
        d3 = _parse_resume_date("2024-06")
        assert d1 <= d2
        assert d1 <= d3

    def test_ge_operator(self) -> None:
        """Greater-than-or-equal comparison."""
        d1 = _parse_resume_date("2024-06")
        d2 = _parse_resume_date("2024-06")
        d3 = _parse_resume_date("2024-01")
        assert d1 >= d2
        assert d1 >= d3

    def test_to_date(self) -> None:
        """to_date returns underlying date."""
        d = _parse_resume_date("2024-06")
        assert d.to_date() == date(2024, 6, 1)

    def test_to_date_present(self) -> None:
        """to_date returns None for Present."""
        p = _parse_resume_date("Present")
        assert p.to_date() is None


class TestProjectDateValidation:
    """Tests for project date validation."""

    def test_project_end_before_start(self) -> None:
        """Reject project with end date before start date."""
        with pytest.raises(ValidationError, match="cannot be before"):
            ProjectEntry(
                id="proj",
                name="Project",
                description="Desc.",
                start_date="2024-01",
                end_date="2023-01",
            )


class TestExperienceDateValidation:
    """Tests for experience date validation."""

    def test_experience_end_before_start(self) -> None:
        """Reject experience with end date before start date."""
        with pytest.raises(ValidationError, match="cannot be before"):
            ExperienceEntry(
                id="exp",
                company="Company",
                role="Role",
                location="Location",
                start_date="2024-01",
                end_date="2023-01",
                highlights=[Highlight(id="h1", text="Text.")],
            )


class TestProjectFileValidation:
    """Tests for project file validation."""

    def test_duplicate_project_ids(self) -> None:
        """Reject duplicate project entry IDs."""
        with pytest.raises(ValidationError, match="Duplicate"):
            ProjectFile(
                entries=[
                    ProjectEntry(
                        id="same-id",
                        name="Project A",
                        description="Desc A.",
                    ),
                    ProjectEntry(
                        id="same-id",
                        name="Project B",
                        description="Desc B.",
                    ),
                ]
            )


# =============================================================================
# Canonical File Tests
# =============================================================================


class TestCanonicalFiles:
    """Tests for canonical YAML reference files."""

    @pytest.fixture
    def data_dir(self) -> Path:
        """Return path to data directory."""
        return Path(__file__).parent.parent / "data"

    @pytest.fixture
    def content_dir(self) -> Path:
        """Return path to content directory."""
        return Path(__file__).parent.parent / "content"

    def test_profile_yaml_valid(self, data_dir: Path) -> None:
        """Canonical profile.yaml passes validation."""
        profile = load_yaml_strict(data_dir / "profile.yaml", Profile)
        assert profile.name
        assert profile.email

    def test_education_yaml_valid(self, data_dir: Path) -> None:
        """Canonical education.yaml passes validation."""
        education = load_yaml_strict(data_dir / "education.yaml", Education)
        assert len(education.entries) > 0

    def test_skills_yaml_valid(self, data_dir: Path) -> None:
        """Canonical skills.yaml passes validation."""
        skills = load_yaml_strict(data_dir / "skills.yaml", Skills)
        assert len(skills.get_all_skills()) > 0

    def test_experience_yaml_valid(self, content_dir: Path) -> None:
        """Canonical experience YAML passes validation."""
        exp = load_yaml_strict(content_dir / "experience" / "google.yaml", ExperienceFile)
        assert len(exp.entries) > 0
        for entry in exp.entries:
            assert len(entry.highlights) > 0

    def test_projects_yaml_valid(self, content_dir: Path) -> None:
        """Canonical projects YAML passes validation."""
        proj = load_yaml_strict(content_dir / "projects" / "projects.yaml", ProjectFile)
        assert len(proj.entries) > 0
