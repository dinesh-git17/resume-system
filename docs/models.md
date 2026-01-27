# Models Reference

Complete schema documentation for all Pydantic models in the RVS system.

## Custom Types

### ResumeID

Unique identifier for addressable resume content.

| Property           | Value                   |
| ------------------ | ----------------------- |
| Base Type          | `str`                   |
| Pattern            | `^[a-z0-9][a-z0-9_-]*$` |
| Case               | Lowercase only          |
| Allowed Characters | `a-z`, `0-9`, `-`, `_`  |
| Must Start With    | Alphanumeric            |

**Valid Examples:**

- `google-staff-swe`
- `stanford-mscs`
- `highlight_01`
- `exp1`

**Invalid Examples:**

- `Google` (uppercase)
- `-google` (starts with hyphen)
- `_google` (starts with underscore)
- `google swe` (contains space)
- `google@swe` (special character)

### TechTag

Technology or skill tag used for categorization.

| Property           | Value                       |
| ------------------ | --------------------------- |
| Base Type          | `str`                       |
| Pattern            | `^[a-z0-9][a-z0-9._-]*$`    |
| Case               | Auto-lowercased             |
| Allowed Characters | `a-z`, `0-9`, `-`, `_`, `.` |
| Must Start With    | Alphanumeric                |

**Valid Examples:**

- `python`
- `node.js`
- `react-native`
- `grpc`
- `cpp`

**Invalid Examples:**

- `.net` (starts with dot)
- `C++` (special character)
- `react native` (contains space)

### ResumeDateValue

Date wrapper supporting YYYY-MM format and "Present" literal.

| Property      | Value                                                |
| ------------- | ---------------------------------------------------- |
| Input Formats | `YYYY-MM` string, `Present` literal, `datetime.date` |
| Output Format | `YYYY-MM` string or `Present`                        |
| Comparison    | `Present` > any concrete date                        |
| Hashable      | Yes                                                  |

**Valid Examples:**

- `"2024-01"` (January 2024)
- `"2015-09"` (September 2015)
- `"Present"` (ongoing)

**Invalid Examples:**

- `"2024/01"` (wrong separator)
- `"24-01"` (two-digit year)
- `"2024-1"` (single-digit month)
- `"2024-13"` (invalid month)

**Comparison Behavior:**

```python
from scripts.rvs.models.base import _parse_resume_date

d1 = _parse_resume_date("2020-01")
d2 = _parse_resume_date("2024-06")
p = _parse_resume_date("Present")

assert d1 < d2      # Earlier date is less
assert d2 < p       # Present is greater than any date
assert p == p       # Present equals Present
```

---

## Atomic Fact Models

### Profile

Contact information and professional links.

**File:** `data/profile.yaml`

| Field      | Type         | Required | Constraints        |
| ---------- | ------------ | -------- | ------------------ |
| `name`     | `str`        | Yes      | 1-100 chars        |
| `email`    | `EmailStr`   | Yes      | Valid email format |
| `phone`    | `str`        | No       | Max 30 chars       |
| `location` | `str`        | No       | Max 100 chars      |
| `linkedin` | `HttpUrl`    | No       | Valid HTTP(S) URL  |
| `github`   | `HttpUrl`    | No       | Valid HTTP(S) URL  |
| `website`  | `HttpUrl`    | No       | Valid HTTP(S) URL  |
| `links`    | `list[Link]` | No       | Default: empty     |

**Link Sub-model:**

| Field   | Type      | Required | Constraints       |
| ------- | --------- | -------- | ----------------- |
| `label` | `str`     | Yes      | 1-50 chars        |
| `url`   | `HttpUrl` | Yes      | Valid HTTP(S) URL |

**Example:**

```yaml
name: Alex Chen
email: alex.chen@example.com
phone: "+1-555-123-4567"
location: San Francisco Bay Area, CA
linkedin: https://linkedin.com/in/alexchen
github: https://github.com/alexchen
website: https://alexchen.dev
links:
  - label: Portfolio
    url: https://portfolio.alexchen.dev
```

