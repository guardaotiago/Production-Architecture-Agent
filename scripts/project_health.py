#!/usr/bin/env python3
"""Display project health dashboard across all SDLC phases.

Reads .sdlc/state.json and phase checklists to show progress,
blockers, and recommendations.

Usage:
    python project_health.py
    python project_health.py --project-dir /path/to/project
    python project_health.py --json
    python project_health.py --help
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PHASES = [
    ("requirements", "Requirements & Planning"),
    ("development", "Development & Git"),
    ("cicd", "CI/CD Pipeline"),
    ("testing", "QA Testing"),
    ("uat", "User Acceptance Testing"),
    ("deployment", "Production Deployment"),
    ("monitoring", "Monitoring & SRE"),
]

STATUS_ICONS = {
    "completed": "✅",
    "in_progress": "🔄",
    "pending": "⬜",
    "blocked": "❌",
}


def load_state(project_dir: Path) -> dict | None:
    """Load SDLC state file."""
    state_path = project_dir / ".sdlc" / "state.json"
    if not state_path.exists():
        return None
    with open(state_path) as f:
        return json.load(f)


def parse_checklist(filepath: Path) -> tuple[int, int]:
    """Parse a markdown checklist, return (checked, total) counts."""
    if not filepath.exists():
        return 0, 0
    content = filepath.read_text()
    total = len(re.findall(r"- \[[ x]\]", content))
    checked = len(re.findall(r"- \[x\]", content, re.IGNORECASE))
    return checked, total


def calculate_health_score(state: dict, project_dir: Path) -> float:
    """Calculate overall health score (0-100)."""
    phases_data = state.get("phases", {})
    total_weight = 0
    weighted_score = 0

    for i, (phase_id, _) in enumerate(PHASES):
        phase = phases_data.get(phase_id, {})
        weight = 1.0

        # Check checklist progress
        checklist_path = project_dir / ".sdlc" / "phases" / f"{i+1:02d}-{phase_id}.md"
        checked, total = parse_checklist(checklist_path)
        checklist_pct = checked / total if total > 0 else 0

        # Check gate status
        gate_passed = 1.0 if phase.get("gate_passed") else 0.0

        # Phase score: 70% checklist + 30% gate
        phase_score = (checklist_pct * 0.7 + gate_passed * 0.3) * 100

        if phase.get("status") == "completed":
            phase_score = max(phase_score, 90)

        total_weight += weight
        weighted_score += phase_score * weight

    return weighted_score / total_weight if total_weight > 0 else 0


def print_dashboard(state: dict, project_dir: Path):
    """Print formatted health dashboard."""
    project_name = state.get("project_name", "Unknown")
    current_phase = state.get("current_phase", "requirements")
    created_at = state.get("created_at", "")

    print(f"\n{'='*60}")
    print(f"  SDLC Health Dashboard: {project_name}")
    print(f"{'='*60}\n")

    if created_at:
        try:
            dt = datetime.fromisoformat(created_at)
            age = datetime.now(timezone.utc) - dt
            print(f"  Project age: {age.days} days")
        except ValueError:
            pass

    print(f"  Current phase: {current_phase}\n")
    print(f"  {'Phase':<30} {'Status':<12} {'Progress':<15} {'Gate'}")
    print(f"  {'-'*30} {'-'*12} {'-'*15} {'-'*6}")

    phases_data = state.get("phases", {})

    for i, (phase_id, phase_name) in enumerate(PHASES):
        phase = phases_data.get(phase_id, {})
        status = phase.get("status", "pending")
        icon = STATUS_ICONS.get(status, "⬜")

        # Parse checklist
        checklist_path = project_dir / ".sdlc" / "phases" / f"{i+1:02d}-{phase_id}.md"
        checked, total = parse_checklist(checklist_path)
        progress = f"{checked}/{total}" if total > 0 else "N/A"

        # Gate status
        gate = "✓" if phase.get("gate_passed") else "—"

        # Highlight current phase
        marker = " ←" if phase_id == current_phase else ""

        print(f"  {icon} {phase_name:<28} {status:<12} {progress:<15} {gate}{marker}")

    # Health score
    score = calculate_health_score(state, project_dir)
    print(f"\n  Overall health score: {score:.0f}/100")

    # Recommendations
    recommendations = []
    current_idx = next(
        (i for i, (pid, _) in enumerate(PHASES) if pid == current_phase), 0
    )
    current_data = phases_data.get(current_phase, {})

    if current_data.get("status") == "pending":
        recommendations.append(f"Start working on {current_phase} phase")
    elif current_data.get("status") == "in_progress" and not current_data.get("gate_passed"):
        recommendations.append(f"Complete gate criteria for {current_phase}")

    # Check for skipped phases
    for i, (phase_id, _) in enumerate(PHASES):
        if i < current_idx:
            phase = phases_data.get(phase_id, {})
            if not phase.get("gate_passed"):
                recommendations.append(f"⚠  Phase '{phase_id}' gate not passed (before current phase)")

    if recommendations:
        print(f"\n  Recommendations:")
        for rec in recommendations:
            print(f"    • {rec}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Display SDLC project health dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        help="Output as JSON",
    )

    args = parser.parse_args()
    project_dir = args.project_dir.resolve()
    state = load_state(project_dir)

    if not state:
        print("✗ No .sdlc/state.json found. Run init_sdlc.py first.")
        sys.exit(1)

    if args.json_output:
        score = calculate_health_score(state, project_dir)
        output = {**state, "health_score": score}
        print(json.dumps(output, indent=2))
    else:
        print_dashboard(state, project_dir)


if __name__ == "__main__":
    main()
