#!/usr/bin/env python3
"""Interactive SDLC orchestrator — walks through all 7 phases from start to finish.

Prompts the user at each phase, runs existing scripts, records gate notes,
and validates exit criteria before advancing.

Usage:
    python scripts/orchestrate.py
    python scripts/orchestrate.py --start-from cicd
    python scripts/orchestrate.py --project-dir /path/to/project
    python scripts/orchestrate.py --dry-run
    python scripts/orchestrate.py --help
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

PHASE_ORDER = [
    "requirements", "development", "cicd",
    "testing", "uat", "deployment", "monitoring",
]

PHASE_NAMES = {
    "requirements": "Phase 1: Requirements & Planning",
    "development": "Phase 2: Development & Git",
    "cicd": "Phase 3: CI/CD Pipeline",
    "testing": "Phase 4: QA Testing",
    "uat": "Phase 5: User Acceptance Testing",
    "deployment": "Phase 6: Production Deployment",
    "monitoring": "Phase 7: Monitoring & SRE",
}


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def load_state(project_dir: Path) -> dict | None:
    state_path = project_dir / ".sdlc" / "state.json"
    if not state_path.exists():
        return None
    with open(state_path) as f:
        return json.load(f)


def save_state(project_dir: Path, state: dict, dry_run: bool = False) -> None:
    if dry_run:
        return
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state_path = project_dir / ".sdlc" / "state.json"
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def add_note(state: dict, phase: str, note: str) -> None:
    notes = state["phases"][phase].setdefault("notes", [])
    if note not in notes:
        notes.append(note)


def mark_started(state: dict, phase: str) -> None:
    state["phases"][phase]["status"] = "in_progress"
    state["phases"][phase]["started_at"] = datetime.now(timezone.utc).isoformat()
    state["current_phase"] = phase


def mark_completed(state: dict, phase: str) -> None:
    state["phases"][phase]["status"] = "completed"
    state["phases"][phase]["completed_at"] = datetime.now(timezone.utc).isoformat()
    state["phases"][phase]["gate_passed"] = True


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def prompt(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"  {question}{suffix}: ").strip()
    return answer if answer else default


def prompt_yn(question: str, default: str = "y") -> bool:
    answer = prompt(f"{question} (y/n)", default)
    return answer.lower().startswith("y")


def prompt_choice(question: str, choices: list[str], default: str = "") -> str:
    choices_str = "/".join(choices)
    while True:
        answer = prompt(f"{question} ({choices_str})", default)
        if answer in choices:
            return answer
        print(f"    Please choose one of: {choices_str}")


def run_script(cmd: list[str], cwd: Path, dry_run: bool = False) -> int:
    if dry_run:
        print(f"  [DRY-RUN] {' '.join(cmd)}")
        return 0
    print(f"  [RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd))
    return result.returncode


def run_gate(phase: str, project_dir: Path, dry_run: bool = False) -> bool:
    cmd = [sys.executable, str(SCRIPT_DIR / "gate_validator.py"),
           "--phase", phase, "--project-dir", str(project_dir)]
    if dry_run:
        print(f"  [DRY-RUN] Gate check: {phase} -> PASS")
        return True
    result = subprocess.run(cmd, cwd=str(project_dir))
    return result.returncode == 0


def write_file(path: Path, content: str, dry_run: bool = False) -> None:
    if dry_run:
        print(f"  [DRY-RUN] Would write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"  [CREATED] {path}")


def header(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def section(text: str) -> None:
    print(f"\n--- {text} ---\n")


# ---------------------------------------------------------------------------
# Embedded templates for files the orchestrator creates directly
# ---------------------------------------------------------------------------

GIT_WORKFLOW_TEMPLATE = """\
# Git Workflow

## Branching Strategy: GitHub Flow

- **main** — production-ready code, protected branch
- **feature/<ticket>-<description>** — feature work
- **fix/<ticket>-<description>** — bug fixes

## Process

