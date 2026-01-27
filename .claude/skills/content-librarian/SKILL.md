# Skill: Content Librarian (content-librarian)

**Version:** 1.0.0
**Type:** Read-Only Search & Retrieval
**Enforcement Level:** STRICT / BLOCKING

## Purpose

To act as the **Gatekeeper of Truth** for the Resume Engine. This skill performs read-only searches against the local YAML repository (`content/` and `data/`) to identify existing professional history. It prevents hallucination by ensuring the agent only "knows" what is explicitly defined in the source files.

## Responsibilities

1.  **Search:** Scan `content/experience/*.yaml` and `content/projects/*.yaml` for keywords or tags.
2.  **Verify:** Confirm that a specific `id` exists in the repository.
3.  **Retrieve:** Return the full text and metadata for selected IDs to allow for context awareness.
4.  **Ground:** If a user asks for a skill (e.g., "Rust") not found in the index, explicitly report "Zero Results".

## Boundaries (Strict Prohibitions)

- **NO Modification:** You MUST NOT edit, delete, or create files via this skill. It is strictly read-only.
- **NO Invention:** You MUST NOT return partial matches as "exact" matches. If the content isn't there, it doesn't exist.
- **NO Formatting:** Return raw data/text. Do not attempt to "polish" the result.

## Input

- `query`: A string of keywords (e.g., "Python, Leadership, System Design").
- `target_type`: Optional filter (`experience`, `project`, `skill`).

## Output

- A JSON list of matching entities, including their `id`, `file_path`, and `relevance_score`.

## Instructions

1.  Receive the search query.
2.  Execute `python3 .claude/skills/content-librarian/scripts/search.py --query "<query>"`.
3.  Parse the JSON output.
4.  If the output is empty, report that no grounded content was found.
5.  If content is found, present the valid `id`s to the user or downstream skill.
