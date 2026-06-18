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
# Multi-step (sophisticated-inference) horizon: a single cue-then-exploit-for-the-
# rest-of-the-horizon policy vs commit-every-step. The cost sits in an
# analytically DERIVED window (asserted in build_horizon_curve), not hand-tuned.
HORIZON_CUE_STEP_COST = 1.3
_HORIZONS: tuple[int, ...] = (1, 2, 3, 4, 5, 6)
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

__all__ = ["step_efe", "policy_efe", "horizon_primitives", "build_horizon_curve", "build_payload", "validate_payload"]


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


def horizon_primitives() -> dict[str, float]:
    """The four single-step EFE primitives, recomputed from the shared functional.

    ``g_exploit_resolved`` = arm step under a resolved belief; ``g_exploit_flat`` =
    arm step under a chance belief; ``g_cue_epistemic`` = a (valid) cue step;
    ``g_blind_epistemic`` = a blinded cue step. No numeric literals enter the
    verdict path -- every horizon quantity is a function of these.
    """
    return {
        "g_exploit_resolved": step_efe(_RESOLVED_BELIEF, _ARM_LIKELIHOOD, _ARM_PREF),
        "g_exploit_flat": step_efe(_FLAT2, _ARM_LIKELIHOOD, _ARM_PREF),
        "g_cue_epistemic": step_efe(_FLAT2, _RESOLVE, _FLAT2),
        "g_blind_epistemic": step_efe(_FLAT2, _UNINFORMATIVE, _FLAT2),
    }


