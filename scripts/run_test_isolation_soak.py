#!/usr/bin/env python3
"""Run repeated chunked test-suite passes and write a durable soak transcript.

This is the evidence collector for AI-TEST-ISOLATION-1. It deliberately wraps
``run_tests_chunked.py`` instead of reimplementing test discovery or pytest
invocation, so the soak uses the same chunking, timeout, deterministic shuffle,
and bounded failure-tail behavior as the maintained test runner.

Usage:
    .venv/bin/python scripts/run_test_isolation_soak.py
    .venv/bin/python scripts/run_test_isolation_soak.py --runs 1 --seed-base 61300
    .venv/bin/python scripts/run_test_isolation_soak.py --runs 5 --required-runs 5
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "output" / "reports" / "test_isolation_soak.json"
TOTAL_RE = re.compile(
    r"^TOTAL: (?P<passed>\d+) passed, (?P<failed>\d+) failed, "
    r"(?P<skipped>\d+) skipped across (?P<chunks>\d+) chunks$"
)
CHUNK_RE = re.compile(r"^chunk\s+(?P<chunk>\d+)/(?P<total>\d+)\s+\[(?P<marker>[^\]]+)\]:", re.MULTILINE)
FAILED_TEST_RE = re.compile(r"^FAILED\s+(?P<nodeid>\S+)", re.MULTILINE)


def parse_total_line(text: str) -> dict[str, Any] | None:
    """Extract the final chunked-run TOTAL line from process output."""
    for line in reversed(text.splitlines()):
        match = TOTAL_RE.match(line.strip())
        if match:
            data = {key: int(value) for key, value in match.groupdict().items()}
            data["summary"] = line.strip()
            return data
    return None


def tail_lines(text: str, limit: int) -> list[str]:
    """Return a bounded diagnostic tail from captured process output."""
    if limit <= 0:
        return []
    return text.strip().splitlines()[-limit:]


def _unique_preserve_order(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    unique: list[Any] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _failure_diagnostics_from_text(text: str) -> dict[str, Any]:
    failed_chunk_ids: list[int] = []
    for match in CHUNK_RE.finditer(text):
        marker = match.group("marker").strip().lower()
        if marker != "ok":
            failed_chunk_ids.append(int(match.group("chunk")))
    failed_tests = [match.group("nodeid") for match in FAILED_TEST_RE.finditer(text)]
    return {
        "failed_chunk_ids": sorted(set(failed_chunk_ids)),
        "failed_tests": _unique_preserve_order(failed_tests),
    }


def attach_failure_diagnostics(row: dict[str, Any]) -> dict[str, Any]:
    """Attach parsed diagnostic locators without expanding the persisted tail."""
    stdout_tail = "\n".join(str(line) for line in row.get("stdout_tail", []) or [])
    stderr_tail = "\n".join(str(line) for line in row.get("stderr_tail", []) or [])
    diagnostics = _failure_diagnostics_from_text("\n".join([stdout_tail, stderr_tail]))
    row["failed_chunk_ids"] = diagnostics["failed_chunk_ids"]
    row["failed_tests"] = diagnostics["failed_tests"]
    if row.get("ok") is True:
        row["diagnostics_complete"] = True
    else:
        has_tail = bool(row.get("stdout_tail") or row.get("stderr_tail"))
        has_failure_locator = bool(row["failed_chunk_ids"] or row["failed_tests"])
        row["diagnostics_complete"] = bool(has_tail and has_failure_locator)
    return row


def _consecutive_counts(rows: list[dict[str, Any]]) -> tuple[int, int]:
    best = 0
    current = 0
    for row in rows:
        if row.get("ok") is True:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best, current


def build_report(rows: list[dict[str, Any]], *, required_runs: int) -> dict[str, Any]:
    """Build the durable JSON report from per-run rows."""
    max_consecutive, trailing_consecutive = _consecutive_counts(rows)
    all_runs_green = bool(rows) and all(row.get("ok") is True for row in rows)
    complete_soak = len(rows) >= required_runs and max_consecutive >= required_runs and all_runs_green
    seed_sequence = [row.get("shuffle_seed") for row in rows]
    failed_chunk_ids = sorted(
        {
            int(chunk_id)
            for row in rows
            for chunk_id in (row.get("failed_chunk_ids", []) or [])
            if isinstance(chunk_id, int)
        }
    )
    failed_tests = _unique_preserve_order(
        [
            test
            for row in rows
            for test in (row.get("failed_tests", []) or [])
            if isinstance(test, str) and test
        ]
    )
    diagnostics_complete = all(
        row.get("diagnostics_complete") is True or (row.get("ok") is True and "diagnostics_complete" not in row)
        for row in rows
    )
    return {
        "schema": "template_active_inference.test_isolation_soak.v1",
        "purpose": "AI-TEST-ISOLATION-1 five-consecutive-run idle-host evidence",
        "required_runs": required_runs,
        "run_count": len(rows),
        "seed_sequence": seed_sequence,
        "all_runs_green": all_runs_green,
        "max_consecutive_green_count": max_consecutive,
        "trailing_consecutive_green_count": trailing_consecutive,
        "failed_chunk_ids": failed_chunk_ids,
        "failed_tests": failed_tests,
        "diagnostics_complete": diagnostics_complete,
        "complete_soak": complete_soak,
        "ok": all_runs_green,
        "rows": rows,
    }


def write_report(rows: list[dict[str, Any]], *, required_runs: int, output_path: Path) -> dict[str, Any]:
    """Write the current transcript so red or interrupted soaks keep evidence."""
    report = build_report(rows, required_runs=required_runs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def validate_report_payload(report: dict[str, Any], *, require_complete: bool = False) -> list[str]:
    """Fail-closed validation for persisted soak evidence."""
    issues: list[str] = []
    if report.get("schema") != "template_active_inference.test_isolation_soak.v1":
        issues.append("schema is not template_active_inference.test_isolation_soak.v1")

    rows_obj = report.get("rows")
    if not isinstance(rows_obj, list) or not rows_obj:
        issues.append("rows must be a non-empty list")
        rows: list[dict[str, Any]] = []
    else:
        rows = [row for row in rows_obj if isinstance(row, dict)]
        if len(rows) != len(rows_obj):
            issues.append("every row must be an object")

    required_runs = report.get("required_runs")
    if not isinstance(required_runs, int) or required_runs <= 0:
        issues.append("required_runs must be a positive integer")
        required_runs = 1

    if report.get("run_count") != len(rows):
        issues.append("run_count does not match rows length")

    expected_seed_sequence: list[int] = []
    expected_failed_chunk_ids: set[int] = set()
    expected_failed_tests: list[Any] = []
    diagnostics_complete = True

    for index, row in enumerate(rows, start=1):
        if row.get("run_index") != index:
            issues.append(f"row {index} has non-sequential run_index")

        shuffle_seed = row.get("shuffle_seed")
        if not isinstance(shuffle_seed, int):
            issues.append(f"row {index} shuffle_seed must be an integer")
        else:
            expected_seed_sequence.append(shuffle_seed)

        returncode = row.get("returncode")
        if not isinstance(returncode, int):
            issues.append(f"row {index} returncode must be an integer")
            returncode = 1

        ok = row.get("ok")
        if not isinstance(ok, bool):
            issues.append(f"row {index} ok must be boolean")
            ok = False

        for key in ("passed", "failed", "skipped", "chunk_count"):
            value = row.get(key)
            if not isinstance(value, int) or value < 0:
                issues.append(f"row {index} {key} must be a non-negative integer")

        summary = str(row.get("summary", ""))
        parsed_summary = parse_total_line(summary)
        if summary.startswith("TOTAL") and parsed_summary is None:
            issues.append(f"row {index} summary is malformed")
        if parsed_summary:
            if row.get("passed") != parsed_summary["passed"]:
                issues.append(f"row {index} passed disagrees with parsed summary")
            if row.get("failed") != parsed_summary["failed"]:
                issues.append(f"row {index} failed disagrees with parsed summary")
            if row.get("skipped") != parsed_summary["skipped"]:
                issues.append(f"row {index} skipped disagrees with parsed summary")
            if row.get("chunk_count") != parsed_summary["chunks"]:
                issues.append(f"row {index} chunk_count disagrees with parsed summary")

        if ok and (returncode != 0 or row.get("failed") != 0 or int(row.get("passed", 0) or 0) <= 0):
            issues.append(f"row {index} is marked ok but counts/returncode are not green")
        if not ok and returncode == 0 and row.get("failed") == 0:
            issues.append(f"row {index} is marked red without a failing returncode or failed test count")

        recomputed = attach_failure_diagnostics(dict(row))
        if row.get("failed_chunk_ids") != recomputed["failed_chunk_ids"]:
            issues.append(f"row {index} failed_chunk_ids disagree with diagnostic tail")
        if row.get("failed_tests") != recomputed["failed_tests"]:
            issues.append(f"row {index} failed_tests disagree with diagnostic tail")
        if row.get("diagnostics_complete") != recomputed["diagnostics_complete"]:
            issues.append(f"row {index} diagnostics_complete is stale or incorrect")
        if row.get("diagnostics_complete") is not True:
            diagnostics_complete = False
            if ok is False:
                issues.append(f"row {index} is red without complete failure diagnostics")
        expected_failed_chunk_ids.update(recomputed["failed_chunk_ids"])
        expected_failed_tests.extend(recomputed["failed_tests"])

    if len(expected_seed_sequence) > 1:
        expected_consecutive = list(range(expected_seed_sequence[0], expected_seed_sequence[0] + len(expected_seed_sequence)))
        if expected_seed_sequence != expected_consecutive:
            issues.append("seed_sequence must be consecutive in run order")
    if report.get("seed_sequence") != expected_seed_sequence:
        issues.append("seed_sequence does not match row shuffle_seed values")

    if report.get("failed_chunk_ids") != sorted(expected_failed_chunk_ids):
        issues.append("failed_chunk_ids does not match row diagnostics")
    if report.get("failed_tests") != _unique_preserve_order(expected_failed_tests):
        issues.append("failed_tests does not match row diagnostics")
    if report.get("diagnostics_complete") != diagnostics_complete:
        issues.append("diagnostics_complete does not match row diagnostics")

    max_consecutive, trailing_consecutive = _consecutive_counts(rows)
    all_runs_green = bool(rows) and all(row.get("ok") is True for row in rows)
    complete_soak = len(rows) >= required_runs and max_consecutive >= required_runs and all_runs_green
    expected_fields = {
        "all_runs_green": all_runs_green,
        "max_consecutive_green_count": max_consecutive,
        "trailing_consecutive_green_count": trailing_consecutive,
        "complete_soak": complete_soak,
        "ok": all_runs_green,
    }
    for key, expected in expected_fields.items():
        if report.get(key) != expected:
            issues.append(f"{key} is {report.get(key)!r}; expected {expected!r}")

    if require_complete and not complete_soak:
        issues.append("complete_soak is required but false")
    return issues


def _run_once(
    *,
    run_index: int,
    shuffle_seed: int,
    chunk_size: int,
    timeout: int,
    failure_tail_lines: int,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "run_tests_chunked.py"),
        "--shuffle-seed",
        str(shuffle_seed),
        "--chunk-size",
        str(chunk_size),
        "--timeout",
        str(timeout),
        "--failure-tail-lines",
        str(failure_tail_lines),
    ]
    started = time.monotonic()
    proc = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    duration_seconds = round(time.monotonic() - started, 3)
    output = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
    totals = parse_total_line(output) or {}
    ok = proc.returncode == 0 and totals.get("failed") == 0 and bool(totals.get("passed"))
    row: dict[str, Any] = {
        "run_index": run_index,
        "shuffle_seed": shuffle_seed,
        "command": command,
        "returncode": proc.returncode,
        "duration_seconds": duration_seconds,
        "ok": ok,
        "summary": totals.get("summary", "(missing TOTAL line)"),
        "passed": int(totals.get("passed", 0) or 0),
        "failed": int(totals.get("failed", 0) or 0),
        "skipped": int(totals.get("skipped", 0) or 0),
        "chunk_count": int(totals.get("chunks", 0) or 0),
    }
    if not ok:
        row["stdout_tail"] = tail_lines(proc.stdout, failure_tail_lines)
        row["stderr_tail"] = tail_lines(proc.stderr, failure_tail_lines)
    attach_failure_diagnostics(row)
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=int, default=5, help="number of consecutive chunked runs to execute")
    parser.add_argument("--required-runs", type=int, default=5, help="green run count required for complete_soak")
    parser.add_argument("--seed-base", type=int, default=61300, help="first deterministic shuffle seed")
    parser.add_argument("--chunk-size", type=int, default=6, help="test files per chunked subprocess")
    parser.add_argument("--timeout", type=int, default=900, help="per-test pytest-timeout value")
    parser.add_argument("--failure-tail-lines", type=int, default=120, help="captured tail lines for red runs")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSON report path")
    parser.add_argument("--validate-report", type=Path, help="validate an existing JSON report instead of running tests")
    parser.add_argument("--require-complete", action="store_true", help="fail unless complete_soak is true")
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="stop after the first red run while still writing the partial transcript",
    )
    args = parser.parse_args(argv)

    if args.validate_report:
        report_path = args.validate_report if args.validate_report.is_absolute() else PROJECT_ROOT / args.validate_report
        report = json.loads(report_path.read_text(encoding="utf-8"))
        issues = validate_report_payload(report, require_complete=args.require_complete)
        if issues:
            for issue in issues:
                print(f"FAIL: {issue}", file=sys.stderr)
            return 1
        print(f"PASS: {report_path} is a valid test-isolation soak report", flush=True)
        return 0

    if args.runs <= 0:
        raise SystemExit("--runs must be positive")
    if args.required_runs <= 0:
        raise SystemExit("--required-runs must be positive")

    output_path = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    rows: list[dict[str, Any]] = []
    report: dict[str, Any] | None = None
    for offset in range(args.runs):
        run_index = offset + 1
        shuffle_seed = args.seed_base + offset
        print(f"soak run {run_index}/{args.runs}: shuffle-seed {shuffle_seed}", flush=True)
        row = _run_once(
            run_index=run_index,
            shuffle_seed=shuffle_seed,
            chunk_size=args.chunk_size,
            timeout=args.timeout,
            failure_tail_lines=args.failure_tail_lines,
        )
        rows.append(row)
        report = write_report(rows, required_runs=args.required_runs, output_path=output_path)
        marker = "ok" if row["ok"] else f"EXIT {row['returncode']}"
        print(f"soak run {run_index}/{args.runs} [{marker}]: {row['summary']}", flush=True)
        if args.stop_on_failure and not row["ok"]:
            break

    if report is None:
        report = write_report(rows, required_runs=args.required_runs, output_path=output_path)
    print(f"test_isolation_soak: {output_path}", flush=True)
    if report["complete_soak"]:
        print(f"PASS: {report['max_consecutive_green_count']} consecutive green runs", flush=True)
    elif report["all_runs_green"]:
        print(
            "PARTIAL: all executed runs were green, but fewer than "
            f"{args.required_runs} consecutive runs were recorded",
            flush=True,
        )
    else:
        print("FAIL: at least one chunked run was red; report the seed and failure tail", flush=True)
    if args.require_complete and not report["complete_soak"]:
        return 1
    return 0 if report["all_runs_green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
