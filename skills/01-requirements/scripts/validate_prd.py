#!/usr/bin/env python3
"""
validate_prd.py — Validate PRD completeness for SDLC Orchestrator.

Usage:
    python validate_prd.py --file docs/prd.md
    python validate_prd.py --file docs/prd.md --json
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Required sections and the patterns used to detect them.
# Each entry is (section_name, display_label, list_of_regex_patterns).
REQUIRED_SECTIONS = [
    (
        "executive_summary",
        "Executive Summary",
        [r"(?i)##?\s*executive\s+summary", r"(?i)##?\s*overview"],
    ),
    (
        "problem_statement",
        "Problem Statement",
        [r"(?i)##?\s*problem\s+statement", r"(?i)##?\s*problem", r"(?i)##?\s*background"],
    ),
    (
        "goals",
        "Goals & Non-Goals",
        [r"(?i)##?\s*goals", r"(?i)##?\s*objectives"],
    ),
    (
        "user_stories",
        "User Stories",
        [r"(?i)##?\s*user\s+stories", r"(?i)as\s+a\s+.+,?\s*I\s+want"],
    ),
    (
        "acceptance_criteria",
        "Acceptance Criteria",
        [
            r"(?i)acceptance\s+criteria",
            r"(?i)given\s+.+when\s+.+then",
            r"(?i)##?\s*acceptance",
        ],
    ),
    (
        "technical_requirements",
        "Technical Requirements",
        [
            r"(?i)##?\s*technical\s+requirements",
            r"(?i)##?\s*technical\s+spec",
            r"(?i)##?\s*architecture",
            r"(?i)##?\s*tech\s+stack",
        ],
    ),
    (
        "success_metrics",
        "Success Metrics",
        [
            r"(?i)##?\s*success\s+metrics",
            r"(?i)##?\s*metrics",
            r"(?i)##?\s*kpis",
            r"(?i)##?\s*key\s+performance",
        ],
    ),
    (
        "timeline",
        "Timeline / Milestones",
        [
            r"(?i)##?\s*timeline",
            r"(?i)##?\s*milestones",
            r"(?i)##?\s*roadmap",
            r"(?i)##?\s*schedule",
        ],
    ),
]

# Optional but recommended sections.
OPTIONAL_SECTIONS = [
    (
        "user_personas",
        "User Personas",
        [r"(?i)##?\s*user\s+personas", r"(?i)##?\s*personas", r"(?i)##?\s*target\s+users"],
    ),
    (
        "non_goals",
        "Non-Goals",
        [r"(?i)##?\s*non[-\s]?goals", r"(?i)out\s+of\s+scope"],
    ),
    (
        "open_questions",
        "Open Questions",
        [r"(?i)##?\s*open\s+questions", r"(?i)##?\s*unknowns", r"(?i)##?\s*risks"],
    ),
]


def check_section(content: str, patterns: list[str]) -> bool:
    """Return True if any pattern matches in the content."""
    for pattern in patterns:
        if re.search(pattern, content):
            return True
    return False


def count_user_stories(content: str) -> int:
    """Count the number of user stories in the document."""
    return len(re.findall(r"(?i)as\s+a\s+", content))


def count_acceptance_criteria(content: str) -> int:
    """Count Given/When/Then blocks."""
    return len(re.findall(r"(?i)given\s+", content))


def validate(content: str) -> dict:
    """Validate PRD content and return a results dict."""
    results = {
        "required": {},
        "optional": {},
        "stats": {},
        "passed": True,
    }

    # Check required sections
    for key, label, patterns in REQUIRED_SECTIONS:
        found = check_section(content, patterns)
        results["required"][key] = {"label": label, "found": found}
        if not found:
            results["passed"] = False

    # Check optional sections
    for key, label, patterns in OPTIONAL_SECTIONS:
        found = check_section(content, patterns)
        results["optional"][key] = {"label": label, "found": found}

    # Gather stats
    results["stats"]["word_count"] = len(content.split())
    results["stats"]["user_story_count"] = count_user_stories(content)
    results["stats"]["acceptance_criteria_count"] = count_acceptance_criteria(content)

    # Additional quality checks
    if results["stats"]["user_story_count"] == 0:
        results["passed"] = False
    if results["stats"]["acceptance_criteria_count"] == 0:
        results["passed"] = False

    return results


def print_report(results: dict, file_path: str) -> None:
    """Print a human-readable validation report."""
    status = "PASS" if results["passed"] else "FAIL"
    print(f"\n{'=' * 60}")
    print(f"  PRD Validation Report: {status}")
    print(f"  File: {file_path}")
    print(f"{'=' * 60}")

    # Required sections
    print(f"\n  Required Sections:")
    for key, info in results["required"].items():
        icon = "[x]" if info["found"] else "[ ]"
        print(f"    {icon} {info['label']}")

    # Optional sections
    print(f"\n  Recommended Sections:")
    for key, info in results["optional"].items():
        icon = "[x]" if info["found"] else "[ ]"
        print(f"    {icon} {info['label']}")

    # Stats
    stats = results["stats"]
    print(f"\n  Document Stats:")
    print(f"    Word count:            {stats['word_count']}")
    print(f"    User stories found:    {stats['user_story_count']}")
    print(f"    Acceptance criteria:    {stats['acceptance_criteria_count']}")

    # Warnings
    warnings = []
    if stats["word_count"] < 200:
        warnings.append("PRD is very short (< 200 words). Consider adding more detail.")
    if stats["user_story_count"] == 0:
        warnings.append("No user stories detected. Add 'As a [user], I want...' stories.")
    if stats["acceptance_criteria_count"] == 0:
        warnings.append("No acceptance criteria detected. Add Given/When/Then blocks.")

    missing_required = [
        info["label"]
        for info in results["required"].values()
        if not info["found"]
    ]
    if missing_required:
        warnings.append(f"Missing required sections: {', '.join(missing_required)}")

    if warnings:
        print(f"\n  Warnings:")
        for w in warnings:
            print(f"    - {w}")

    print(f"\n  Result: {status}")
    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Validate PRD document completeness.",
        epilog="Example: python validate_prd.py --file docs/prd.md",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the PRD markdown file to validate.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON instead of human-readable text.",
    )

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    content = file_path.read_text(encoding="utf-8")

    if not content.strip():
        print(f"Error: File is empty: {file_path}", file=sys.stderr)
        return 1

    results = validate(content)

    if args.json_output:
        output = {
            "file": str(file_path),
            "passed": results["passed"],
            "required_sections": {
                k: v["found"] for k, v in results["required"].items()
            },
            "optional_sections": {
                k: v["found"] for k, v in results["optional"].items()
            },
            "stats": results["stats"],
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(results, str(file_path))

    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
