#!/usr/bin/env python3
"""Validate phase exit criteria before advancing to the next SDLC phase.

Checks that required artifacts exist, quality thresholds are met,
and mandatory sign-offs are recorded.

Usage:
    python gate_validator.py --phase requirements
    python gate_validator.py --phase development --project-dir /path/to/project
    python gate_validator.py --all
    python gate_validator.py --help
"""

import argparse
import json
import sys
from pathlib import Path

PHASE_ORDER = [
    "requirements",
    "development",
    "cicd",
    "testing",
    "uat",
    "deployment",
    "monitoring",
]

# Gate criteria: list of (description, check_function_name)
GATE_CRITERIA = {
    "requirements": [
        ("PRD document exists", "check_file", "docs/prd.md"),
        ("User stories defined", "check_file_pattern", "docs/user-stories*"),
        ("Acceptance criteria present in PRD", "check_content", "docs/prd.md", "acceptance criteria"),
        ("Technical feasibility assessed", "check_file_pattern", "docs/tech-feasibility*"),
        ("Stakeholder sign-off recorded", "check_state_note", "requirements", "sign-off"),
    ],
    "development": [
        ("Git repository initialized", "check_dir", ".git"),
        ("Branching strategy documented", "check_file_pattern", "*git*workflow*"),
        ("Pre-commit hooks configured", "check_file", ".pre-commit-config.yaml"),
        ("README exists", "check_file", "README.md"),
        ("Code review process defined", "check_state_note", "development", "code review"),
    ],
    "cicd": [
        ("CI pipeline config exists", "check_any_file", [
            ".github/workflows/*.yml",
            ".github/workflows/*.yaml",
            ".gitlab-ci.yml",
            "Jenkinsfile",
        ]),
        ("Build step defined", "check_state_note", "cicd", "build"),
        ("Test step in pipeline", "check_state_note", "cicd", "test"),
        ("Linting configured", "check_any_file", [
            ".eslintrc*", ".flake8", "pyproject.toml", ".prettierrc*",
        ]),
        ("Pipeline tested end-to-end", "check_state_note", "cicd", "verified"),
    ],
    "testing": [
        ("Unit tests exist", "check_file_pattern", "*test*"),
        ("Test coverage report generated", "check_any_file", [
            "coverage/*", "htmlcov/*", ".coverage",
        ]),
        ("Coverage meets threshold (>80%)", "check_state_note", "testing", "coverage"),
        ("Critical bugs resolved", "check_state_note", "testing", "bugs resolved"),
        ("Test plan documented", "check_file_pattern", "docs/test-plan*"),
    ],
    "uat": [
        ("UAT plan created", "check_file_pattern", "docs/uat*"),
        ("UAT environment available", "check_state_note", "uat", "environment"),
        ("All UAT cases executed", "check_state_note", "uat", "executed"),
        ("Stakeholder sign-off obtained", "check_state_note", "uat", "sign-off"),
    ],
    "deployment": [
        ("Deployment runbook exists", "check_file_pattern", "docs/deployment*"),
        ("Rollback procedure documented", "check_file_pattern", "docs/rollback*"),
        ("Smoke tests defined", "check_file_pattern", "*smoke*"),
        ("Deployment strategy chosen", "check_state_note", "deployment", "strategy"),
        ("Pre-deployment checklist complete", "check_state_note", "deployment", "checklist"),
    ],
    "monitoring": [
        ("Monitoring configured", "check_state_note", "monitoring", "configured"),
        ("Alerts defined", "check_file_pattern", "*alert*"),
        ("SLOs documented", "check_file_pattern", "docs/slo*"),
        ("Incident response plan exists", "check_file_pattern", "docs/incident*"),
        ("Dashboard created", "check_state_note", "monitoring", "dashboard"),
    ],
}


def load_state(project_dir: Path) -> dict | None:
    """Load SDLC state from project directory."""
    state_path = project_dir / ".sdlc" / "state.json"
    if not state_path.exists():
        return None
    with open(state_path) as f:
        return json.load(f)