### Education

Container for academic credentials.

**File:** `data/education.yaml`

| Field     | Type                   | Required | Constraints |
| --------- | ---------------------- | -------- | ----------- |
| `entries` | `list[EducationEntry]` | Yes      | Min 1 entry |

**Validation:** All entry IDs must be unique within the file.

**EducationEntry Sub-model:**

| Field            | Type              | Required | Constraints           |
| ---------------- | ----------------- | -------- | --------------------- |
| `id`             | `ResumeID`        | Yes      | Unique within file    |
| `institution`    | `str`             | Yes      | 1-200 chars           |
| `degree`         | `str`             | Yes      | 1-200 chars           |
| `field_of_study` | `str`             | No       | Max 200 chars         |
| `location`       | `str`             | No       | Max 100 chars         |
| `start_date`     | `ResumeDateValue` | Yes      | YYYY-MM or Present    |
| `end_date`       | `ResumeDateValue` | No       | Must be >= start_date |
| `gpa`            | `str`             | No       | Max 20 chars          |
| `honors`         | `list[str]`       | No       | Default: empty        |
| `coursework`     | `list[str]`       | No       | Default: empty        |

**Example:**

```yaml
entries:
  - id: stanford-mscs
    institution: Stanford University
    degree: Master of Science
    field_of_study: Computer Science
    location: Stanford, CA
    start_date: "2015-09"
    end_date: "2017-06"
    gpa: "3.92/4.0"
    honors:
      - Graduate Fellowship Recipient
    coursework:
      - Distributed Systems
```

### Skills

Categorized skill taxonomy.

**File:** `data/skills.yaml`

| Field           | Type            | Required | Constraints                      |
| --------------- | --------------- | -------- | -------------------------------- |
| `languages`     | `list[TechTag]` | No       | No duplicates (case-insensitive) |
| `frameworks`    | `list[TechTag]` | No       | No duplicates (case-insensitive) |
| `databases`     | `list[TechTag]` | No       | No duplicates (case-insensitive) |
| `tools`         | `list[TechTag]` | No       | No duplicates (case-insensitive) |
| `platforms`     | `list[TechTag]` | No       | No duplicates (case-insensitive) |
| `methodologies` | `list[str]`     | No       | No duplicates (case-insensitive) |
| `other`         | `list[str]`     | No       | No duplicates (case-insensitive) |

**Validation:** No duplicate items within any category (case-insensitive comparison).

**Helper Methods:**

- `get_all_skills() -> list[str]`: Flat list of all skills
- `get_skills_by_category() -> dict[str, list[str]]`: Skills organized by category

**Example:**

```yaml
languages:
  - python
  - go
  - java
frameworks:
  - django
  - react
  - node.js
databases:
  - postgresql
  - redis
tools:
  - docker
  - kubernetes
platforms:
  - gcp
  - aws
methodologies:
  - Agile/Scrum
  - Test-Driven Development
other:
  - Technical Leadership
```

---

## Narrative Brick Models

### ExperienceFile

Container for work experience entries.

**File:** `content/experience/*.yaml`

| Field     | Type                    | Required | Constraints |
| --------- | ----------------------- | -------- | ----------- |
| `entries` | `list[ExperienceEntry]` | Yes      | Min 1 entry |

**Validation:** All entry IDs must be unique within the file.

### ExperienceEntry

Single work position.

| Field        | Type              | Required | Constraints           |
| ------------ | ----------------- | -------- | --------------------- |
| `id`         | `ResumeID`        | Yes      | Unique within file    |
| `company`    | `str`             | Yes      | 1-200 chars           |
| `role`       | `str`             | Yes      | 1-200 chars           |
| `location`   | `str`             | Yes      | 1-100 chars           |
| `start_date` | `ResumeDateValue` | Yes      | YYYY-MM or Present    |
| `end_date`   | `ResumeDateValue` | No       | Must be >= start_date |
| `highlights` | `list[Highlight]` | Yes      | Min 1 highlight       |
| `team`       | `str`             | No       | Max 200 chars         |
| `department` | `str`             | No       | Max 200 chars         |

