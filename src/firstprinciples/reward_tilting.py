"""Reward-tilted targets: the bridge from RL to variational inference.

Maximum-entropy / KL-regularised reinforcement learning maximises

    J(pi) = E_{y~pi}[R(y)] - beta * D_KL(pi || pi_ref)

whose unique maximiser is the *reward-tilted* (Gibbs) policy

    pi*(y) proportional to pi_ref(y) * exp(R(y) / beta).

This is exactly the target distribution that active inference fits with a
variational posterior, and the object that every distillation method
approximates (Levine 2018; Abdolmaleki et al. 2018). Up to an additive
constant, ``-J(pi)`` is the variational free energy of ``pi`` relative to the
reward-tilted generative model, which is why on-policy distillation and active
inference share one objective.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from analytical.free_energy import kl_divergence, shannon_entropy

ArrayF = NDArray[np.float64]

__all__ = [
    "reward_tilted_target",
    "expected_reward",
    "kl_regularized_objective",
    "free_energy_against_tilted",
    "verify_optimality",
]


def _normalize(p: ArrayF) -> ArrayF:
    pa = np.asarray(p, dtype=np.float64).ravel()
    total = float(pa.sum())
    if total <= 0.0:
        raise ValueError("reference policy must have positive mass")
    return pa / total


def reward_tilted_target(reference: ArrayF, reward: ArrayF, beta: float) -> ArrayF:
    r"""Return ``pi*(y) ∝ pi_ref(y) exp(R(y)/beta)`` (numerically stable)."""
    if beta <= 0.0:
        raise ValueError("temperature beta must be positive")
    ref = _normalize(reference)
    r = np.asarray(reward, dtype=np.float64).ravel()
    if r.shape != ref.shape:
        raise ValueError("reward and reference must share a shape")
    logits = np.log(np.where(ref > 0.0, ref, 1e-300)) + r / beta
    logits -= logits.max()
    weights = np.exp(logits)
    return weights / weights.sum()


def expected_reward(policy: ArrayF, reward: ArrayF) -> float:
    pi = _normalize(policy)
    r = np.asarray(reward, dtype=np.float64).ravel()
    return float(np.sum(pi * r))


def kl_regularized_objective(policy: ArrayF, reference: ArrayF, reward: ArrayF, beta: float) -> float:
    r"""``J(pi) = E_pi[R] - beta * D_KL(pi || pi_ref)``."""
    pi = _normalize(policy)
    ref = _normalize(reference)
    return expected_reward(pi, reward) - beta * kl_divergence(pi, ref)


def free_energy_against_tilted(policy: ArrayF, reference: ArrayF, reward: ArrayF, beta: float) -> float:
    r"""Variational free energy of ``policy`` against the reward-tilted model.

    ``F(pi) = D_KL(pi || pi*)`` where ``pi*`` is the reward-tilted target. This
    equals ``(log Z - J(pi)) / beta`` up to the log-partition constant, so
    minimising free energy and maximising the KL-regularised RL objective are
    the same optimisation — the identity at the heart of the title.
    """
    pi = _normalize(policy)
    target = reward_tilted_target(reference, reward, beta)
    return kl_divergence(pi, target)


def verify_optimality(reference: ArrayF, reward: ArrayF, beta: float, *, trials: int = 64, seed: int = 0) -> dict[str, object]:
    """Numerically confirm the reward-tilted target maximises ``J``.

    Draws ``trials`` Dirichlet-perturbed policies and checks none beats the
    closed-form target. Returns the target's objective, the best competitor,
    and an ``optimal`` flag.
    """
    ref = _normalize(reference)
    r = np.asarray(reward, dtype=np.float64).ravel()
    target = reward_tilted_target(ref, r, beta)
    target_value = kl_regularized_objective(target, ref, r, beta)
    rng = np.random.default_rng(seed)
    best_other = -np.inf
    for _ in range(trials):
        candidate = rng.dirichlet(np.ones(ref.size))
        value = kl_regularized_objective(candidate, ref, r, beta)
        best_other = max(best_other, value)
    # The target must also dominate the unperturbed reference and a uniform policy.
    uniform = np.full(ref.size, 1.0 / ref.size)
    best_other = max(best_other, kl_regularized_objective(ref, ref, r, beta))
    best_other = max(best_other, kl_regularized_objective(uniform, ref, r, beta))
    return {
        "target": target.tolist(),
        "target_objective": target_value,
        "best_competitor_objective": float(best_other),
        "target_entropy": shannon_entropy(target),
        "optimal": bool(target_value >= best_other - 1e-9),
    }
