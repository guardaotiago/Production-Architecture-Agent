#!/usr/bin/env python3
"""Initialize SDLC tracking for a new or existing project.

Creates .sdlc/ directory with state tracking, phase checklists,
and optionally scaffolds from a project template.

Usage:
    python init_sdlc.py --project-name "My Project"
    python init_sdlc.py --project-name "My App" --template react-vite
    python init_sdlc.py --project-name "API" --template fastapi --output-dir ./my-api
    python init_sdlc.py --help
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TEMPLATES_DIR = REPO_ROOT / "templates"

PHASES = [
    {"id": "requirements", "name": "Requirements & Planning", "order": 1},
    {"id": "development", "name": "Development & Git", "order": 2},
    {"id": "cicd", "name": "CI/CD Pipeline", "order": 3},
    {"id": "testing", "name": "QA Testing", "order": 4},
    {"id": "uat", "name": "User Acceptance Testing", "order": 5},
    {"id": "deployment", "name": "Production Deployment", "order": 6},
    {"id": "monitoring", "name": "Monitoring & SRE", "order": 7},
]

TEMPLATE_MAP = {
    "react-vite": "react-typescript-vite",
    "react-typescript-vite": "react-typescript-vite",
    "fastapi": "python-fastapi",
    "python-fastapi": "python-fastapi",
    "nextjs": "nextjs-typescript",
    "nextjs-typescript": "nextjs-typescript",
}


def create_state(project_name: str) -> dict:
    """Create initial SDLC state."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "project_name": project_name,
        "created_at": now,
        "updated_at": now,
        "current_phase": "requirements",
        "phases": {
            phase["id"]: {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "gate_passed": False,
                "notes": [],
            }
            for phase in PHASES
        },
    }


def create_phase_checklist(phase: dict) -> str:
    """Generate a markdown checklist for a phase."""
    checklists = {
        "requirements": [
            "Define project vision and goals",
            "Identify stakeholders",
            "Write PRD (Product Requirements Document)",
            "Create user stories with acceptance criteria",
            "Assess technical feasibility",
            "Define success metrics",
            "Get stakeholder sign-off",
        ],
        "development": [
            "Set up repository and branching strategy",
            "Configure development environment",
            "Install pre-commit hooks",
            "Implement core features",
            "Write inline documentation",
            "Conduct code reviews",
            "Maintain clean commit history",
        ],
        "cicd": [
            "Set up CI pipeline (build + test)",
            "Configure linting and formatting checks",
            "Add security scanning (SAST)",
            "Set up artifact publishing",
            "Configure branch protection rules",
            "Add deployment pipeline",
            "Test pipeline end-to-end",
        ],
        "testing": [
            "Write unit tests (>80% coverage target)",
            "Write integration tests for critical paths",
            "Set up E2E test suite",
            "Run regression tests",
            "Conduct performance/load testing",
            "Fix all critical/high severity bugs",
            "Generate test coverage report",
        ],
        "uat": [
            "Create UAT test plan from user stories",
            "Set up UAT environment",
            "Brief stakeholders on testing scope",
            "Execute UAT test cases",
            "Collect and triage feedback",
            "Fix blocking issues",
            "Obtain stakeholder sign-off",
        ],
        "deployment": [
            "Create deployment runbook",
            "Set up feature flags (if applicable)",
            "Configure deployment strategy",
            "Run pre-deployment smoke tests",
            "Execute deployment",
            "Run post-deployment smoke tests",
            "Verify rollback procedure works",
        ],
        "monitoring": [
            "Set up application metrics",
            "Configure log aggregation",
            "Define SLOs and error budgets",
            "Create alerting rules",
            "Set up dashboards",
            "Document incident response procedure",
            "Conduct game day / chaos testing",
        ],
    }

    items = checklists.get(phase["id"], [])
    lines = [f"# Phase {phase['order']}: {phase['name']}\n"]
    for item in items:
        lines.append(f"- [ ] {item}")
    return "\n".join(lines) + "\n"


def init_sdlc(project_name: str, output_dir: Path, template: str | None = None):
    """Initialize SDLC tracking in the target directory."""
    sdlc_dir = output_dir / ".sdlc"

    if sdlc_dir.exists():
        print(f"⚠  .sdlc/ already exists in {output_dir}")
        print("   Use --force to reinitialize (preserves existing state)")
        sys.exit(1)

    # Create .sdlc directory
    sdlc_dir.mkdir(parents=True, exist_ok=True)
    (sdlc_dir / "phases").mkdir(exist_ok=True)

    # Write state file
    state = create_state(project_name)
    state_path = sdlc_dir / "state.json"
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)
    print(f"✓ Created {state_path}")

    # Write phase checklists
    for phase in PHASES:
        checklist_path = sdlc_dir / "phases" / f"{phase['order']:02d}-{phase['id']}.md"
        checklist_path.write_text(create_phase_checklist(phase))
        print(f"✓ Created {checklist_path.name}")

    # Copy template if specified
    if template:
        template_name = TEMPLATE_MAP.get(template)
        if not template_name:
            available = ", ".join(sorted(TEMPLATE_MAP.keys()))
            print(f"✗ Unknown template: {template}")
            print(f"  Available: {available}")
            sys.exit(1)

        template_dir = TEMPLATES_DIR / template_name
        if not template_dir.exists():
            print(f"✗ Template directory not found: {template_dir}")
            sys.exit(1)

        for item in template_dir.iterdir():
            dest = output_dir / item.name
            if dest.exists():
                print(f"  Skipping {item.name} (already exists)")
                continue
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
            print(f"✓ Copied template: {item.name}")

    print(f"\n🎯 SDLC initialized for '{project_name}'")
    print(f"   Current phase: requirements")
    print(f"   Next step: /plan {project_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize SDLC tracking for a project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --project-name "My Project"
  %(prog)s --project-name "My App" --template react-vite
  %(prog)s --project-name "API" --template fastapi --output-dir ./api

Available templates: react-vite, fastapi, nextjs
        """,
    )
    parser.add_argument(
        "--project-name", required=True, help="Name of the project"
    )
    parser.add_argument(
        "--template",
        choices=sorted(set(TEMPLATE_MAP.keys())),
        help="Project template to scaffold from",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to initialize (default: current directory)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reinitialize even if .sdlc/ exists",
    )

    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.force and (output_dir / ".sdlc").exists():
        shutil.rmtree(output_dir / ".sdlc")

    init_sdlc(args.project_name, output_dir, args.template)


if __name__ == "__main__":
    main()
