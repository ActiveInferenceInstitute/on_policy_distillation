#!/usr/bin/env python3
"""Run the test suite in small per-process chunks (thin orchestrator).

On a heavily loaded machine (resident co-actor pipelines, LLM servers) a single
long-lived pytest process is reliably killed by resource pressure (observed as
exit 144). Running the suite as N-file chunks, each in its own short-lived
subprocess, survives the same load and yields the same coverage of test files.

Exit code is honest: 0 only when every chunk reports 0 failures and exits 0.

Usage:
    .venv/bin/python scripts/run_tests_chunked.py              # whole suite, 6 files/chunk
    .venv/bin/python scripts/run_tests_chunked.py --chunk-size 3
    .venv/bin/python scripts/run_tests_chunked.py --timeout 900
    .venv/bin/python scripts/run_tests_chunked.py --failure-tail-lines 120
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_TAIL_RE = re.compile(r"(?:(\d+) failed)?(?:,? ?(\d+) passed)?(?:,? ?(\d+) skipped)?")


def collect_chunks(project_root: Path, chunk_size: int, shuffle_seed: int | None = None) -> list[list[str]]:
    """Group test files into chunks; with a seed, shuffle deterministically.

    The shuffle is file-order coverage for AI-TEST-ISOLATION-1 chain B: the
    same seed always yields the same order, so a red shuffled run is exactly
    reproducible (never re-roll to a passing seed — report it instead).
    """
    files = sorted(str(p.relative_to(project_root)) for p in (project_root / "tests").glob("test_*.py"))
    gates = project_root / "tests" / "gates"
    if gates.is_dir() and any(gates.glob("test_*.py")):
        files.append("tests/gates")
    if shuffle_seed is not None:
        import random

        random.Random(shuffle_seed).shuffle(files)
    return [files[i : i + chunk_size] for i in range(0, len(files), chunk_size)]


def _parse_counts(tail: str) -> tuple[int, int, int]:
    failed = passed = skipped = 0
    for m in re.finditer(r"(\d+) (failed|passed|skipped)", tail):
        n, kind = int(m.group(1)), m.group(2)
        failed, passed, skipped = (
            failed + (n if kind == "failed" else 0),
            passed + (n if kind == "passed" else 0),
            skipped + (n if kind == "skipped" else 0),
        )
    return failed, passed, skipped


def _tail_lines(text: str, limit: int) -> list[str]:
    """Return a bounded diagnostic tail without inventing output on success."""
    if limit <= 0:
        return []
    return text.strip().splitlines()[-limit:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--chunk-size", type=int, default=6, help="test files per subprocess")
    parser.add_argument("--timeout", type=int, default=900, help="per-test timeout (pytest-timeout)")
    parser.add_argument(
        "--shuffle-seed",
        type=int,
        default=None,
        help="deterministically shuffle test-file order (same seed = same order); "
        "order-coverage soak for AI-TEST-ISOLATION-1 chain B",
    )
    parser.add_argument(
        "--failure-tail-lines",
        type=int,
        default=120,
        help="stdout/stderr lines to print for a failing chunk; use 0 to suppress failure tails",
    )
    args = parser.parse_args(argv)

    chunks = collect_chunks(PROJECT_ROOT, args.chunk_size, args.shuffle_seed)
    if args.shuffle_seed is not None:
        print(f"shuffle-seed: {args.shuffle_seed} (deterministic file-order shuffle)", flush=True)
    total_failed = total_passed = total_skipped = 0
    bad_chunks: list[int] = []
    for i, chunk in enumerate(chunks, 1):
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                *chunk,
                "-q",
                f"--timeout={args.timeout}",
                "-p",
                "no:cacheprovider",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        tail = (proc.stdout or proc.stderr or "").strip().splitlines()
        summary = tail[-1] if tail else "(no output)"
        failed, passed, skipped = _parse_counts(summary)
        total_failed += failed
        total_passed += passed
        total_skipped += skipped
        marker = "ok" if proc.returncode == 0 else f"EXIT {proc.returncode}"
        print(f"chunk {i}/{len(chunks)} [{marker}]: {summary}", flush=True)
        if proc.returncode != 0:
            bad_chunks.append(i)
            stdout_tail = _tail_lines(proc.stdout, args.failure_tail_lines)
            stderr_tail = _tail_lines(proc.stderr, args.failure_tail_lines)
            if stdout_tail:
                print(f"--- chunk {i} stdout tail ({len(stdout_tail)} lines) ---", flush=True)
                print("\n".join(stdout_tail), flush=True)
            if stderr_tail:
                print(f"--- chunk {i} stderr tail ({len(stderr_tail)} lines) ---", flush=True)
                print("\n".join(stderr_tail), flush=True)

    print(
        f"TOTAL: {total_passed} passed, {total_failed} failed, {total_skipped} skipped across {len(chunks)} chunks",
        flush=True,
    )
    if bad_chunks:
        print(f"FAIL: chunk(s) {bad_chunks} did not exit clean", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
