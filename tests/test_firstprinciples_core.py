"""Tests for the pure first-principles OPD<->active-inference modules."""

from __future__ import annotations

import math

import numpy as np
import pytest

from firstprinciples import divergences as dv
from firstprinciples import exposure_bias as eb
from firstprinciples import mapping
from firstprinciples import reward_tilting as rt
from firstprinciples import sdpg
from firstprinciples import taxonomy


# --------------------------------------------------------------------------- #
# divergences
# --------------------------------------------------------------------------- #
def test_normalize_projects_to_simplex() -> None:
    out = dv.normalize(np.array([1.0, 3.0]))
    assert pytest.approx(out.tolist()) == [0.25, 0.75]


def test_normalize_rejects_negative_and_zero() -> None:
    with pytest.raises(ValueError):
        dv.normalize(np.array([-1.0, 2.0]))
    with pytest.raises(ValueError):
        dv.normalize(np.array([0.0, 0.0]))


def test_kl_identity_is_zero_and_directional() -> None:
    p = np.array([0.7, 0.2, 0.1])
    assert dv.reverse_kl(p, p) == pytest.approx(0.0, abs=1e-12)
    assert dv.forward_kl(p, p) == pytest.approx(0.0, abs=1e-12)
    teacher = np.array([0.8, 0.15, 0.05])
    student = np.array([0.5, 0.3, 0.2])
    # forward and reverse KL differ (asymmetry) for distinct distributions.
    assert dv.forward_kl(teacher, student) != pytest.approx(dv.reverse_kl(student, teacher))


def test_symmetric_and_jensen_shannon_bounds() -> None:
    p = np.array([0.9, 0.1])
    q = np.array([0.1, 0.9])
    assert dv.symmetric_kl(p, q) > 0.0
    js = dv.jensen_shannon(p, q)
    assert 0.0 < js <= math.log(2.0) + 1e-9


def test_skew_kl_limits_and_validation() -> None:
    teacher = np.array([0.6, 0.4])
    student = np.array([0.5, 0.5])
    assert dv.skew_kl(teacher, student, 0.0) == pytest.approx(0.0, abs=1e-12)
    assert dv.skew_kl(teacher, student, 1.0) == pytest.approx(dv.forward_kl(teacher, student))
    with pytest.raises(ValueError):
        dv.skew_kl(teacher, student, 1.5)


def test_alpha_divergence_limits() -> None:
    p = np.array([0.7, 0.3])
    q = np.array([0.4, 0.6])
    assert dv.alpha_divergence(p, q, 1.0) == pytest.approx(dv.forward_kl(p, q))
    assert dv.alpha_divergence(p, q, 0.0) == pytest.approx(dv.reverse_kl(q, p))
    mid = dv.alpha_divergence(p, q, 0.5)
    assert mid > 0.0


def test_clipped_pointwise_kl_clips_and_infinite() -> None:
    student = np.array([0.5, 0.5])
    teacher = np.array([0.99, 0.01])
    unclipped = dv.clipped_pointwise_kl(student, teacher, clip=0.0)
    clipped = dv.clipped_pointwise_kl(student, teacher, clip=0.1)
    assert clipped <= unclipped
    # teacher zero where student has mass -> infinite
    assert math.isinf(dv.clipped_pointwise_kl(np.array([0.5, 0.5]), np.array([1.0, 0.0]), clip=0.0))


def test_mode_concentration_flags_mode_seeking() -> None:
    teacher = np.array([0.4, 0.3, 0.3])
    student = np.array([0.9, 0.05, 0.05])
    info = dv.mode_concentration(student, teacher)
    assert info["mode_seeking"] is True
    assert info["student_entropy"] < info["teacher_entropy"]


# --------------------------------------------------------------------------- #
# reward tilting
# --------------------------------------------------------------------------- #
def test_reward_tilted_target_is_optimal() -> None:
    reference = np.array([0.25, 0.25, 0.25, 0.25])
    reward = np.array([2.0, 0.5, -0.5, -2.0])
    cert = rt.verify_optimality(reference, reward, beta=1.0, trials=128)
    assert cert["optimal"] is True
    target = rt.reward_tilted_target(reference, reward, beta=1.0)
    assert target[0] > target[-1]  # mass shifts toward higher reward


def test_reward_tilting_validation() -> None:
    with pytest.raises(ValueError):
        rt.reward_tilted_target(np.array([0.5, 0.5]), np.array([1.0, 0.0]), beta=0.0)
    with pytest.raises(ValueError):
        rt.reward_tilted_target(np.array([0.5, 0.5]), np.array([1.0]), beta=1.0)
    with pytest.raises(ValueError):
        rt.reward_tilted_target(np.array([0.0, 0.0]), np.array([1.0, 0.0]), beta=1.0)


