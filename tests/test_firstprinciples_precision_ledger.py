"""Tests for the result-integrity ledger (synthesis: all-precise + all-controlled)."""

from __future__ import annotations

import copy
from pathlib import Path

from firstprinciples import precision_ledger as pl


def test_all_results_precise_and_controlled(project_root: Path) -> None:
    p = pl.build_payload(project_root)
    assert p["all_precise"] is True
    assert p["all_controlled"] is True
    assert p["ok"] is True
    assert p["max_residual"] < p["precision_tolerance"]
    assert p["result_count"] >= 6 and p["control_count"] >= 5
    for r in p["precision_rows"]:
        assert r["within_tol"] is True
    for r in p["control_rows"]:
        assert r["bites"] is True


def test_validate_payload_internal_consistency(project_root: Path) -> None:
    p = pl.build_payload(project_root)
    assert pl.validate_payload(p) == []
    bad = copy.deepcopy(p)
    bad["precision_rows"][0]["residual"] = 9.9  # exceeds tol but stored flag left true
    assert pl.validate_payload(bad)  # re-derived all_precise disagrees


def test_cross_read_catches_lying_residual(project_root: Path) -> None:
    # A row that claims a residual the source artifact does not contain is caught.
    p = pl.build_payload(project_root)
    assert pl.validate_against_sources(project_root, p) == []
    bad = copy.deepcopy(p)
    bad["precision_rows"][1]["residual"] = 9.9  # source says ~0
    assert any("does not match source" in i for i in pl.validate_against_sources(project_root, bad))


def test_cross_read_catches_lying_control(project_root: Path) -> None:
    p = pl.build_payload(project_root)
    bad = copy.deepcopy(p)
    bad["control_rows"][0]["bites"] = False  # source says True
    assert any("control" in i and "does not match" in i for i in pl.validate_against_sources(project_root, bad))
