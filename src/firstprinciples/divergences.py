"""Divergence geometry shared by on-policy distillation and active inference.

Every objective in the on-policy distillation (OPD) literature is a divergence
between a *student* policy ``q`` (the variational posterior) and a *teacher*
distribution ``p`` (the generative model). This module collects the closed-form
divergences used across the field — forward KL (mode-covering, the SFT limit),
reverse KL (mode-seeking, the self-distillation limit), Jensen–Shannon and skew
KL (the symmetric DistiLLM family), the alpha-divergence interpolant, and the
per-token pointwise-clipped KL introduced by OPSD — all in nats, all
deterministic, all defined on categorical distributions.

The single source of truth for the base ``D_KL(q || p)`` is
``analytical.free_energy.kl_divergence`` so that the manuscript's analytical
track and this package never disagree by an implementation detail.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from analytical.free_energy import kl_divergence, shannon_entropy

ArrayF = NDArray[np.float64]

__all__ = [
    "normalize",
    "forward_kl",
    "reverse_kl",
    "symmetric_kl",
    "jensen_shannon",
    "skew_kl",
    "alpha_divergence",
    "clipped_pointwise_kl",
    "mode_concentration",
]


def normalize(p: ArrayF) -> ArrayF:
    """Project a non-negative vector onto the probability simplex."""
    pa = np.asarray(p, dtype=np.float64).ravel()
    if np.any(pa < 0.0):
        raise ValueError("normalize requires non-negative entries")
    total = float(pa.sum())
    if total <= 0.0:
        raise ValueError("normalize requires positive total mass")
    return pa / total


def forward_kl(teacher: ArrayF, student: ArrayF) -> float:
    r"""Mode-covering forward KL ``D_KL(teacher || student)``.

    This is the gradient direction of supervised fine-tuning / vanilla
    knowledge distillation: the student is forced to put mass everywhere the
    teacher does, so it *covers* every teacher mode (Hinton et al. 2015).
    """
    return kl_divergence(normalize(teacher), normalize(student))


def reverse_kl(student: ArrayF, teacher: ArrayF) -> float:
    r"""Mode-seeking reverse KL ``D_KL(student || teacher)``.

    This is the variational free-energy objective of active inference and the
    self-distillation limit of OPD (MiniLLM, GKD): the student concentrates on
    a high-confidence subset of teacher modes, and the divergence is exactly
    zero iff ``student == teacher``.
    """
    return kl_divergence(normalize(student), normalize(teacher))


def symmetric_kl(p: ArrayF, q: ArrayF) -> float:
    """Symmetric KL ``D_KL(p || q) + D_KL(q || p)``."""
    pa, qa = normalize(p), normalize(q)
    return kl_divergence(pa, qa) + kl_divergence(qa, pa)


def jensen_shannon(p: ArrayF, q: ArrayF) -> float:
    """Jensen–Shannon divergence (bounded, symmetric) in nats."""
    pa, qa = normalize(p), normalize(q)
    m = 0.5 * (pa + qa)
    return 0.5 * kl_divergence(pa, m) + 0.5 * kl_divergence(qa, m)


def skew_kl(p: ArrayF, q: ArrayF, alpha: float) -> float:
    r"""Skew KL ``D_KL(p || (1-alpha) p + alpha q)`` (DistiLLM family).

    ``alpha = 0`` is degenerate (zero); ``alpha = 1`` recovers ``D_KL(p || q)``.
    The skew keeps the support of the second argument non-vanishing wherever
    ``p`` has mass, so the divergence stays finite even when ``q`` has zeros.
    """
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("skew_kl requires alpha in [0, 1]")
    pa, qa = normalize(p), normalize(q)
    mixture = (1.0 - alpha) * pa + alpha * qa
    return kl_divergence(pa, mixture)


def alpha_divergence(p: ArrayF, q: ArrayF, alpha: float) -> float:
    r"""Amari alpha-divergence interpolating forward (alpha->0) and reverse.

    For ``alpha not in {0, 1}``::

        D_alpha(p || q) = (1 / (alpha (1-alpha))) (1 - sum_i p_i^alpha q_i^{1-alpha})

    The ``alpha -> 1`` limit is ``D_KL(p || q)`` and ``alpha -> 0`` is
    ``D_KL(q || p)``; we delegate those exact limits to the KL implementation.
    """
    pa, qa = normalize(p), normalize(q)
    if np.isclose(alpha, 1.0):
        return kl_divergence(pa, qa)
    if np.isclose(alpha, 0.0):
        return kl_divergence(qa, pa)
    support = (pa > 0.0) & (qa > 0.0)
    bhattacharyya = float(np.sum(pa[support] ** alpha * qa[support] ** (1.0 - alpha)))
    return float((1.0 - bhattacharyya) / (alpha * (1.0 - alpha)))


def clipped_pointwise_kl(student: ArrayF, teacher: ArrayF, clip: float) -> float:
    r"""Per-token pointwise-clipped reverse KL (OPSD, Zhao et al. 2026).

    OPSD clips each token's pointwise contribution ``q_i (log q_i - log p_i)``
    so that a handful of high-divergence stylistic tokens cannot dominate the
    semantically load-bearing reasoning tokens. ``clip <= 0`` disables clipping
    and recovers the exact reverse KL.
    """
    qa, pa = normalize(student), normalize(teacher)
    mask = qa > 0.0
    if np.any(pa[mask] <= 0.0):
        return float("inf")
    pointwise = qa[mask] * (np.log(qa[mask]) - np.log(pa[mask]))
    if clip > 0.0:
        pointwise = np.clip(pointwise, -clip, clip)
    return float(np.sum(pointwise))


def mode_concentration(student: ArrayF, teacher: ArrayF) -> dict[str, float]:
    """Quantify mode-seeking vs mode-covering behaviour of the two KLs.

    Returns the reverse/forward KL values, the student/teacher entropies, and a
    ``mode_seeking`` flag that is ``True`` when the reverse-KL solution would be
    lower-entropy than the teacher (the mode-seeking regime that makes reverse
    KL "unhackable" for distillation).
    """
    qa, pa = normalize(student), normalize(teacher)
    h_student = shannon_entropy(qa)
    h_teacher = shannon_entropy(pa)
    return {
        "reverse_kl": kl_divergence(qa, pa),
        "forward_kl": kl_divergence(pa, qa),
        "student_entropy": h_student,
        "teacher_entropy": h_teacher,
        "entropy_gap": h_teacher - h_student,
        "mode_seeking": bool(h_student <= h_teacher + 1e-12),
    }
