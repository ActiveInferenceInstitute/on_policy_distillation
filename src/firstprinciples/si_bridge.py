"""Analytical <-> pymdp bridge: the active-selection result predicts the SI agent.

This is the unification between the closed-form active-selection result
(:mod:`firstprinciples.active_selection`) and the project's existing pymdp
sophisticated-inference (SI) T-maze simulation. It makes a QUANTITATIVE, not merely
ordinal, prediction and checks it against the committed SI trace artifacts.

Honest scope (the prototype confirmed pymdp does not expose internal EFE terms, so
an internal-EFE bridge is impossible): the claim is bound to OBSERVABLES of the SI
run -- the realized location sequence and the belief entropy -- never to pymdp's
internal expected-free-energy values.

Three bound claims, all read from ``output/data/si_tmaze_{trace,summary}.json``:

1. **Behavioural:** the SI agent visits the cue location BEFORE any arm (epistemic
   action precedes the pragmatic one), and its belief entropy collapses at the cue
   observation.
2. **Quantitative:** the analytical residual ``E_o[H(r|o)]`` at the environment's
   own cue validity equals the SI agent's post-cue belief entropy to < 1e-6. The
   cue validity is read from the summary (source of truth), never hardcoded.
3. **Selection:** with the cue set to the environment's validity, the analytical
   EFE menu still selects the cue.

Negative controls: (a) a blinded cue (validity 0.5) flips the EFE selection to an
arm and re-opens the analytical residual; (b) validity-specificity -- the analytical
residual at the WRONG validity (0.5 or 1.0) does NOT match the SI post-cue entropy,
so the match is a real prediction bound to the environment, not a coincidence.

The analytical quantities come from :mod:`firstprinciples.active_selection` (no new
EFE/entropy definitions). Reads committed artifacts only; runs no pymdp.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from analytical.free_energy import shannon_entropy

from . import active_selection as asel

SCHEMA = "firstprinciples.si_bridge_demo.v1"

_TRACE = ("output", "data", "si_tmaze_trace.json")
_SUMMARY = ("output", "data", "si_tmaze_summary.json")
_ARM_LOCATIONS = {"left_arm", "right_arm"}
_MATCH_TOL = 1e-6
_MISMATCH_MARGIN = 1e-2

__all__ = [
    "analytical_residual_at_validity",
    "efe_menu_selects_cue",
    "analytical_entropy_trajectory",
    "build_payload",
    "validate_payload",
]


def analytical_entropy_trajectory(cue_obs: list[int], outcome_obs: list[int], validity: float) -> list[float]:
    """Running-Bayesian belief-entropy trajectory over the reward-location latent.

    Flat prior gives ``H = ln 2``; a cue observation (cue_left / cue_right)
    sharpens the posterior to ``H([v, 1-v])``; a reward outcome resolves the
    latent, so ``H -> 0``. Reuses the shared :func:`shannon_entropy`; the one-hot
    direction after resolution is irrelevant to the entropy. The closed-form
    prediction of the pymdp SI agent's belief entropy at every step.
    """
    v = float(validity)
    post = np.array([0.5, 0.5], dtype=np.float64)
    traj: list[float] = []
    for cue, outcome in zip(cue_obs, outcome_obs, strict=True):
        if cue == 1:  # cue_left
            post = post * np.array([v, 1.0 - v])
            post = post / post.sum()
        elif cue == 2:  # cue_right
            post = post * np.array([1.0 - v, v])
            post = post / post.sum()
        if outcome == 1:  # reward resolves the latent
            post = np.array([1.0, 0.0])
        traj.append(float(shannon_entropy(post)))
    return traj


def _load(root: Path, parts: tuple[str, ...]) -> dict:
    return json.loads(root.joinpath(*parts).read_text(encoding="utf-8"))


def analytical_residual_at_validity(validity: float) -> float:
    """Closed-form residual E_o[H(r|o)] for a symmetric binary cue (reuses active_selection)."""
    return asel.score_policy(asel._symmetric_cue(validity)).residual_gap


def efe_menu_selects_cue(validity: float) -> bool:
    """Does the analytical EFE menu (cue at this validity) still pick the cue?"""
    menu = [asel._symmetric_cue(validity)] + [p for p in asel.canonical_policies() if p.name != "cue"]
    scores = [asel.score_policy(p) for p in menu]
    return asel.rank_by_efe(scores)[0].name.startswith("cue")


def build_payload(root: Path | None = None) -> dict[str, object]:
    """Certify the observable + quantitative bridge from the committed SI artifacts."""
    base = (root or Path(".")).resolve()
    trace = _load(base, _TRACE)
    summary = _load(base, _SUMMARY)
    steps = trace.get("steps") or []

    cue_validity = float(summary["config"]["environment"]["cue_validity"])
    locations = [s["observation_names_by_modality"]["location"] for s in steps]
    belief_entropy = [float(s["belief_entropy"]) for s in steps]

    cue_step = next((i for i, loc in enumerate(locations) if loc == "cue_location"), None)
    first_arm_step = next((i for i, loc in enumerate(locations) if loc in _ARM_LOCATIONS), None)
    cue_before_arm = bool(cue_step is not None and (first_arm_step is None or cue_step < first_arm_step))

    post_cue_entropy = belief_entropy[cue_step] if cue_step is not None else float("nan")
    entropy_drop_at_cue = (
        belief_entropy[cue_step - 1] - belief_entropy[cue_step]
        if cue_step is not None and cue_step > 0
        else 0.0
    )
    entropy_collapses_at_cue = bool(entropy_drop_at_cue > 1e-3)

    analytical_residual = analytical_residual_at_validity(cue_validity)
    residual_match_abs = abs(analytical_residual - post_cue_entropy)
    quantitative_match = bool(residual_match_abs < _MATCH_TOL)

    efe_selects_cue_at_validity = efe_menu_selects_cue(cue_validity)

    # NC (a): blinded cue (validity 0.5) -> EFE no longer picks cue, residual re-opens.
    blinded_efe_picks_cue = efe_menu_selects_cue(0.5)
    blinded_residual = analytical_residual_at_validity(0.5)
    blinded_control_bites = bool((not blinded_efe_picks_cue) and blinded_residual > analytical_residual + _MISMATCH_MARGIN)

    # NC (b): validity-specificity -- wrong validities must NOT match the SI entropy.
    mismatch_at_one = abs(analytical_residual_at_validity(1.0) - post_cue_entropy) > _MISMATCH_MARGIN
    mismatch_at_half = abs(analytical_residual_at_validity(0.5) - post_cue_entropy) > _MISMATCH_MARGIN
    match_is_validity_specific = bool(mismatch_at_one and mismatch_at_half)

    # Per-step trajectory bridge: the closed-form running-Bayesian belief entropy
    # predicts the pymdp SI agent's belief entropy at EVERY step, not just post-cue.
    cue_obs_by_step = [int(s["observations_by_modality"]["cue"]) for s in steps]
    outcome_obs_by_step = [int(s["observations_by_modality"]["outcome"]) for s in steps]
    analytical_traj = analytical_entropy_trajectory(cue_obs_by_step, outcome_obs_by_step, cue_validity)
    per_step_abs_error = [abs(analytical_traj[i] - belief_entropy[i]) for i in range(len(steps))]
    max_trajectory_error_abs = max(per_step_abs_error) if per_step_abs_error else 0.0
    trajectory_match = bool(max_trajectory_error_abs < _MATCH_TOL)
    monotone_collapse_measured = bool(all(belief_entropy[i] >= belief_entropy[i + 1] - 1e-9 for i in range(len(belief_entropy) - 1)))
    monotone_collapse_predicted = bool(all(analytical_traj[i] >= analytical_traj[i + 1] - 1e-9 for i in range(len(analytical_traj) - 1)))
    # Controls along the WHOLE trajectory: wrong validity and shuffled observation
    # order must both break the match.
    wrong_validity_traj = analytical_entropy_trajectory(cue_obs_by_step, outcome_obs_by_step, 1.0)
    wrong_validity_trajectory_max_error = max(
        (abs(wrong_validity_traj[i] - belief_entropy[i]) for i in range(len(steps))), default=0.0
    )
    wrong_validity_breaks_trajectory = bool(wrong_validity_trajectory_max_error > _MISMATCH_MARGIN)
    rev_traj = analytical_entropy_trajectory(list(reversed(cue_obs_by_step)), list(reversed(outcome_obs_by_step)), cue_validity)
    shuffled_order_breaks_trajectory = bool(
        max(abs(rev_traj[i] - belief_entropy[i]) for i in range(len(steps))) > _MISMATCH_MARGIN
    )

    ok = bool(
        cue_before_arm
        and entropy_collapses_at_cue
        and quantitative_match
        and efe_selects_cue_at_validity
        and blinded_control_bites
        and match_is_validity_specific
        and trajectory_match
        and monotone_collapse_measured
        and monotone_collapse_predicted
        and wrong_validity_breaks_trajectory
        and shuffled_order_breaks_trajectory
    )
    return {
        "schema": SCHEMA,
        "cue_validity": cue_validity,
        "realized_location_sequence": locations,
        "belief_entropy_by_step": belief_entropy,
        "cue_step": cue_step,
        "first_arm_step": first_arm_step,
        "cue_before_arm": cue_before_arm,
        "post_cue_belief_entropy": post_cue_entropy,
        "entropy_drop_at_cue": entropy_drop_at_cue,
        "entropy_collapses_at_cue": entropy_collapses_at_cue,
        "analytical_residual_at_env_validity": analytical_residual,
        "residual_entropy_match_abs": residual_match_abs,
        "quantitative_match": quantitative_match,
        "efe_selects_cue_at_validity": efe_selects_cue_at_validity,
        "blinded_control_bites": blinded_control_bites,
        "blinded_efe_residual_margin": float(blinded_residual - analytical_residual),
        "wrong_validity_trajectory_max_error": float(wrong_validity_trajectory_max_error),
        "match_is_validity_specific": match_is_validity_specific,
        "cue_obs_by_step": cue_obs_by_step,
        "outcome_obs_by_step": outcome_obs_by_step,
        "analytical_entropy_by_step": analytical_traj,
        "per_step_abs_error": per_step_abs_error,
        "max_trajectory_error_abs": max_trajectory_error_abs,
        "trajectory_match": trajectory_match,
        "monotone_collapse_measured": monotone_collapse_measured,
        "monotone_collapse_predicted": monotone_collapse_predicted,
        "wrong_validity_breaks_trajectory": wrong_validity_breaks_trajectory,
        "shuffled_order_breaks_trajectory": shuffled_order_breaks_trajectory,
        "ok": ok,
    }


def validate_payload(payload: dict[str, object]) -> list[str]:
    """Re-derive the bridge verdict from the stored trace-derived rows."""
    issues: list[str] = []
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        issues.append("schema mismatch")
    loc_raw = payload.get("realized_location_sequence")
    ent_raw = payload.get("belief_entropy_by_step")
    locations = list(loc_raw) if isinstance(loc_raw, list) else []
    entropies = [float(x) for x in ent_raw] if isinstance(ent_raw, list) else []
    cue_step = payload.get("cue_step")
    try:
        validity = float(payload["cue_validity"])  # type: ignore[arg-type]
    except (KeyError, TypeError, ValueError) as exc:
        return [*issues, f"malformed bridge payload: {exc}"]
    if "cue_location" not in locations:
        issues.append("no cue_location in realized sequence")
    else:
        re_cue = locations.index("cue_location")
        re_arm = next((i for i, loc in enumerate(locations) if loc in _ARM_LOCATIONS), None)
        if not (re_arm is None or re_cue < re_arm):
            issues.append("cue does not precede arm (re-derived)")
        if cue_step != re_cue:
            issues.append("stored cue_step disagrees with re-derived")
    # Quantitative match re-derived from the analytical side + the stored post-cue entropy.
    if isinstance(cue_step, int) and 0 <= cue_step < len(entropies):
        re_resid = analytical_residual_at_validity(validity)
        if abs(re_resid - float(entropies[cue_step])) >= _MATCH_TOL:
            issues.append("analytical residual does not match SI post-cue entropy (re-derived)")
        # validity-specificity: wrong validities must NOT match
        if abs(analytical_residual_at_validity(1.0) - float(entropies[cue_step])) <= _MISMATCH_MARGIN:
            issues.append("match not validity-specific (v=1.0 also matches)")

    # Re-derive the WHOLE entropy trajectory from the stored observation sequences
    # (never trust the stored analytical_entropy_by_step vector).
    cue_raw = payload.get("cue_obs_by_step")
    out_raw = payload.get("outcome_obs_by_step")
    cue_seq = [int(x) for x in cue_raw] if isinstance(cue_raw, list) else []
    out_seq = [int(x) for x in out_raw] if isinstance(out_raw, list) else []
    if not cue_seq or len(cue_seq) != len(entropies) or len(out_seq) != len(entropies):
        issues.append("observation sequences missing or wrong length")
    else:
        re_traj = analytical_entropy_trajectory(cue_seq, out_seq, validity)
        if max(abs(re_traj[i] - entropies[i]) for i in range(len(entropies))) >= _MATCH_TOL:
            issues.append("analytical entropy trajectory does not match SI trajectory (re-derived)")
        # wrong-validity control must break the whole-trajectory match
        wrong = analytical_entropy_trajectory(cue_seq, out_seq, 1.0)
        if max(abs(wrong[i] - entropies[i]) for i in range(len(entropies))) <= _MISMATCH_MARGIN:
            issues.append("trajectory match not validity-specific (v=1.0 also matches)")

    if bool(payload.get("ok")) != (not issues):
        issues.append("stored ok disagrees with re-derived verdict")
    return issues


if __name__ == "__main__":  # pragma: no cover - runnable self-check
    p = build_payload(Path("."))
    print(json.dumps(p, indent=2, sort_keys=True))
    assert p["ok"] and validate_payload(p) == [], "si_bridge certificate failed"
    print("\nsi_bridge self-check OK")
