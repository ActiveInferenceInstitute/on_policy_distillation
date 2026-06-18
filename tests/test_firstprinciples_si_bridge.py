"""Tests for the analytical <-> pymdp SI bridge (observable + quantitative)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from firstprinciples import si_bridge


def test_cue_before_arm_and_entropy_collapse(project_root: Path) -> None:
    p = si_bridge.build_payload(project_root)
    assert p["cue_before_arm"] is True
    assert p["cue_step"] < p["first_arm_step"]
    assert p["entropy_collapses_at_cue"] is True


def test_quantitative_match_to_si_post_cue_entropy(project_root: Path) -> None:
    # The headline: analytical residual == pymdp post-cue belief entropy to <1e-6.
    p = si_bridge.build_payload(project_root)
    assert p["quantitative_match"] is True
    assert p["residual_entropy_match_abs"] < 1e-6
    assert p["efe_selects_cue_at_validity"] is True


def test_match_is_validity_specific_and_blinded_control_bites(project_root: Path) -> None:
    p = si_bridge.build_payload(project_root)
    assert p["match_is_validity_specific"] is True   # wrong validities do NOT match
    assert p["blinded_control_bites"] is True


def test_analytical_residual_tracks_validity() -> None:
    # closed-form residual falls as the cue sharpens (reuses active_selection)
    assert si_bridge.analytical_residual_at_validity(0.5) > si_bridge.analytical_residual_at_validity(0.95)
    assert si_bridge.analytical_residual_at_validity(1.0) < 1e-9


def test_per_step_trajectory_matches_pymdp(project_root: Path) -> None:
    # The analytical running-Bayesian belief entropy predicts the pymdp SI agent's
    # entropy at EVERY step, not just post-cue.
    p = si_bridge.build_payload(project_root)
    assert p["trajectory_match"] is True
    assert p["max_trajectory_error_abs"] < 1e-6
    assert len(p["analytical_entropy_by_step"]) == len(p["belief_entropy_by_step"])
    assert p["monotone_collapse_measured"] is True and p["monotone_collapse_predicted"] is True


def test_trajectory_controls_bite(project_root: Path) -> None:
    p = si_bridge.build_payload(project_root)
    assert p["wrong_validity_breaks_trajectory"] is True   # wrong cue validity
    assert p["shuffled_order_breaks_trajectory"] is True    # reversed observation order


def test_trajectory_rederived_from_obs_not_stored_vector(project_root: Path) -> None:
    # A lie in the stored analytical vector is harmless (validate recomputes from
    # the observation sequences); a tampered observation sequence is caught.
    import copy

    p = si_bridge.build_payload(project_root)
    lied_vector = copy.deepcopy(p)
    lied_vector["analytical_entropy_by_step"] = [0.1] * len(p["belief_entropy_by_step"])
    assert si_bridge.validate_payload(lied_vector) == []  # recomputed, not trusted
    tampered_obs = copy.deepcopy(p)
    tampered_obs["cue_obs_by_step"] = [0] * len(p["cue_obs_by_step"])  # remove the cue
    assert si_bridge.validate_payload(tampered_obs)


def test_analytical_entropy_trajectory_shape() -> None:
    import math

    # flat -> cue -> reward: ln2, H([0.9,0.1]), 0
    traj = si_bridge.analytical_entropy_trajectory([0, 1, 0], [0, 0, 1], 0.9)
    assert traj[0] == pytest.approx(math.log(2), abs=1e-9)
    assert traj[1] == pytest.approx(-0.9 * math.log(0.9) - 0.1 * math.log(0.1), abs=1e-9)
    assert traj[2] == pytest.approx(0.0, abs=1e-12)


def test_validate_payload_accepts_honest_and_catches_lie(project_root: Path) -> None:
    p = si_bridge.build_payload(project_root)
    assert si_bridge.validate_payload(p) == []
    bad = copy.deepcopy(p)
    # move the cue after the arm in the stored sequence -> re-derivation must catch
    bad["realized_location_sequence"] = ["center", "left_arm", "cue_location"]
    bad["cue_step"] = 2
    assert si_bridge.validate_payload(bad)