def test_free_energy_zero_at_target() -> None:
    reference = np.array([0.3, 0.7])
    reward = np.array([1.0, -1.0])
    target = rt.reward_tilted_target(reference, reward, beta=0.5)
    fe = rt.free_energy_against_tilted(target, reference, reward, beta=0.5)
    assert fe == pytest.approx(0.0, abs=1e-9)
    assert rt.expected_reward(target, reward) > rt.expected_reward(reference, reward)


# --------------------------------------------------------------------------- #
# exposure bias
# --------------------------------------------------------------------------- #
def test_drift_on_policy_beats_off_policy() -> None:
    spec = eb.DriftSpec(accuracy=0.9, horizon=24, on_recovery=0.5, off_recovery=0.0)
    curves = eb.drift_curves(spec)
    assert len(curves["off_policy"]) == 24
    assert curves["on_policy"][-1] > curves["off_policy"][-1]
    gap = eb.exposure_gap(spec)
    assert gap["off_policy_collapses"] is True
    assert gap["on_policy_fixed_point"] == pytest.approx(0.5 / (0.1 + 0.5))


def test_drift_validation() -> None:
    with pytest.raises(ValueError):
        eb.DriftSpec(accuracy=1.5)
    with pytest.raises(ValueError):
        eb.DriftSpec(horizon=0)


# --------------------------------------------------------------------------- #
# SDPG
# --------------------------------------------------------------------------- #
def test_sdpg_config_validation() -> None:
    with pytest.raises(ValueError):
        sdpg.SDPGConfig(kl_mode="bogus")
    with pytest.raises(ValueError):
        sdpg.SDPGConfig(beta=-1.0)


def test_softmax_is_distribution_and_validates() -> None:
    out = sdpg.softmax(np.array([1.0, 2.0, 3.0]))
    assert out.sum() == pytest.approx(1.0)
    with pytest.raises(ValueError):
        sdpg.softmax(np.array([1.0]), temperature=0.0)


def test_sdpg_loss_terms_and_modes() -> None:
    teacher = sdpg.softmax(np.array([2.0, 0.0, -1.0]))
    student = sdpg.softmax(np.array([0.3, 0.2, 0.0]))
    reference = sdpg.softmax(np.array([0.0, 0.0, 0.0]))
    for mode in ("fkl", "rkl", "ufkl", "urkl"):
        out = sdpg.sdpg_loss(student, teacher, reference, advantage=1.0, config=sdpg.SDPGConfig(kl_mode=mode))
        assert set(out) >= {"clip_term", "distill_term", "ref_kl_term", "total"}
        assert math.isfinite(out["total"])
    # forward and reverse self-distillation differ.
    fwd = sdpg.self_distillation_term(student, teacher, "fkl")
    rev = sdpg.self_distillation_term(student, teacher, "rkl")
    assert fwd != pytest.approx(rev)
    with pytest.raises(ValueError):
        sdpg.self_distillation_term(student, teacher, "bad")


def test_sdpg_signal_density_is_dense() -> None:
    teacher = sdpg.softmax(np.array([2.0, 0.0, -1.0, -2.0]))
    student = sdpg.softmax(np.array([0.5, 0.2, 0.0, -0.5]))
    density = sdpg.signal_density(student, teacher)
    assert density["denser_than_scalar"] is True
    assert density["density_ratio"] >= 2.0


# --------------------------------------------------------------------------- #
# mapping + taxonomy
# --------------------------------------------------------------------------- #
def test_mapping_is_sound_and_queryable() -> None:
    assert mapping.validate_mapping() == []
    payload = mapping.build_payload()
    assert payload["ok"] is True
    assert payload["row_count"] == len(mapping.CORRESPONDENCES)
    row = mapping.lookup("Markov blanket")
    assert "asymmetry" in row.opd_counterpart.lower()
    with pytest.raises(KeyError):
        mapping.lookup("not a real component")
    assert "Active inference" in mapping.markdown_table()


def test_taxonomy_structure() -> None:
    payload = taxonomy.build_payload()
    assert payload["method_count"] == len(taxonomy.METHODS)
    assert payload["on_policy_count"] >= 6
    assert payload["privileged_info_count"] >= 5
    # SDPG is present and is a privileged-info on-policy method.
    sdpg_method = next(m for m in taxonomy.METHODS if m.acronym == "SDPG")
    assert sdpg_method.on_policy and sdpg_method.privileged_info
    assert sdpg_method.bibkey == "liu2026sdpg"
    assert taxonomy.loss_share_total() == pytest.approx(1.0, abs=1e-9)
    assert "SDPG" in taxonomy.markdown_table()
    # Hinton KD is the off-policy baseline.
    assert taxonomy.METHODS[0].on_policy is False
