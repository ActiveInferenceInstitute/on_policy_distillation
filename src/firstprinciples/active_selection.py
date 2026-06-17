"""Active rollout selection: EFE closes the *active* half of the OPD<->AI map.

The energy module (:mod:`firstprinciples.energy`) establishes the **passive**
half of the correspondence: on a fixed model, the reverse-KL distillation loss
``D_KL(pi_S || pi_T)`` is the variational free energy of the student up to a
constant. That is the realized-rollout (VFE) reading. It says nothing about
*which* states the student should roll out on -- the data-collection decision
that the word "on-policy" actually names. The 25-row correspondence map records
exactly this hole: the "expected free energy (planning)" row is annotated
"action selected by EFE; loss evaluated by VFE" with the action side left
un-formalised.

This module closes that hole with the **active** (expected-free-energy) half.
On-policy distillation does not distil on a fixed observation stream; a
data-collection policy chooses which states the student visits, and therefore
which teacher signal the student ever sees. We score each candidate
data-collection policy by its expected free energy and prove a toy-exact
identity that makes EFE the right scorer:

    The student<->teacher belief gap that distilling on policy ``pi`` can close
    is exactly the EFE **epistemic value** of ``pi``:

        gap_closed(pi) = H(r) - E_o[H(r | o)] = I(o; r) = epistemic_value(pi).

A student trained to match the (privileged) teacher posterior on ``pi``'s own
observation distribution reproduces that posterior per observation; its expected
residual uncertainty about the reward-relevant latent ``r`` is then exactly the
conditional entropy ``E_o[H(r|o)]``, and the teacher signal it could ever absorb
is the mutual information the channel carries -- the epistemic term of the
expected free energy.

Consequence (the active loop), demonstrated on a deliberately minimal T-maze
menu under declared assumptions:

* Minimising EFE over the menu selects the **cue** policy, and cue-informed
  rollouts close the residual distillation gap **exactly** (to machine zero).
* A purely **pragmatic** selector (the epistemic term ablated -- greedy for the
  preferred "reward" observation) commits to an arm and leaves the gap fully
  open: on-policy distillation cannot be driven by reward/pragmatic value alone.
* A **uniform/random** selector leaves a strictly positive expected residual.
* The result is **non-vacuous**: blinding the cue (diagnosticity forced to
  chance) collapses its epistemic value and re-opens the gap, so the gate is
  measuring a real channel property, not a tautology.

Active inference is therefore not decoration on the distillation story -- the
epistemic term of the expected free energy is exactly what makes on-policy
distillation exact in a partially observed world.

Everything here is closed-form, deterministic, and seedless. Expected free
energy is computed by :func:`firstprinciples.energy.efe_epistemic_pragmatic`
(one definition, shared with the passive half) so the two halves cannot drift.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from analytical.free_energy import shannon_entropy

from . import energy
from .divergences import normalize

ArrayF = NDArray[np.float64]

SCHEMA = "firstprinciples.active_selection_demo.v1"

# Residual closes to machine zero for the perfectly diagnostic cue; the gate
# tolerance sits far below the next-best candidate's residual (see build_payload).
_RESIDUAL_TOL = 1e-9
# Margin separating the cue from epistemically blind policies in the controls.
_GAP_MARGIN = 1e-3

# Likelihood p(o | r) for each canonical data-collection policy, as 2x2 rows.
# A diagnostic channel has distinct rows (observation discriminates r); a blind
# channel has identical rows (observation independent of r).
_PERFECT_CUE = ((1.0, 0.0), (0.0, 1.0))
_BLIND_LEFT = ((0.8, 0.2), (0.8, 0.2))
_BLIND_RIGHT = ((0.2, 0.8), (0.2, 0.8))
_BLIND_FLAT = ((0.5, 0.5), (0.5, 0.5))

__all__ = [
    "RolloutPolicy",
    "PolicyScore",
    "policy_model",
    "expected_conditional_entropy",
    "score_policy",
    "rank_by_efe",
    "rank_by_pragmatic_only",
    "canonical_policies",
    "validity_sweep",
    "build_payload",
]


@dataclass(frozen=True)
class RolloutPolicy:
    """A candidate on-policy data-collection policy.

    ``likelihood`` is ``p(o | r)`` for the binary observation channel this policy
    induces over the reward-relevant latent ``r`` (rows = states, columns =
    observations). Distinct rows make the channel diagnostic (epistemically
    rich); identical rows make it blind. ``preferences`` is the goal prior
    ``p(o)`` over this policy's two observations -- a reward-tilted policy places
    its mass on the "good" observation, an information-seeking policy stays flat.
    """

    name: str
    likelihood: tuple[tuple[float, float], tuple[float, float]]
    preferences: tuple[float, float]

    def likelihood_array(self) -> ArrayF:
        a = np.array(self.likelihood, dtype=np.float64)
        if not np.allclose(a.sum(axis=1), 1.0, atol=1e-8):
            raise ValueError(f"policy {self.name!r}: likelihood rows must be normalised")
        return a


@dataclass(frozen=True)
class PolicyScore:
    name: str
    efe: float
    epistemic_value: float
    pragmatic_value: float
    residual_gap: float
    closeable_gap: float


def policy_model(policy: RolloutPolicy) -> energy.GenerativeModel:
    """Build the categorical generative model a rollout policy induces.

    Two reward-relevant latent states ``r in {reward_left, reward_right}`` with a
    flat prior; the policy supplies the observation likelihood ``p(o|r)`` and the
    preferences ``p(o)``. The prior is fixed flat by construction: this is a
    deterministic flat-prior toy (project genre), and the residual identity
    proved here requires the data-collection prior to *be* the EFE recognition
    density ``q(s)`` -- so the single flat prior is shared by both sides on
    purpose. A non-flat prior would need that coincidence re-established per side.
    """
    prior = np.array([0.5, 0.5], dtype=np.float64)
    preferences = normalize(np.array(policy.preferences, dtype=np.float64))
    return energy.GenerativeModel(prior=prior, likelihood=policy.likelihood_array(), preferences=preferences)


def expected_conditional_entropy(model: energy.GenerativeModel) -> float:
    """``E_o[H(r | o)]`` -- the residual uncertainty an on-policy student keeps.

    A student that matches the privileged teacher posterior ``p(r|o)`` on the
    policy's own observation distribution ``q(o)`` carries exactly this expected
    residual entropy about ``r``. It is the part of the teacher's signal the
    channel never delivers. The ``gap_closed = epistemic`` identity holds because
    this marginalises over the *same* ``q(s) = model.prior`` that the EFE
    epistemic term uses; the two sides must share that recognition density.
    """
    q_o = energy.predicted_observations(model.prior, model)
    total = 0.0
    for o in range(model.num_obs):
        if q_o[o] <= 0.0:
            continue
        post = energy.posterior(model, o)
        total += float(q_o[o]) * shannon_entropy(post)
    return total


def score_policy(policy: RolloutPolicy) -> PolicyScore:
    """Score one rollout policy with the shared EFE functional + the residual.

    The closeable gap is the EFE epistemic value; the residual is the prior
    entropy minus that closeable gap, i.e. ``E_o[H(r|o)]``. The identity
    ``H(r) - E_o[H(r|o)] = I(o;r) = epistemic`` is asserted to machine precision
    in :func:`build_payload`.
    """
    model = policy_model(policy)
    _g, epistemic, pragmatic = energy.efe_epistemic_pragmatic(model.prior, model)
    g_report = energy.efe_report(model.prior, model)
    residual = expected_conditional_entropy(model)
    return PolicyScore(
        name=policy.name,
        efe=float(g_report["efe_epistemic_pragmatic"]),
        epistemic_value=float(epistemic),
        pragmatic_value=float(pragmatic),
        residual_gap=residual,
        closeable_gap=float(epistemic),
    )


def rank_by_efe(scores: list[PolicyScore]) -> list[PolicyScore]:
    """Active-inference selection: ascending expected free energy (best first)."""
    return sorted(scores, key=lambda s: (s.efe, s.name))


def rank_by_pragmatic_only(scores: list[PolicyScore]) -> list[PolicyScore]:
    """Negative-control selector: most reward-tilted first, epistemics ablated."""
    return sorted(scores, key=lambda s: (-s.pragmatic_value, s.name))


def canonical_policies() -> list[RolloutPolicy]:
    """The toy T-maze data-collection menu (declared assumptions A1-A4).

    ``cue`` visits the cue location: a perfectly diagnostic channel with flat
    preferences -- epistemically rich, pragmatically neutral. ``commit_left`` /
    ``commit_right`` head straight for an arm: a channel blind to ``r`` but with
    reward-tilted preferences it reliably observes -- pragmatically attractive,
    epistemically empty. ``stay`` does nothing.
    """
    return [
        RolloutPolicy("cue", likelihood=_PERFECT_CUE, preferences=(0.5, 0.5)),
        RolloutPolicy("commit_left", likelihood=_BLIND_LEFT, preferences=(0.8, 0.2)),
        RolloutPolicy("commit_right", likelihood=_BLIND_RIGHT, preferences=(0.2, 0.8)),
        RolloutPolicy("stay", likelihood=_BLIND_FLAT, preferences=(0.5, 0.5)),
    ]


def _symmetric_cue(validity: float) -> RolloutPolicy:
    v = float(validity)
    return RolloutPolicy(
        f"cue_v{v:.2f}",
        likelihood=((v, 1.0 - v), (1.0 - v, v)),
        preferences=(0.5, 0.5),
    )


def validity_sweep(validities: tuple[float, ...] = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)) -> list[dict[str, float]]:
    """Graded cue diagnosticity: residual = H(r) - epistemic across validities.

    Shows the ``gap_closed = epistemic`` identity is not a single-point artefact:
    as the cue sharpens, epistemic value rises and the residual falls in lockstep
    to zero, monotonically.
    """
    rows: list[dict[str, float]] = []
    for v in validities:
        score = score_policy(_symmetric_cue(v))
        rows.append(
            {
                "cue_validity": float(v),
                "epistemic_value": score.epistemic_value,
                "residual_gap": score.residual_gap,
            }
        )
    return rows


def build_payload() -> dict[str, object]:
    """Build the ``firstprinciples.active_selection_demo`` artifact.

    Certifies the active-loop result: the EFE-optimal data-collection policy is
    ``cue``; its rollouts drive the residual distillation gap to machine zero; a
    pragmatic-only selector picks an arm and keeps the gap fully open; a uniform
    selector keeps a strictly positive expected residual; and the result is
    non-vacuous (a blinded cue re-opens the gap).
    """
    policies = canonical_policies()
    scores = [score_policy(p) for p in policies]
    by_name = {s.name: s for s in scores}
    prior_entropy = float(shannon_entropy(np.array([0.5, 0.5], dtype=np.float64)))

    efe_ranked = rank_by_efe(scores)
    pragmatic_ranked = rank_by_pragmatic_only(scores)
    efe_pick = efe_ranked[0]
    pragmatic_pick = pragmatic_ranked[0]
    uniform_expected_residual = float(np.mean([s.residual_gap for s in scores]))

    # Core identity, per policy: H(r) - E_o[H(r|o)] == I(o;r) == epistemic.
    identity_residuals = [abs((prior_entropy - s.residual_gap) - s.epistemic_value) for s in scores]
    identity_holds = bool(max(identity_residuals) < 1e-12)

    sweep = validity_sweep()
    # Monotone: sharper cue => more epistemic value, less residual.
    sweep_monotone = bool(
        all(sweep[i]["epistemic_value"] <= sweep[i + 1]["epistemic_value"] + 1e-12 for i in range(len(sweep) - 1))
        and all(sweep[i]["residual_gap"] >= sweep[i + 1]["residual_gap"] - 1e-12 for i in range(len(sweep) - 1))
    )
    # Strictness floor: a flat sweep would satisfy the tolerant monotone check
    # vacuously, so require the endpoints to actually separate (non-vacuity).
    sweep_strict = bool(
        sweep[-1]["epistemic_value"] > sweep[0]["epistemic_value"] + _GAP_MARGIN
        and sweep[0]["residual_gap"] > sweep[-1]["residual_gap"] + _GAP_MARGIN
    )

    # Non-vacuity control: blind the cue and the gap must re-open.
    blinded_score = score_policy(_symmetric_cue(0.5))
    blinding_reopens_gap = bool(
        blinded_score.residual_gap > by_name["cue"].residual_gap + _GAP_MARGIN
        and blinded_score.epistemic_value < by_name["cue"].epistemic_value - _GAP_MARGIN
    )

    efe_selects_cue = bool(efe_pick.name == "cue")
    efe_pick_closes_gap = bool(efe_pick.residual_gap < _RESIDUAL_TOL)
    pragmatic_avoids_cue = bool(pragmatic_pick.name != "cue")
    pragmatic_pick_keeps_residual = bool(pragmatic_pick.residual_gap > efe_pick.residual_gap + _GAP_MARGIN)
    uniform_keeps_residual = bool(uniform_expected_residual > efe_pick.residual_gap + _GAP_MARGIN)

    ok = bool(
        identity_holds
        and sweep_monotone
        and sweep_strict
        and efe_selects_cue
        and efe_pick_closes_gap
        and pragmatic_avoids_cue
        and pragmatic_pick_keeps_residual
        and uniform_keeps_residual
        and blinding_reopens_gap
    )

    return {
        "schema": SCHEMA,
        "prior_entropy_nats": prior_entropy,
        "residual_tolerance": _RESIDUAL_TOL,
        "policies": [
            {
                "name": s.name,
                "efe": s.efe,
                "epistemic_value": s.epistemic_value,
                "pragmatic_value": s.pragmatic_value,
                "residual_gap": s.residual_gap,
                "closeable_gap": s.closeable_gap,
            }
            for s in scores
        ],
        "efe_ranking": [s.name for s in efe_ranked],
        "pragmatic_only_ranking": [s.name for s in pragmatic_ranked],
        "efe_selected_policy": efe_pick.name,
        "pragmatic_only_selected_policy": pragmatic_pick.name,
        "efe_selected_residual_gap": efe_pick.residual_gap,
        "pragmatic_only_residual_gap": pragmatic_pick.residual_gap,
        "uniform_expected_residual_gap": uniform_expected_residual,
        "blinded_cue_residual_gap": blinded_score.residual_gap,
        "blinded_cue_epistemic_value": blinded_score.epistemic_value,
        "validity_sweep": sweep,
        "gap_closed_equals_epistemic_identity": identity_holds,
        "max_identity_residual": float(max(identity_residuals)),
        "validity_sweep_monotone": sweep_monotone,
        "validity_sweep_strict": sweep_strict,
        "efe_selects_cue": efe_selects_cue,
        "efe_pick_closes_gap": efe_pick_closes_gap,
        "pragmatic_only_avoids_cue": pragmatic_avoids_cue,
        "pragmatic_only_keeps_residual": pragmatic_pick_keeps_residual,
        "uniform_keeps_residual": uniform_keeps_residual,
        "blinding_reopens_gap": blinding_reopens_gap,
        "ok": ok,
    }


if __name__ == "__main__":  # pragma: no cover - runnable self-check
    import json

    payload = build_payload()
    print(json.dumps(payload, indent=2, sort_keys=True))
    assert payload["ok"], "active-selection certificate failed"
    assert payload["efe_selected_policy"] == "cue"
    assert payload["pragmatic_only_selected_policy"] != "cue"
    residual = payload["efe_selected_residual_gap"]
    assert isinstance(residual, float) and residual < 1e-9
    print("\nactive_selection self-check OK")
