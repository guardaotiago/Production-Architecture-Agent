#!/usr/bin/env python3
"""
Post-Deployment Smoke Test Runner — SDLC Orchestrator Phase 6

Runs HTTP-based smoke tests against a deployed service to verify it is
functioning correctly after deployment.

Usage:
    python smoke_test.py --url https://app.example.com --config smoke-tests.json
    python smoke_test.py --url https://app.example.com
    python smoke_test.py --help

Config file format (JSON):
    {
        "tests": [
            {
                "name": "Health check",
                "method": "GET",
                "path": "/health",
                "expected_status": 200,
                "expected_body_contains": "ok"
            },
            {
                "name": "API version",
                "method": "GET",
                "path": "/api/version",
                "expected_status": 200,
                "expected_body_contains": "v"
            },
            {
                "name": "Create resource",
                "method": "POST",
                "path": "/api/resource",
                "headers": {"Content-Type": "application/json"},
                "body": "{\"name\": \"smoke-test\"}",
                "expected_status": 201
            }
        ]
    }
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TestResult:
    name: str
    passed: bool
    status_code: Optional[int] = None
    expected_status: Optional[int] = None
    body_check_passed: Optional[bool] = None
    duration_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class SmokeTest:
    name: str
    method: str = "GET"
    path: str = "/"
    headers: dict = field(default_factory=dict)
    body: Optional[str] = None
    expected_status: int = 200
    expected_body_contains: Optional[str] = None


def load_tests_from_config(config_path: str) -> list[SmokeTest]:
    """Load test definitions from a JSON config file."""
    path = Path(config_path)
    if not path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tests = []
    for entry in data.get("tests", []):
        tests.append(SmokeTest(
            name=entry.get("name", "Unnamed test"),
            method=entry.get("method", "GET").upper(),
            path=entry.get("path", "/"),
            headers=entry.get("headers", {}),
            body=entry.get("body", None),
            expected_status=entry.get("expected_status", 200),
            expected_body_contains=entry.get("expected_body_contains", None),
        ))

    if not tests:
        print("WARNING: Config file contains no tests. Running default health check.")
        tests = [default_health_check()]

    return tests


def default_health_check() -> SmokeTest:
    """Return a basic health check test."""
    return SmokeTest(
        name="Default health check (GET /)",
        method="GET",
        path="/",
        expected_status=200,
    )


def run_test(base_url: str, test: SmokeTest, timeout: int) -> TestResult:
    """Execute a single smoke test and return the result."""
    url = base_url.rstrip("/") + test.path
    start_time = time.time()

    try:
        body_bytes = test.body.encode("utf-8") if test.body else None
        req = urllib.request.Request(
            url=url,
            data=body_bytes,
            headers=test.headers,
            method=test.method,
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.status
            response_body = response.read().decode("utf-8", errors="replace")

    except urllib.error.HTTPError as e:
        status_code = e.code
        try:
            response_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            response_body = ""
    except urllib.error.URLError as e:
        duration_ms = (time.time() - start_time) * 1000
        return TestResult(
            name=test.name,
            passed=False,
            duration_ms=duration_ms,
            error=f"Connection error: {e.reason}",
        )
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        return TestResult(
            name=test.name,
            passed=False,
            duration_ms=duration_ms,
            error=f"Unexpected error: {e}",
        )

    duration_ms = (time.time() - start_time) * 1000

    # Check status code
    status_ok = status_code == test.expected_status

    # Check body contains (if specified)
    body_check_passed = None
    if test.expected_body_contains is not None:
        body_check_passed = test.expected_body_contains in response_body

    passed = status_ok and (body_check_passed is None or body_check_passed)

    return TestResult(
        name=test.name,
        passed=passed,
        status_code=status_code,
        expected_status=test.expected_status,
        body_check_passed=body_check_passed,
        duration_ms=duration_ms,
    )


def print_results(results: list[TestResult]) -> None:
    """Print a formatted test results summary."""
    print("")
    print("=" * 70)
    print("  SMOKE TEST RESULTS")
    print("=" * 70)
    print("")

    for result in results:
        icon = "PASS" if result.passed else "FAIL"
        status_info = ""

        if result.error:
            status_info = f" | Error: {result.error}"
        elif result.status_code is not None:
            status_info = f" | Status: {result.status_code} (expected {result.expected_status})"
            if result.body_check_passed is not None:
                body_status = "matched" if result.body_check_passed else "NOT matched"
                status_info += f" | Body: {body_status}"

        print(f"  [{icon}] {result.name} ({result.duration_ms:.0f}ms){status_info}")

    print("")
    print("-" * 70)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    print(f"  Total: {total} | Passed: {passed} | Failed: {failed}")

    if failed == 0:
        print("  Status: ALL TESTS PASSED")
    else:
        print("  Status: SOME TESTS FAILED")

    print("=" * 70)
    print("")


def main():
    parser = argparse.ArgumentParser(
        description="Run post-deployment smoke tests against a deployed service.",
        epilog="Example: python smoke_test.py --url https://app.example.com --config smoke-tests.json",
    )
    parser.add_argument(
        "--url",
        required=True,
        type=str,
        help="Base URL of the deployed service (e.g., https://app.example.com)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to JSON config file with test definitions (optional)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout in seconds for each HTTP request (default: 10)",
    )

    args = parser.parse_args()

    # Load tests
    if args.config:
        tests = load_tests_from_config(args.config)
        print(f"Loaded {len(tests)} test(s) from {args.config}")
    else:
        tests = [default_health_check()]
        print("No config file provided. Running default health check.")

    print(f"Target: {args.url}")
    print(f"Timeout: {args.timeout}s per request")
    print("")

    # Run tests
    results = []
    for test in tests:
        print(f"  Running: {test.name} ({test.method} {test.path}) ...", end="", flush=True)
        result = run_test(args.url, test, args.timeout)
        status = "PASS" if result.passed else "FAIL"
        print(f" [{status}]")
        results.append(result)

    # Print summary
    print_results(results)

    # Exit code
    all_passed = all(r.passed for r in results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
