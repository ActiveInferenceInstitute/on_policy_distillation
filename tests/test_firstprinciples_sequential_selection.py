"""Tests for sequential (horizon-dependent) active selection."""

from __future__ import annotations

import copy

import pytest

from firstprinciples import sequential_selection as seq


def test_horizon_matters_myopic_commits_sequential_cues() -> None:
    p = seq.build_payload()
    assert p["myopic_prefers_commit"] is True
    assert p["sequential_prefers_cue"] is True
    assert p["horizon_matters"] is True


def test_cue_first_lowest_policy_efe_and_highest_reward() -> None:
    p = seq.build_payload()
    pol = p["policies"]
    assert pol["cue_first"]["policy_efe"] < pol["commit_now"]["policy_efe"]
    assert pol["cue_first"]["expected_reward"] > pol["commit_now"]["expected_reward"]


def test_blind_cue_collapses_advantage() -> None:
    p = seq.build_payload()
    pol = p["policies"]
    # a blinded cue cannot resolve r, so cue-first is no better than commit
    assert pol["blind_cue_first"]["policy_efe"] >= pol["commit_now"]["policy_efe"] - 1e-9
    assert p["blind_cue_collapses_advantage"] is True


def test_validate_payload_accepts_honest_and_catches_lie() -> None:
    p = seq.build_payload()
    assert seq.validate_payload(p) == []
    bad = copy.deepcopy(p)
    bad["policies"]["cue_first"]["policy_efe"] = 9.0  # now sequential would not prefer cue
    assert seq.validate_payload(bad)


def test_horizon_gap_scales_linearly_with_remaining_steps() -> None:
    hz = seq.build_horizon_curve()
    gaps = [r["gap"] for r in hz["rows"]]
    delta = hz["per_step_instrumental_value"]
    increments = [gaps[i] - gaps[i - 1] for i in range(1, len(gaps))]
    # the cue's instrumental value is constant per remaining exploit step
    assert all(abs(inc - delta) < 1e-9 for inc in increments)
    assert hz["gap_strictly_increasing"] is True


def test_horizon_myopic_commits_but_all_h_ge_2_cue() -> None:
    hz = seq.build_horizon_curve()
    rows = {int(r["horizon"]): r for r in hz["rows"]}
    assert rows[1]["sequential_prefers_cue"] is False   # myopic commits
    assert all(rows[h]["sequential_prefers_cue"] for h in range(2, 7))
    assert 1.0 < hz["break_even_horizon"] < 2.0


def test_horizon_cost_in_derived_window_not_tuned() -> None:
    hz = seq.build_horizon_curve()
    assert hz["cost_in_derived_window"] is True
    assert hz["window_lower"] < hz["cost"] < hz["window_upper"]
    # a cost outside the derived window must NOT yield the regime
    below = seq.build_horizon_curve(cost=hz["window_lower"] - 0.1)
    assert below["myopic_prefers_commit_h1"] is False


def test_horizon_window_endpoints_are_energy_derived() -> None:
    # Pin the window endpoints to their INDEPENDENTLY-computed energy-derived values,
    # so a future hardcoded endpoint (RedTeam green-by-construction surface) is caught.
    p = seq.horizon_primitives()
    g_r, g_f, g_e = p["g_exploit_resolved"], p["g_exploit_flat"], p["g_cue_epistemic"]
    hz = seq.build_horizon_curve()
    assert hz["window_lower"] == pytest.approx(g_f - g_e, abs=1e-12)
    assert hz["window_upper"] == pytest.approx(2.0 * g_f - g_r - g_e, abs=1e-12)


def test_horizon_cost_above_window_breaks_cue_win() -> None:
    # A cost ABOVE the derived upper endpoint must make some H>=2 NOT prefer cue
    # (the other side of the window; tests previously only pinned the lower side).
    hz = seq.build_horizon_curve()
    above = seq.build_horizon_curve(cost=hz["window_upper"] + 0.1)
    assert above["cue_wins_for_all_horizon_ge_2"] is False


def test_validate_catches_fabricated_policy_block() -> None:
    # A policy block satisfying the inequalities but inconsistent with the energy
    # functional must now be caught (RedTeam-found gap: relational-only check).
    payload = copy.deepcopy(seq.build_payload())
    payload["policies"]["cue_first"]["g1"] = 0.05
    payload["policies"]["cue_first"]["g2"] = 0.05
    payload["policies"]["cue_first"]["policy_efe"] = 0.1  # still lowest, but wrong energy
    assert any("re-run energy" in i for i in seq.validate_payload(payload))


def test_horizon_blind_cue_collapses_at_every_horizon() -> None:
    hz = seq.build_horizon_curve()
    assert hz["blind_collapses_all_horizons"] is True
    assert all(r["blind_policy_efe"] >= r["commit_policy_efe"] - 1e-9 for r in hz["rows"])


def test_validate_payload_catches_lying_horizon_cost() -> None:
    import copy

    payload = copy.deepcopy(seq.build_payload())
    payload["horizon_curve"]["cost"] = 0.5  # below window -> myopic would not commit
    assert seq.validate_payload(payload)


def test_policy_efe_breakdown_is_consistent() -> None:
    row = seq.policy_efe(cue_first=True, cue_resolves=True)
    assert abs(row["policy_efe"] - (row["g1"] + row["g2"])) < 1e-12
