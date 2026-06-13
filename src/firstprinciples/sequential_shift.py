"""Finite sequential distribution-shift witness for OPD as active sampling.

This module is deliberately small and closed form. A four-state, two-action
student can visit states under its own policy that teacher-forced training
underweights. The artifact compares the teacher-forced train visitation against
the student-induced test visitation before and after a deterministic
on-policy correction. It is a witness for distribution-shift accounting, not an
empirical OPD benchmark.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .divergences import reverse_kl

ArrayF = NDArray[np.float64]

SCHEMA = "firstprinciples.sequential_shift.v1"
SENSITIVITY_SCHEMA = "firstprinciples.sequential_shift_sensitivity.v1"
STATE_NAMES = ("prompt", "teacher_path", "student_drift", "repair")
ACTION_NAMES = ("stay_on_task", "shortcut")
CORRECTION_FRACTIONS = (0.0, 0.25, 0.5, 0.75, 1.0)

__all__ = [
    "ACTION_NAMES",
    "CORRECTION_FRACTIONS",
    "SCHEMA",
    "SENSITIVITY_SCHEMA",
    "STATE_NAMES",
    "SequentialShiftProblem",
    "build_payload",
    "build_sensitivity_payload",
    "induced_transition",
    "validate_payload",
    "validate_sensitivity_payload",
    "visitation",
]


@dataclass(frozen=True)
class SequentialShiftProblem:
    """A finite policy-induced state-visitation problem."""

    teacher_policy: ArrayF
    student_policy_before: ArrayF
    student_policy_after: ArrayF
    action_transitions: ArrayF
    start: ArrayF
    horizon: int = 8

    def __post_init__(self) -> None:
        states = len(STATE_NAMES)
        actions = len(ACTION_NAMES)
        arrays = {
            "teacher_policy": np.asarray(self.teacher_policy, dtype=np.float64),
            "student_policy_before": np.asarray(self.student_policy_before, dtype=np.float64),
            "student_policy_after": np.asarray(self.student_policy_after, dtype=np.float64),
            "action_transitions": np.asarray(self.action_transitions, dtype=np.float64),
            "start": np.asarray(self.start, dtype=np.float64),
        }
        if arrays["teacher_policy"].shape != (states, actions):
            raise ValueError("teacher_policy must have shape (states, actions)")
        if arrays["student_policy_before"].shape != (states, actions):
            raise ValueError("student_policy_before must have shape (states, actions)")
        if arrays["student_policy_after"].shape != (states, actions):
            raise ValueError("student_policy_after must have shape (states, actions)")
        if arrays["action_transitions"].shape != (actions, states, states):
            raise ValueError("action_transitions must have shape (actions, states, states)")
        if arrays["start"].shape != (states,):
            raise ValueError("start must have one entry per state")
        if self.horizon <= 0:
            raise ValueError("horizon must be positive")
        for name in ("teacher_policy", "student_policy_before", "student_policy_after"):
            _require_row_stochastic(arrays[name], name)
        for action_idx in range(actions):
            _require_row_stochastic(arrays["action_transitions"][action_idx], f"action_transitions[{action_idx}]")
        _require_vector_stochastic(arrays["start"], "start")


def _require_row_stochastic(matrix: ArrayF, name: str) -> None:
    if not np.all(np.isfinite(matrix)) or np.any(matrix < 0.0):
        raise ValueError(f"{name} must contain finite non-negative probabilities")
    if not np.allclose(matrix.sum(axis=1), 1.0, atol=1e-9):
        raise ValueError(f"{name} rows must be normalized")


def _require_vector_stochastic(vector: ArrayF, name: str) -> None:
    if not np.all(np.isfinite(vector)) or np.any(vector < 0.0):
        raise ValueError(f"{name} must contain finite non-negative probabilities")
    if not np.isclose(float(vector.sum()), 1.0, atol=1e-9):
        raise ValueError(f"{name} must be normalized")


def induced_transition(policy: ArrayF, action_transitions: ArrayF) -> ArrayF:
    """Return the state transition induced by a state-conditioned policy."""
    policy = np.asarray(policy, dtype=np.float64)
    action_transitions = np.asarray(action_transitions, dtype=np.float64)
    transition = np.einsum("sa,asj->sj", policy, action_transitions)
    _require_row_stochastic(transition, "induced_transition")
    return transition


def visitation(policy: ArrayF, problem: SequentialShiftProblem) -> ArrayF:
    """Average finite-horizon visitation under the policy-induced transition."""
    transition = induced_transition(policy, problem.action_transitions)
    dist = np.asarray(problem.start, dtype=np.float64)
    acc = np.zeros_like(dist)
    for _ in range(problem.horizon):
        acc += dist
        dist = dist @ transition
    _require_vector_stochastic(acc / acc.sum(), "visitation")
    return acc / acc.sum()


def _per_state_reverse_kl(student_policy: ArrayF, teacher_policy: ArrayF) -> ArrayF:
    return np.array(
        [reverse_kl(student_policy[idx], teacher_policy[idx]) for idx in range(student_policy.shape[0])],
        dtype=np.float64,
    )


def _mix_policy(before: ArrayF, after: ArrayF, fraction: float) -> ArrayF:
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("correction fraction must lie in [0, 1]")
    policy = (1.0 - fraction) * before + fraction * after
    _require_row_stochastic(policy, "mixed_policy")
    return policy


def _canonical_problem() -> SequentialShiftProblem:
    teacher_policy = np.array(
        [
            [0.85, 0.15],
            [0.90, 0.10],
            [0.82, 0.18],
            [0.78, 0.22],
        ],
        dtype=np.float64,
    )
    student_before = np.array(
        [
            [0.80, 0.20],
            [0.55, 0.45],
            [0.25, 0.75],
            [0.62, 0.38],
        ],
        dtype=np.float64,
    )
    student_after = np.array(
        [
            [0.82, 0.18],
            [0.70, 0.30],
            [0.70, 0.30],
            [0.72, 0.28],
        ],
        dtype=np.float64,
    )
    stay_on_task = np.array(
        [
            [0.00, 1.00, 0.00, 0.00],
            [0.00, 0.86, 0.00, 0.14],
            [0.00, 0.20, 0.05, 0.75],
            [0.00, 0.82, 0.00, 0.18],
        ],
        dtype=np.float64,
    )
    shortcut = np.array(
        [
            [0.00, 0.65, 0.35, 0.00],
            [0.00, 0.30, 0.60, 0.10],
            [0.00, 0.00, 0.82, 0.18],
            [0.00, 0.45, 0.35, 0.20],
        ],
        dtype=np.float64,
    )
    return SequentialShiftProblem(
        teacher_policy=teacher_policy,
        student_policy_before=student_before,
        student_policy_after=student_after,
        action_transitions=np.stack([stay_on_task, shortcut]),
        start=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
        horizon=8,
    )


def build_payload() -> dict[str, Any]:
    """Assemble the sequential distribution-shift witness artifact."""
    problem = _canonical_problem()
    train_visitation = visitation(problem.teacher_policy, problem)
    test_before = visitation(problem.student_policy_before, problem)
    test_after = visitation(problem.student_policy_after, problem)
    kl_before = _per_state_reverse_kl(problem.student_policy_before, problem.teacher_policy)
    kl_after = _per_state_reverse_kl(problem.student_policy_after, problem.teacher_policy)
    train_loss = float(train_visitation @ kl_before)
    test_loss_before = float(test_before @ kl_before)
    test_loss_after = float(test_after @ kl_after)
    shift_mass = float(0.5 * np.abs(test_before - train_visitation).sum())
    gap_closed = float(test_loss_before - test_loss_after)
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "claim_scope": "deterministic finite sequential-shift witness; not an empirical OPD benchmark",
        "state_names": list(STATE_NAMES),
        "action_names": list(ACTION_NAMES),
        "state_count": len(STATE_NAMES),
        "action_count": len(ACTION_NAMES),
        "horizon": problem.horizon,
        "start": problem.start.tolist(),
        "teacher_policy": problem.teacher_policy.tolist(),
        "student_policy_before": problem.student_policy_before.tolist(),
        "student_policy_after": problem.student_policy_after.tolist(),
        "action_transitions": problem.action_transitions.tolist(),
        "teacher_forced_transition": induced_transition(problem.teacher_policy, problem.action_transitions).tolist(),
        "student_transition_before": induced_transition(problem.student_policy_before, problem.action_transitions).tolist(),
        "student_transition_after": induced_transition(problem.student_policy_after, problem.action_transitions).tolist(),
        "train_visitation": train_visitation.tolist(),
        "student_test_visitation_before": test_before.tolist(),
        "student_test_visitation_after": test_after.tolist(),
        "per_state_reverse_kl": kl_before.tolist(),
        "per_state_reverse_kl_after": kl_after.tolist(),
        "train_loss": train_loss,
        "student_induced_test_loss_before": test_loss_before,
        "test_loss_before": test_loss_before,
        "test_loss_after": test_loss_after,
        "shift_mass": shift_mass,
        "gap_closed": gap_closed,
        "teacher_forced_train_underestimates_student_test": bool(train_loss < test_loss_before),
        "on_policy_correction_reduces_test_loss": bool(test_loss_after < test_loss_before),
    }
    payload["ok"] = not validate_payload(payload)
    return payload


def build_sensitivity_payload(correction_fractions: tuple[float, ...] = CORRECTION_FRACTIONS) -> dict[str, Any]:
    """Assemble a finite correction-dose sensitivity sweep for the shift witness."""
    problem = _canonical_problem()
    train_visitation = visitation(problem.teacher_policy, problem)
    rows: list[dict[str, Any]] = []
    for fraction in correction_fractions:
        policy = _mix_policy(problem.student_policy_before, problem.student_policy_after, float(fraction))
        test_visitation = visitation(policy, problem)
        per_state_kl = _per_state_reverse_kl(policy, problem.teacher_policy)
        train_loss = float(train_visitation @ per_state_kl)
        test_loss = float(test_visitation @ per_state_kl)
        shift_mass = float(0.5 * np.abs(test_visitation - train_visitation).sum())
        rows.append(
            {
                "correction_fraction": float(fraction),
                "train_loss": train_loss,
                "student_induced_test_loss": test_loss,
                "test_loss": test_loss,
                "shift_mass": shift_mass,
                "train_underestimates_test": bool(train_loss < test_loss),
                "teacher_path_visitation": float(test_visitation[1]),
                "student_drift_visitation": float(test_visitation[2]),
                "repair_visitation": float(test_visitation[3]),
                "student_policy": policy.tolist(),
                "student_test_visitation": test_visitation.tolist(),
                "per_state_reverse_kl": per_state_kl.tolist(),
                "finite": bool(
                    np.all(np.isfinite(policy))
                    and np.all(np.isfinite(test_visitation))
                    and np.all(np.isfinite(per_state_kl))
                    and np.isfinite(train_loss)
                    and np.isfinite(test_loss)
                    and np.isfinite(shift_mass)
                ),
                "normalized": bool(
                    np.allclose(policy.sum(axis=1), 1.0, atol=1e-9)
                    and np.isclose(float(test_visitation.sum()), 1.0, atol=1e-9)
                ),
            }
        )
    baseline_loss = float(rows[0]["test_loss"]) if rows else 0.0
    final_loss = float(rows[-1]["test_loss"]) if rows else 0.0
    baseline_shift = float(rows[0]["shift_mass"]) if rows else 0.0
    final_shift = float(rows[-1]["shift_mass"]) if rows else 0.0
    losses = [float(row["test_loss"]) for row in rows]
    shift_masses = [float(row["shift_mass"]) for row in rows]
    payload: dict[str, Any] = {
        "schema": SENSITIVITY_SCHEMA,
        "claim_scope": "deterministic finite correction-dose sensitivity; not an empirical OPD benchmark",
        "state_names": list(STATE_NAMES),
        "action_names": list(ACTION_NAMES),
        "horizon": problem.horizon,
        "correction_fractions": [float(value) for value in correction_fractions],
        "rows": rows,
        "row_count": len(rows),
        "baseline_test_loss": baseline_loss,
        "final_test_loss": final_loss,
        "baseline_shift_mass": baseline_shift,
        "final_shift_mass": final_shift,
        "test_loss_reduction": float(baseline_loss - final_loss),
        "shift_mass_reduction": float(baseline_shift - final_shift),
        "monotone_test_loss_decrease": all(
            losses[idx + 1] <= losses[idx] + 1e-12 for idx in range(max(0, len(losses) - 1))
        ),
        "monotone_shift_mass_decrease": all(
            shift_masses[idx + 1] <= shift_masses[idx] + 1e-12 for idx in range(max(0, len(shift_masses) - 1))
        ),
        "all_probabilities_normalized": bool(rows) and all(row["normalized"] for row in rows),
        "all_losses_finite": bool(rows) and all(row["finite"] for row in rows),
    }
    payload["ok"] = not validate_sensitivity_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    """Return validation issues for a sequential-shift payload."""
    issues: list[str] = []
    if payload.get("schema") != SCHEMA:
        issues.append("schema mismatch")
    if payload.get("state_names") != list(STATE_NAMES):
        issues.append("state names mismatch")
    if payload.get("action_names") != list(ACTION_NAMES):
        issues.append("action names mismatch")
    for key in (
        "start",
        "train_visitation",
        "student_test_visitation_before",
        "student_test_visitation_after",
    ):
        try:
            _require_vector_stochastic(np.asarray(payload.get(key), dtype=np.float64), key)
        except (TypeError, ValueError) as exc:
            issues.append(str(exc))
    for key in ("teacher_policy", "student_policy_before", "student_policy_after"):
        try:
            _require_row_stochastic(np.asarray(payload.get(key), dtype=np.float64), key)
        except (TypeError, ValueError) as exc:
            issues.append(str(exc))
    for key in (
        "per_state_reverse_kl",
        "per_state_reverse_kl_after",
        "train_loss",
        "test_loss_before",
        "test_loss_after",
        "shift_mass",
        "gap_closed",
    ):
        values = np.asarray(payload.get(key), dtype=np.float64)
        if not np.all(np.isfinite(values)):
            issues.append(f"{key} must be finite")
    train_loss = float(payload.get("train_loss", float("nan")))
    before = float(payload.get("test_loss_before", float("nan")))
    after = float(payload.get("test_loss_after", float("nan")))
    if not train_loss < before:
        issues.append("teacher-forced train loss must underestimate student-induced test loss")
    if not after < before:
        issues.append("on-policy correction must reduce student-induced test loss")
    if float(payload.get("shift_mass", 0.0) or 0.0) <= 0.0:
        issues.append("shift_mass must be positive")
    if float(payload.get("gap_closed", 0.0) or 0.0) <= 0.0:
        issues.append("gap_closed must be positive")
    if payload.get("teacher_forced_train_underestimates_student_test") is not True:
        issues.append("underestimate flag must be true")
    if payload.get("on_policy_correction_reduces_test_loss") is not True:
        issues.append("correction flag must be true")
    if payload.get("ok") is not True and "ok" in payload:
        issues.append("ok flag must be true")
    return issues


def validate_sensitivity_payload(payload: dict[str, Any]) -> list[str]:
    """Return validation issues for a sequential-shift correction-dose sweep."""
    issues: list[str] = []
    if payload.get("schema") != SENSITIVITY_SCHEMA:
        issues.append("schema mismatch")
    if payload.get("state_names") != list(STATE_NAMES):
        issues.append("state names mismatch")
    if payload.get("action_names") != list(ACTION_NAMES):
        issues.append("action names mismatch")
    rows = payload.get("rows") or []
    if not rows:
        issues.append("rows must be non-empty")
    if int(payload.get("row_count", -1) or -1) != len(rows):
        issues.append("row_count must equal rows length")
    fractions = [float(row.get("correction_fraction", float("nan"))) for row in rows]
    if fractions != sorted(fractions) or not np.all(np.isfinite(fractions)):
        issues.append("correction fractions must be finite and sorted")
    if fractions and (not np.isclose(fractions[0], 0.0) or not np.isclose(fractions[-1], 1.0)):
        issues.append("correction fractions must include 0 and 1 endpoints")
    losses: list[float] = []
    shift_masses: list[float] = []
    for idx, row in enumerate(rows):
        for key in ("student_test_visitation",):
            try:
                _require_vector_stochastic(np.asarray(row.get(key), dtype=np.float64), f"rows[{idx}].{key}")
            except (TypeError, ValueError) as exc:
                issues.append(str(exc))
        for key in ("student_policy",):
            try:
                _require_row_stochastic(np.asarray(row.get(key), dtype=np.float64), f"rows[{idx}].{key}")
            except (TypeError, ValueError) as exc:
                issues.append(str(exc))
        for key in (
            "train_loss",
            "student_induced_test_loss",
            "test_loss",
            "shift_mass",
            "teacher_path_visitation",
            "student_drift_visitation",
            "repair_visitation",
            "per_state_reverse_kl",
        ):
            values = np.asarray(row.get(key), dtype=np.float64)
            if not np.all(np.isfinite(values)):
                issues.append(f"rows[{idx}].{key} must be finite")
        if not np.isclose(float(row.get("student_induced_test_loss", float("nan"))), float(row.get("test_loss", float("nan")))):
            issues.append(f"rows[{idx}].student_induced_test_loss must equal test_loss")
        if row.get("finite") is not True:
            issues.append(f"rows[{idx}].finite must be true")
        if row.get("normalized") is not True:
            issues.append(f"rows[{idx}].normalized must be true")
        losses.append(float(row.get("test_loss", float("nan"))))
        shift_masses.append(float(row.get("shift_mass", float("nan"))))
    if losses and not all(losses[idx + 1] <= losses[idx] + 1e-12 for idx in range(len(losses) - 1)):
        issues.append("test loss must decrease monotonically with correction fraction")
    if shift_masses and not all(
        shift_masses[idx + 1] <= shift_masses[idx] + 1e-12 for idx in range(len(shift_masses) - 1)
    ):
        issues.append("shift mass must decrease monotonically with correction fraction")
    if losses and not losses[-1] < losses[0]:
        issues.append("final correction must reduce baseline test loss")
    if shift_masses and not shift_masses[-1] < shift_masses[0]:
        issues.append("final correction must reduce baseline shift mass")
    if rows and rows[0].get("train_underestimates_test") is not True:
        issues.append("baseline row must preserve the train-underestimates-test witness")
    expected_summary = {
        "baseline_test_loss": losses[0] if losses else float("nan"),
        "final_test_loss": losses[-1] if losses else float("nan"),
        "baseline_shift_mass": shift_masses[0] if shift_masses else float("nan"),
        "final_shift_mass": shift_masses[-1] if shift_masses else float("nan"),
        "test_loss_reduction": (losses[0] - losses[-1]) if losses else float("nan"),
        "shift_mass_reduction": (shift_masses[0] - shift_masses[-1]) if shift_masses else float("nan"),
    }
    for key, expected in expected_summary.items():
        if not np.isclose(float(payload.get(key, float("nan"))), expected, atol=1e-9):
            issues.append(f"{key} summary mismatch")
    if payload.get("monotone_test_loss_decrease") is not True:
        issues.append("monotone_test_loss_decrease flag must be true")
    if payload.get("monotone_shift_mass_decrease") is not True:
        issues.append("monotone_shift_mass_decrease flag must be true")
    if payload.get("all_probabilities_normalized") is not True:
        issues.append("all_probabilities_normalized flag must be true")
    if payload.get("all_losses_finite") is not True:
        issues.append("all_losses_finite flag must be true")
    if payload.get("ok") is not True and "ok" in payload:
        issues.append("ok flag must be true")
    return issues
