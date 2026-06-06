"""Statistics for the distillation claims: bootstrap CIs, tests, effect sizes.

The classroom and sweeps produce small samples (per-step divergences, per-seed
signals). This module supplies the inferential machinery to report them honestly:
percentile bootstrap confidence intervals, a paired permutation test, a paired
sign test, and Cohen's d effect size. Everything is seeded and deterministic so
the manuscript's statistics are reproducible.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

ArrayF = NDArray[np.float64]

SCHEMA = "firstprinciples.statistics_demo.v1"

__all__ = [
    "Summary",
    "summarize",
    "bootstrap_ci",
    "cohens_d",
    "paired_permutation_test",
    "paired_sign_test",
    "build_payload",
]


@dataclass(frozen=True)
class Summary:
    n: int
    mean: float
    std: float
    minimum: float
    maximum: float


def _array(data: Sequence[float]) -> ArrayF:
    arr = np.asarray(list(data), dtype=np.float64)
    if arr.size == 0:
        raise ValueError("statistics require a non-empty sample")
    return arr


def summarize(data: Sequence[float]) -> Summary:
    arr = _array(data)
    return Summary(
        n=int(arr.size),
        mean=float(arr.mean()),
        std=float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
        minimum=float(arr.min()),
        maximum=float(arr.max()),
    )


def bootstrap_ci(
    data: Sequence[float], *, n_boot: int = 2000, alpha: float = 0.05, seed: int = 0
) -> dict[str, float]:
    """Percentile bootstrap CI for the mean (seeded, deterministic)."""
    arr = _array(data)
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot, dtype=np.float64)
    n = arr.size
    for b in range(n_boot):
        means[b] = arr[rng.integers(0, n, n)].mean()
    lo = float(np.percentile(means, 100.0 * (alpha / 2.0)))
    hi = float(np.percentile(means, 100.0 * (1.0 - alpha / 2.0)))
    return {
        "point": float(arr.mean()),
        "ci_low": lo,
        "ci_high": hi,
        "alpha": alpha,
        "n": int(n),
        "n_boot": int(n_boot),
    }


def cohens_d(a: Sequence[float], b: Sequence[float]) -> float:
    """Cohen's d effect size (pooled SD) for two independent samples."""
    aa, bb = _array(a), _array(b)
    na, nb = aa.size, bb.size
    if na < 2 or nb < 2:
        raise ValueError("Cohen's d requires at least two observations per group")
    pooled_var = ((na - 1) * aa.var(ddof=1) + (nb - 1) * bb.var(ddof=1)) / (na + nb - 2)
    pooled_sd = float(np.sqrt(pooled_var))
    if pooled_sd == 0.0:
        return 0.0
    return float((aa.mean() - bb.mean()) / pooled_sd)


def paired_permutation_test(
    a: Sequence[float], b: Sequence[float], *, n_perm: int = 5000, seed: int = 0
) -> dict[str, float]:
    """Two-sided paired permutation test on the mean difference a - b."""
    aa, bb = _array(a), _array(b)
    if aa.size != bb.size:
        raise ValueError("paired test requires equal-length samples")
    diff = aa - bb
    observed = float(diff.mean())
    rng = np.random.default_rng(seed)
    count = 0
    abs_obs = abs(observed)
    for _ in range(n_perm):
        signs = rng.choice(np.array([-1.0, 1.0]), size=diff.size)
        if abs(float((signs * diff).mean())) >= abs_obs - 1e-15:
            count += 1
    return {
        "mean_difference": observed,
        "p_value": (count + 1) / (n_perm + 1),
        "n": int(diff.size),
        "n_perm": int(n_perm),
    }


def paired_sign_test(a: Sequence[float], b: Sequence[float]) -> dict[str, float]:
    """Exact two-sided sign test on paired differences a - b."""
    aa, bb = _array(a), _array(b)
    if aa.size != bb.size:
        raise ValueError("paired test requires equal-length samples")
    diff = aa - bb
    pos = int(np.sum(diff > 0))
    neg = int(np.sum(diff < 0))
    n = pos + neg
    # Exact binomial two-sided p under H0 p=0.5 (no SciPy dependency).
    if n == 0:
        return {"positive": pos, "negative": neg, "p_value": 1.0}
    k = min(pos, neg)
    from math import comb

    tail = sum(comb(n, i) for i in range(0, k + 1)) / (2.0 ** n)
    p = min(1.0, 2.0 * tail)
    return {"positive": float(pos), "negative": float(neg), "n": float(n), "p_value": float(p)}


def build_payload() -> dict[str, object]:
    """Statistics demo on a fixed paired dataset (teacher vs student belief entropy)."""
    # Synthetic but illustrative: per-condition teacher and student belief entropies
    # where the privileged teacher is consistently more certain (lower entropy).
    teacher = [0.21, 0.25, 0.19, 0.27, 0.23, 0.20]
    student = [0.34, 0.36, 0.31, 0.38, 0.33, 0.30]
    diff = [s - t for s, t in zip(student, teacher, strict=True)]
    return {
        "schema": SCHEMA,
        "teacher_entropy": teacher,
        "student_entropy": student,
        "teacher_summary": summarize(teacher).__dict__,
        "student_summary": summarize(student).__dict__,
        "advantage_bootstrap_ci": bootstrap_ci(diff),
        "cohens_d_student_minus_teacher": cohens_d(student, teacher),
        "paired_permutation": paired_permutation_test(student, teacher),
        "paired_sign_test": paired_sign_test(student, teacher),
        "ok": bool(bootstrap_ci(diff)["ci_low"] > 0.0),
    }
