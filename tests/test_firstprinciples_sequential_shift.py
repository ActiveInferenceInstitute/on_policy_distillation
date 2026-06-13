"""Tests for the deterministic finite sequential-shift witness."""

from __future__ import annotations

import numpy as np
import pytest

from firstprinciples import sequential_shift


def test_sequential_shift_payload_contract() -> None:
    payload = sequential_shift.build_payload()
    assert payload["schema"] == sequential_shift.SCHEMA
    assert payload["state_names"] == list(sequential_shift.STATE_NAMES)
    assert payload["action_names"] == list(sequential_shift.ACTION_NAMES)
    assert payload["state_count"] == 4
    assert payload["action_count"] == 2
    assert payload["horizon"] == 8
    assert payload["ok"] is True
    assert sequential_shift.validate_payload(payload) == []

    for key in ("train_visitation", "student_test_visitation_before", "student_test_visitation_after"):
        values = np.array(payload[key], dtype=np.float64)
        assert values.sum() == pytest.approx(1.0)
        assert np.all(np.isfinite(values))
        assert np.all(values >= 0.0)

    assert payload["teacher_forced_train_underestimates_student_test"] is True
    assert payload["on_policy_correction_reduces_test_loss"] is True
    assert payload["train_loss"] < payload["test_loss_before"]
    assert payload["test_loss_after"] < payload["test_loss_before"]
    assert payload["shift_mass"] > 0.0
    assert payload["gap_closed"] > 0.0


def test_sequential_shift_sensitivity_payload_contract() -> None:
    payload = sequential_shift.build_sensitivity_payload()
    assert payload["schema"] == sequential_shift.SENSITIVITY_SCHEMA
    assert payload["state_names"] == list(sequential_shift.STATE_NAMES)
    assert payload["action_names"] == list(sequential_shift.ACTION_NAMES)
    assert payload["row_count"] == len(sequential_shift.CORRECTION_FRACTIONS)
    assert payload["correction_fractions"] == list(sequential_shift.CORRECTION_FRACTIONS)
    assert payload["ok"] is True
    assert sequential_shift.validate_sensitivity_payload(payload) == []

    rows = payload["rows"]
    losses = [row["test_loss"] for row in rows]
    shifts = [row["shift_mass"] for row in rows]
    assert all(b <= a for a, b in zip(losses, losses[1:], strict=False))
    assert all(b <= a for a, b in zip(shifts, shifts[1:], strict=False))
    assert payload["test_loss_reduction"] == pytest.approx(losses[0] - losses[-1])
    assert payload["shift_mass_reduction"] == pytest.approx(shifts[0] - shifts[-1])
    assert payload["test_loss_reduction"] > 0.0
    assert payload["shift_mass_reduction"] > 0.0
    assert rows[0]["train_underestimates_test"] is True
    assert all(row["normalized"] and row["finite"] for row in rows)

    for row in rows:
        policy = np.array(row["student_policy"], dtype=np.float64)
        visitation = np.array(row["student_test_visitation"], dtype=np.float64)
        assert np.allclose(policy.sum(axis=1), 1.0)
        assert visitation.sum() == pytest.approx(1.0)


def test_sequential_shift_problem_rejects_non_normalized_probabilities() -> None:
    good_policy = np.array([[0.5, 0.5]] * 4, dtype=np.float64)
    good_transitions = np.stack([np.eye(4, dtype=np.float64), np.eye(4, dtype=np.float64)])
    start = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    with pytest.raises(ValueError, match="teacher_policy rows must be normalized"):
        sequential_shift.SequentialShiftProblem(
            teacher_policy=good_policy * 2.0,
            student_policy_before=good_policy,
            student_policy_after=good_policy,
            action_transitions=good_transitions,
            start=start,
        )


def test_sequential_shift_validator_negative_controls() -> None:
    payload = sequential_shift.build_payload()
    bad = dict(payload)
    bad["train_visitation"] = [0.5, 0.5, 0.5, 0.5]
    bad["ok"] = True
    assert sequential_shift.validate_payload(bad)

    bad = dict(payload)
    bad["test_loss_after"] = bad["test_loss_before"]
    bad["on_policy_correction_reduces_test_loss"] = False
    bad["ok"] = True
    issues = sequential_shift.validate_payload(bad)
    assert any("correction" in issue for issue in issues)


def test_sequential_shift_sensitivity_validator_negative_controls() -> None:
    payload = sequential_shift.build_sensitivity_payload()
    bad = dict(payload)
    bad["rows"] = [dict(row) for row in payload["rows"]]
    bad["rows"][1]["test_loss"] = bad["rows"][0]["test_loss"] + 1.0
    bad["rows"][1]["student_induced_test_loss"] = bad["rows"][1]["test_loss"]
    bad["ok"] = True
    issues = sequential_shift.validate_sensitivity_payload(bad)
    assert any("monotonically" in issue for issue in issues)

    bad = dict(payload)
    bad["rows"] = [dict(row) for row in payload["rows"]]
    bad["rows"][0]["student_test_visitation"] = [0.5, 0.5, 0.5, 0.5]
    bad["rows"][0]["normalized"] = True
    bad["ok"] = True
    issues = sequential_shift.validate_sensitivity_payload(bad)
    assert any("student_test_visitation" in issue for issue in issues)
