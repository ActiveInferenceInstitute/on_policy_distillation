"""On-policy distillation (GKD) vs off-policy: exposure bias, made executable.

Generalized Knowledge Distillation (Agarwal et al. 2024) trains the student on
its *own* rollouts scored token-by-token by the teacher, instead of on the
teacher's (or ground-truth) trajectories. The difference is entirely in the
*visitation distribution* under which the per-token divergence is averaged:

* off-policy / SFT: states are visited by the **teacher** (teacher forcing), so
  the student never trains on the off-distribution states its own sampling
  induces -- exposure bias.
* on-policy / GKD: states are visited by the **student**, so the loss puts mass
  exactly where the student actually goes and where it errs.

This module is a deterministic, sampling-free *stylized illustration* of that
contrast on a small Markov chain of token-states: visitation distributions are
computed in closed form, and the GKD objective is the visitation-weighted token
divergence under a chosen direction (reverse KL by default). Two honesty caveats:
(1) the on-policy >= off-policy exposure gap is *example-dependent* -- it holds
for the constructed canonical example (a student that drifts on its own preferred
states) but the sign is not universal across arbitrary problems; and (2) the
visitation model uses a transition matrix shared by teacher and student with a
scalar policy-stickiness reweighting, which is an *analogy* for on-policy
visitation, not a faithful GKD model where emitted tokens drive the transitions.
It illustrates -- it does not prove -- the title's "posterior generates its own
observations" clause.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .divergences import forward_kl, normalize, reverse_kl

ArrayF = NDArray[np.float64]

SCHEMA = "firstprinciples.gkd_demo.v1"

__all__ = ["GKDProblem", "visitation", "gkd_loss", "exposure_bias_gap", "build_payload"]


@dataclass(frozen=True)
class GKDProblem:
    """A minimal token-state distillation problem.

    states: number of token-states (a small Markov chain over generation states).
    teacher: row-stochastic (states x vocab) next-token distributions of pi_T.
    student: row-stochastic (states x vocab) next-token distributions of pi_S.
    transition: row-stochastic (states x states) successor map given the current
        state (the generative process the chosen policy walks).
    start: initial state distribution.
    """

    teacher: ArrayF
    student: ArrayF
    transition: ArrayF
    start: ArrayF

    def __post_init__(self) -> None:
        t = np.asarray(self.teacher, dtype=np.float64)
        s = np.asarray(self.student, dtype=np.float64)
        m = np.asarray(self.transition, dtype=np.float64)
        d = np.asarray(self.start, dtype=np.float64)
        if t.shape != s.shape:
            raise ValueError("teacher and student must share shape (states x vocab)")
        if m.shape[0] != m.shape[1] or m.shape[0] != t.shape[0]:
            raise ValueError("transition must be (states x states) matching the state count")
        if d.shape[0] != t.shape[0]:
            raise ValueError("start must have one entry per state")
        for name, arr in (("teacher", t), ("student", s), ("transition", m)):
            if not np.allclose(arr.sum(axis=1), 1.0, atol=1e-8):
                raise ValueError(f"{name} rows must be normalised")


def _stationary_visitation(policy_rows: ArrayF, problem: GKDProblem, horizon: int) -> ArrayF:
    """Average state visitation over a finite horizon under a policy's walk.

    The successor of a state is governed by ``transition`` (the generative
    process); ``policy_rows`` only shifts *where the walk is evaluated* through
    a policy-dependent reweighting of the transition toward higher-probability
    tokens, modelling how a sharper policy revisits its preferred states.
    """
    states = problem.transition.shape[0]
    # Policy-tilted transition: weight successors by how much probability mass
    # the policy concentrates (sharper policy -> more self-reinforcing walk).
    concentration = (policy_rows ** 2).sum(axis=1)  # in (1/vocab, 1]
    tilt = np.eye(states) * concentration[:, None]
    walk = normalize_rows((1.0 - concentration)[:, None] * problem.transition + tilt)
    dist = normalize(problem.start)
    acc = np.zeros(states, dtype=np.float64)
    for _ in range(horizon):
        acc += dist
        dist = dist @ walk
    return acc / acc.sum()


def normalize_rows(matrix: ArrayF) -> ArrayF:
    m = np.asarray(matrix, dtype=np.float64)
    sums = m.sum(axis=1, keepdims=True)
    sums = np.where(sums > 0.0, sums, 1.0)
    return m / sums


def visitation(problem: GKDProblem, *, on_policy: bool, horizon: int = 8) -> ArrayF:
    """State visitation distribution under the student (on-policy) or teacher."""
    rows = problem.student if on_policy else problem.teacher
    return _stationary_visitation(rows, problem, horizon)


def gkd_loss(
    problem: GKDProblem,
    *,
    on_policy: bool,
    horizon: int = 8,
    divergence: Callable[[ArrayF, ArrayF], float] | None = None,
) -> float:
    """Visitation-weighted per-token divergence (reverse KL by default)."""
    visit = visitation(problem, on_policy=on_policy, horizon=horizon)
    total = 0.0
    for state in range(problem.teacher.shape[0]):
        student_row = problem.student[state]
        teacher_row = problem.teacher[state]
        if divergence is None:
            d = reverse_kl(student_row, teacher_row)
        else:
            d = divergence(student_row, teacher_row)
        total += float(visit[state]) * d
    return total


def exposure_bias_gap(problem: GKDProblem, *, horizon: int = 8) -> dict[str, float]:
    """Contrast off-policy and on-policy GKD objectives.

    The on-policy objective up-weights states the student actually visits (where
    it has drifted and errs), so for a student that disagrees with the teacher
    more on its own preferred states, the on-policy loss exceeds the off-policy
    loss -- a stylized illustration of exposure bias (the gap sign is
    example-dependent; see the module docstring caveats).
    """
    off = gkd_loss(problem, on_policy=False, horizon=horizon)
    on = gkd_loss(problem, on_policy=True, horizon=horizon)
    return {
        "off_policy_loss": off,
        "on_policy_loss": on,
        "exposure_gap": on - off,
        "on_policy_sees_more_error": bool(on >= off - 1e-12),
    }


def _canonical_problem() -> GKDProblem:
    # 3 token-states; the student drifts most on state 2 (its own preferred sink).
    teacher = np.array(
        [[0.70, 0.20, 0.10], [0.10, 0.80, 0.10], [0.15, 0.15, 0.70]], dtype=np.float64
    )
    student = np.array(
        [[0.60, 0.25, 0.15], [0.20, 0.70, 0.10], [0.45, 0.10, 0.45]], dtype=np.float64
    )
    transition = np.array(
        [[0.20, 0.30, 0.50], [0.25, 0.25, 0.50], [0.20, 0.20, 0.60]], dtype=np.float64
    )
    start = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    return GKDProblem(teacher=teacher, student=student, transition=transition, start=start)


def build_payload() -> dict[str, object]:
    """Assemble the GKD on-policy-vs-off-policy demonstration artifact."""
    problem = _canonical_problem()
    gap = exposure_bias_gap(problem)
    return {
        "schema": SCHEMA,
        "state_count": int(problem.teacher.shape[0]),
        "off_policy_visitation": visitation(problem, on_policy=False).tolist(),
        "on_policy_visitation": visitation(problem, on_policy=True).tolist(),
        "reverse_kl": gap,
        "forward_kl_off_policy": gkd_loss(problem, on_policy=False, divergence=forward_kl),
        "forward_kl_on_policy": gkd_loss(problem, on_policy=True, divergence=forward_kl),
        "ok": gap["on_policy_sees_more_error"],
    }
