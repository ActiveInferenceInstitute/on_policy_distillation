"""Energy-based formulation: variational and expected free energy for OPD.

Active inference is an energy-based model. This module makes the two central
functionals explicit on categorical generative models and shows how on-policy
distillation reads off each decomposition.

Generative model over hidden states ``s`` (size S) and observations ``o`` (size O):

* prior ``p(s)`` (the reference / base policy),
* likelihood ``p(o|s)`` (S x O, row-stochastic),
* an approximate posterior ``q(s)`` (the student),
* preferences ``p(o)`` over observations (the reward tilt / goal prior).

**Variational free energy** of ``q`` given an observation ``o`` admits three equal
decompositions (verified to machine precision in :func:`vfe_report`):

    F = E_q[-ln p(o,s)] - H[q]                      (energy - entropy)
      = D_KL(q(s) || p(s)) - E_q[ln p(o|s)]         (complexity - accuracy)
      = D_KL(q(s) || p(s|o)) - ln p(o)              (divergence - log-evidence)

The third form is the OPD identity: with ``q = pi_S`` (student) and
``p(s|o) = pi_T`` (the teacher = exact privileged posterior), the reverse-KL
distillation loss ``D_KL(pi_S || pi_T)`` is the variational free energy up to the
constant ``-ln p(o)``; minimising the distillation loss maximises model evidence.

**Expected free energy** of a policy admits two equal decompositions
(verified in :func:`efe_report`):

    G = D_KL(q(o) || p(o)) + E_q(s)[H[p(o|s)]]      (risk + ambiguity)
      = -I(o; s) - E_q(o)[ln p(o)]                  (-epistemic - pragmatic)

Risk is the reward-tilt term (pragmatic/KL+RL); the epistemic term is the
information gain that on-policy rollouts harvest from novel student states.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from analytical.free_energy import kl_divergence, shannon_entropy

from .divergences import normalize

ArrayF = NDArray[np.float64]

SCHEMA = "firstprinciples.energy_demo.v1"
_LOG_FLOOR = 1e-300

__all__ = [
    "GenerativeModel",
    "posterior",
    "evidence",
    "vfe_energy_entropy",
    "vfe_complexity_accuracy",
    "vfe_divergence_evidence",
    "vfe_report",
    "predicted_observations",
    "efe_risk_ambiguity",
    "efe_epistemic_pragmatic",
    "efe_report",
    "build_payload",
]


def _safe_log(p: ArrayF) -> ArrayF:
    pa = np.asarray(p, dtype=np.float64)
    return np.log(np.where(pa > 0.0, pa, _LOG_FLOOR))


def _values_agree(values: list[float], tol: float = 1e-9) -> bool:
    """True if all values are pairwise close, or all are the same infinity."""
    import math

    if all(math.isinf(v) and v > 0 for v in values):
        return True
    if all(math.isinf(v) and v < 0 for v in values):
        return True
    if any(not math.isfinite(v) for v in values):
        return False
    return (max(values) - min(values)) < tol


def _expected_log(q: ArrayF, x: ArrayF) -> float:
    """E_q[ln x], returning -inf if q places mass where x == 0 (no flooring).

    This keeps all three VFE forms in exact agreement (at +inf) under structural
    zeros in the prior or likelihood, instead of silently flooring ln(0).
    """
    qa = np.asarray(q, dtype=np.float64)
    xa = np.asarray(x, dtype=np.float64)
    mask = qa > 0.0
    if np.any(xa[mask] <= 0.0):
        return float("-inf")
    return float(np.sum(qa[mask] * np.log(xa[mask])))


@dataclass(frozen=True)
class GenerativeModel:
    """A categorical generative model ``p(s) p(o|s)`` with preferences ``p(o)``."""

    prior: ArrayF  # p(s), size S
    likelihood: ArrayF  # p(o|s), shape (S, O), rows sum to 1
    preferences: ArrayF  # p(o), size O (goal prior / reward tilt)

    def __post_init__(self) -> None:
        pr = np.asarray(self.prior, dtype=np.float64)
        a = np.asarray(self.likelihood, dtype=np.float64)
        c = np.asarray(self.preferences, dtype=np.float64)
        if a.ndim != 2 or a.shape[0] != pr.shape[0]:
            raise ValueError("likelihood must be (S, O) matching the prior length S")
        if c.shape[0] != a.shape[1]:
            raise ValueError("preferences must have one entry per observation O")
        if not np.allclose(a.sum(axis=1), 1.0, atol=1e-8):
            raise ValueError("likelihood rows must be normalised")

    @property
    def num_states(self) -> int:
        return int(self.prior.shape[0])

    @property
    def num_obs(self) -> int:
        return int(self.likelihood.shape[1])


def evidence(model: GenerativeModel, o: int) -> float:
    """Marginal likelihood ``p(o) = sum_s p(o|s) p(s)``."""
    pr = normalize(model.prior)
    return float(np.sum(pr * model.likelihood[:, o]))


def posterior(model: GenerativeModel, o: int) -> ArrayF:
    """Exact Bayesian posterior ``p(s|o)`` (the teacher target)."""
    pr = normalize(model.prior)
    joint = pr * model.likelihood[:, o]
    total = float(joint.sum())
    if total <= 0.0:
        raise ValueError("observation has zero evidence under the model")
    return joint / total


def vfe_energy_entropy(q: ArrayF, model: GenerativeModel, o: int) -> float:
    """F = E_q[-ln p(o,s)] - H[q]."""
    qa = normalize(q)
    pr = normalize(model.prior)
    exp_log_joint = _expected_log(qa, pr) + _expected_log(qa, model.likelihood[:, o])  # E_q[ln p(s) + ln p(o|s)]
    energy = -exp_log_joint  # +inf if q has mass on a zero-probability (s, o)
    return energy - shannon_entropy(qa)


def vfe_complexity_accuracy(q: ArrayF, model: GenerativeModel, o: int) -> tuple[float, float, float]:
    """Return (F, complexity, accuracy) with F = complexity - accuracy."""
    qa = normalize(q)
    pr = normalize(model.prior)
    complexity = kl_divergence(qa, pr)
    accuracy = _expected_log(qa, model.likelihood[:, o])  # -inf if q has mass on a zero-likelihood state
    return complexity - accuracy, complexity, accuracy


def vfe_divergence_evidence(q: ArrayF, model: GenerativeModel, o: int) -> tuple[float, float, float]:
    """Return (F, divergence, log_evidence) with F = divergence - log_evidence."""
    qa = normalize(q)
    post = posterior(model, o)
    divergence = kl_divergence(qa, post)
    log_evidence = float(np.log(max(evidence(model, o), _LOG_FLOOR)))
    return divergence - log_evidence, divergence, log_evidence


def vfe_report(q: ArrayF, model: GenerativeModel, o: int) -> dict[str, float | bool]:
    """All three VFE decompositions plus an exact-agreement certificate."""
    f1 = vfe_energy_entropy(q, model, o)
    f2, complexity, accuracy = vfe_complexity_accuracy(q, model, o)
    f3, divergence, log_evidence = vfe_divergence_evidence(q, model, o)
    return {
        "vfe_energy_entropy": f1,
        "vfe_complexity_accuracy": f2,
        "vfe_divergence_evidence": f3,
        "complexity": complexity,
        "accuracy": accuracy,
        "divergence_to_posterior": divergence,
        "log_evidence": log_evidence,
        "decompositions_agree": _values_agree([f1, f2, f3]),
    }


def predicted_observations(q_s: ArrayF, model: GenerativeModel) -> ArrayF:
    """Predicted observation distribution ``q(o) = sum_s p(o|s) q(s)``."""
    qa = normalize(q_s)
    return qa @ model.likelihood


def efe_risk_ambiguity(q_s: ArrayF, model: GenerativeModel) -> tuple[float, float, float]:
    """Return (G, risk, ambiguity) with G = risk + ambiguity."""
    qa = normalize(q_s)
    q_o = predicted_observations(qa, model)
    pref = normalize(model.preferences)
    risk = kl_divergence(q_o, pref)
    ambiguity = float(np.sum(qa * np.array([shannon_entropy(model.likelihood[s]) for s in range(model.num_states)])))
    return risk + ambiguity, risk, ambiguity


def efe_epistemic_pragmatic(q_s: ArrayF, model: GenerativeModel) -> tuple[float, float, float]:
    """Return (G, epistemic_value, pragmatic_value) with G = -(epistemic + pragmatic).

    Epistemic value is the expected information gain (the mutual information
    between hidden states and predicted observations); pragmatic value is the
    expected log preference of predicted observations.
    """
    qa = normalize(q_s)
    q_o = predicted_observations(qa, model)
    pref = normalize(model.preferences)
    # Information gain I(o;s) = sum_o q(o) D_KL(q(s|o) || q(s)).
    epistemic = 0.0
    for o in range(model.num_obs):
        if q_o[o] <= 0.0:
            continue
        q_s_given_o = qa * model.likelihood[:, o]
        q_s_given_o = q_s_given_o / q_s_given_o.sum()
        epistemic += float(q_o[o]) * kl_divergence(q_s_given_o, qa)
    pragmatic = float(np.sum(q_o * _safe_log(pref)))
    g = -(epistemic + pragmatic)
    return g, epistemic, pragmatic


def efe_report(q_s: ArrayF, model: GenerativeModel) -> dict[str, float | bool]:
    """Both EFE decompositions plus an exact-agreement certificate."""
    g1, risk, ambiguity = efe_risk_ambiguity(q_s, model)
    g2, epistemic, pragmatic = efe_epistemic_pragmatic(q_s, model)
    return {
        "efe_risk_ambiguity": g1,
        "efe_epistemic_pragmatic": g2,
        "risk": risk,
        "ambiguity": ambiguity,
        "epistemic_value": epistemic,
        "pragmatic_value": pragmatic,
        "decompositions_agree": _values_agree([g1, g2]),
    }


def _canonical_model() -> GenerativeModel:
    prior = np.array([0.5, 0.5], dtype=np.float64)
    likelihood = np.array([[0.85, 0.15], [0.15, 0.85]], dtype=np.float64)  # informative cue
    preferences = np.array([0.9, 0.1], dtype=np.float64)  # prefer observation 0
    return GenerativeModel(prior=prior, likelihood=likelihood, preferences=preferences)


def build_payload() -> dict[str, object]:
    """Energy-based demonstration: VFE at the prior vs the exact posterior, and EFE."""
    model = _canonical_model()
    o = 0
    prior_report = vfe_report(model.prior, model, o)
    post = posterior(model, o)
    posterior_report = vfe_report(post, model, o)
    efe = efe_report(model.prior, model)
    # The exact posterior is the VFE minimiser: F(posterior) = -ln p(o).
    minimised = bool(
        posterior_report["vfe_divergence_evidence"] <= prior_report["vfe_divergence_evidence"] + 1e-12
        and abs(float(posterior_report["divergence_to_posterior"])) < 1e-9
    )
    return {
        "schema": SCHEMA,
        "model": {
            "prior": model.prior.tolist(),
            "likelihood": model.likelihood.tolist(),
            "preferences": model.preferences.tolist(),
        },
        "observation": o,
        "log_evidence": prior_report["log_evidence"],
        "vfe_at_prior": prior_report,
        "vfe_at_posterior": posterior_report,
        "efe": efe,
        "posterior_minimises_vfe": minimised,
        "ok": bool(prior_report["decompositions_agree"] and efe["decompositions_agree"] and minimised),
    }
