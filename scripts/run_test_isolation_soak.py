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
    return {
        "schema": "template_active_inference.test_isolation_soak.v1",
        "purpose": "AI-TEST-ISOLATION-1 five-consecutive-run idle-host evidence",
        "required_runs": required_runs,
        "run_count": len(rows),
        "all_runs_green": all_runs_green,
        "max_consecutive_green_count": max_consecutive,
        "trailing_consecutive_green_count": trailing_consecutive,
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
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="stop after the first red run while still writing the partial transcript",
    )
    args = parser.parse_args(argv)

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
    return 0 if report["all_runs_green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
