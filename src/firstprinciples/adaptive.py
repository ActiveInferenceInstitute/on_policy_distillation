"""Adaptive per-token divergence: entropy-gated forward/reverse switching.

A 2025-2026 research direction (AKL, ToDi, EDGE) abandons a single fixed
divergence and chooses the direction *per token* from the student's local
uncertainty. The active-inference reading is precision-weighting: where the
student is confident (low entropy) use mode-seeking reverse KL to commit; where
it is uncertain (high entropy) use mode-covering forward KL to keep exploring --
the epistemic/pragmatic balance of expected free energy, applied token-wise.

This module implements the gate on a batch of token positions and shows the
adaptive objective lies between the all-forward and all-reverse extremes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from analytical.free_energy import shannon_entropy

from .divergences import forward_kl, normalize, reverse_kl

ArrayF = NDArray[np.float64]

SCHEMA = "firstprinciples.adaptive_demo.v1"

__all__ = ["TokenDirections", "token_directions", "adaptive_loss", "build_payload"]


@dataclass(frozen=True)
class TokenDirections:
    directions: list[str]
    per_token: list[float]
    total: float
    reverse_fraction: float


def _entropy_threshold(students: ArrayF) -> float:
    """Default gate: the median student entropy across the token batch."""
    ents = np.array([shannon_entropy(normalize(row)) for row in students], dtype=np.float64)
    return float(np.median(ents))


def token_directions(
    teachers: ArrayF, students: ArrayF, *, threshold: float | None = None
) -> TokenDirections:
    """Per-token adaptive KL: reverse where student is confident, forward where uncertain.

    ``teachers``/``students`` are (tokens x vocab) row-stochastic batches. A token
    with student entropy at or below ``threshold`` (default: batch median) uses
    reverse KL (commit); above it, forward KL (explore).
    """
    t = np.asarray(teachers, dtype=np.float64)
    s = np.asarray(students, dtype=np.float64)
    if t.shape != s.shape:
        raise ValueError("teachers and students must share shape (tokens x vocab)")
    gate = _entropy_threshold(s) if threshold is None else threshold
    directions: list[str] = []
    per_token: list[float] = []
    for teacher_row, student_row in zip(t, s, strict=True):
        ent = shannon_entropy(normalize(student_row))
        if ent <= gate:
            directions.append("reverse")
            per_token.append(reverse_kl(student_row, teacher_row))
        else:
            directions.append("forward")
            per_token.append(forward_kl(teacher_row, student_row))
    reverse_fraction = directions.count("reverse") / len(directions) if directions else 0.0
    return TokenDirections(
        directions=directions,
        per_token=per_token,
        total=float(np.sum(per_token)),
        reverse_fraction=reverse_fraction,
    )


def adaptive_loss(teachers: ArrayF, students: ArrayF, *, threshold: float | None = None) -> float:
    """Summed adaptive per-token divergence."""
    return token_directions(teachers, students, threshold=threshold).total


def _all_one_direction(teachers: ArrayF, students: ArrayF, *, reverse: bool) -> float:
    total = 0.0
    for teacher_row, student_row in zip(teachers, students, strict=True):
        total += reverse_kl(student_row, teacher_row) if reverse else forward_kl(teacher_row, student_row)
    return float(total)


def build_payload() -> dict[str, object]:
    """Build the canonical `firstprinciples.adaptive_demo` artifact payload."""
    teachers = np.array(
        [[0.80, 0.15, 0.05], [0.34, 0.33, 0.33], [0.10, 0.10, 0.80], [0.40, 0.35, 0.25]],
        dtype=np.float64,
    )
    students = np.array(
        [[0.70, 0.20, 0.10], [0.34, 0.33, 0.33], [0.20, 0.20, 0.60], [0.34, 0.33, 0.33]],
        dtype=np.float64,
    )
    adaptive = token_directions(teachers, students)
    all_reverse = _all_one_direction(teachers, students, reverse=True)
    all_forward = _all_one_direction(teachers, students, reverse=False)
    lo, hi = sorted((all_reverse, all_forward))
    return {
        "schema": SCHEMA,
        "directions": adaptive.directions,
        "per_token": adaptive.per_token,
        "adaptive_total": adaptive.total,
        "reverse_fraction": adaptive.reverse_fraction,
        "all_reverse_total": all_reverse,
        "all_forward_total": all_forward,
        "between_extremes": bool(lo - 1e-9 <= adaptive.total <= hi + 1e-9),
        "ok": bool(0.0 < adaptive.reverse_fraction < 1.0),
    }
