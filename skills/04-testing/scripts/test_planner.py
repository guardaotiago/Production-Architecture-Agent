#!/usr/bin/env python3
"""
Test Planner — Generates a structured test plan from a PRD document.

Parses a Product Requirements Document for user stories and acceptance criteria,
then produces a categorized test plan (unit, integration, E2E) with priorities,
preconditions, steps, and expected results.

Usage:
    python test_planner.py --prd docs/prd.md --output docs/test-plan.md
    python test_planner.py --prd docs/prd.md  # prints to stdout
    python test_planner.py --help
"""

import argparse
import re
import sys
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class Priority(Enum):
    P0 = "P0 — Critical"
    P1 = "P1 — High"
    P2 = "P2 — Medium"


class TestType(Enum):
    UNIT = "Unit"
    INTEGRATION = "Integration"
    E2E = "E2E"


@dataclass
class TestCase:
    id: str
    title: str
    test_type: TestType
    priority: Priority
    preconditions: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    expected_results: list[str] = field(default_factory=list)
    source_story: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class UserStory:
    id: str
    title: str
    description: str
    acceptance_criteria: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# PRD Parsing
# ---------------------------------------------------------------------------

def parse_prd(prd_path: Path) -> list[UserStory]:
    """Parse a PRD markdown file and extract user stories with acceptance criteria."""
    content = prd_path.read_text(encoding="utf-8")
    stories: list[UserStory] = []

    # Strategy 1: Look for explicit "User Story" or "Story" headings
    # Matches patterns like: ## US-001: As a user... / ### Story: Login / ## User Story 1
    story_pattern = re.compile(
        r"^#{2,4}\s*(?:(?:User\s*)?Story\s*[:\-#]*\s*)?(?:US[-_]?(\d+)\s*[:\-]\s*)?(.+)$",
        re.MULTILINE | re.IGNORECASE,
    )

    # Find all headings that look like stories
    heading_matches = list(story_pattern.finditer(content))

    if heading_matches:
        for i, match in enumerate(heading_matches):
            # Extract section content (from this heading to next heading of same/higher level)
            start = match.end()
            if i + 1 < len(heading_matches):
                end = heading_matches[i + 1].start()
            else:
                end = len(content)
            section = content[start:end]

            story_id = f"US-{match.group(1) if match.group(1) else str(i + 1).zfill(3)}"
            title = match.group(2).strip()
            description = _extract_description(section)
            criteria = _extract_acceptance_criteria(section)

            stories.append(UserStory(
                id=story_id,
                title=title,
                description=description,
                acceptance_criteria=criteria,
            ))

    # Strategy 2: Fallback — look for "As a ... I want ... so that" patterns
    if not stories:
        as_a_pattern = re.compile(
            r"(As an?\s+.+?,\s*I\s+want\s+.+?)(?:\n|$)",
            re.IGNORECASE,
        )
        for i, match in enumerate(as_a_pattern.finditer(content)):
            story_text = match.group(1).strip()
            # Get surrounding context for acceptance criteria
            ctx_start = max(0, match.start() - 50)
            ctx_end = min(len(content), match.end() + 500)
            context = content[match.end():ctx_end]
            criteria = _extract_acceptance_criteria(context)

            stories.append(UserStory(
                id=f"US-{str(i + 1).zfill(3)}",
                title=story_text[:80],
                description=story_text,
                acceptance_criteria=criteria if criteria else [story_text],
            ))

    # Strategy 3: Last resort — extract from any requirements-like sections
    if not stories:
        req_headings = re.finditer(
            r"^#{1,4}\s*(Requirements?|Features?|Functional)\s*$",
            content,
            re.MULTILINE | re.IGNORECASE,
        )
        bullet_items = []
        for heading in req_headings:
            section_start = heading.end()
            next_heading = re.search(r"^#{1,4}\s", content[section_start:], re.MULTILINE)
            section_end = section_start + next_heading.start() if next_heading else len(content)
            section = content[section_start:section_end]
            bullets = re.findall(r"^[\s]*[-*]\s+(.+)$", section, re.MULTILINE)
            bullet_items.extend(bullets)

        for i, item in enumerate(bullet_items):
            stories.append(UserStory(
                id=f"US-{str(i + 1).zfill(3)}",
                title=item.strip()[:80],
                description=item.strip(),
                acceptance_criteria=[item.strip()],
            ))

    if not stories:
        print(
            "WARNING: No user stories or requirements found in PRD. "
            "Generating a skeleton test plan from document structure.",
            file=sys.stderr,
        )
        stories.append(UserStory(
            id="US-001",
            title="General application functionality",
            description="Verify core application behavior as described in the PRD.",
            acceptance_criteria=["Application works as described"],
        ))

    return stories


