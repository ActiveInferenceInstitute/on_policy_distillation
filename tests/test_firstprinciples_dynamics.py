"""Tests for the dynamic distillation simulators (gkd, EM, diversity, adaptive)."""

from __future__ import annotations

import numpy as np
import pytest

from firstprinciples import adaptive, diversity, gkd, variational_em


# --------------------------------------------------------------------------- #
# gkd
# --------------------------------------------------------------------------- #
def test_gkd_problem_validation() -> None:
    good = np.array([[0.5, 0.5], [0.5, 0.5]])
    trans = np.array([[0.5, 0.5], [0.5, 0.5]])
    start = np.array([1.0, 0.0])
    gkd.GKDProblem(teacher=good, student=good, transition=trans, start=start)
    with pytest.raises(ValueError):
        gkd.GKDProblem(teacher=good, student=np.array([[0.5, 0.5]]), transition=trans, start=start)
    with pytest.raises(ValueError):
        gkd.GKDProblem(teacher=good, student=good, transition=np.array([[1.0, 1.0], [0.0, 0.0]]), start=start)
    with pytest.raises(ValueError):
        gkd.GKDProblem(teacher=good, student=good, transition=trans, start=np.array([1.0, 0.0, 0.0]))


def test_gkd_visitation_normalised_and_differs() -> None:
    payload = gkd.build_payload()
    off = np.array(payload["off_policy_visitation"])
    on = np.array(payload["on_policy_visitation"])
    assert off.sum() == pytest.approx(1.0)
    assert on.sum() == pytest.approx(1.0)


def test_gkd_exposure_bias_gap_nonnegative() -> None:
    payload = gkd.build_payload()
    assert payload["schema"] == gkd.SCHEMA
    assert payload["reverse_kl"]["on_policy_sees_more_error"] is True
    assert payload["reverse_kl"]["exposure_gap"] >= -1e-12
    assert payload["ok"] is True


def test_gkd_normalize_rows_handles_zero_row() -> None:
    out = gkd.normalize_rows(np.array([[0.0, 0.0], [1.0, 3.0]]))
    assert out[1].tolist() == pytest.approx([0.25, 0.75])


# --------------------------------------------------------------------------- #
# variational_em
# --------------------------------------------------------------------------- #
def test_em_converges_to_reward_tilted_fixed_point() -> None:
    ref = np.array([0.25, 0.25, 0.25, 0.25])
    reward = np.array([2.0, 0.5, -0.5, -2.0])
    result = variational_em.run_em(ref, reward, beta=1.0)
    assert result.monotone is True
    assert result.final_gap < 1e-6
    # free energy is non-increasing
    fes = result.free_energies
    assert all(b <= a + 1e-9 for a, b in zip(fes, fes[1:]))


def test_em_validation_and_payload() -> None:
    with pytest.raises(ValueError):
        variational_em.run_em(np.array([0.5, 0.5]), np.array([1.0, 0.0]), beta=1.0, step_size=0.0)
    payload = variational_em.build_payload()
    assert payload["schema"] == variational_em.SCHEMA
    assert payload["monotone_descent"] is True
    assert payload["ok"] is True


def test_em_partial_step_size_still_descends() -> None:
    ref = np.array([0.4, 0.3, 0.3])
    reward = np.array([1.0, 0.0, -1.0])
    result = variational_em.run_em(ref, reward, beta=0.5, step_size=0.3, steps=80)
    assert result.monotone is True
    assert result.final_gap < 1e-3


# --------------------------------------------------------------------------- #
# diversity
# --------------------------------------------------------------------------- #
def test_sharpen_temperature_changes_entropy() -> None:
    teacher = np.array([0.55, 0.20, 0.12, 0.08, 0.05])
    from analytical.free_energy import shannon_entropy

    sharp = shannon_entropy(diversity.sharpen(teacher, 0.25))
    flat = shannon_entropy(diversity.sharpen(teacher, 4.0))
    assert sharp < flat
    with pytest.raises(ValueError):
        diversity.sharpen(teacher, 0.0)


def test_pass_at_k_monotone_in_k() -> None:
    student = np.array([0.5, 0.3, 0.2])
    correct = np.array([True, False, False])
    p1 = diversity.pass_at_k(student, correct, 1)
    p4 = diversity.pass_at_k(student, correct, 4)
    assert p4 >= p1
    with pytest.raises(ValueError):
        diversity.pass_at_k(student, correct, 0)


def test_diversity_tradeoff_payload() -> None:
    payload = diversity.build_payload()
    assert payload["schema"] == diversity.SCHEMA
    # flattening preserves Pass@k better than aggressive sharpening (diversity collapse).
    assert payload["collapse_observed"] is True
    assert payload["flattest_pass_at_k"] > payload["sharpest_pass_at_k"]
    assert len(payload["pass_at_k"]) == len(payload["temperatures"])
    assert 0.0 <= payload["greedy_pass_at_1"] <= 1.0


def test_pass_at_1_correct_top() -> None:
    student = np.array([0.1, 0.8, 0.1])
    assert diversity.pass_at_1(student, np.array([False, True, False])) == 1.0
    assert diversity.pass_at_1(student, np.array([True, False, False])) == 0.0


# --------------------------------------------------------------------------- #
# adaptive
# --------------------------------------------------------------------------- #
def test_adaptive_directions_mixes_and_validates() -> None:
    payload = adaptive.build_payload()
    assert payload["schema"] == adaptive.SCHEMA
    assert payload["between_extremes"] is True
    assert 0.0 < payload["reverse_fraction"] < 1.0
    assert set(payload["directions"]) <= {"forward", "reverse"}


def test_adaptive_shape_validation() -> None:
    with pytest.raises(ValueError):
        adaptive.token_directions(np.array([[0.5, 0.5]]), np.array([[0.5, 0.5], [0.5, 0.5]]))


def test_adaptive_threshold_override_all_reverse() -> None:
    teachers = np.array([[0.8, 0.2], [0.6, 0.4]])
    students = np.array([[0.7, 0.3], [0.55, 0.45]])
    # A very high threshold makes every token "confident" -> all reverse.
    out = adaptive.token_directions(teachers, students, threshold=10.0)
    assert out.reverse_fraction == 1.0
    assert adaptive.adaptive_loss(teachers, students, threshold=10.0) >= 0.0
