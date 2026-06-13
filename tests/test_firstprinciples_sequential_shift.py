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
