"""SDPG: Self-Distilled Policy Gradient (Liu, Zhang, Zhang & Gu 2026).

SDPG (arXiv:2606.04036; github.com/lauyikfung/SDPG) is the cleanest instance of
the title's claim. A single policy ``pi_theta`` is its own teacher and student:
the *teacher* conditions on privileged context ``c`` (a hint, a verified trace,
ground truth) and the *student* sees only the prompt ``x``. The objective adds
an exact full-vocabulary on-policy self-distillation term to a clipped policy
gradient and a frozen-reference KL anchor::

    L = L_clip
        + beta  * D_KL( pi_theta(.|x)  ||  pi_theta(.|c, x) )      # self-distill
        + alpha * D_KL( pi_theta(.|x)  ||  pi_ref(.|x) )           # anchor

The middle term is a *dense, per-token* signal — exactly the privileged
generative model of active inference supplying prediction errors at every step,
in contrast to a single sparse scalar reward. ``KL_MODE`` selects the direction
(``fkl`` forward, ``rkl`` reverse) and whether the per-token weights are treated
as a detached baseline (the ``u`` "unbiased" variants).

This module is a faithful, dependency-free numerical model of the SDPG objective
on a categorical next-token distribution; it is not the GPU training loop.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .divergences import forward_kl, normalize, reverse_kl

ArrayF = NDArray[np.float64]

_VALID_MODES = ("fkl", "rkl", "ufkl", "urkl")

__all__ = ["SDPGConfig", "softmax", "self_distillation_term", "sdpg_loss", "signal_density"]


@dataclass(frozen=True)
class SDPGConfig:
    """SDPG hyperparameters mirroring the reference implementation defaults."""

    beta: float = 0.001
    alpha: float = 0.001
    kl_mode: str = "urkl"

    def __post_init__(self) -> None:
        if self.kl_mode not in _VALID_MODES:
            raise ValueError(f"kl_mode must be one of {_VALID_MODES}")
        if self.beta < 0.0 or self.alpha < 0.0:
            raise ValueError("beta and alpha must be non-negative")


def softmax(logits: ArrayF, temperature: float = 1.0) -> ArrayF:
    """Numerically stable softmax over the last axis (single distribution)."""
    if temperature <= 0.0:
        raise ValueError("temperature must be positive")
    z = np.asarray(logits, dtype=np.float64).ravel() / temperature
    z -= z.max()
    e = np.exp(z)
    return e / e.sum()


def self_distillation_term(student: ArrayF, teacher: ArrayF, kl_mode: str) -> float:
    """The privileged-context self-distillation KL under the chosen direction.

    ``fkl``/``ufkl`` use forward KL ``D_KL(teacher || student)``; ``rkl``/``urkl``
    use reverse KL ``D_KL(student || teacher)``. The ``u`` variants share the
    same value here (they differ only in gradient estimator, not loss value).
    """
    if kl_mode not in _VALID_MODES:
        raise ValueError(f"kl_mode must be one of {_VALID_MODES}")
    if kl_mode in ("fkl", "ufkl"):
        return forward_kl(teacher, student)
    return reverse_kl(student, teacher)


def sdpg_loss(
    student: ArrayF,
    teacher: ArrayF,
    reference: ArrayF,
    advantage: float,
    config: SDPGConfig | None = None,
) -> dict[str, float]:
    """Evaluate the three SDPG terms for one token position.

    ``student`` = ``pi_theta(.|x)``, ``teacher`` = ``pi_theta(.|c,x)`` (privileged
    context), ``reference`` = frozen ``pi_ref``. ``advantage`` is the
    group-relative verifier advantage scaling the (here surrogate) policy term.
    """
    cfg = config or SDPGConfig()
    pi = normalize(student)
    distill = self_distillation_term(pi, teacher, cfg.kl_mode)
    ref_kl = reverse_kl(pi, reference)
    # Surrogate clipped policy-gradient term: advantage-weighted negative
    # log-likelihood of the student's own most-probable token (sign convention:
    # positive advantage lowers the loss).
    clip_term = -float(advantage) * float(np.log(pi.max()))
    total = clip_term + cfg.beta * distill + cfg.alpha * ref_kl
    return {
        "clip_term": clip_term,
        "distill_term": cfg.beta * distill,
        "ref_kl_term": cfg.alpha * ref_kl,
        "self_distillation_kl": distill,
        "reference_kl": ref_kl,
        "total": total,
    }


def signal_density(student: ArrayF, teacher: ArrayF) -> dict[str, float]:
    """Contrast the density of the self-distillation signal vs a scalar reward.

    The self-distillation term supplies a gradient component at every vocabulary
    entry where teacher and student disagree; a scalar reward supplies exactly
    one. ``density_ratio`` is the count of active per-token components divided by
    one, quantifying why dense supervision is so much more sample-efficient.
    """
    pi = normalize(student)
    p = normalize(teacher)
    active = int(np.sum(~np.isclose(pi, p, atol=1e-12)))
    return {
        "active_components": float(active),
        "scalar_reward_components": 1.0,
        "density_ratio": float(active),
        "denser_than_scalar": bool(active > 1),
    }
