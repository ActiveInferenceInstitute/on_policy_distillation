"""Exposure bias as the failure of off-policy (passive) belief updating.

The core problem on-policy distillation solves is *exposure bias*: an
autoregressive student trained only on the teacher's (or ground-truth)
trajectories never visits the off-distribution states its own sampling
produces, so errors compound and it cannot recover. Active inference makes the
same diagnosis: passive Bayesian updating against a fixed dataset diverges from
the states the agent's own actions induce, and only *active* sampling closes
the gap.

We model this with a two-state Markov chain over a horizon ``L``. The student
is ``ON`` track or ``OFF`` track. Off-policy training only ever observes ``ON``
states, so it learns the ``ON`` transition but assigns the default (chance)
recovery to ``OFF`` states. On-policy training also visits ``OFF`` states and
learns to recover with probability ``recovery``. The survival curve (probability
of being ``ON`` at step ``t``) is computed in closed form — no sampling.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["DriftSpec", "drift_curves", "exposure_gap"]


@dataclass(frozen=True)
class DriftSpec:
    """Parameters of the on-track / off-track survival chain.

    accuracy: per-step probability of staying ON given currently ON.
    horizon: number of autoregressive steps.
    on_recovery: per-step probability an on-policy student returns ON from OFF.
    off_recovery: per-step recovery for an off-policy student (it never trained
        on OFF states, so this is the chance/default rate, typically ~0).
    """

    accuracy: float = 0.9
    horizon: int = 24
    on_recovery: float = 0.5
    off_recovery: float = 0.0

    def __post_init__(self) -> None:
        for name in ("accuracy", "on_recovery", "off_recovery"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.horizon < 1:
            raise ValueError("horizon must be >= 1")


def _survival(accuracy: float, recovery: float, horizon: int) -> list[float]:
    """P(ON at step t) for t = 1..horizon under the two-state chain."""
    p_on = 1.0
    curve: list[float] = []
    for _ in range(horizon):
        # next P(ON) = P(ON)*accuracy + P(OFF)*recovery
        p_on = p_on * accuracy + (1.0 - p_on) * recovery
        curve.append(float(p_on))
    return curve


def drift_curves(spec: DriftSpec) -> dict[str, list[float]]:
    """Return off-policy and on-policy survival curves over the horizon."""
    return {
        "off_policy": _survival(spec.accuracy, spec.off_recovery, spec.horizon),
        "on_policy": _survival(spec.accuracy, spec.on_recovery, spec.horizon),
    }


def exposure_gap(spec: DriftSpec) -> dict[str, float]:
    """Summarise the terminal advantage of on-policy over off-policy training.

    For the canonical defaults the off-policy curve decays geometrically toward
    zero while the on-policy curve converges to the recovery fixed point
    ``recovery / (1 - accuracy + recovery)`` — a finite, positive plateau.
    """
    curves = drift_curves(spec)
    off_final = curves["off_policy"][-1]
    on_final = curves["on_policy"][-1]
    fixed_point = spec.on_recovery / (1.0 - spec.accuracy + spec.on_recovery)
    return {
        "off_policy_final": off_final,
        "on_policy_final": on_final,
        "terminal_gap": on_final - off_final,
        "on_policy_fixed_point": float(fixed_point),
        "off_policy_collapses": bool(off_final < on_final),
    }
