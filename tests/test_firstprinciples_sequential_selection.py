"""Tests for sequential (horizon-dependent) active selection."""

from __future__ import annotations

import copy

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


def test_policy_efe_breakdown_is_consistent() -> None:
    row = seq.policy_efe(cue_first=True, cue_resolves=True)
    assert abs(row["policy_efe"] - (row["g1"] + row["g2"])) < 1e-12
