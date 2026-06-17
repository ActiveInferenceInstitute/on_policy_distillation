"""Tests for the multi-state generality of the active-selection identity."""

from __future__ import annotations

import copy

import pytest

from firstprinciples import active_selection_general as gen


def test_identity_holds_for_all_channels() -> None:
    payload = gen.build_payload()
    assert payload["identity_holds_multistate"] is True
    assert payload["max_identity_residual"] < 1e-12
    for row in payload["channels"]:
        assert abs((row["prior_entropy"] - row["residual_gap"]) - row["epistemic_value"]) < 1e-12


def test_perfect_channels_close_gap_underresolving_does_not() -> None:
    rows = {r["name"]: r for r in gen.build_payload()["channels"]}
    assert rows["perfect3_k3"]["residual_gap"] < 1e-9
    assert rows["perfect4_k4"]["residual_gap"] < 1e-9
    assert rows["perfect3_k4"]["residual_gap"] < 1e-9  # k>n still resolves
    assert rows["under4_k3"]["residual_gap"] > 1e-3   # k<n cannot reach zero


def test_blind_channel_zero_epistemic_and_ranks_last() -> None:
    payload = gen.build_payload()
    rows = {r["name"]: r for r in payload["channels"]}
    assert rows["blind3_k3"]["epistemic_value"] < 1e-12
    assert payload["epistemic_ranking"][-1] == "blind3_k3"


def test_wrong_measure_ablation_breaks_identity() -> None:
    payload = gen.build_payload()
    assert payload["wrong_measure_breaks_identity"] is True
    assert payload["wrong_measure_residual_gap"] > 1e-3


def test_validate_payload_accepts_honest_and_catches_lie() -> None:
    payload = gen.build_payload()
    assert gen.validate_payload(payload) == []
    bad = copy.deepcopy(payload)
    bad["channels"][0]["residual_gap"] = bad["channels"][0]["residual_gap"] + 0.5
    assert gen.validate_payload(bad)  # identity now violated -> caught


def test_validate_rederives_selection_flags_not_just_identity() -> None:
    # Give the blind channel a high epistemic value but keep its row identity intact
    # (residual = H - epistemic). The re-derived ranking must still catch that the
    # blind channel no longer ranks last -- proving validate checks selection from
    # rows, not just the per-row identity. (RedTeam-found gap.)
    payload = gen.build_payload()
    bad = copy.deepcopy(payload)
    for r in bad["channels"]:
        if r["name"] == "blind3_k3":
            r["epistemic_value"] = 1.0
            r["residual_gap"] = r["prior_entropy"] - 1.0  # identity preserved
    issues = gen.validate_payload(bad)
    assert any("rank last" in i for i in issues)


def test_unnormalised_channel_raises() -> None:
    with pytest.raises(ValueError):
        gen.score_channel(gen.Channel("bad", ((0.7, 0.7, 0.7), (0.1, 0.1, 0.1), (0.2, 0.2, 0.2))))
