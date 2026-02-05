#!/usr/bin/env python3
"""
Coverage Analyzer — Parses test coverage reports and identifies gaps.

Supports LCOV, Cobertura XML, and coverage.py JSON formats. Reports overall
coverage, uncovered files, critical gaps, and suggests high-impact tests.

Usage:
    python coverage_analyzer.py --report coverage/lcov.info
    python coverage_analyzer.py --report coverage.xml --threshold 80
    python coverage_analyzer.py --report coverage.json --json
    python coverage_analyzer.py --help

Exit codes:
    0 — Coverage meets threshold (or no threshold specified)
    1 — Coverage below threshold
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class FileCoverage:
    path: str
    total_lines: int = 0
    covered_lines: int = 0
    missed_lines: int = 0
    total_branches: int = 0
    covered_branches: int = 0
    total_functions: int = 0
    covered_functions: int = 0
    uncovered_line_numbers: list[int] = field(default_factory=list)

    @property
    def line_rate(self) -> float:
        if self.total_lines == 0:
            return 100.0
        return (self.covered_lines / self.total_lines) * 100

    @property
    def branch_rate(self) -> float:
        if self.total_branches == 0:
            return 100.0
        return (self.covered_branches / self.total_branches) * 100

    @property
    def function_rate(self) -> float:
        if self.total_functions == 0:
            return 100.0
        return (self.covered_functions / self.total_functions) * 100


@dataclass
class CoverageReport:
    files: list[FileCoverage] = field(default_factory=list)
    format_detected: str = "unknown"

    @property
    def total_lines(self) -> int:
        return sum(f.total_lines for f in self.files)

    @property
    def covered_lines(self) -> int:
        return sum(f.covered_lines for f in self.files)

    @property
    def overall_line_rate(self) -> float:
        if self.total_lines == 0:
            return 100.0
        return (self.covered_lines / self.total_lines) * 100

    @property
    def total_branches(self) -> int:
        return sum(f.total_branches for f in self.files)

    @property
    def covered_branches(self) -> int:
        return sum(f.covered_branches for f in self.files)

    @property
    def overall_branch_rate(self) -> float:
        if self.total_branches == 0:
            return 100.0
        return (self.covered_branches / self.total_branches) * 100

    @property
    def total_functions(self) -> int:
        return sum(f.total_functions for f in self.files)

    @property
    def covered_functions(self) -> int:
        return sum(f.covered_functions for f in self.files)

    @property
    def overall_function_rate(self) -> float:
        if self.total_functions == 0:
            return 100.0
        return (self.covered_functions / self.total_functions) * 100


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def detect_format(path: Path) -> str:
    """Detect the coverage report format from file extension and content."""
    suffix = path.suffix.lower()
    if suffix == ".xml":
        return "cobertura"
    if suffix == ".json":
        return "coverage_py"

    # Peek at content for LCOV format
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(512)
        if "SF:" in head or "TN:" in head:
            return "lcov"
        if head.strip().startswith("<?xml") or head.strip().startswith("<coverage"):
            return "cobertura"
        if head.strip().startswith("{"):
            return "coverage_py"
    except Exception:
        pass

    return "lcov"  # default assumption


def parse_lcov(path: Path) -> CoverageReport:
    """Parse LCOV / lcov.info format."""
    report = CoverageReport(format_detected="lcov")
    content = path.read_text(encoding="utf-8", errors="replace")

    current_file: Optional[FileCoverage] = None

    for line in content.split("\n"):
        line = line.strip()

        if line.startswith("SF:"):
            current_file = FileCoverage(path=line[3:])

        elif line.startswith("DA:") and current_file:
            # DA:line_number,execution_count
            parts = line[3:].split(",")
            if len(parts) >= 2:
                line_no = int(parts[0])
                hits = int(parts[1])
                current_file.total_lines += 1
                if hits > 0:
                    current_file.covered_lines += 1
                else:
                    current_file.uncovered_line_numbers.append(line_no)

        elif line.startswith("BRDA:") and current_file:
            # BRDA:line,block,branch,taken
            parts = line[5:].split(",")
            if len(parts) >= 4:
                current_file.total_branches += 1
                taken = parts[3]
                if taken != "-" and int(taken) > 0:
                    current_file.covered_branches += 1

        elif line.startswith("FNF:") and current_file:
            current_file.total_functions = int(line[4:])

        elif line.startswith("FNH:") and current_file:
            current_file.covered_functions = int(line[4:])

        elif line == "end_of_record" and current_file:
            current_file.missed_lines = (
                current_file.total_lines - current_file.covered_lines
            )
            report.files.append(current_file)
            current_file = None

    return report


def parse_cobertura(path: Path) -> CoverageReport:
    """Parse Cobertura XML format."""
    report = CoverageReport(format_detected="cobertura")
    tree = ET.parse(path)
    root = tree.getroot()

    # Handle namespace if present
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    for pkg in root.iter(f"{ns}package"):
        for cls in pkg.iter(f"{ns}class"):
            filename = cls.get("filename", "unknown")
            fc = FileCoverage(path=filename)

            for line_el in cls.iter(f"{ns}line"):
                fc.total_lines += 1
                hits = int(line_el.get("hits", "0"))
                if hits > 0:
                    fc.covered_lines += 1
                else:
                    line_no = int(line_el.get("number", "0"))
                    fc.uncovered_line_numbers.append(line_no)

                if line_el.get("branch") == "true":
                    condition = line_el.get("condition-coverage", "")
                    match = re.search(r"\((\d+)/(\d+)\)", condition)
                    if match:
                        fc.covered_branches += int(match.group(1))
                        fc.total_branches += int(match.group(2))

            # Count methods as functions
            for method in cls.iter(f"{ns}method"):
                fc.total_functions += 1
                method_lines = list(method.iter(f"{ns}line"))
                if method_lines and any(int(l.get("hits", "0")) > 0 for l in method_lines):
                    fc.covered_functions += 1

            fc.missed_lines = fc.total_lines - fc.covered_lines
            report.files.append(fc)

    return report


def parse_coverage_py_json(path: Path) -> CoverageReport:
    """Parse coverage.py JSON format."""
    report = CoverageReport(format_detected="coverage_py")
    data = json.loads(path.read_text(encoding="utf-8"))

    files_data = data.get("files", {})
    for filepath, file_info in files_data.items():
        summary = file_info.get("summary", {})
        fc = FileCoverage(
            path=filepath,
            total_lines=summary.get("num_statements", 0),
            covered_lines=summary.get("covered_lines", 0),
            missed_lines=summary.get("missing_lines", 0),
            total_branches=summary.get("num_branches", 0),
            covered_branches=summary.get("covered_branches", 0),
        )

        missing = file_info.get("missing_lines", [])
        fc.uncovered_line_numbers = missing

        # Recalculate if summary fields are missing
        if fc.total_lines == 0:
            executed = file_info.get("executed_lines", [])
            all_missing = file_info.get("missing_lines", [])
            fc.total_lines = len(executed) + len(all_missing)
            fc.covered_lines = len(executed)
            fc.missed_lines = len(all_missing)

        report.files.append(fc)

    return report


def parse_report(path: Path) -> CoverageReport:
    """Detect format and parse the coverage report."""
    fmt = detect_format(path)
    parsers = {
        "lcov": parse_lcov,
        "cobertura": parse_cobertura,
        "coverage_py": parse_coverage_py_json,
    }
    parser_fn = parsers.get(fmt, parse_lcov)
    return parser_fn(path)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

@dataclass
class CoverageGap:
    file_path: str
    line_rate: float
    missed_lines: int
    reason: str
    suggestion: str


def analyze_gaps(report: CoverageReport) -> list[CoverageGap]:
    """Identify coverage gaps and suggest improvements."""
    gaps: list[CoverageGap] = []

    # Sort files by missed lines (most uncovered first)
    sorted_files = sorted(report.files, key=lambda f: f.missed_lines, reverse=True)

    for fc in sorted_files:
        if fc.missed_lines == 0:
            continue

        reasons = []
        suggestions = []

        if fc.line_rate < 50:
            reasons.append("critically low coverage")
            suggestions.append(f"Add unit tests for {fc.path} — only {fc.line_rate:.0f}% covered")
        elif fc.line_rate < 80:
            reasons.append("below target coverage")
            suggestions.append(f"Add tests for uncovered lines in {fc.path}")

        if fc.total_branches > 0 and fc.branch_rate < 60:
            reasons.append(f"low branch coverage ({fc.branch_rate:.0f}%)")
            suggestions.append(f"Add tests for conditional branches in {fc.path}")

        if fc.total_functions > 0 and fc.function_rate < 70:
            reasons.append(f"untested functions ({fc.covered_functions}/{fc.total_functions})")
            suggestions.append(f"Add tests for uncovered functions in {fc.path}")

        # Flag critical paths
        critical_patterns = [
            "auth", "login", "payment", "checkout", "security", "middleware",
            "api", "route", "controller", "service", "model",
        ]
        lower_path = fc.path.lower()
        if any(pattern in lower_path for pattern in critical_patterns):
            reasons.append("critical path file")
            suggestions.insert(0, f"HIGH PRIORITY: {fc.path} is a critical path file")

        if reasons:
            gaps.append(CoverageGap(
                file_path=fc.path,
                line_rate=fc.line_rate,
                missed_lines=fc.missed_lines,
                reason="; ".join(reasons),
                suggestion=suggestions[0] if suggestions else "Add more tests",
            ))

    return gaps


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def render_text_report(report: CoverageReport, gaps: list[CoverageGap], threshold: Optional[float]) -> str:
    """Render a human-readable text report."""
    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("  COVERAGE ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Overall metrics
    lines.append(f"Format detected:     {report.format_detected}")
    lines.append(f"Files analyzed:      {len(report.files)}")
    lines.append(f"")
    lines.append(f"Line coverage:       {report.overall_line_rate:6.1f}%  ({report.covered_lines}/{report.total_lines})")
    if report.total_branches > 0:
        lines.append(f"Branch coverage:     {report.overall_branch_rate:6.1f}%  ({report.covered_branches}/{report.total_branches})")
    if report.total_functions > 0:
        lines.append(f"Function coverage:   {report.overall_function_rate:6.1f}%  ({report.covered_functions}/{report.total_functions})")
    lines.append("")

    if threshold is not None:
        status = "PASS" if report.overall_line_rate >= threshold else "FAIL"
        lines.append(f"Threshold:           {threshold}%")
        lines.append(f"Status:              {status}")
        lines.append("")

    # Worst files
    uncovered_files = [f for f in report.files if f.missed_lines > 0]
    uncovered_files.sort(key=lambda f: f.missed_lines, reverse=True)

    if uncovered_files:
        lines.append("-" * 60)
        lines.append("  FILES WITH LOWEST COVERAGE")
        lines.append("-" * 60)
        lines.append(f"{'File':<45} {'Rate':>6} {'Missed':>7}")
        lines.append(f"{'-'*45} {'-'*6} {'-'*7}")
        for fc in uncovered_files[:15]:
            name = fc.path if len(fc.path) <= 44 else "..." + fc.path[-41:]
            lines.append(f"{name:<45} {fc.line_rate:5.1f}% {fc.missed_lines:>7}")
        lines.append("")

    # Gaps and suggestions
    if gaps:
        lines.append("-" * 60)
        lines.append("  SUGGESTED IMPROVEMENTS (highest impact first)")
        lines.append("-" * 60)
        for i, gap in enumerate(gaps[:10], 1):
            lines.append(f"  {i}. {gap.suggestion}")
            lines.append(f"     ({gap.reason})")
            lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def render_json_report(report: CoverageReport, gaps: list[CoverageGap], threshold: Optional[float]) -> str:
    """Render a JSON report."""
    passes_threshold = True
    if threshold is not None:
        passes_threshold = report.overall_line_rate >= threshold

    output = {
        "summary": {
            "format": report.format_detected,
            "files_analyzed": len(report.files),
            "line_coverage": round(report.overall_line_rate, 2),
            "branch_coverage": round(report.overall_branch_rate, 2),
            "function_coverage": round(report.overall_function_rate, 2),
            "total_lines": report.total_lines,
            "covered_lines": report.covered_lines,
            "total_branches": report.total_branches,
            "covered_branches": report.covered_branches,
            "total_functions": report.total_functions,
            "covered_functions": report.covered_functions,
        },
        "threshold": threshold,
        "passes_threshold": passes_threshold,
        "files": [],
        "gaps": [],
    }

    for fc in sorted(report.files, key=lambda f: f.line_rate):
        output["files"].append({
            "path": fc.path,
            "line_rate": round(fc.line_rate, 2),
            "branch_rate": round(fc.branch_rate, 2),
            "function_rate": round(fc.function_rate, 2),
            "total_lines": fc.total_lines,
            "covered_lines": fc.covered_lines,
            "missed_lines": fc.missed_lines,
            "uncovered_line_numbers": fc.uncovered_line_numbers[:50],  # Limit output size
        })

    for gap in gaps:
        output["gaps"].append(asdict(gap))

    return json.dumps(output, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze test coverage reports and identify gaps.",
        epilog=(
            "Examples:\n"
            "  python coverage_analyzer.py --report coverage/lcov.info\n"
            "  python coverage_analyzer.py --report coverage.xml --threshold 80\n"
            "  python coverage_analyzer.py --report coverage.json --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--report", "-r",
        required=True,
        type=Path,
        help="Path to coverage report file (lcov, cobertura XML, or coverage.py JSON)",
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=None,
        help="Minimum coverage percentage threshold. Exit code 1 if not met.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.report.exists():
        print(f"ERROR: Coverage report not found: {args.report}", file=sys.stderr)
        sys.exit(1)

    report = parse_report(args.report)

    if not report.files:
        print("WARNING: No files found in coverage report.", file=sys.stderr)

    gaps = analyze_gaps(report)

    if args.json_output:
        print(render_json_report(report, gaps, args.threshold))
    else:
        print(render_text_report(report, gaps, args.threshold))

    # Exit code based on threshold
    if args.threshold is not None and report.overall_line_rate < args.threshold:
        sys.exit(1)


if __name__ == "__main__":
    main()