**Validation:**

- `end_date >= start_date` when both present
- All highlight IDs unique within entry

### Highlight

Addressable bullet point within an experience entry.

| Field    | Type            | Required | Constraints                |
| -------- | --------------- | -------- | -------------------------- |
| `id`     | `ResumeID`      | Yes      | Unique within parent entry |
| `text`   | `str`           | Yes      | 1-1000 chars               |
| `tags`   | `list[TechTag]` | No       | Default: empty             |
| `impact` | `str`           | No       | Max 500 chars              |

**Example:**

```yaml
entries:
  - id: google-staff-swe
    company: Google
    role: Staff Software Engineer
    location: Mountain View, CA
    team: Cloud Infrastructure
    department: Google Cloud Platform
    start_date: "2021-03"
    end_date: Present
    highlights:
      - id: google-staff-arch
        text: Architected distributed caching layer serving 2M+ QPS.
        tags:
          - go
          - grpc
          - kubernetes
        impact: Reduced costs by $2.4M annually.
```

### ProjectFile

Container for project entries.

**File:** `content/projects/*.yaml`

| Field     | Type                 | Required | Constraints |
| --------- | -------------------- | -------- | ----------- |
| `entries` | `list[ProjectEntry]` | Yes      | Min 1 entry |

**Validation:** All entry IDs must be unique within the file.

### ProjectEntry

Single project/portfolio item.

| Field          | Type                     | Required | Constraints           |
| -------------- | ------------------------ | -------- | --------------------- |
| `id`           | `ResumeID`               | Yes      | Unique within file    |
| `name`         | `str`                    | Yes      | 1-200 chars           |
| `description`  | `str`                    | Yes      | 1-1000 chars          |
| `start_date`   | `ResumeDateValue`        | No       | YYYY-MM or Present    |
| `end_date`     | `ResumeDateValue`        | No       | Must be >= start_date |
| `url`          | `HttpUrl`                | No       | Valid HTTP(S) URL     |
| `repository`   | `HttpUrl`                | No       | Valid HTTP(S) URL     |
| `technologies` | `list[TechTag]`          | No       | Default: empty        |
| `highlights`   | `list[ProjectHighlight]` | No       | Default: empty        |
| `role`         | `str`                    | No       | Max 200 chars         |
| `organization` | `str`                    | No       | Max 200 chars         |

**Validation:**

- `end_date >= start_date` when both present
- All highlight IDs unique within entry

### ProjectHighlight

Addressable bullet point within a project entry.

| Field  | Type            | Required | Constraints                |
| ------ | --------------- | -------- | -------------------------- |
| `id`   | `ResumeID`      | Yes      | Unique within parent entry |
| `text` | `str`           | Yes      | 1-1000 chars               |
| `tags` | `list[TechTag]` | No       | Default: empty             |

**Example:**

```yaml
entries:
  - id: distributed-cache
    name: DistCache
    description: Open-source distributed caching library.
    start_date: "2022-01"
    end_date: Present
    url: https://distcache.dev
    repository: https://github.com/alexchen/distcache
    role: Creator and Maintainer
    technologies:
      - go
      - grpc
      - redis
    highlights:
      - id: distcache-adoption
        text: Achieved 2,500+ GitHub stars.
        tags:
          - go
          - open-source
```

---

## Base Model Configuration

All models inherit from `BaseResumeModel` with:

```python
model_config = ConfigDict(
    extra="forbid",           # Reject unknown fields
    str_strip_whitespace=True, # Strip whitespace from strings
    validate_default=True,     # Validate default values
)
```

This ensures:

- No schema drift from extra fields
- Consistent whitespace handling
- Validation of all fields including defaults
