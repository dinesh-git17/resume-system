# Skill: Job Description Analyzer (jd-analyzer)

**Version:** 1.0.0
**Type:** Deterministic Extraction
**Enforcement Level:** STRICT

## Purpose

To extract structured, machine-readable signals from unstructured Job Description (JD) text. This skill converts human-written requirements into a standardized JSON format for downstream processing.

## Responsibilities

1.  **Ingest:** Read raw text from a provided file path or text block.
2.  **Extract:** Identify and categorize requirements into "Must Have" and "Nice to Have".
3.  **Normalize:** Map JD terminology to standard domain tags (e.g., "K8s" -> "Kubernetes", "Golang" -> "Go").
4.  **Structure:** Output strictly compliant JSON based on `assets/schema.json`.

## Boundaries (Strict Prohibitions)

- **NO Matching:** You MUST NOT attempt to compare these requirements to the candidate's resume or experience. This skill analyzes the JD _only_.
- **NO Inference:** You MUST NOT infer skills not explicitly mentioned (e.g., do not assume "Git" just because "CI/CD" is mentioned).
- **NO Creative Writing:** You MUST NOT summarize the company culture or benefits unless they contain explicit keyword signals.

## Input

- Raw text or file path to a Job Description.

## Output

- A single JSON object adhering strictly to the schema defined in `assets/schema.json`.

## Instructions

1.  Read the input text.
2.  Extract key technical skills, experience levels, and domain tags.
3.  Categorize skills into `required` vs `preferred` based on context clues (e.g., "strong plus", "bonus", "must have").
4.  Format the output as JSON.
5.  Verify the JSON against `assets/schema.json`.
6.  Output the JSON block only.
