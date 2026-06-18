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
    assert p["result_count"] >= 6 and p["control_count"] >= 5
    for r in p["precision_rows"]:
        assert r["residual"] < r["tolerance"]  # each within its TIER tolerance
        assert r["within_tol"] is True
    for r in p["control_rows"]:
        assert r["margin"] > r["min_margin"]   # each control bites by a MEASURED margin
        assert r["bites"] is True


def test_tolerances_are_tight_not_vacuous(project_root: Path) -> None:
    # Tier-aware tolerances with single-digit headroom (RedTeam: a 28x-loose tol is vacuous).
    p = pl.build_payload(project_root)
    assert p["tier_tolerances"]["1"] <= 1e-12  # identities held to near machine zero
    assert p["tier_tolerances"]["2"] <= 1e-07  # witnesses
    # the worst Tier-2 residual is within ~one order of magnitude of its tolerance
    t2 = [r for r in p["precision_rows"] if r["tier"] == 2]
    worst = max(r["residual"] for r in t2)
    assert worst < p["tier_tolerances"]["2"]
    assert worst * 100 > p["tier_tolerances"]["2"]  # not absurdly loose (< 100x headroom)


def test_a_degraded_residual_fails_precision(project_root: Path) -> None:
    # A Tier-1 identity residual just above its tolerance must fail (falsifiable).
    p = copy.deepcopy(pl.build_payload(project_root))
    t1 = next(r for r in p["precision_rows"] if r["tier"] == 1)
    t1["residual"] = float(t1["tolerance"]) * 10
    issues = pl.validate_payload(p)
    assert any("all_precise" in i for i in issues)


def test_a_collapsed_control_margin_fails(project_root: Path) -> None:
    # A control whose margin falls below the threshold must fail (control no longer bites).
    p = copy.deepcopy(pl.build_payload(project_root))
    p["control_rows"][0]["margin"] = 1e-9  # below min_margin
    issues = pl.validate_payload(p)
    assert any("all_controlled" in i for i in issues)


def test_cross_read_catches_lying_residual_and_margin(project_root: Path) -> None:
    p = pl.build_payload(project_root)
    assert pl.validate_against_sources(project_root, p) == []
    bad_res = copy.deepcopy(p)
    bad_res["precision_rows"][1]["residual"] = 9.9  # source says ~0
    assert any("residual" in i and "does not match source" in i for i in pl.validate_against_sources(project_root, bad_res))
    bad_ctrl = copy.deepcopy(p)
    bad_ctrl["control_rows"][0]["margin"] = 42.0  # source says ~0.693
    assert any("control margin" in i and "does not match source" in i for i in pl.validate_against_sources(project_root, bad_ctrl))
