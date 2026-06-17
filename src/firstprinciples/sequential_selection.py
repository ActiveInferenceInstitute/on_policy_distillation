"""Sequential (sophisticated-inference) active selection: why visit the cue FIRST.

The single-step :mod:`firstprinciples.active_selection` result shows the cue HAS
the highest epistemic value, but it cannot show the canonical active-inference
reason an agent *goes to the cue first*: epistemic value is **instrumental** to a
later pragmatic goal. A myopic one-step planner is not enough to demonstrate this
-- and indeed, in the zero-cost toy a myopic planner already prefers the cue
(committing at chance is risk-punished), so "myopic avoids the cue" is a
green-by-construction trap (flagged by the prototype sweep).

The honest, horizon-dependent regime requires a declared **cue step-cost**: the
cue costs something now and pays off later. With a cue step-cost in the open
window ``(0.693, 1.524)`` nats (here ``cue_step_cost = 1.0``):

* a **myopic** one-step planner prefers ``commit`` (the cue's immediate cost
  outweighs its immediate value), but
* a **2-step (sophisticated)** planner still prefers ``cue``, because the cue
  resolves ``r`` and makes the step-2 arm choice near-free, so the summed policy
  EFE is lowest for cue-first.

That gap is the whole point: the planning horizon is what creates the preference.
Negative control: blinding the cue (it can no longer resolve ``r``) makes its
step-2 just as uncertain as commit, and the cue-first advantage collapses.

Per-step expected free energy is computed by :func:`energy.efe_report` (the shared
functional -- no new EFE definition). Everything is closed-form and seedless.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from . import energy

ArrayF = NDArray[np.float64]

SCHEMA = "firstprinciples.sequential_selection_demo.v1"

# Declared toy constants (the horizon-dependent regime; window ~ (0.693, 1.524)).
CUE_STEP_COST = 1.0
_FLAT2 = np.array([0.5, 0.5], dtype=np.float64)
_RESOLVE = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float64)      # cue resolves r
_UNINFORMATIVE = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=np.float64)  # commit / blind cue: no info on r
_ARM_LIKELIHOOD = np.array([[0.95, 0.05], [0.05, 0.95]], dtype=np.float64)  # step-2 reward/punish
_ARM_PREF = np.array([0.95, 0.05], dtype=np.float64)                # prefer reward
_RESOLVED_BELIEF = np.array([1.0, 0.0], dtype=np.float64)           # after a valid cue
# Expected reward derived from the arm likelihood (not hardcoded): a resolved
# belief picks the correct arm (reward prob = diagonal), chance averages the row.
_REWARD_PROB_CORRECT = float(_ARM_LIKELIHOOD[0, 0])
_REWARD_PROB_CHANCE = 0.5 * float(_ARM_LIKELIHOOD[0, 0] + _ARM_LIKELIHOOD[1, 0])

__all__ = ["step_efe", "policy_efe", "build_payload", "validate_payload"]


def step_efe(belief: ArrayF, likelihood: ArrayF, preferences: ArrayF) -> float:
    """Expected free energy of one step, via the shared energy.efe_report."""
    model = energy.GenerativeModel(prior=belief, likelihood=likelihood, preferences=preferences)
    return float(energy.efe_report(belief, model)["efe_epistemic_pragmatic"])


def policy_efe(*, cue_first: bool, cue_resolves: bool, cue_step_cost: float = CUE_STEP_COST) -> dict[str, float]:
    """Two-step policy EFE breakdown for a cue-first or commit-now policy.

    ``cue_first``: step 1 visits the cue (paying ``cue_step_cost``), step 2 chooses
    the arm under the resulting belief. Otherwise step 1 commits to an arm at
    chance and step 2 cannot improve. ``cue_resolves=False`` blinds the cue.
    """
    if cue_first:
        g1 = step_efe(_FLAT2, _RESOLVE if cue_resolves else _UNINFORMATIVE, _FLAT2) + cue_step_cost
        step2_belief = _RESOLVED_BELIEF if cue_resolves else _FLAT2
        g2 = step_efe(step2_belief, _ARM_LIKELIHOOD, _ARM_PREF)
        expected_reward = _REWARD_PROB_CORRECT if cue_resolves else _REWARD_PROB_CHANCE
    else:
        g1 = step_efe(_FLAT2, _UNINFORMATIVE, _FLAT2)
        g2 = step_efe(_FLAT2, _ARM_LIKELIHOOD, _ARM_PREF)
        expected_reward = _REWARD_PROB_CHANCE
    return {"g1": g1, "g2": g2, "policy_efe": g1 + g2, "expected_reward": expected_reward}


def build_payload() -> dict[str, object]:
    """Certify the horizon-dependent active-selection result with its controls."""
    cue = policy_efe(cue_first=True, cue_resolves=True)
    commit = policy_efe(cue_first=False, cue_resolves=True)
    blind_cue = policy_efe(cue_first=True, cue_resolves=False)  # NC: blinded cue

    # Myopic (step-1 only) vs sequential (2-step) decision.
    myopic_prefers_commit = bool(commit["g1"] < cue["g1"])
    sequential_prefers_cue = bool(cue["policy_efe"] < commit["policy_efe"])
    horizon_matters = bool(myopic_prefers_commit and sequential_prefers_cue)

    cue_first_lowest_policy_efe = bool(cue["policy_efe"] < commit["policy_efe"] and cue["policy_efe"] < blind_cue["policy_efe"])
    cue_first_highest_expected_reward = bool(cue["expected_reward"] > commit["expected_reward"])
    blind_cue_collapses_advantage = bool(blind_cue["policy_efe"] >= commit["policy_efe"] - 1e-9)

    ok = bool(
        horizon_matters
        and cue_first_lowest_policy_efe
        and cue_first_highest_expected_reward
        and blind_cue_collapses_advantage
    )
    return {
        "schema": SCHEMA,
        "cue_step_cost": CUE_STEP_COST,
        "policies": {"cue_first": cue, "commit_now": commit, "blind_cue_first": blind_cue},
        "myopic_prefers_commit": myopic_prefers_commit,
        "sequential_prefers_cue": sequential_prefers_cue,
        "horizon_matters": horizon_matters,
        "cue_first_lowest_policy_efe": cue_first_lowest_policy_efe,
        "cue_first_highest_expected_reward": cue_first_highest_expected_reward,
        "blind_cue_collapses_advantage": blind_cue_collapses_advantage,
        "ok": ok,
    }


def validate_payload(payload: dict[str, object]) -> list[str]:
    """Re-derive the horizon-dependence verdict from the per-step G rows."""
    issues: list[str] = []
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        issues.append("schema mismatch")
    pol = payload.get("policies")
    if not isinstance(pol, dict) or not {"cue_first", "commit_now", "blind_cue_first"} <= set(pol):
        return [*issues, "missing policy rows"]
    try:
        cue, commit, blind = pol["cue_first"], pol["commit_now"], pol["blind_cue_first"]
        for name, row in (("cue", cue), ("commit", commit), ("blind", blind)):
            if abs(float(row["policy_efe"]) - (float(row["g1"]) + float(row["g2"]))) > 1e-9:
                issues.append(f"policy_efe != g1+g2 for {name}")
        # Re-derive the horizon-dependence from the rows.
        if not (float(commit["g1"]) < float(cue["g1"])):
            issues.append("myopic does not prefer commit (re-derived)")
        if not (float(cue["policy_efe"]) < float(commit["policy_efe"])):
            issues.append("sequential does not prefer cue (re-derived)")
        if not (float(blind["policy_efe"]) >= float(commit["policy_efe"]) - 1e-9):
            issues.append("blind-cue advantage did not collapse (re-derived)")
        if not (float(cue["expected_reward"]) > float(commit["expected_reward"])):
            issues.append("cue-first not higher expected reward (re-derived)")
    except (KeyError, TypeError, ValueError) as exc:
        return [*issues, f"malformed policy rows: {exc}"]
    if bool(payload.get("ok")) != (not issues):
        issues.append("stored ok disagrees with re-derived verdict")
    return issues


if __name__ == "__main__":  # pragma: no cover - runnable self-check
    import json

    p = build_payload()
    print(json.dumps(p, indent=2, sort_keys=True))
    assert p["ok"] and validate_payload(p) == [], "sequential certificate failed"
    print("\nsequential_selection self-check OK")
