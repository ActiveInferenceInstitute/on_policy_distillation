"""Result-integrity ledger: a synthesis audit over the result set.

The manuscript accumulates many first-principles results; this ledger makes the
two integrity properties of the *quantitative identity / cross-check* results
auditable in one artifact and one figure, rather than leaving them implicit
across a dozen separate certificates:

* **PRECISION** -- every quantitative correspondence's residual/error is below a
  *tier-aware* tolerance: proved closed-form identities (Tier 1) to within
  ``1e-12``, and numerical witnesses (Tier 2, which carry pymdp/optimizer float
  noise) to within ``1e-7``. The tolerances are tight (single-digit headroom over
  the live worst case), so a real degradation would fail the gate.
* **CONTROLS** -- every result's negative control bites by a *measured margin*,
  not a self-reported boolean: the ledger reads the magnitude that proves each
  control fires (the reopened gap, the wrong-measure gap, the blind-collapse
  margin, the wrong-validity error) and requires it to exceed ``1e-3``.

Scope: this covers the results that make a machine-precision *exactness* claim
(identities and analytical<->simulation cross-checks). Results that report a
*direction or reduction* rather than an exactness residual -- e.g. the
sequential-shift loss drop or the classroom KL magnitude -- are reported in their
own sections and are not precision rows here.

The ledger is a SYNTHESIS over already-audited results (each source carries its
own re-derivation validator gated in ``validate_outputs``); it adds a cross-read
(:func:`validate_against_sources`) so it cannot claim a residual or margin a
source does not contain. It introduces no new science.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

SCHEMA = "firstprinciples.precision_ledger_demo.v1"
# Tier-aware precision tolerance: identities are exact, witnesses carry float noise.
_TIER_TOL: dict[int, float] = {1: 1e-12, 2: 1e-7}
_CONTROL_MIN_MARGIN = 1e-3
_CROSS_READ_TOL = 1e-12

# (label, source artifact (relative), residual field, claim tier)
_PRECISION_SOURCES: tuple[tuple[str, str, str, int], ...] = (
    ("Analytical MI two-route residual", "output/data/analytical_observable_sweep.json", "max_abs_residual", 1),
    ("Active-selection identity", "output/data/firstprinciples/active_selection_demo.json", "max_identity_residual", 1),
    ("Multi-state identity (n,k in {3,4})", "output/data/firstprinciples/active_selection_general_demo.json", "max_identity_residual", 1),
    ("Parallel reverse-KL / VFE convergence", "output/data/firstprinciples/parallel_demo.json", "max_abs_difference", 2),
    ("pymdp bridge (post-cue entropy)", "output/data/firstprinciples/si_bridge_demo.json", "residual_entropy_match_abs", 2),
    ("pymdp bridge (per-step trajectory)", "output/data/firstprinciples/si_bridge_demo.json", "max_trajectory_error_abs", 2),
)
# (label, source artifact (relative), MARGIN field that must exceed _CONTROL_MIN_MARGIN)
_CONTROL_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("Active-selection: blinding reopens the gap", "output/data/firstprinciples/active_selection_demo.json", "blinded_cue_residual_gap"),
    ("Multi-state: wrong-measure breaks the identity", "output/data/firstprinciples/active_selection_general_demo.json", "wrong_measure_residual_gap"),
    ("Sequential: blinded cue collapses the advantage", "output/data/firstprinciples/sequential_selection_demo.json", "blind_collapse_margin"),
    ("Bridge: blinded cue reopens the residual", "output/data/firstprinciples/si_bridge_demo.json", "blinded_efe_residual_margin"),
    ("Bridge: wrong validity breaks the trajectory", "output/data/firstprinciples/si_bridge_demo.json", "wrong_validity_trajectory_max_error"),
)

__all__ = ["build_payload", "validate_payload", "validate_against_sources"]


def _read(root: Path, rel: str) -> dict:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def build_payload(root: Path | None = None) -> dict[str, object]:
    """Aggregate the precision and control margins from the live source artifacts."""
    base = (root or Path(".")).resolve()
    precision_rows: list[dict[str, object]] = []
    residual_values: list[float] = []
    for label, rel, field, tier in _PRECISION_SOURCES:
        val = float(_read(base, rel).get(field, math.nan))
        residual_values.append(val)
        tol = _TIER_TOL[tier]
        precision_rows.append(
            {"name": label, "source": rel, "field": field, "tier": tier, "tolerance": tol,
             "residual": val, "within_tol": bool(math.isfinite(val) and val < tol)}
        )
    control_rows: list[dict[str, object]] = []
    control_margins: list[float] = []
    for label, rel, field in _CONTROL_SOURCES:
        margin = float(_read(base, rel).get(field, math.nan))
        control_margins.append(margin)
        control_rows.append(
            {"name": label, "source": rel, "field": field, "margin": margin, "min_margin": _CONTROL_MIN_MARGIN,
             "bites": bool(math.isfinite(margin) and margin > _CONTROL_MIN_MARGIN)}
        )

    max_residual = max(residual_values, default=math.inf)
    min_control_margin = min(control_margins, default=0.0)
    all_precise = bool(all(r["within_tol"] for r in precision_rows))
    all_controlled = bool(all(r["bites"] for r in control_rows))
    ok = bool(all_precise and all_controlled and math.isfinite(max_residual))
    return {
        "schema": SCHEMA,
        "tier_tolerances": {str(k): v for k, v in _TIER_TOL.items()},
        "control_min_margin": _CONTROL_MIN_MARGIN,
        "precision_rows": precision_rows,
        "control_rows": control_rows,
        "result_count": len(precision_rows),
        "control_count": len(control_rows),
        "max_residual": max_residual,
        "min_control_margin": min_control_margin,
        "all_precise": all_precise,
        "all_controlled": all_controlled,
        "ok": ok,
    }


def validate_payload(payload: dict[str, object]) -> list[str]:
    """Re-derive the certificate from the stored ledger rows (internal consistency)."""
    issues: list[str] = []
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        issues.append("schema mismatch")
    prows = payload.get("precision_rows")
    crows = payload.get("control_rows")
    if not isinstance(prows, list) or not prows or not isinstance(crows, list) or not crows:
        return [*issues, "missing precision/control rows"]
    try:
        residuals = [float(r["residual"]) for r in prows]
        all_precise = all(math.isfinite(float(r["residual"])) and float(r["residual"]) < float(r["tolerance"]) for r in prows)
        margins = [float(r["margin"]) for r in crows]
        all_controlled = all(math.isfinite(float(r["margin"])) and float(r["margin"]) > float(r["min_margin"]) for r in crows)
    except (KeyError, TypeError, ValueError) as exc:
        return [*issues, f"malformed ledger rows: {exc}"]
    if bool(payload.get("all_precise")) != all_precise:
        issues.append("all_precise disagrees with re-derived (tier tolerance)")
    if bool(payload.get("all_controlled")) != all_controlled:
        issues.append("all_controlled disagrees with re-derived (margin)")
    if abs(float(payload.get("max_residual", math.inf)) - max(residuals)) > 1e-15:  # type: ignore[arg-type]
        issues.append("max_residual disagrees with re-derived")
    if abs(float(payload.get("min_control_margin", -1.0)) - min(margins)) > 1e-12:  # type: ignore[arg-type]
        issues.append("min_control_margin disagrees with re-derived")
    if bool(payload.get("ok")) != (all_precise and all_controlled):
        issues.append("stored ok disagrees with re-derived verdict")
    return issues


def validate_against_sources(root: Path, payload: dict[str, object]) -> list[str]:
    """Cross-read: confirm every ledger row reproduces its live source value.

    Makes the ledger an audit rather than a self-report -- a row that claims a
    residual or control margin the source artifact does not contain (including a
    stale ledger whose source has since drifted) is caught.
    """
    issues = validate_payload(payload)
    base = Path(root).resolve()
    prows = payload.get("precision_rows") or []
    crows = payload.get("control_rows") or []
    for r in prows if isinstance(prows, list) else []:
        try:
            live = float(_read(base, str(r["source"])).get(str(r["field"]), math.nan))
            if not math.isfinite(live) or abs(live - float(r["residual"])) > _CROSS_READ_TOL:
                issues.append(f"ledger residual for {r.get('name')} does not match source")
        except (KeyError, TypeError, ValueError, FileNotFoundError, OSError) as exc:
            issues.append(f"cannot cross-read precision source {r.get('name')}: {exc}")
    for r in crows if isinstance(crows, list) else []:
        try:
            live = float(_read(base, str(r["source"])).get(str(r["field"]), math.nan))
            if not math.isfinite(live) or abs(live - float(r["margin"])) > _CROSS_READ_TOL:
                issues.append(f"ledger control margin for {r.get('name')} does not match source")
        except (KeyError, TypeError, ValueError, FileNotFoundError, OSError) as exc:
            issues.append(f"cannot cross-read control source {r.get('name')}: {exc}")
    return issues


if __name__ == "__main__":  # pragma: no cover - runnable self-check
    p = build_payload(Path("."))
    print(json.dumps(p, indent=2, sort_keys=True))
    assert p["ok"] and validate_payload(p) == [] and validate_against_sources(Path("."), p) == []
    print("\nprecision_ledger self-check OK")
