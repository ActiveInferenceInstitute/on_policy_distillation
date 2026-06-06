"""First-principles formalisation of on-policy distillation as active inference.

    On-Policy Distillation is Active Inference where the Variational Posterior
    Generates Its Own Observations and the Generative Model Is Conditioned on
    Privileged Beliefs.

This package builds that thesis from the ground up as composable, tested
modules:

* :mod:`firstprinciples.mapping` - the audited active-inference <-> OPD dictionary.
* :mod:`firstprinciples.divergences` - the divergence geometry (FKL/RKL/JSD/skew/alpha,
  per-token clipped KL) shared by both frameworks.
* :mod:`firstprinciples.reward_tilting` - the reward-tilted target that unifies
  KL-regularised RL, variational inference, and distillation.
* :mod:`firstprinciples.exposure_bias` - exposure bias as the failure of passive
  off-policy updating.
* :mod:`firstprinciples.sdpg` - Self-Distilled Policy Gradient: a single model as
  its own teacher conditioned on privileged context.
* :mod:`firstprinciples.taxonomy` - the structured OPD literature landscape.
* :mod:`firstprinciples.classroom` - the executable two-agent pymdp classroom.
* :mod:`firstprinciples.gkd` - on-policy vs off-policy distillation (exposure bias).
* :mod:`firstprinciples.variational_em` - pi-Distill variational-EM fixed point.
* :mod:`firstprinciples.diversity` - the Pass@1 vs Pass@k mode-collapse tradeoff.
* :mod:`firstprinciples.adaptive` - entropy-gated adaptive per-token divergence.
* :mod:`firstprinciples.artifacts` - deterministic artifact emitters.
"""

from __future__ import annotations

from . import (
    adaptive,
    artifacts,
    classroom,
    divergences,
    diversity,
    energy,
    exposure_bias,
    gkd,
    mapping,
    privilege,
    reward_tilting,
    sdpg,
    statistics,
    taxonomy,
    variational_em,
)

THESIS = (
    "On-Policy Distillation is Active Inference where the Variational Posterior "
    "Generates Its Own Observations and the Generative Model Is Conditioned on "
    "Privileged Beliefs"
)

__all__ = [
    "THESIS",
    "adaptive",
    "artifacts",
    "classroom",
    "divergences",
    "diversity",
    "energy",
    "exposure_bias",
    "gkd",
    "mapping",
    "privilege",
    "reward_tilting",
    "sdpg",
    "statistics",
    "taxonomy",
    "variational_em",
]