def _extract_description(section: str) -> str:
    """Extract the first paragraph of text as the description."""
    lines = []
    for line in section.strip().split("\n"):
        stripped = line.strip()
        if not stripped:
            if lines:
                break
            continue
        if stripped.startswith("#"):
            break
        if re.match(r"^[-*]\s+", stripped):
            break
        lines.append(stripped)
    return " ".join(lines) if lines else ""


def _extract_acceptance_criteria(section: str) -> list[str]:
    """Extract acceptance criteria from a section of text."""
    criteria = []

    # Look for explicit "Acceptance Criteria" subsection
    ac_match = re.search(
        r"(?:Acceptance\s*Criteria|AC|Given\s*/\s*When\s*/\s*Then)\s*[:\-]?\s*\n",
        section,
        re.IGNORECASE,
    )
    if ac_match:
        ac_section = section[ac_match.end():]
        # Stop at next heading
        next_heading = re.search(r"^#{1,4}\s", ac_section, re.MULTILINE)
        if next_heading:
            ac_section = ac_section[:next_heading.start()]
        bullets = re.findall(r"^[\s]*[-*]\s+(.+)$", ac_section, re.MULTILINE)
        criteria.extend(b.strip() for b in bullets)

    # Also look for Given/When/Then patterns anywhere in section
    gwt = re.findall(
        r"(Given\s+.+?(?:When\s+.+?)?Then\s+.+?)(?:\n|$)",
        section,
        re.IGNORECASE,
    )
    criteria.extend(g.strip() for g in gwt if g.strip() not in criteria)

    # Checkbox items: - [ ] or - [x]
    checkboxes = re.findall(r"^[\s]*[-*]\s+\[[ x]\]\s+(.+)$", section, re.MULTILINE)
    criteria.extend(c.strip() for c in checkboxes if c.strip() not in criteria)

    return criteria


# ---------------------------------------------------------------------------
# Test Case Generation
# ---------------------------------------------------------------------------

def generate_test_cases(stories: list[UserStory]) -> list[TestCase]:
    """Generate test cases from user stories."""
    cases: list[TestCase] = []
    case_counter = {"unit": 0, "integration": 0, "e2e": 0}

    for story in stories:
        story_cases = _generate_cases_for_story(story, case_counter)
        cases.extend(story_cases)

    return cases


def _generate_cases_for_story(
    story: UserStory, counter: dict[str, int]
) -> list[TestCase]:
    """Generate unit, integration, and E2E test cases for a single user story."""
    cases: list[TestCase] = []

    for criterion in story.acceptance_criteria:
        # --- Unit Test ---
        counter["unit"] += 1
        cases.append(TestCase(
            id=f"TC-U{counter['unit']:03d}",
            title=f"Unit: Verify {_summarize(criterion)}",
            test_type=TestType.UNIT,
            priority=_infer_priority(criterion),
            preconditions=["Module under test is importable", "Dependencies are mocked"],
            steps=[
                "Arrange: Set up input data and mocks",
                f"Act: Call the function/method related to: {_summarize(criterion)}",
                "Assert: Verify return value matches expected output",
            ],
            expected_results=[
                f"Function correctly handles: {criterion}",
                "No unexpected side effects",
            ],
            source_story=story.id,
            tags=["unit", "automated"],
        ))

        # --- Integration Test ---
        counter["integration"] += 1
        cases.append(TestCase(
            id=f"TC-I{counter['integration']:03d}",
            title=f"Integration: Verify {_summarize(criterion)} across components",
            test_type=TestType.INTEGRATION,
            priority=_infer_priority(criterion),
            preconditions=[
                "Test environment is running",
                "Database/services are available",
                "Test data is seeded",
            ],
            steps=[
                "Set up test fixtures and seed data",
                f"Execute the workflow related to: {_summarize(criterion)}",
                "Verify data flows correctly between components",
                "Check database/state changes",
            ],
            expected_results=[
                f"Components interact correctly for: {criterion}",
                "Data persists as expected",
                "Error cases are handled gracefully",
            ],
            source_story=story.id,
            tags=["integration", "automated"],
        ))

    # --- E2E Test (one per story, not per criterion) ---
    counter["e2e"] += 1
    cases.append(TestCase(
        id=f"TC-E{counter['e2e']:03d}",
        title=f"E2E: {story.title}",
        test_type=TestType.E2E,
        priority=Priority.P0 if _is_critical_story(story) else Priority.P1,
        preconditions=[
            "Application is deployed to test environment",
            "Test user accounts exist",
            "Browser/client is configured",
        ],
        steps=[
            f"Navigate to the feature related to: {story.title}",
            "Complete the full user journey",
            "Verify each acceptance criterion:",
        ] + [f"  - Check: {ac}" for ac in story.acceptance_criteria],
        expected_results=[
            "Full user journey completes without errors",
            "UI displays correct information",
            "All acceptance criteria pass",
        ],
        source_story=story.id,
        tags=["e2e", "automated", "user-journey"],
    ))

    return cases


