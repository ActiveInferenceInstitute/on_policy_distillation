"""Multi-state generality of the active-selection identity.

The committed :mod:`firstprinciples.active_selection` result is stated on a 2x2
binary toy. This module shows the central identity

    gap_closed = H(r) - E_o[H(r | o)] = I(o; r) = epistemic_value

is not an artefact of the binary case: it holds, to machine precision, for
``n``-state latents and ``k``-outcome observation channels (``n, k`` in {3, 4}),
reusing the SAME functionals (:func:`energy.efe_epistemic_pragmatic` for the
epistemic term, :func:`active_selection.expected_conditional_entropy` for the
residual) so there is one definition and no drift.

Three honest caveats are encoded as part of the contract rather than hidden:

* **The identity is measure-coupled, not algebraic.** It holds because the
  residual ``E_o[H(r|o)]`` marginalises over the *same* ``q(o) = prior @ p(o|r)``
  that the EFE epistemic term uses. The ``wrong_measure`` negative control
  recomputes the residual under a uniform ``q(o)`` and shows the identity breaks
  by ~1e-2 -- proving the gate is not vacuous.
* **Exact gap closure needs ``k >= n``.** A channel with fewer outcomes than
  states under-resolves ``r``; its residual cannot reach zero. The certificate
  asserts a residual floor for the declared ``k < n`` channel.
* **Selection is stated for the epistemic term.** Under flat preferences EFE
  argmin coincides with epistemic argmax; this module ranks channels by epistemic
  value (the active term), which selects the most diagnostic channel.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from analytical.free_energy import shannon_entropy

from . import energy
from .active_selection import expected_conditional_entropy

ArrayF = NDArray[np.float64]

SCHEMA = "firstprinciples.active_selection_general_demo.v1"

_IDENTITY_TOL = 1e-12
_ZERO_RESIDUAL_TOL = 1e-9
_BLIND_EPISTEMIC_TOL = 1e-12

__all__ = ["Channel", "ChannelScore", "score_channel", "canonical_channels", "build_payload", "validate_payload"]


@dataclass(frozen=True)
class Channel:
    """A named observation channel ``p(o | r)`` over ``n`` states, ``k`` outcomes."""

    name: str
    likelihood: tuple[tuple[float, ...], ...]

    def array(self) -> ArrayF:
        a = np.array(self.likelihood, dtype=np.float64)
        if not np.allclose(a.sum(axis=1), 1.0, atol=1e-8):
            raise ValueError(f"channel {self.name!r}: rows must be row-stochastic")
        return a


def _flat_prior(n: int) -> ArrayF:
    return np.full(n, 1.0 / n, dtype=np.float64)


def _model(channel: Channel) -> energy.GenerativeModel:
    likelihood = channel.array()
    n, k = likelihood.shape
    prior = _flat_prior(n)
    preferences = _flat_prior(k)  # flat: info-only, so EFE argmin == epistemic argmax
    return energy.GenerativeModel(prior=prior, likelihood=likelihood, preferences=preferences)


def _wrong_measure_conditional_entropy(model: energy.GenerativeModel) -> float:
    """Ablation: weight H(r|o) by a UNIFORM q(o) instead of the true predicted q(o).

    For a channel whose predicted observation distribution is non-uniform this
    diverges from the true ``E_o[H(r|o)]`` and breaks the identity -- the control
    that proves the identity is measuring the real coupled quantity.
    """
    k = model.num_obs
    total = 0.0
    live = 0
    for o in range(k):
        try:
            post = energy.posterior(model, o)
        except ValueError:
            continue  # zero-evidence outcome
        total += shannon_entropy(post)
        live += 1
    return total / live if live else 0.0


@dataclass(frozen=True)
class ChannelScore:
    name: str
    n_states: int
    k_obs: int
    prior_entropy: float
    epistemic_value: float
    residual_gap: float
    identity_residual: float

    def as_row(self) -> dict[str, object]:
        return {
            "name": self.name,
            "n_states": float(self.n_states),
            "k_obs": float(self.k_obs),
            "prior_entropy": self.prior_entropy,
            "epistemic_value": self.epistemic_value,
            "residual_gap": self.residual_gap,
            "identity_residual": self.identity_residual,
        }


def score_channel(channel: Channel) -> ChannelScore:
    model = _model(channel)
    _g, epistemic, _pragmatic = energy.efe_epistemic_pragmatic(model.prior, model)
    residual = expected_conditional_entropy(model)
    prior_entropy = float(shannon_entropy(model.prior))
    n, k = model.likelihood.shape
    return ChannelScore(
        name=channel.name,
        n_states=int(n),
        k_obs=int(k),
        prior_entropy=prior_entropy,
        epistemic_value=float(epistemic),
        residual_gap=float(residual),
        identity_residual=abs((prior_entropy - residual) - float(epistemic)),
    )


def canonical_channels() -> list[Channel]:
    """A menu spanning n,k in {3,4}: perfect (k>=n), noisy, under-resolving, blind."""
    return [
        Channel("perfect3_k3", ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))),
        Channel("noisy3_k3", ((0.8, 0.15, 0.05), (0.2, 0.7, 0.1), (0.1, 0.3, 0.6))),
        Channel("blind3_k3", ((1 / 3, 1 / 3, 1 / 3),) * 3),
        Channel("perfect3_k4", ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0))),
        Channel("perfect4_k4", tuple(tuple(1.0 if i == j else 0.0 for j in range(4)) for i in range(4))),
        Channel("under4_k3", ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, 1.0))),
    ]


def build_payload() -> dict[str, object]:
    """Certify the multi-state identity + caveats over the canonical channel menu."""
    scores = [score_channel(c) for c in canonical_channels()]
    by_name = {s.name: s for s in scores}

    identity_holds = bool(max(s.identity_residual for s in scores) < _IDENTITY_TOL)

    # Selection by the epistemic (active) term: most-diagnostic channel wins;
    # blind channel ranks strictly last.
    epistemic_ranked = sorted(scores, key=lambda s: (-s.epistemic_value, s.name))
    blind = by_name["blind3_k3"]
    blind_epistemic_zero = bool(blind.epistemic_value < _BLIND_EPISTEMIC_TOL)
    blind_ranks_last = bool(epistemic_ranked[-1].name == "blind3_k3")

    # k >= n perfect channels close the gap to ~zero; k < n cannot.
    perfect_closes = bool(
        by_name["perfect3_k3"].residual_gap < _ZERO_RESIDUAL_TOL
        and by_name["perfect4_k4"].residual_gap < _ZERO_RESIDUAL_TOL
    )
    under_resolves_floor = bool(by_name["under4_k3"].residual_gap > 1e-3)

    # Wrong-measure ablation must break the identity on a non-uniform-q(o) channel.
    noisy_model = _model(next(c for c in canonical_channels() if c.name == "noisy3_k3"))
    true_resid = expected_conditional_entropy(noisy_model)
    wrong_resid = _wrong_measure_conditional_entropy(noisy_model)
    wrong_measure_breaks_identity = bool(abs(true_resid - wrong_resid) > 1e-3)

    ok = bool(
        identity_holds
        and blind_epistemic_zero
        and blind_ranks_last
        and perfect_closes
        and under_resolves_floor
        and wrong_measure_breaks_identity
    )
    return {
        "schema": SCHEMA,
        "identity_tolerance": _IDENTITY_TOL,
        "channels": [s.as_row() for s in scores],
        "epistemic_ranking": [s.name for s in epistemic_ranked],
        "max_identity_residual": float(max(s.identity_residual for s in scores)),
        "wrong_measure_residual_gap": float(abs(true_resid - wrong_resid)),
        "identity_holds_multistate": identity_holds,
        "blind_epistemic_zero": blind_epistemic_zero,
        "blind_ranks_last": blind_ranks_last,
        "perfect_channels_close_gap": perfect_closes,
        "under_resolving_keeps_residual": under_resolves_floor,
        "wrong_measure_breaks_identity": wrong_measure_breaks_identity,
        "ok": ok,
    }


def validate_payload(payload: dict[str, object]) -> list[str]:
    """Re-derive the multi-state identity from the channel rows; return issues."""
    issues: list[str] = []
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        issues.append("schema mismatch")
    channels = payload.get("channels") or []
    if not isinstance(channels, list) or len(channels) < 6:
        return [*issues, "expected >=6 channel rows"]
    try:
        for row in channels:
            pe = float(row["prior_entropy"])
            res = float(row["residual_gap"])
            eps = float(row["epistemic_value"])
            if abs((pe - res) - eps) > _IDENTITY_TOL:
                issues.append(f"identity violated for {row.get('name')}")
            if eps < -1e-12:
                issues.append(f"negative epistemic value for {row.get('name')}")
    except (KeyError, TypeError, ValueError) as exc:
        return [*issues, f"malformed channel rows: {exc}"]
    if float(payload.get("wrong_measure_residual_gap", 0.0)) <= 1e-3:  # type: ignore[arg-type]
        issues.append("wrong-measure ablation does not break the identity (vacuous)")
    if bool(payload.get("ok")) != (not issues):
        issues.append("stored ok disagrees with re-derived verdict")
    return issues


if __name__ == "__main__":  # pragma: no cover - runnable self-check
    import json

    p = build_payload()
    print(json.dumps(p, indent=2, sort_keys=True))
    assert p["ok"], "multi-state certificate failed"
    assert validate_payload(p) == []
    print("\nactive_selection_general self-check OK")
