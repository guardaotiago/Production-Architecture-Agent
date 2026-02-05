#!/usr/bin/env python3
"""
Generate UAT Plan from PRD

Parses a Product Requirements Document for user stories and acceptance criteria,
then produces a structured UAT test plan in business-friendly language.

Usage:
    python generate_uat_plan.py --prd docs/prd.md --output docs/uat-plan.md
    python generate_uat_plan.py --help
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def read_file(path: str) -> str:
    """Read a file and return its contents."""
    p = Path(path)
    if not p.exists():
        print(f"Error: file not found — {path}", file=sys.stderr)
        sys.exit(1)
    return p.read_text(encoding="utf-8")


def extract_user_stories(prd_text: str) -> list[dict]:
    """
    Extract user stories from the PRD.

    Recognises two common patterns:
      1. Classic format — "As a <role>, I want <action> so that <benefit>"
      2. Heading-based — any heading whose text contains "user stor" (case-insensitive)
         followed by bullet points describing the stories.

    Returns a list of dicts:
        {
            "raw": <original matched text>,
            "role": <user role or empty string>,
            "action": <desired action or raw text>,
            "benefit": <expected benefit or empty string>,
        }
    """
    stories: list[dict] = []

    # Pattern 1: explicit "As a … I want … so that …"
    classic = re.finditer(
        r"[Aa]s\s+an?\s+(?P<role>[^,]+),\s*[Ii]\s+want\s+(?P<action>.+?)\s+so\s+that\s+(?P<benefit>[^.\n]+)",
        prd_text,
    )
    for m in classic:
        stories.append({
            "raw": m.group(0).strip(),
            "role": m.group("role").strip(),
            "action": m.group("action").strip(),
            "benefit": m.group("benefit").strip(),
        })

    # Pattern 2: bullet items under a "User Stor(y|ies)" heading
    heading_blocks = re.finditer(
        r"^#{1,4}\s+.*[Uu]ser\s+[Ss]tor(?:y|ies).*$\n((?:[ \t]*[-*]\s+.+\n?)+)",
        prd_text,
        re.MULTILINE,
    )
    for block in heading_blocks:
        bullets = re.findall(r"[-*]\s+(.+)", block.group(1))
        for bullet in bullets:
            # Avoid duplicates if the bullet is already captured by pattern 1
            if any(bullet.strip() in s["raw"] for s in stories):
                continue
            stories.append({
                "raw": bullet.strip(),
                "role": "",
                "action": bullet.strip(),
                "benefit": "",
            })

    return stories


def extract_acceptance_criteria(prd_text: str) -> list[str]:
    """
    Pull acceptance criteria from the PRD.

    Looks for bullet lists under headings containing "acceptance criteria"
    (case-insensitive). Returns a flat list of criteria strings.
    """
    criteria: list[str] = []

    blocks = re.finditer(
        r"^#{1,4}\s+.*[Aa]cceptance\s+[Cc]riteria.*$\n((?:[ \t]*[-*]\s+.+\n?)+)",
        prd_text,
        re.MULTILINE,
    )
    for block in blocks:
        items = re.findall(r"[-*]\s+(.+)", block.group(1))
        criteria.extend(item.strip() for item in items)

    return criteria


def detect_feature_areas(prd_text: str) -> list[str]:
    """
    Detect feature areas from second-level headings in the PRD.

    Returns a list of heading texts that likely represent feature areas.
    Excludes common non-feature headings (overview, introduction, etc.).
    """
    excluded = {
        "overview", "introduction", "summary", "background", "context",
        "appendix", "references", "glossary", "table of contents",
        "acceptance criteria", "user stories", "non-functional requirements",
    }
    headings = re.findall(r"^##\s+(.+)$", prd_text, re.MULTILINE)
    return [
        h.strip()
        for h in headings
        if h.strip().lower() not in excluded
    ]


# ---------------------------------------------------------------------------
# UAT plan generation
# ---------------------------------------------------------------------------

def build_test_cases(
    stories: list[dict],
    criteria: list[str],
    feature_areas: list[str],
) -> list[dict]:
    """
    Build UAT test cases from extracted stories and criteria.

    Each test case contains:
        id, feature_area, user_story, preconditions, steps, expected_result
    """
    test_cases: list[dict] = []
    case_num = 1

    # Map stories to feature areas by simple keyword overlap.
    # If no match, assign to "General".
    def match_area(text: str) -> str:
        text_lower = text.lower()
        for area in feature_areas:
            # Check if any significant word from the area appears in the story
            area_words = {w.lower() for w in area.split() if len(w) > 3}
            if any(w in text_lower for w in area_words):
                return area
        return "General"

    for story in stories:
        area = match_area(story["raw"])
        steps = build_steps_from_story(story)
        expected = story["benefit"] if story["benefit"] else "The user can successfully complete the described action."

        test_cases.append({
            "id": f"UAT-{case_num:03d}",
            "feature_area": area,
            "user_story": story["raw"],
            "preconditions": derive_precondition(story),
            "steps": steps,
            "expected_result": expected,
        })
        case_num += 1

    # Create additional test cases from acceptance criteria that are not
    # already covered by a user story.
    covered_text = " ".join(s["raw"].lower() for s in stories)
    for criterion in criteria:
        if criterion.lower() in covered_text:
            continue
        area = match_area(criterion)
        test_cases.append({
            "id": f"UAT-{case_num:03d}",
            "feature_area": area,
            "user_story": f"Acceptance criterion: {criterion}",
            "preconditions": "System is accessible and user is logged in.",
            "steps": [f"Verify that: {criterion}"],
            "expected_result": criterion,
        })
        case_num += 1

    return test_cases


def build_steps_from_story(story: dict) -> list[str]:
    """
    Derive human-readable test steps from a user story.
    """
    steps: list[str] = []
    if story["role"]:
        steps.append(f"Log in as a {story['role']}.")
    else:
        steps.append("Log in to the application.")

    action = story["action"]
    # Split on common conjunctions to break compound actions into steps
    sub_actions = re.split(r"\s+and\s+|\s+then\s+", action, flags=re.IGNORECASE)
    for sub in sub_actions:
        sub = sub.strip().rstrip(".")
        if sub:
            # Capitalise the first letter for readability
            steps.append(sub[0].upper() + sub[1:] + ".")

    steps.append("Observe the result and verify it matches the expected outcome.")
    return steps


def derive_precondition(story: dict) -> str:
    """
    Derive a reasonable precondition string from a user story.
    """
    if story["role"]:
        return f"User has a valid {story['role']} account and is logged in."
    return "System is accessible and user is logged in."


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def render_markdown(
    test_cases: list[dict],
    prd_path: str,
) -> str:
    """
    Render test cases as a Markdown UAT plan document.
    """
    now = datetime.now().strftime("%Y-%m-%d")
    lines: list[str] = []

    lines.append("# UAT Test Plan")
    lines.append("")
    lines.append(f"**Generated**: {now}  ")
    lines.append(f"**Source PRD**: `{prd_path}`  ")
    lines.append(f"**Total test cases**: {len(test_cases)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    areas = sorted({tc["feature_area"] for tc in test_cases})
    lines.append("| Feature Area | Test Cases |")
    lines.append("|---|---|")
    for area in areas:
        count = sum(1 for tc in test_cases if tc["feature_area"] == area)
        lines.append(f"| {area} | {count} |")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Test cases grouped by feature area
    lines.append("## Test Cases")
    lines.append("")
    for area in areas:
        lines.append(f"### {area}")
        lines.append("")
        area_cases = [tc for tc in test_cases if tc["feature_area"] == area]
        for tc in area_cases:
            lines.append(f"#### {tc['id']}")
            lines.append("")
            lines.append(f"**User Story**: {tc['user_story']}  ")
            lines.append(f"**Precondition**: {tc['preconditions']}  ")
            lines.append("")
            lines.append("**Steps**:")
            lines.append("")
            for i, step in enumerate(tc["steps"], 1):
                lines.append(f"{i}. {step}")
            lines.append("")
            lines.append(f"**Expected Result**: {tc['expected_result']}  ")
            lines.append("**Actual Result**: _to be filled by tester_  ")
            lines.append("**Status**: `PENDING`  ")
            lines.append("**Notes**:  ")
            lines.append("")
            lines.append("---")
            lines.append("")

    # Sign-off section
    lines.append("## Sign-off")
    lines.append("")
    lines.append("| Stakeholder | Role | Date | Signature |")
    lines.append("|---|---|---|---|")
    lines.append("| | | | |")
    lines.append("| | | | |")
    lines.append("| | | | |")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a UAT test plan from a Product Requirements Document (PRD).",
        epilog="Example: python generate_uat_plan.py --prd docs/prd.md --output docs/uat-plan.md",
    )
    parser.add_argument(
        "--prd",
        required=True,
        help="Path to the PRD markdown file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path for the generated UAT plan markdown file.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print extraction details to stderr.",
    )

    args = parser.parse_args()

    # --- Read and parse ---
    prd_text = read_file(args.prd)

    stories = extract_user_stories(prd_text)
    criteria = extract_acceptance_criteria(prd_text)
    feature_areas = detect_feature_areas(prd_text)

    if args.verbose:
        print(f"[info] Extracted {len(stories)} user stories", file=sys.stderr)
        print(f"[info] Extracted {len(criteria)} acceptance criteria", file=sys.stderr)
        print(f"[info] Detected {len(feature_areas)} feature areas", file=sys.stderr)

    if not stories and not criteria:
        print(
            "Warning: no user stories or acceptance criteria found in the PRD.\n"
            "The UAT plan will be empty. Ensure the PRD contains user stories in\n"
            "the format 'As a <role>, I want <action> so that <benefit>' or under\n"
            "a '## User Stories' heading.",
            file=sys.stderr,
        )

    # --- Build and render ---
    test_cases = build_test_cases(stories, criteria, feature_areas)
    markdown = render_markdown(test_cases, args.prd)

    # --- Write output ---
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"UAT plan written to {args.output} ({len(test_cases)} test cases)")


if __name__ == "__main__":
    main()
