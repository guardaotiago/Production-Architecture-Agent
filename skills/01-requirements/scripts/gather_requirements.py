#!/usr/bin/env python3
"""
gather_requirements.py — Interactive requirement gathering for SDLC Orchestrator.

Usage:
    python gather_requirements.py --project "ProjectName"
    python gather_requirements.py --project "ProjectName" --non-interactive
    python gather_requirements.py --project "ProjectName" --output custom_path.md
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


QUESTIONS = {
    "problem_statement": {
        "prompt": "What problem does this project solve? What pain point are we addressing?",
        "placeholder": "[Describe the core problem this project aims to solve]",
        "required": True,
    },
    "target_users": {
        "prompt": "Who are the target users? Describe the primary and secondary audiences.",
        "placeholder": "[Describe who will use this and why they need it]",
        "required": True,
    },
    "core_features": {
        "prompt": "What are the core features? List the must-have capabilities (one per line).",
        "placeholder": "- [Feature 1]\n- [Feature 2]\n- [Feature 3]",
        "required": True,
        "multiline": True,
    },
    "non_goals": {
        "prompt": "What are the non-goals? What is explicitly out of scope?",
        "placeholder": "- [Non-goal 1]\n- [Non-goal 2]",
        "multiline": True,
    },
    "nfr_performance": {
        "prompt": "Performance requirements? (e.g., response time, throughput, concurrency)",
        "placeholder": "[e.g., API responses under 200ms at p95, support 1000 concurrent users]",
    },
    "nfr_security": {
        "prompt": "Security requirements? (e.g., auth, encryption, compliance)",
        "placeholder": "[e.g., OAuth 2.0, data encrypted at rest, GDPR compliant]",
    },
    "nfr_scalability": {
        "prompt": "Scalability requirements? (e.g., expected growth, data volume)",
        "placeholder": "[e.g., handle 10x growth in first year, store up to 1TB of data]",
    },
    "constraints_timeline": {
        "prompt": "Timeline constraints? When does this need to ship?",
        "placeholder": "[e.g., MVP in 4 weeks, full release in 8 weeks]",
    },
    "constraints_budget": {
        "prompt": "Budget or resource constraints?",
        "placeholder": "[e.g., 2 developers, no paid third-party services for MVP]",
    },
    "constraints_tech": {
        "prompt": "Technology constraints? (e.g., must use specific stack, integrate with existing systems)",
        "placeholder": "[e.g., Must use Python/FastAPI, must integrate with existing PostgreSQL database]",
    },
    "success_metrics": {
        "prompt": "How will you measure success? Define 2-4 key metrics.",
        "placeholder": "- [Metric 1: e.g., 80% user adoption in first month]\n- [Metric 2: e.g., 50% reduction in manual processing time]",
        "multiline": True,
    },
    "open_questions": {
        "prompt": "Any open questions or unknowns that need to be resolved?",
        "placeholder": "- [Question 1]\n- [Question 2]",
        "multiline": True,
    },
}


def ask_question(key: str, info: dict) -> str:
    """Ask a single question interactively and return the answer."""
    required_tag = " (required)" if info.get("required") else " (press Enter to skip)"
    print(f"\n{'=' * 60}")
    print(f"  {info['prompt']}{required_tag}")
    print(f"{'=' * 60}")

    if info.get("multiline"):
        print("  (Enter each item on a new line. Type 'done' on a blank line to finish.)")
        lines = []
        while True:
            line = input("  > ").strip()
            if line.lower() == "done" or (line == "" and lines):
                break
            if line:
                lines.append(line)
        answer = "\n".join(lines)
    else:
        answer = input("  > ").strip()

    if not answer and info.get("required"):
        print("  This field is required. Please provide an answer.")
        return ask_question(key, info)

    return answer if answer else info["placeholder"]


def gather_interactive(project_name: str) -> dict:
    """Run interactive requirement gathering session."""
    print(f"\n{'#' * 60}")
    print(f"  Requirements Gathering: {project_name}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'#' * 60}")
    print("\nAnswer each question to build your requirements document.")
    print("For multiline answers, type 'done' on a blank line to finish.\n")

    answers = {}
    for key, info in QUESTIONS.items():
        answers[key] = ask_question(key, info)

    return answers


def gather_non_interactive() -> dict:
    """Return blank template answers (placeholders)."""
    return {key: info["placeholder"] for key, info in QUESTIONS.items()}


def format_requirements(project_name: str, answers: dict) -> str:
    """Format gathered requirements into a markdown document."""
    date_str = datetime.now().strftime("%Y-%m-%d")

    doc = f"""# Requirements: {project_name}

> Generated on {date_str} by SDLC Orchestrator Phase 1

---

## 1. Problem Statement

{answers['problem_statement']}

## 2. Target Users

{answers['target_users']}

## 3. Core Features

{answers['core_features']}

## 4. Non-Goals (Out of Scope)

{answers.get('non_goals', 'TBD')}

## 5. Non-Functional Requirements

### Performance
{answers.get('nfr_performance', 'TBD')}

### Security
{answers.get('nfr_security', 'TBD')}

### Scalability
{answers.get('nfr_scalability', 'TBD')}

## 6. Constraints

### Timeline
{answers.get('constraints_timeline', 'TBD')}

### Budget / Resources
{answers.get('constraints_budget', 'TBD')}

### Technology
{answers.get('constraints_tech', 'TBD')}

## 7. Success Metrics

{answers.get('success_metrics', 'TBD')}

## 8. Open Questions

{answers.get('open_questions', 'None identified yet.')}

---

## Next Steps
1. Draft the PRD using `skills/01-requirements/reference/prd_template.md`
2. Define user stories following `skills/01-requirements/reference/user_story_guide.md`
3. Validate with `python skills/01-requirements/scripts/validate_prd.py --file docs/prd.md`
"""
    return doc


def main():
    parser = argparse.ArgumentParser(
        description="Gather project requirements interactively.",
        epilog="Example: python gather_requirements.py --project 'My App'",
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Name of the project to gather requirements for.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Output a blank template instead of running the interactive session.",
    )
    parser.add_argument(
        "--output",
        default="docs/requirements.md",
        help="Output file path (default: docs/requirements.md).",
    )

    args = parser.parse_args()

    if args.non_interactive:
        print(f"Generating blank requirements template for '{args.project}'...")
        answers = gather_non_interactive()
    else:
        answers = gather_interactive(args.project)

    document = format_requirements(args.project, answers)

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(document, encoding="utf-8")
    print(f"\nRequirements saved to: {output_path}")
    print(f"Next step: Draft a PRD using the template in reference/prd_template.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