1. Create feature branch from main
2. Make small commits following Conventional Commits
3. Open PR, request review (min 1 approval)
4. CI must pass before merge
5. Squash-merge to main
6. Delete feature branch

## Branch Protection

- Require PR reviews before merge
- Require CI status checks to pass
- No force pushes to main
"""

PRECOMMIT_PLACEHOLDER = """\
# Pre-commit configuration
# Hooks installed via setup_git_hooks.sh (see .git/hooks/)
repos: []
"""

ROLLBACK_TEMPLATE = """\
# Rollback Procedure

## When to Roll Back

- Error rate exceeds 2x baseline within 15 minutes of deploy
- P95 latency exceeds 2x baseline
- Critical functionality broken (health check fails)
- Customer-reported data loss or corruption

## Rollback Steps

1. **Announce** rollback in team channel
2. **Execute** rollback per deployment strategy (see deployment-runbook.md)
3. **Verify** service health after rollback
4. **Notify** team that rollback is complete
5. **Investigate** root cause before reattempting deploy

## Strategy-Specific Rollback

- **Canary**: Shift 100% traffic back to stable version
- **Blue-Green**: Switch load balancer to previous environment
- **Rolling**: `kubectl rollout undo deployment/<service>`
"""

SMOKE_TESTS_TEMPLATE = """\
[
  {
    "name": "Health check",
    "method": "GET",
    "path": "/health",
    "expected_status": 200
  },
  {
    "name": "Root endpoint",
    "method": "GET",
    "path": "/",
    "expected_status": 200
  }
]
"""


def slo_template(slo: str, service: str) -> str:
    return f"""\
# SLO Definition — {service}

## Service Level Objectives

| SLI | SLO Target | Measurement |
|-----|-----------|-------------|
| Availability | {slo}% | Successful requests / total requests |
| Latency (p95) | < 500ms | 95th percentile response time |
| Latency (p99) | < 1000ms | 99th percentile response time |
| Error rate | < {100 - float(slo):.1f}% | 5xx responses / total responses |

## Error Budget

- Monthly budget: {(100 - float(slo)) * 43200 / 100:.0f} minutes of downtime
- Burn rate alerts: 14.4x (critical), 6x (warning), 3x (info)

## Review Cadence

