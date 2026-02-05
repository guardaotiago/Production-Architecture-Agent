#!/usr/bin/env python3
"""Evaluation harness for SDLC Orchestrator scenarios.

Loads YAML scenario files and executes their setup, steps, and assertions
to validate the orchestrator works correctly.

Usage:
    python runner.py                              # Run all scenarios
    python runner.py --scenario 01-greenfield-react
    python runner.py --tags full-lifecycle,react
    python runner.py --list                       # List available scenarios
    python runner.py --help
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
SCENARIOS_DIR = SCRIPT_DIR / "scenarios"
REPO_ROOT = SCRIPT_DIR.parent


def load_scenarios(filter_name: str | None = None, filter_tags: list[str] | None = None) -> list[dict]:
    """Load scenario YAML files, optionally filtered."""
    scenarios = []
    for f in sorted(SCENARIOS_DIR.glob("*.yaml")):
        with open(f) as fh:
            scenario = yaml.safe_load(fh)
            scenario["_file"] = f.name

        if filter_name and filter_name not in f.stem:
            continue
        if filter_tags:
            scenario_tags = set(scenario.get("tags", []))
            if not scenario_tags.intersection(filter_tags):
                continue

        scenarios.append(scenario)
    return scenarios


def run_command(command: str, cwd: str, timeout: int = 60) -> tuple[int, str, str]:
    """Run a shell command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"


def check_assertion(assertion: dict, work_dir: str) -> tuple[bool, str]:
    """Check a single assertion. Returns (passed, message)."""
    desc = assertion["description"]
    atype = assertion["type"]
    target = assertion.get("target", "")
    expected = assertion.get("expected", "")

    if atype == "file_exists":
        path = Path(work_dir) / target
        if path.exists():
            return True, f"  ✓ {desc}"
        return False, f"  ✗ {desc} (file not found: {target})"

    elif atype == "dir_exists":
        path = Path(work_dir) / target
        if path.is_dir():
            return True, f"  ✓ {desc}"
        return False, f"  ✗ {desc} (directory not found: {target})"

    elif atype == "exit_code":
        code, stdout, stderr = run_command(target, work_dir)
        if str(code) == str(expected):
            return True, f"  ✓ {desc}"
        return False, f"  ✗ {desc} (exit code {code}, expected {expected})"

    elif atype == "output_contains":
        code, stdout, stderr = run_command(target, work_dir)
        output = stdout + stderr
        if expected.lower() in output.lower():
            return True, f"  ✓ {desc}"
        return False, f"  ✗ {desc} (output missing: '{expected}')"

    elif atype == "state_check":
        state_path = Path(work_dir) / ".sdlc" / "state.json"
        if not state_path.exists():
            return False, f"  ✗ {desc} (no state.json)"
        with open(state_path) as f:
            state = json.load(f)
        # target is a dot-path like "phases.requirements.status"
        value = state
        for key in target.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
        if str(value) == str(expected):
            return True, f"  ✓ {desc}"
        return False, f"  ✗ {desc} (got '{value}', expected '{expected}')"

    elif atype == "file_contains":
        path = Path(work_dir) / target
        if not path.exists():
            return False, f"  ✗ {desc} (file not found: {target})"
        content = path.read_text()
        if expected.lower() in content.lower():
            return True, f"  ✓ {desc}"
        return False, f"  ✗ {desc} (file missing content: '{expected}')"

    else:
        return False, f"  ? {desc} (unknown assertion type: {atype})"


def run_scenario(scenario: dict, verbose: bool = False) -> tuple[int, int]:
    """Run a single scenario. Returns (passed_count, failed_count)."""
    name = scenario.get("name", "Unknown")
    desc = scenario.get("description", "")

    print(f"\n{'='*60}")
    print(f"Scenario: {name}")
    print(f"  {desc}")
    print(f"{'='*60}")

    # Create temp working directory
    work_dir = tempfile.mkdtemp(prefix="sdlc-eval-")

    try:
        # Run setup steps
        setup_steps = scenario.get("setup", [])
        for step in setup_steps:
            cmd = step.get("command", "").replace("$REPO_ROOT", str(REPO_ROOT))
            if cmd:
                if verbose:
                    print(f"  [setup] {step.get('description', cmd)}")
                code, stdout, stderr = run_command(cmd, work_dir)
                if code != 0 and verbose:
                    print(f"    ⚠ Setup step failed: {stderr[:200]}")

        # Run scenario steps
        steps = scenario.get("steps", [])
        for step in steps:
            cmd = step.get("command", "").replace("$REPO_ROOT", str(REPO_ROOT))
            if cmd:
                if verbose:
                    print(f"  [step] {step.get('action', cmd)}")
                code, stdout, stderr = run_command(cmd, work_dir)
                if verbose and code != 0:
                    print(f"    ⚠ Step failed (exit {code}): {stderr[:200]}")

        # Check assertions
        assertions = scenario.get("assertions", [])
        passed = 0
        failed = 0

        print(f"\n  Assertions:")
        for assertion in assertions:
            ok, msg = check_assertion(assertion, work_dir)
            print(msg)
            if ok:
                passed += 1
            else:
                failed += 1

        return passed, failed

    finally:
        # Cleanup
        shutil.rmtree(work_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description="Run SDLC Orchestrator evaluation scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Run all scenarios
  %(prog)s --scenario greenfield        # Run matching scenario
  %(prog)s --tags react,testing         # Run scenarios with these tags
  %(prog)s --list                       # List available scenarios
  %(prog)s --verbose                    # Show step-by-step output
        """,
    )
    parser.add_argument("--scenario", help="Filter by scenario name (substring match)")
    parser.add_argument("--tags", help="Filter by tags (comma-separated)")
    parser.add_argument("--list", action="store_true", help="List scenarios without running")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON output")

    args = parser.parse_args()
    tags = args.tags.split(",") if args.tags else None
    scenarios = load_scenarios(args.scenario, tags)

    if not scenarios:
        print("No matching scenarios found.")
        sys.exit(1)

    if args.list:
        print(f"\nAvailable scenarios ({len(scenarios)}):\n")
        for s in scenarios:
            tags_str = ", ".join(s.get("tags", []))
            print(f"  {s['_file']:<40} {s.get('name', 'Unknown')}")
            if tags_str:
                print(f"    Tags: {tags_str}")
        return

    total_passed = 0
    total_failed = 0
    results = {}

    for scenario in scenarios:
        passed, failed = run_scenario(scenario, verbose=args.verbose)
        total_passed += passed
        total_failed += failed
        results[scenario.get("name", "Unknown")] = {
            "passed": passed,
            "failed": failed,
        }

    # Summary
    total = total_passed + total_failed
    print(f"\n{'='*60}")
    print(f"SUMMARY: {total_passed}/{total} assertions passed across {len(scenarios)} scenarios")
    if total_failed:
        print(f"  ❌ {total_failed} assertions FAILED")
    else:
        print(f"  ✅ All assertions passed!")
    print(f"{'='*60}\n")

    if args.json_output:
        print(json.dumps(results, indent=2))

    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
