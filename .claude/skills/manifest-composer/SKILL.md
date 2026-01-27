# Skill: Manifest Composer (manifest-composer)

**Version:** 1.0.0
**Type:** Deterministic Configuration Generation
**Enforcement Level:** STRICT

## Purpose

To mechanically construct valid `config/*.yaml` Build Manifests. This skill translates a list of selected Content IDs into a strictly schema-compliant configuration file used by the build engine. It ensures that the "Tailoring" process results in a valid artifact.

## Responsibilities

1.  **Construct:** Map input variables (IDs, profile, template) into the standard YAML manifest structure.
2.  **Format:** Ensure output adheres to YAML 1.2 standards (2-space indentation, UTF-8).
3.  **Write:** Save the generated content to `config/<target_filename>.yaml`.
4.  **Isolate:** Ensure no "glue text" or conversational filler exists in the output file.

## Boundaries (Strict Prohibitions)

- **NO Hallucination:** You MUST NOT add `id`s to the manifest that were not explicitly provided in the input list.
- **NO Ambiguity:** You MUST NOT guess the `profile` (default to 'default' if unspecified).
- **NO Invalid Fields:** You MUST NOT add fields like `notes`, `comments`, or `description` to the YAML. The schema forbids extra fields.

## Input

- `target_filename`: The name of the file to create (e.g., `google-staff.yaml`).
- `profile`: The profile key to use (default: `default`).
- `experience_ids`: A list of strings representing Experience Entry IDs.
- `project_ids`: A list of strings representing Project IDs.

## Output

- A new file at `config/<target_filename>.yaml`.
- A confirmation message containing the path of the created file.

## Instructions

1.  Receive the input variables.
2.  Load the Jinja2 template at `.claude/skills/manifest-composer/templates/manifest.j2`.
3.  Render the template with the provided variables.
4.  Write the rendered string to `config/<target_filename>.yaml`.
5.  Output: `[SUCCESS] Manifest created at config/<target_filename>.yaml`.