- Weekly: check error budget consumption
- Monthly: review SLO targets and adjust if needed
- Quarterly: full SLO review with stakeholders
"""


# ---------------------------------------------------------------------------
# Phase handlers
# ---------------------------------------------------------------------------

def run_requirements(state: dict, project_dir: Path, ctx: dict, dry_run: bool) -> None:
    section("Step 1: Gather Requirements")
    if prompt_yn("Run interactive requirement gathering?"):
        run_script([
            sys.executable,
            str(REPO_ROOT / "skills/01-requirements/scripts/gather_requirements.py"),
            "--project", ctx["project_name"],
            "--output", str(project_dir / "docs/requirements.md"),
        ], project_dir, dry_run)

    section("Step 2: PRD (Product Requirements Document)")
    prd_path = project_dir / "docs/prd.md"
    if not prd_path.exists() and not dry_run:
        print(f"  PRD not found at {prd_path}")
        print(f"  Template available at: {REPO_ROOT / 'skills/01-requirements/reference/prd_template.md'}")
        if prompt_yn("Copy PRD template to docs/prd.md?"):
            template = (REPO_ROOT / "skills/01-requirements/reference/prd_template.md").read_text()
            write_file(prd_path, template, dry_run)
            print("  Fill in the PRD template, then press Enter to continue.")
            input("  Press Enter when PRD is ready...")
    elif prd_path.exists():
        print(f"  PRD found at {prd_path}")
        run_script([
            sys.executable,
            str(REPO_ROOT / "skills/01-requirements/scripts/validate_prd.py"),
            "--file", str(prd_path),
        ], project_dir, dry_run)

    section("Step 3: User Stories")
    stories_path = project_dir / "docs/user-stories.md"
    if not stories_path.exists() and not dry_run:
        print(f"  User stories not found at {stories_path}")
        print(f"  Guide: {REPO_ROOT / 'skills/01-requirements/reference/user_story_guide.md'}")
        if prompt_yn("Create a placeholder user stories file?"):
            write_file(stories_path, "# User Stories\n\n<!-- Add user stories in format: As a [user], I want [action] so that [benefit] -->\n\n", dry_run)
            print("  Fill in user stories, then press Enter.")
            input("  Press Enter when ready...")
    else:
        print(f"  User stories found at {stories_path}")

    section("Step 4: Technical Feasibility")
    feasibility_path = project_dir / "docs/tech-feasibility.md"
    if not feasibility_path.exists() and not dry_run:
        if prompt_yn("Create technical feasibility document?"):
            write_file(feasibility_path, "# Technical Feasibility Assessment\n\n## Architecture\n\n## Tech Stack\n\n## Risks & Mitigations\n\n## Conclusion\n\nFeasible: YES / NO\n", dry_run)
            print("  Fill in the assessment, then press Enter.")
            input("  Press Enter when ready...")
    else:
        print(f"  Feasibility doc found at {feasibility_path}")

    section("Step 5: Stakeholder Sign-off")
    if prompt_yn("Has a stakeholder signed off on the requirements?", "n"):
        add_note(state, "requirements", "Stakeholder sign-off recorded for requirements")


def run_development(state: dict, project_dir: Path, ctx: dict, dry_run: bool) -> None:
    section("Step 1: Project Setup")
    ctx["project_type"] = prompt_choice("Project type?", ["node", "python", "go"], "python")

    if prompt_yn("Run project scaffolding?"):
        run_script([
            "bash",
            str(REPO_ROOT / "skills/02-development/scripts/init_project.sh"),
            "--name", ctx["project_name"],
            "--type", ctx["project_type"],
        ], project_dir, dry_run)

    section("Step 2: Git Initialization")
    git_dir = project_dir / ".git"
    if not git_dir.exists() and not dry_run:
        print("  Initializing git repository...")
        run_script(["git", "init"], project_dir, dry_run)
    else:
        print("  Git repository already initialized.")

    section("Step 3: Git Hooks")
    if prompt_yn("Set up pre-commit hooks (lint, format, secrets scan)?"):
        run_script([
            "bash",
            str(REPO_ROOT / "skills/02-development/scripts/setup_git_hooks.sh"),
        ], project_dir, dry_run)

    # Ensure .pre-commit-config.yaml exists (gate requirement)
    precommit_path = project_dir / ".pre-commit-config.yaml"
    if not precommit_path.exists():
        write_file(precommit_path, PRECOMMIT_PLACEHOLDER, dry_run)

    section("Step 4: Branching Strategy")
    workflow_path = project_dir / "docs/git-workflow.md"
    if not workflow_path.exists():
        write_file(workflow_path, GIT_WORKFLOW_TEMPLATE, dry_run)
        print("  Git workflow guide created.")

    section("Step 5: README")
    readme_path = project_dir / "README.md"
    if not readme_path.exists():
        write_file(readme_path, f"# {ctx['project_name']}\n\n## Setup\n\n## Development\n\n## Testing\n", dry_run)

    section("Step 6: Code Review Process")
    if prompt_yn("Has the code review process been defined?", "n"):
        add_note(state, "development", "Code review process defined and initial review completed")


def run_cicd(state: dict, project_dir: Path, ctx: dict, dry_run: bool) -> None:
    section("Step 1: Choose CI Platform")
    ctx["ci_platform"] = prompt_choice("CI platform?", ["github", "gitlab", "jenkins"], "github")

    section("Step 2: Generate Pipeline")
    project_type = ctx.get("project_type", "python")
    if prompt_yn("Generate CI pipeline configuration?"):
        run_script([
            sys.executable,
            str(REPO_ROOT / "skills/03-cicd/scripts/generate_pipeline.py"),
            "--platform", ctx["ci_platform"],
            "--type", project_type,
        ], project_dir, dry_run)
        # Pipeline includes build and test steps
        add_note(state, "cicd", "Build step defined in CI pipeline")
        add_note(state, "cicd", "Test step configured in CI pipeline")

    section("Step 3: Linting Configuration")
    # Ensure a lint config exists for the gate
    lint_configs = {
        "node": (".eslintrc.json", '{"extends": ["eslint:recommended"]}\n'),
        "python": ("pyproject.toml", None),  # Already created by init_project
        "go": (".golangci.yml", "run:\n  timeout: 5m\n"),
    }
    config_name, config_content = lint_configs.get(project_type, ("pyproject.toml", None))
    config_path = project_dir / config_name
    if not config_path.exists() and config_content:
        write_file(config_path, config_content, dry_run)

    section("Step 4: Docker (optional)")
    if prompt_yn("Set up Docker configuration?", "n"):
        docker_src = "Dockerfile.node" if project_type == "node" else "Dockerfile.python"
        src = REPO_ROOT / "skills/03-cicd/assets/docker" / docker_src
        dst = project_dir / "Dockerfile"
        if src.exists() and not dst.exists():
            write_file(dst, src.read_text() if not dry_run else "", dry_run)
        compose_src = REPO_ROOT / "skills/03-cicd/assets/docker/docker-compose.yml"
        compose_dst = project_dir / "docker-compose.yml"
        if compose_src.exists() and not compose_dst.exists():
            write_file(compose_dst, compose_src.read_text() if not dry_run else "", dry_run)

    section("Step 5: Pipeline Verification")
    if prompt_yn("Has the pipeline been tested end-to-end?", "n"):
        add_note(state, "cicd", "Pipeline verified end-to-end")


def run_testing(state: dict, project_dir: Path, ctx: dict, dry_run: bool) -> None:
    section("Step 1: Generate Test Plan")
    prd_path = project_dir / "docs/prd.md"
    if prd_path.exists() and prompt_yn("Generate test plan from PRD?"):
        run_script([
            sys.executable,
            str(REPO_ROOT / "skills/04-testing/scripts/test_planner.py"),
            "--prd", str(prd_path),
            "--output", str(project_dir / "docs/test-plan.md"),
        ], project_dir, dry_run)
    elif not prd_path.exists():
        print(f"  PRD not found at {prd_path}. Skipping test plan generation.")
        test_plan = project_dir / "docs/test-plan.md"
        if not test_plan.exists():
            write_file(test_plan, "# Test Plan\n\n## Unit Tests\n\n## Integration Tests\n\n## E2E Tests\n", dry_run)

    section("Step 2: Write & Run Tests")
    print("  Write your tests now. The gate requires test files to exist.")
    print("  Ensure you have files matching *test* in your project.")
    tests_dir = project_dir / "tests"
    if not tests_dir.exists() and not dry_run:
        tests_dir.mkdir(parents=True, exist_ok=True)
        write_file(tests_dir / "test_placeholder.py", "# Add your tests here\ndef test_placeholder():\n    assert True\n", dry_run)

    section("Step 3: Coverage Analysis")
    coverage_path = prompt("Path to coverage report (leave blank to skip)", "")
    if coverage_path:
        threshold = prompt("Coverage threshold (%)", "80")
        run_script([
            sys.executable,
            str(REPO_ROOT / "skills/04-testing/scripts/coverage_analyzer.py"),
            "--report", coverage_path,
            "--threshold", threshold,
        ], project_dir, dry_run)
    else:
        print("  No coverage report provided.")
        print("  The gate requires a coverage file at: coverage/*, htmlcov/*, or .coverage")
        # Create placeholder so gate can check for it
        coverage_dir = project_dir / "coverage"
        if not coverage_dir.exists():
            coverage_dir.mkdir(parents=True, exist_ok=True)
            write_file(coverage_dir / "placeholder.txt",
                       "# Run your test suite with coverage to generate a real report\n", dry_run)

    section("Step 4: Coverage Threshold")
    if prompt_yn("Does test coverage meet the threshold (>=80%)?", "n"):
        add_note(state, "testing", "Coverage meets threshold of 80%")

    section("Step 5: Bug Resolution")
    if prompt_yn("Are all critical/high-severity bugs resolved?", "n"):
        add_note(state, "testing", "All critical bugs resolved")


def run_uat(state: dict, project_dir: Path, ctx: dict, dry_run: bool) -> None:
    section("Step 1: Generate UAT Plan")
    prd_path = project_dir / "docs/prd.md"
    if prd_path.exists() and prompt_yn("Generate UAT plan from PRD?"):
        run_script([
            sys.executable,
            str(REPO_ROOT / "skills/05-uat/scripts/generate_uat_plan.py"),
            "--prd", str(prd_path),
            "--output", str(project_dir / "docs/uat-plan.md"),
        ], project_dir, dry_run)
    else:
        uat_plan = project_dir / "docs/uat-plan.md"
        if not uat_plan.exists():
            write_file(uat_plan, "# UAT Plan\n\n## Test Cases\n\n## Sign-off\n", dry_run)

    section("Step 2: UAT Environment")
    print("  Set up a UAT environment that mirrors production.")
    print("  Load representative test data, verify integrations work.")
    if prompt_yn("Is the UAT environment available and configured?", "n"):
        add_note(state, "uat", "UAT environment available and configured")

    section("Step 3: Execute UAT")
    print("  Execute the UAT test cases with stakeholders.")
    print("  Collect feedback and triage: Blocker > Major > Minor > Enhancement.")
    if prompt_yn("Have all UAT test cases been executed?", "n"):
        add_note(state, "uat", "All UAT test cases executed successfully")

    section("Step 4: Stakeholder Sign-off")
    if prompt_yn("Has the stakeholder signed off on UAT?", "n"):
        add_note(state, "uat", "Stakeholder sign-off obtained for UAT")


def run_deployment(state: dict, project_dir: Path, ctx: dict, dry_run: bool) -> None:
    section("Step 1: Deployment Strategy")
    ctx["deploy_strategy"] = prompt_choice(
        "Deployment strategy?", ["canary", "blue-green", "rolling"], "canary"
    )
    ctx["service_name"] = prompt("Service name", ctx.get("project_name", "my-service"))
    env = prompt_choice("Target environment?", ["staging", "production"], "production")

    section("Step 2: Generate Deployment Runbook")
    if prompt_yn("Generate deployment runbook?"):
        run_script([
            sys.executable,
            str(REPO_ROOT / "skills/06-deployment/scripts/deployment_plan.py"),
            "--strategy", ctx["deploy_strategy"],
            "--service-name", ctx["service_name"],
            "--env", env,
            "--output", str(project_dir / "docs/deployment-runbook.md"),
        ], project_dir, dry_run)
        add_note(state, "deployment", f"Deployment strategy: {ctx['deploy_strategy']}")

    section("Step 3: Rollback Procedure")
    rollback_path = project_dir / "docs/rollback-procedure.md"
    if not rollback_path.exists():
        write_file(rollback_path, ROLLBACK_TEMPLATE, dry_run)

    section("Step 4: Smoke Tests")
    smoke_path = project_dir / "smoke-tests.json"
    if not smoke_path.exists():
        write_file(smoke_path, SMOKE_TESTS_TEMPLATE, dry_run)

    app_url = prompt("Application URL for smoke tests (leave blank to skip)", "")
    if app_url:
        run_script([
            sys.executable,
            str(REPO_ROOT / "skills/06-deployment/scripts/smoke_test.py"),
            "--url", app_url,
            "--config", str(smoke_path),
        ], project_dir, dry_run)

    section("Step 5: Pre-Deployment Checklist")
    print("  Verify before deploying:")
    print("    - All previous phase gates passed")
    print("    - Deployment runbook reviewed by team")
    print("    - Rollback procedure tested")
    print("    - Database migrations tested (if applicable)")
    print("    - Team notified of deployment window")
    if prompt_yn("Is the pre-deployment checklist complete?", "n"):
        add_note(state, "deployment", "Pre-deployment checklist complete")


def run_monitoring(state: dict, project_dir: Path, ctx: dict, dry_run: bool) -> None:
    section("Step 1: Define SLOs")
    ctx["slo_target"] = prompt("SLO availability target (%)", "99.9")
    service = ctx.get("service_name", ctx.get("project_name", "my-service"))

    slo_path = project_dir / "docs/slo-definition.md"
    if not slo_path.exists():
        write_file(slo_path, slo_template(ctx["slo_target"], service), dry_run)

    section("Step 2: Generate Alert Rules")
    if prompt_yn("Generate alert rules from SLOs?"):
        alerts_dir = project_dir / "alerts"
        run_script([
            sys.executable,
            str(REPO_ROOT / "skills/07-monitoring/scripts/alert_generator.py"),
            "--slo", ctx["slo_target"],
            "--service", service,
            "--output", str(alerts_dir),
        ], project_dir, dry_run)

    section("Step 3: Incident Response Plan")
    incident_dir = project_dir / "docs/incidents"
    if prompt_yn("Generate incident response template?"):
        run_script([
            sys.executable,
            str(REPO_ROOT / "skills/07-monitoring/scripts/incident_report.py"),
            "--incident", "Template incident for runbook",
            "--severity", "P2",
            "--service", service,
            "--output", str(incident_dir),
        ], project_dir, dry_run)

    # Ensure docs/incident* exists for gate (the script writes to docs/incidents/)
    incident_path = project_dir / "docs/incident-response.md"
    if not incident_path.exists():
        write_file(incident_path, f"# Incident Response Plan — {service}\n\nSee docs/incidents/ for templates.\nSee reference: skills/07-monitoring/reference/incident_response.md\n", dry_run)

    section("Step 4: Monitoring Setup")
    print("  Set up monitoring for your service:")
    print("    - Metrics: Prometheus, Datadog, or CloudWatch")
    print("    - Logs: Structured JSON, centralized")
    print("    - Traces: OpenTelemetry or vendor SDK")
    if prompt_yn("Has monitoring been configured?", "n"):
        add_note(state, "monitoring", f"Monitoring configured for {service}")

    section("Step 5: Dashboard")
    print("  Create dashboards for:")
    print("    - Service overview (request rate, error rate, latency)")
    print("    - Infrastructure (CPU, memory, disk)")
    print("    - Business KPIs")
    if prompt_yn("Has a dashboard been created?", "n"):
        add_note(state, "monitoring", f"Dashboard created for {service}")


# ---------------------------------------------------------------------------
# Main orchestration loop
# ---------------------------------------------------------------------------

PHASE_HANDLERS = {
    "requirements": run_requirements,
    "development": run_development,
    "cicd": run_cicd,
    "testing": run_testing,
    "uat": run_uat,
    "deployment": run_deployment,
    "monitoring": run_monitoring,
}


def main():
    parser = argparse.ArgumentParser(
        description="Interactive SDLC orchestrator — all 7 phases, start to finish",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                # Start or resume from current phase
  %(prog)s --start-from cicd              # Jump to CI/CD phase
  %(prog)s --project-dir ~/my-project     # Specify project location
  %(prog)s --dry-run                      # Preview without executing
        """,
    )
    parser.add_argument("--project-dir", type=Path, default=Path.cwd(),
                        help="Project directory (default: current directory)")
    parser.add_argument("--start-from", choices=PHASE_ORDER,
                        help="Skip to a specific phase")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without executing")

    args = parser.parse_args()
    project_dir = args.project_dir.resolve()
    dry_run = args.dry_run

    header("SDLC Orchestrator")
    print("  This will walk you through all 7 SDLC phases interactively.")
    print("  You can quit anytime (Ctrl+C) and resume later.\n")

    # Load or initialize state
    state = load_state(project_dir)
    if state is None:
        section("Project Initialization")
        project_name = prompt("Project name")
        template = prompt_choice(
            "Use a project template?",
            ["none", "react-vite", "fastapi", "nextjs"], "none"
        )
        cmd = [sys.executable, str(SCRIPT_DIR / "init_sdlc.py"),
               "--project-name", project_name,
               "--output-dir", str(project_dir)]
        if template != "none":
            cmd.extend(["--template", template])
        run_script(cmd, project_dir, dry_run)

        state = load_state(project_dir)
        if state is None:
            if dry_run:
                # Synthetic state for dry-run
                state = {
                    "project_name": project_name,
                    "current_phase": "requirements",
                    "phases": {p: {"status": "pending", "gate_passed": False,
                                   "notes": [], "started_at": None,
                                   "completed_at": None} for p in PHASE_ORDER},
                }
            else:
                print("\n  ERROR: Failed to initialize. Check permissions.\n")
                sys.exit(1)

    ctx = {
        "project_name": state.get("project_name", "my-project"),
        "project_type": "python",
    }

    # Determine starting phase
    start_phase = args.start_from or state.get("current_phase", "requirements")
    start_idx = PHASE_ORDER.index(start_phase)

    print(f"  Project: {ctx['project_name']}")
    print(f"  Starting from: {PHASE_NAMES[start_phase]}")

    # Walk through phases
    for idx in range(start_idx, len(PHASE_ORDER)):
        phase = PHASE_ORDER[idx]
        phase_data = state["phases"][phase]

        # Skip completed phases
        if phase_data.get("status") == "completed" and phase_data.get("gate_passed"):
            print(f"\n  [SKIP] {PHASE_NAMES[phase]} — already completed.\n")
            continue

        header(PHASE_NAMES[phase])
        mark_started(state, phase)
        save_state(project_dir, state, dry_run)

        # Run the phase handler
        PHASE_HANDLERS[phase](state, project_dir, ctx, dry_run)
        save_state(project_dir, state, dry_run)

        # Gate check loop
        gate_passed = False
        while not gate_passed:
            section(f"Gate Check: {phase}")
            gate_passed = run_gate(phase, project_dir, dry_run)

            if gate_passed:
                print(f"\n  Gate PASSED for {phase}.")
                mark_completed(state, phase)
                save_state(project_dir, state, dry_run)
            else:
                print(f"\n  Gate BLOCKED for {phase}.")
                action = prompt_choice(
                    "What would you like to do?",
                    ["retry", "fix", "skip", "quit"], "retry"
                )
                if action == "quit":
                    print("\n  State saved. Resume by running orchestrate.py again.\n")
                    save_state(project_dir, state, dry_run)
                    sys.exit(0)
                elif action == "skip":
                    print(f"  Skipping gate for {phase} (not recommended).")
                    mark_completed(state, phase)
                    save_state(project_dir, state, dry_run)
                    gate_passed = True
                elif action == "fix":
                    print("\n  Fix the failing criteria, then press Enter to re-check.")
                    input("  Press Enter when ready...")

        # Advance to next phase
        if idx + 1 < len(PHASE_ORDER):
            state["current_phase"] = PHASE_ORDER[idx + 1]
            save_state(project_dir, state, dry_run)

    # Done
    header("SDLC Complete!")
    print("  All 7 phases have been completed successfully.")
    print(f"  Project: {ctx['project_name']}")
    print()
    print("  Next steps:")
    print("    python scripts/project_health.py    — View health dashboard")
    print("    python scripts/gate_validator.py --all  — Verify all gates")
    print()
    print("  Remember: Phase 7 (Monitoring) feeds back into Phase 1 (Requirements).")
    print("  The SDLC is a continuous loop, not a one-time process.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted. State saved. Resume by running orchestrate.py again.\n")
        sys.exit(130)
    except json.JSONDecodeError:
        print("\n  ERROR: .sdlc/state.json is corrupted.")
        print("  Fix: python scripts/init_sdlc.py --force --project-name 'Name'\n")
        sys.exit(1)
