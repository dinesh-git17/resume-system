#!/usr/bin/env python3
"""
Deterministic Content Search Tool
Scans local content/ directory for YAML files and matches keywords.
Returns JSON-formatted results.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

# Configuration
CONTENT_ROOT = Path("content")
DATA_ROOT = Path("data")


def load_yaml(path: Path) -> dict[str, Any] | None:
    """Load and parse a YAML file, returning its contents as a dict."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                return data
            return None
    except (OSError, yaml.YAMLError):
        return None


def score_match(data: dict[str, Any], terms: list[str]) -> int:
    """
    Simple deterministic scoring:
    +10 for tag match
    +5 for role/title match
    +1 for text body match
    """
    score = 0
    text_dump = str(data).lower()

    for term in terms:
        term = term.lower()
        # check tags if they exist
        if "tags" in data and isinstance(data["tags"], list):
            if any(term == t.lower() for t in data["tags"]):
                score += 10

        # check title/role
        if "role" in data and term in str(data.get("role", "")).lower():
            score += 5
        if "title" in data and term in str(data.get("title", "")).lower():
            score += 5

        # check body
        if term in text_dump:
            score += 1

    return score


def search_content(query: str) -> list[dict[str, Any]]:
    """Search content directories for entries matching comma-separated keywords."""
    results: list[dict[str, Any]] = []
    terms = [t.strip() for t in query.split(",") if t.strip()]

    if not terms:
        return []

    # 1. Search Experience
    exp_dir = CONTENT_ROOT / "experience"
    if exp_dir.exists():
        for f in exp_dir.glob("*.yaml"):
            data = load_yaml(f)
            if not data:
                continue

            # Check the entry itself
            entry_score = score_match(data, terms)

            # Check bullets (Highlights)
            if "highlights" in data:
                for bullet in data["highlights"]:
                    b_score = score_match(bullet, terms)
                    if b_score > 0 or entry_score > 0:
                        results.append(
                            {
                                "id": bullet.get("id", "unknown"),
                                "parent_id": data.get("id"),
                                "type": "bullet",
                                "file": str(f),
                                "score": b_score + entry_score,
                                "snippet": bullet.get("text", "")[:100] + "...",
                            }
                        )

    # 2. Search Projects
    proj_dir = CONTENT_ROOT / "projects"
    if proj_dir.exists():
        for f in proj_dir.glob("*.yaml"):
            data = load_yaml(f)
            if not data:
                continue

            s = score_match(data, terms)
            if s > 0:
                results.append(
                    {
                        "id": data.get("id", "unknown"),
                        "type": "project",
                        "file": str(f),
                        "score": s,
                        "snippet": data.get("description", "")[:100] + "...",
                    }
                )

    # Sort by score descending
    return sorted(results, key=lambda x: x["score"], reverse=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resume Content Search")
    parser.add_argument("--query", required=True, help="Comma-separated keywords")
    args = parser.parse_args()

    matches = search_content(args.query)
    print(json.dumps(matches, indent=2))