def build_horizon_curve(
    cost: float = HORIZON_CUE_STEP_COST, horizons: tuple[int, ...] = _HORIZONS
) -> dict[str, object]:
    """Multi-step policy EFE over a planning horizon: cue-then-exploit vs commit.

    For a horizon ``H``, a cue-first policy pays the cue cost once, then exploits
    a resolved belief for the remaining ``H-1`` steps; a commit policy acts at
    chance every step; a blinded-cue policy pays the cost but cannot resolve, so
    its exploit stays flat. The per-step instrumental value of the cue is exactly
    ``delta = g_exploit_flat - g_exploit_resolved``, so the cue/commit gap grows
    linearly with the horizon -- the cue's value scales with how long it can be
    exploited. The cost is asserted to lie in the analytically-derived window in
    which a myopic (H=1) planner commits but every H>=2 planner cues.
    """
    p = horizon_primitives()
    g_r, g_f, g_e, g_b = p["g_exploit_resolved"], p["g_exploit_flat"], p["g_cue_epistemic"], p["g_blind_epistemic"]
    delta = g_f - g_r

    def cue_efe(h: int) -> float:
        return (g_e + cost) + (h - 1) * g_r

    def commit_efe(h: int) -> float:
        return h * g_f

    def blind_efe(h: int) -> float:
        return (g_b + cost) + (h - 1) * g_f

    rows = [
        {
            "horizon": float(h),
            "cue_policy_efe": cue_efe(h),
            "commit_policy_efe": commit_efe(h),
            "blind_policy_efe": blind_efe(h),
            "gap": commit_efe(h) - cue_efe(h),
            "sequential_prefers_cue": bool(cue_efe(h) < commit_efe(h)),
            "blind_collapses": bool(blind_efe(h) >= commit_efe(h) - 1e-9),
        }
        for h in horizons
    ]
    # Derived window: myopic (H=1) commits iff cost > g_f - g_e; the cue wins at
    # H=2 iff cost < 2*g_f - g_r - g_e. cost lying strictly inside makes the
    # horizon regime principled rather than tuned.
    window_lower = g_f - g_e
    window_upper = 2.0 * g_f - g_r - g_e
    cost_in_derived_window = bool(window_lower < cost < window_upper)
    break_even_horizon = (cost + g_e - g_r) / delta if delta != 0 else float("inf")

    gaps = [row["gap"] for row in rows]
    gap_increments = [gaps[i] - gaps[i - 1] for i in range(1, len(gaps))]
    return {
        "cost": float(cost),
        "horizons": [int(h) for h in horizons],
        "primitives": {k: float(v) for k, v in p.items()},
        "per_step_instrumental_value": float(delta),
        "window_lower": float(window_lower),
        "window_upper": float(window_upper),
        "cost_in_derived_window": cost_in_derived_window,
        "break_even_horizon": float(break_even_horizon),
        "rows": rows,
        "myopic_prefers_commit_h1": bool(rows[0]["commit_policy_efe"] < rows[0]["cue_policy_efe"]),
        "cue_wins_for_all_horizon_ge_2": bool(all(r["sequential_prefers_cue"] for r in rows if r["horizon"] >= 2)),
        "gap_strictly_increasing": bool(all(g > 1e-12 for g in gap_increments)),
        "gap_increments_constant": bool(all(abs(g - delta) < 1e-9 for g in gap_increments)),
        "blind_collapses_all_horizons": bool(all(r["blind_collapses"] for r in rows)),
    }


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

    horizon = build_horizon_curve()
    horizon_ok = bool(
        horizon["cost_in_derived_window"]
        and horizon["myopic_prefers_commit_h1"]
        and horizon["cue_wins_for_all_horizon_ge_2"]
        and horizon["gap_strictly_increasing"]
        and horizon["gap_increments_constant"]
        and horizon["blind_collapses_all_horizons"]
    )

    ok = bool(
        horizon_matters
        and cue_first_lowest_policy_efe
        and cue_first_highest_expected_reward
        and blind_cue_collapses_advantage
        and horizon_ok
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
        "horizon_regime_holds": horizon_ok,
        "horizon_curve": horizon,
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
        # Re-run the energy functional for the 2-step policies (not just relational
        # consistency): a fabricated policy block is caught even if its inequalities hold.
        for name, stored, recomp in (
            ("cue", cue, policy_efe(cue_first=True, cue_resolves=True)),
            ("commit", commit, policy_efe(cue_first=False, cue_resolves=True)),
            ("blind", blind, policy_efe(cue_first=True, cue_resolves=False)),
        ):
            if abs(float(stored["policy_efe"]) - recomp["policy_efe"]) > 1e-9:
                issues.append(f"{name} policy_efe disagrees with re-run energy functional")
    except (KeyError, TypeError, ValueError) as exc:
        return [*issues, f"malformed policy rows: {exc}"]

    # Re-derive the whole horizon curve from the energy primitives (never trust
    # the stored rows): recompute cue/commit/blind EFE at each horizon and the
    # linear-gap, window, and control flags, then require the stored block to agree.
    hz = payload.get("horizon_curve")
    if not isinstance(hz, dict):
        issues.append("horizon_curve missing")
    else:
        try:
            cost = float(hz["cost"])
            stored_rows = hz["rows"]
            recomputed = build_horizon_curve(cost=cost, horizons=tuple(int(h) for h in hz["horizons"]))
            for key in (
                "cost_in_derived_window", "myopic_prefers_commit_h1", "cue_wins_for_all_horizon_ge_2",
                "gap_strictly_increasing", "gap_increments_constant", "blind_collapses_all_horizons",
            ):
                if bool(hz.get(key)) != bool(recomputed[key]):
                    issues.append(f"horizon flag {key} disagrees with re-derived")
            if not recomputed["cost_in_derived_window"]:
                issues.append("horizon cost not in the derived window")
            stored_psiv = float(hz.get("per_step_instrumental_value", 0.0))  # type: ignore[arg-type]
            re_psiv = float(recomputed["per_step_instrumental_value"])  # type: ignore[arg-type]
            if abs(stored_psiv - re_psiv) > 1e-9:
                issues.append("per-step instrumental value disagrees with re-derived")
            re_rows = recomputed["rows"]
            re_list = re_rows if isinstance(re_rows, list) else []
            stored_list = stored_rows if isinstance(stored_rows, list) else []
            if len(stored_list) != len(re_list) or any(
                abs(float(stored_list[i]["gap"]) - float(re_list[i]["gap"])) > 1e-9 for i in range(len(re_list))
            ):
                issues.append("stored horizon gaps disagree with re-derived")
        except (KeyError, TypeError, ValueError) as exc:
            issues.append(f"malformed horizon_curve: {exc}")

    if bool(payload.get("ok")) != (not issues):
        issues.append("stored ok disagrees with re-derived verdict")
    return issues


if __name__ == "__main__":  # pragma: no cover - runnable self-check
    import json

    p = build_payload()
    print(json.dumps(p, indent=2, sort_keys=True))
    assert p["ok"] and validate_payload(p) == [], "sequential certificate failed"
    print("\nsequential_selection self-check OK")