def _summarize(text: str, max_len: int = 60) -> str:
    """Create a short summary suitable for a test case title."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[:max_len - 3].rsplit(" ", 1)[0] + "..."


def _infer_priority(criterion: str) -> Priority:
    """Infer test priority from the language of the acceptance criterion."""
    critical_keywords = [
        "must", "critical", "security", "auth", "login", "payment", "data loss",
        "crash", "block", "required",
    ]
    high_keywords = [
        "should", "important", "validation", "error handling", "performance",
    ]
    lower = criterion.lower()
    if any(kw in lower for kw in critical_keywords):
        return Priority.P0
    if any(kw in lower for kw in high_keywords):
        return Priority.P1
    return Priority.P2


def _is_critical_story(story: UserStory) -> bool:
    """Determine if a story is critical based on its content."""
    critical_indicators = [
        "login", "auth", "payment", "checkout", "security", "signup", "register",
        "password", "admin", "delete", "remove",
    ]
    text = f"{story.title} {story.description}".lower()
    return any(ind in text for ind in critical_indicators)


# ---------------------------------------------------------------------------
# Markdown Output
# ---------------------------------------------------------------------------

def render_test_plan(stories: list[UserStory], cases: list[TestCase]) -> str:
    """Render the test plan as a markdown document."""
    lines: list[str] = []

    lines.append("# Test Plan")
    lines.append("")
    lines.append(f"*Generated by test_planner.py*")
    lines.append("")

    # --- Summary ---
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| User Stories | {len(stories)} |")
    lines.append(f"| Total Test Cases | {len(cases)} |")

    by_type = {}
    for c in cases:
        by_type.setdefault(c.test_type.value, []).append(c)
    for ttype, tcases in by_type.items():
        lines.append(f"| {ttype} Tests | {len(tcases)} |")

    by_priority = {}
    for c in cases:
        by_priority.setdefault(c.priority.value, []).append(c)
    for prio, pcases in sorted(by_priority.items()):
        lines.append(f"| {prio} | {len(pcases)} |")

    lines.append("")

    # --- Traceability Matrix ---
    lines.append("## Traceability Matrix")
    lines.append("")
    lines.append("| Story ID | Story Title | Unit | Integration | E2E |")
    lines.append("|----------|-------------|------|-------------|-----|")
    for story in stories:
        story_cases = [c for c in cases if c.source_story == story.id]
        u = sum(1 for c in story_cases if c.test_type == TestType.UNIT)
        i = sum(1 for c in story_cases if c.test_type == TestType.INTEGRATION)
        e = sum(1 for c in story_cases if c.test_type == TestType.E2E)
        lines.append(f"| {story.id} | {story.title[:50]} | {u} | {i} | {e} |")
    lines.append("")

    # --- Test Cases by Type ---
    for test_type in [TestType.UNIT, TestType.INTEGRATION, TestType.E2E]:
        type_cases = [c for c in cases if c.test_type == test_type]
        if not type_cases:
            continue

        lines.append(f"## {test_type.value} Tests")
        lines.append("")

        for tc in type_cases:
            lines.append(f"### {tc.id}: {tc.title}")
            lines.append("")
            lines.append(f"- **Priority:** {tc.priority.value}")
            lines.append(f"- **Source:** {tc.source_story}")
            lines.append(f"- **Tags:** {', '.join(tc.tags)}")
            lines.append("")

            if tc.preconditions:
                lines.append("**Preconditions:**")
                for pre in tc.preconditions:
                    lines.append(f"- {pre}")
                lines.append("")

            lines.append("**Steps:**")
            for j, step in enumerate(tc.steps, 1):
                lines.append(f"{j}. {step}")
            lines.append("")

            lines.append("**Expected Results:**")
            for er in tc.expected_results:
                lines.append(f"- {er}")
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a structured test plan from a Product Requirements Document.",
        epilog="Example: python test_planner.py --prd docs/prd.md --output docs/test-plan.md",
    )
    parser.add_argument(
        "--prd",
        required=True,
        type=Path,
        help="Path to the PRD markdown file",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output path for the test plan (default: stdout)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output test cases as JSON instead of markdown",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.prd.exists():
        print(f"ERROR: PRD file not found: {args.prd}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing PRD: {args.prd}", file=sys.stderr)
    stories = parse_prd(args.prd)
    print(f"Found {len(stories)} user stories", file=sys.stderr)

    cases = generate_test_cases(stories)
    print(f"Generated {len(cases)} test cases", file=sys.stderr)

    if args.json_output:
        output_data = []
        for tc in cases:
            d = asdict(tc)
            d["test_type"] = tc.test_type.value
            d["priority"] = tc.priority.value
            output_data.append(d)
        output = json.dumps(output_data, indent=2)
    else:
        output = render_test_plan(stories, cases)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Test plan written to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
