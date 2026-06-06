"""The Pass@1 vs Pass@k diversity tradeoff of mode-seeking distillation.

A documented failure mode of on-policy / reverse-KL (mode-seeking) distillation
is *diversity collapse*: temperature-sharpening the student toward its dominant
mode pushes each problem's correct-answer mass toward 0 or 1, which raises greedy
single-answer accuracy but lowers Pass@k -- because Pass@k = ``1 - (1 - c)^k`` is
*concave* in the correct mass ``c``, so spreading samples across uncertain
problems beats committing. Forward-KL / higher-temperature students preserve
Pass@k at the cost of sharpness.

We model the student as a temperature-sharpened teacher
``pi_tau(y) proportional to pi_T(y)^{1/tau}`` and evaluate over an *ensemble* of
problems (the collapse is an aggregate, ensemble effect -- a single distribution
cannot exhibit it). All quantities are closed-form (no sampling). Low ``tau`` is
the reverse-KL / self-distillation regime; high ``tau`` flattens toward uniform.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from analytical.free_energy import shannon_entropy

from .divergences import normalize

ArrayF = NDArray[np.float64]
BoolArr = NDArray[np.bool_]
Problem = tuple[ArrayF, BoolArr]

SCHEMA = "firstprinciples.diversity_demo.v1"

__all__ = [
    "DiversityCurve",
    "sharpen",
    "correct_mass",
    "pass_at_1",
    "pass_at_k",
    "diversity_tradeoff",
    "build_payload",
]


@dataclass(frozen=True)
class DiversityCurve:
    temperatures: list[float]
    greedy_pass_at_1: float
    pass_at_k: list[float]
    entropy: list[float]
    k: int
    crossover_temperature: float | None


def sharpen(teacher: ArrayF, tau: float) -> ArrayF:
    """Temperature-sharpened student ``pi_T^{1/tau}`` renormalised."""
    if tau <= 0.0:
        raise ValueError("temperature tau must be positive")
    p = normalize(teacher)
    powered = np.power(p, 1.0 / tau)
    return powered / powered.sum()


def correct_mass(student: ArrayF, correct: BoolArr) -> float:
    """Total student probability on the correct token set ``c``."""
    s = normalize(student)
    return float(s[np.asarray(correct, dtype=bool)].sum())


def pass_at_1(student: ArrayF, correct: BoolArr) -> float:
    """Greedy Pass@1: whether the most-likely token is correct (tau-invariant)."""
    s = normalize(student)
    return float(bool(correct[int(np.argmax(s))]))


def pass_at_k(student: ArrayF, correct: BoolArr, k: int) -> float:
    """Sampling Pass@k: probability at least one of ``k`` i.i.d. samples is correct."""
    if k < 1:
        raise ValueError("k must be >= 1")
    c = correct_mass(student, correct)
    return float(1.0 - (1.0 - c) ** k)


def diversity_tradeoff(problems: Sequence[Problem], temperatures: Sequence[float], k: int = 8) -> DiversityCurve:
    """Mean greedy Pass@1 (tau-invariant) and mean sampling Pass@k across a sweep."""
    if not problems:
        raise ValueError("at least one problem is required")
    greedy = float(np.mean([pass_at_1(t, c) for t, c in problems]))
    pk: list[float] = []
    ent: list[float] = []
    for tau in temperatures:
        sharp = [sharpen(t, tau) for t, _ in problems]
        pk.append(float(np.mean([pass_at_k(s, c, k) for s, (_, c) in zip(sharp, problems, strict=True)])))
        ent.append(float(np.mean([shannon_entropy(s) for s in sharp])))
    # Crossover: smallest temperature where sampling Pass@k exceeds greedy Pass@1.
    crossover: float | None = None
    for tau, value in zip(temperatures, pk, strict=True):
        if value > greedy + 1e-12:
            crossover = float(tau)
            break
    return DiversityCurve(
        temperatures=list(temperatures),
        greedy_pass_at_1=greedy,
        pass_at_k=pk,
        entropy=ent,
        k=k,
        crossover_temperature=crossover,
    )


def _ensemble() -> list[Problem]:
    # A mix of an argmax-correct problem and argmax-wrong-but-recoverable problems;
    # flattening lets sampling recover the correct mass the sharpened student drops.
    return [
        (np.array([0.50, 0.30, 0.20], dtype=np.float64), np.array([True, False, False], dtype=bool)),
        (np.array([0.45, 0.25, 0.18, 0.12], dtype=np.float64), np.array([False, True, True, True], dtype=bool)),
        (np.array([0.40, 0.32, 0.28], dtype=np.float64), np.array([False, True, True], dtype=bool)),
    ]


def build_payload() -> dict[str, object]:
    problems = _ensemble()
    temperatures = [0.25, 0.5, 1.0, 2.0, 4.0]
    curve = diversity_tradeoff(problems, temperatures, k=8)
    sharpest, flattest = curve.pass_at_k[0], curve.pass_at_k[-1]
    return {
        "schema": SCHEMA,
        "k": curve.k,
        "temperatures": curve.temperatures,
        "greedy_pass_at_1": curve.greedy_pass_at_1,
        "pass_at_k": curve.pass_at_k,
        "entropy": curve.entropy,
        "crossover_temperature": curve.crossover_temperature,
        "sharpest_pass_at_k": sharpest,
        "flattest_pass_at_k": flattest,
        "collapse_observed": bool(flattest > sharpest),
        "ok": bool(flattest > sharpest),
    }
