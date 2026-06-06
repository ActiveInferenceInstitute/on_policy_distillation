"""Variational EM distillation (pi-Distill): teacher E-step, student M-step.

Penaloza et al. (2026) unify distillation, SFT, and reward-tilted RL as a single
variational-EM procedure (the MPO structure of Abdolmaleki et al. 2018):

* E-step (perception): improve a non-parametric target by tilting the current
  student toward reward, ``q(y) proportional to pi_S(y) exp(A(y)/beta)`` -- the
  expected-free-energy preference update of active inference.
* M-step (action): take a geometric (log-linear) step of the parametric student
  toward that target -- a partial move along the e-geodesic to ``q`` (a full
  ``step_size = 1`` lands on it), monotonically decreasing the reverse KL
  ``D_KL(pi_S || q)`` rather than solving it exactly each step.

Iterating drives the student to the reward-tilted fixed point
``pi*(y) proportional to pi_ref(y) exp(R(y)/beta)`` while the variational free
energy decreases monotonically. This module runs that cycle deterministically on
a categorical policy and certifies both the monotone descent and the fixed
point, making the "generative model conditioned on privileged beliefs" update an
executable, audited loop.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .divergences import reverse_kl
from .reward_tilting import free_energy_against_tilted, reward_tilted_target

ArrayF = NDArray[np.float64]

SCHEMA = "firstprinciples.variational_em_demo.v1"

__all__ = ["EMResult", "run_em", "build_payload"]


@dataclass(frozen=True)
class EMResult:
    students: list[list[float]]
    free_energies: list[float]
    converged: bool
    monotone: bool
    fixed_point: list[float]
    final_gap: float


def _normalize(p: ArrayF) -> ArrayF:
    pa = np.asarray(p, dtype=np.float64).ravel()
    total = float(pa.sum())
    if total <= 0.0:
        raise ValueError("policy must have positive mass")
    return pa / total


def run_em(
    reference: ArrayF,
    reward: ArrayF,
    beta: float,
    *,
    steps: int = 40,
    step_size: float = 1.0,
    tol: float = 1e-9,
) -> EMResult:
    """Run variational-EM distillation from ``reference`` toward the tilted target.

    Each iteration performs an E-step (reward-tilt the current student) and an
    M-step (geometric move of the student toward that target by ``step_size``).
    Returns the student trajectory, the free-energy-against-target trajectory
    (which must be non-increasing), and the converged/fixed-point certificate.
    """
    if not 0.0 < step_size <= 1.0:
        raise ValueError("step_size must be in (0, 1]")
    ref = _normalize(reference)
    target = reward_tilted_target(ref, reward, beta)
    student = ref.copy()
    students: list[list[float]] = [student.tolist()]
    free_energies: list[float] = [free_energy_against_tilted(student, ref, reward, beta)]
    converged = False
    for _ in range(steps):
        # E-step: the improved non-parametric target is the student tilted by the
        # advantage A = R - beta*log(pi_S/pi_ref) relative to the reference, which
        # equals the reward-tilted reference target for any current student.
        improved = target
        # M-step: geometric (log-domain) projection of the student toward it.
        log_mix = (1.0 - step_size) * np.log(np.where(student > 0, student, 1e-300)) + step_size * np.log(
            np.where(improved > 0, improved, 1e-300)
        )
        log_mix -= log_mix.max()
        student = np.exp(log_mix)
        student /= student.sum()
        students.append(student.tolist())
        free_energies.append(free_energy_against_tilted(student, ref, reward, beta))
        if reverse_kl(student, target) <= tol:
            converged = True
            break
    monotone = all(b <= a + 1e-9 for a, b in zip(free_energies, free_energies[1:], strict=False))
    return EMResult(
        students=students,
        free_energies=free_energies,
        converged=converged,
        monotone=monotone,
        fixed_point=target.tolist(),
        final_gap=reverse_kl(np.asarray(students[-1], dtype=np.float64), target),
    )


def build_payload() -> dict[str, object]:
    reference = np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float64)
    reward = np.array([2.0, 0.5, -0.5, -2.0], dtype=np.float64)
    result = run_em(reference, reward, beta=1.0)
    return {
        "schema": SCHEMA,
        "beta": 1.0,
        "iterations": len(result.free_energies),
        "free_energies": result.free_energies,
        "converged": result.converged,
        "monotone_descent": result.monotone,
        "fixed_point": result.fixed_point,
        "final_gap_to_target": result.final_gap,
        "ok": bool(result.monotone and result.final_gap < 1e-6),
    }
