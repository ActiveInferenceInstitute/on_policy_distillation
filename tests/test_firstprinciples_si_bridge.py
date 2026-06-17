"""Tests for the analytical <-> pymdp SI bridge (observable + quantitative)."""

from __future__ import annotations

import copy
from pathlib import Path

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


def test_validate_payload_accepts_honest_and_catches_lie(project_root: Path) -> None:
    p = si_bridge.build_payload(project_root)
    assert si_bridge.validate_payload(p) == []
    bad = copy.deepcopy(p)
    # move the cue after the arm in the stored sequence -> re-derivation must catch
    bad["realized_location_sequence"] = ["center", "left_arm", "cue_location"]
    bad["cue_step"] = 2
    assert si_bridge.validate_payload(bad)