def check_file(project_dir: Path, filepath: str) -> bool:
    """Check if a specific file exists."""
    return (project_dir / filepath).exists()


def check_dir(project_dir: Path, dirpath: str) -> bool:
    """Check if a directory exists."""
    return (project_dir / dirpath).is_dir()


def check_file_pattern(project_dir: Path, pattern: str) -> bool:
    """Check if any file matches a glob pattern."""
    return len(list(project_dir.rglob(pattern))) > 0


def check_any_file(project_dir: Path, patterns: list[str]) -> bool:
    """Check if any file matches any of the given patterns."""
    return any(check_file_pattern(project_dir, p) for p in patterns)


def check_content(project_dir: Path, filepath: str, keyword: str) -> bool:
    """Check if a file contains a keyword (case-insensitive)."""
    target = project_dir / filepath
    if not target.exists():
        return False
    return keyword.lower() in target.read_text().lower()


def check_state_note(project_dir: Path, phase: str, keyword: str) -> bool:
    """Check if a phase has a note containing the keyword."""
    state = load_state(project_dir)
    if not state:
        return False
    phase_data = state.get("phases", {}).get(phase, {})
    notes = phase_data.get("notes", [])
    return any(keyword.lower() in note.lower() for note in notes)


CHECKERS = {
    "check_file": lambda pd, args: check_file(pd, args[0]),
    "check_dir": lambda pd, args: check_dir(pd, args[0]),
    "check_file_pattern": lambda pd, args: check_file_pattern(pd, args[0]),
    "check_any_file": lambda pd, args: check_any_file(pd, args[0]),
    "check_content": lambda pd, args: check_content(pd, args[0], args[1]),
    "check_state_note": lambda pd, args: check_state_note(pd, args[0], args[1]),
}


def validate_phase(phase: str, project_dir: Path) -> tuple[list, list]:
    """Validate all gate criteria for a phase. Returns (passed, failed) lists."""
    criteria = GATE_CRITERIA.get(phase, [])
    passed = []
    failed = []

    for criterion in criteria:
        description = criterion[0]
        checker_name = criterion[1]
        checker_args = criterion[2:]
        checker = CHECKERS.get(checker_name)

        if checker and checker(project_dir, checker_args):
            passed.append(description)
        else:
            failed.append(description)

    return passed, failed


def print_gate_result(phase: str, passed: list, failed: list):
    """Print formatted gate validation results."""
    total = len(passed) + len(failed)
    print(f"\n{'='*50}")
    print(f"Phase Gate: {phase.upper()}")
    print(f"{'='*50}\n")

    for item in passed:
        print(f"  ✓ {item}")
    for item in failed:
        print(f"  ✗ {item}")

    print(f"\n  Result: {len(passed)}/{total} criteria met")

    if failed:
        print(f"  Status: ❌ BLOCKED")
        print(f"\n  Fix the {len(failed)} failing criteria before advancing.")
    else:
        print(f"  Status: ✅ PASSED")
        idx = PHASE_ORDER.index(phase)
        if idx < len(PHASE_ORDER) - 1:
            next_phase = PHASE_ORDER[idx + 1]
            print(f"\n  Ready to advance to: {next_phase}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Validate SDLC phase exit criteria",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --phase requirements
  %(prog)s --phase development --project-dir /path/to/project
  %(prog)s --all

Phases: requirements, development, cicd, testing, uat, deployment, monitoring
        """,
    )
    parser.add_argument(
        "--phase",
        choices=PHASE_ORDER,
        help="Phase to validate",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all phases",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    if not args.phase and not args.all:
        parser.error("Specify --phase or --all")

    project_dir = args.project_dir.resolve()
    phases_to_check = PHASE_ORDER if args.all else [args.phase]

    all_results = {}
    overall_pass = True

    for phase in phases_to_check:
        passed, failed = validate_phase(phase, project_dir)
        all_results[phase] = {"passed": passed, "failed": failed}
        if failed:
            overall_pass = False

        if not args.json_output:
            print_gate_result(phase, passed, failed)

    if args.json_output:
        print(json.dumps(all_results, indent=2))

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
