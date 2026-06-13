"""Durable test-isolation soak report contract."""

from __future__ import annotations

import importlib.util
import json
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


def _green_row(index: int, seed: int) -> dict[str, object]:
    return {
        "run_index": index,
        "shuffle_seed": seed,
        "returncode": 0,
        "ok": True,
        "summary": "TOTAL: 529 passed, 0 failed, 1 skipped across 11 chunks",
        "passed": 529,
        "failed": 0,
        "skipped": 1,
        "chunk_count": 11,
        "failed_chunk_ids": [],
        "failed_tests": [],
        "diagnostics_complete": True,
    }


def _red_row(soak: ModuleType, index: int, seed: int) -> dict[str, object]:
    row = {
        "run_index": index,
        "shuffle_seed": seed,
        "returncode": 1,
        "ok": False,
        "summary": "TOTAL: 528 passed, 1 failed, 1 skipped across 11 chunks",
        "passed": 528,
        "failed": 1,
        "skipped": 1,
        "chunk_count": 11,
        "stdout_tail": [
            "chunk 4/11 [EXIT 1]: tests/test_alpha.py tests/test_beta.py",
            "FAILED tests/test_alpha.py::test_order_sensitive - AssertionError: leaked state",
            "TOTAL: 528 passed, 1 failed, 1 skipped across 11 chunks",
        ],
        "stderr_tail": [],
    }
    return soak.attach_failure_diagnostics(row)


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
    green_row = _green_row(1, 61300)

    partial = soak.build_report([green_row], required_runs=5)
    complete = soak.build_report([_green_row(index + 1, 61300 + index) for index in range(5)], required_runs=5)

    assert partial["all_runs_green"] is True
    assert partial["complete_soak"] is False
    assert partial["max_consecutive_green_count"] == 1
    assert complete["all_runs_green"] is True
    assert complete["complete_soak"] is True
    assert complete["max_consecutive_green_count"] == 5


def test_soak_report_resets_consecutive_count_on_failure(project_root: Path) -> None:
    soak = _load_soak_module(project_root)
    rows = [
        _green_row(1, 61300),
        _green_row(2, 61301),
        _red_row(soak, 3, 61302),
        _green_row(4, 61303),
    ]

    report = soak.build_report(rows, required_runs=3)

    assert report["all_runs_green"] is False
    assert report["complete_soak"] is False
    assert report["max_consecutive_green_count"] == 2
    assert report["trailing_consecutive_green_count"] == 1


def test_failure_diagnostics_extract_chunk_and_failed_test(project_root: Path) -> None:
    soak = _load_soak_module(project_root)
    row = _red_row(soak, 1, 61300)

    assert row["failed_chunk_ids"] == [4]
    assert row["failed_tests"] == ["tests/test_alpha.py::test_order_sensitive"]
    assert row["diagnostics_complete"] is True


def test_validate_report_accepts_complete_soak(project_root: Path, tmp_path: Path) -> None:
    soak = _load_soak_module(project_root)
    report = soak.build_report([_green_row(index + 1, 61300 + index) for index in range(5)], required_runs=5)
    report_path = tmp_path / "soak.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    assert soak.validate_report_payload(report, require_complete=True) == []
    assert soak.main(["--validate-report", str(report_path), "--require-complete"]) == 0


def test_validate_report_rejects_false_complete_soak(project_root: Path) -> None:
    soak = _load_soak_module(project_root)
    report = soak.build_report([_green_row(1, 61300)], required_runs=5)
    report["complete_soak"] = True

    issues = soak.validate_report_payload(report)

    assert any("complete_soak" in issue for issue in issues)


def test_validate_report_rejects_red_rows_without_diagnostics(project_root: Path) -> None:
    soak = _load_soak_module(project_root)
    row = _red_row(soak, 1, 61300)
    row["stdout_tail"] = []
    row["failed_chunk_ids"] = []
    row["failed_tests"] = []
    row["diagnostics_complete"] = False
    report = soak.build_report([row], required_runs=5)

    issues = soak.validate_report_payload(report)

    assert any("red without complete failure diagnostics" in issue for issue in issues)


def test_validate_report_rejects_non_consecutive_seeds(project_root: Path) -> None:
    soak = _load_soak_module(project_root)
    report = soak.build_report([_green_row(1, 61300), _green_row(2, 61302)], required_runs=2)

    issues = soak.validate_report_payload(report)

    assert any("consecutive" in issue for issue in issues)


def test_validate_report_rejects_malformed_totals(project_root: Path) -> None:
    soak = _load_soak_module(project_root)
    row = _green_row(1, 61300)
    row["summary"] = "TOTAL: 528 passed, 0 failed, 1 skipped across 11 chunks"
    report = soak.build_report([row], required_runs=1)

    issues = soak.validate_report_payload(report)

    assert any("passed disagrees" in issue for issue in issues)
