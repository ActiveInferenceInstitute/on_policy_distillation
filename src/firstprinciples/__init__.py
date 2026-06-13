"""First-principles formalisation of a finite-model active-inference reading of OPD.

    A Finite-Model Active-Inference Reading of On-Policy Distillation.

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
* :mod:`firstprinciples.sequential_shift` - finite sequential train/test shift witness.
* :mod:`firstprinciples.artifacts` - deterministic artifact emitters.
"""

from __future__ import annotations

from . import (
    adaptive,
    artifacts,
    classroom,
    divergences,
    diversity,
    empirical,
    energy,
    exposure_bias,
    gkd,
    mapping,
    parallel,
    privilege,
    reward_tilting,
    sdpg,
    sequential_shift,
    statistics,
    taxonomy,
    variational_em,
)

THESIS = (
    "A Finite-Model Active-Inference Reading of On-Policy Distillation"
)

__all__ = [
    "THESIS",
    "adaptive",
    "artifacts",
    "classroom",
    "divergences",
    "diversity",
    "empirical",
    "energy",
    "exposure_bias",
    "gkd",
    "mapping",
    "parallel",
    "privilege",
    "reward_tilting",
    "sdpg",
    "sequential_shift",
    "statistics",
    "taxonomy",
    "variational_em",
]
