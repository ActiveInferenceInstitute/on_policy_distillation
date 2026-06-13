"""Durable test-isolation soak report contract."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def _load_soak_module(project_root: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "run_test_isolation_soak",
        project_root / "scripts" / "run_test_isolation_soak.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_total_line_extracts_chunked_summary(project_root: Path) -> None:
    soak = _load_soak_module(project_root)
    payload = """
shuffle-seed: 61300 (deterministic file-order shuffle)
chunk 1/2 [ok]: 8 passed in 3.21s
chunk 2/2 [ok]: 7 passed, 1 skipped in 2.98s
TOTAL: 15 passed, 0 failed, 1 skipped across 2 chunks
"""

    totals = soak.parse_total_line(payload)

    assert totals == {
        "passed": 15,
        "failed": 0,
        "skipped": 1,
        "chunks": 2,
        "summary": "TOTAL: 15 passed, 0 failed, 1 skipped across 2 chunks",
    }


def test_soak_report_distinguishes_partial_and_complete_runs(project_root: Path) -> None:
    soak = _load_soak_module(project_root)
    green_row = {
        "run_index": 1,
        "shuffle_seed": 61300,
        "returncode": 0,
        "ok": True,
        "summary": "TOTAL: 529 passed, 0 failed, 1 skipped across 11 chunks",
        "passed": 529,
        "failed": 0,
        "skipped": 1,
        "chunk_count": 11,
    }

    partial = soak.build_report([green_row], required_runs=5)
    complete = soak.build_report([{**green_row, "run_index": index + 1} for index in range(5)], required_runs=5)

    assert partial["all_runs_green"] is True
    assert partial["complete_soak"] is False
    assert partial["max_consecutive_green_count"] == 1
    assert complete["all_runs_green"] is True
    assert complete["complete_soak"] is True
    assert complete["max_consecutive_green_count"] == 5


def test_soak_report_resets_consecutive_count_on_failure(project_root: Path) -> None:
    soak = _load_soak_module(project_root)
    rows = [
        {"run_index": 1, "ok": True},
        {"run_index": 2, "ok": True},
        {"run_index": 3, "ok": False, "returncode": 1},
        {"run_index": 4, "ok": True},
    ]

    report = soak.build_report(rows, required_runs=3)

    assert report["all_runs_green"] is False
    assert report["complete_soak"] is False
    assert report["max_consecutive_green_count"] == 2
    assert report["trailing_consecutive_green_count"] == 1
