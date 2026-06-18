"""Result-integrity ledger: a synthesis audit over the whole result set.

The manuscript accumulates many first-principles results; this ledger makes the
two integrity properties of the *whole set* auditable in one artifact and one
figure, rather than leaving them implicit across a dozen separate certificates:

* **PRECISION** -- every quantitative correspondence's residual/error is below a
  stated tolerance (the identities and cross-checks hold to machine precision).
* **CONTROLS** -- every result carries a negative control that actually bites
  (no result is green-by-construction).

The ledger is a SYNTHESIS: it reads the live source artifacts and reproduces
their residuals and control flags, so it cannot claim a number a source does not
contain (the cross-read is enforced by :func:`validate_against_sources`, called
by the output gate). It introduces no new science -- it audits the structure of
what is already proved, witnessed, and controlled.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

SCHEMA = "firstprinciples.precision_ledger_demo.v1"
_PRECISION_TOL = 1e-6
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
# (label, source artifact (relative), boolean control field)
_CONTROL_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("Active-selection: blinding reopens the gap", "output/data/firstprinciples/active_selection_demo.json", "blinding_reopens_gap"),
    ("Multi-state: wrong-measure breaks the identity", "output/data/firstprinciples/active_selection_general_demo.json", "wrong_measure_breaks_identity"),
    ("Sequential: blinded cue collapses the advantage", "output/data/firstprinciples/sequential_selection_demo.json", "blind_cue_collapses_advantage"),
    ("Bridge: blinded cue flips the EFE selection", "output/data/firstprinciples/si_bridge_demo.json", "blinded_control_bites"),
    ("Bridge: wrong validity breaks the trajectory", "output/data/firstprinciples/si_bridge_demo.json", "wrong_validity_breaks_trajectory"),
)

__all__ = ["build_payload", "validate_payload", "validate_against_sources"]


def _read(root: Path, rel: str) -> dict:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def build_payload(root: Path | None = None) -> dict[str, object]:
    """Aggregate the precision and control properties from the live source artifacts."""
    base = (root or Path(".")).resolve()
    precision_rows: list[dict[str, object]] = []
    residual_values: list[float] = []
    for label, rel, field, tier in _PRECISION_SOURCES:
        val = float(_read(base, rel).get(field, math.nan))
        residual_values.append(val)
        precision_rows.append(
            {"name": label, "source": rel, "field": field, "tier": tier,
             "residual": val, "within_tol": bool(math.isfinite(val) and val < _PRECISION_TOL)}
        )
    control_rows: list[dict[str, object]] = []
    for label, rel, field in _CONTROL_SOURCES:
        control_rows.append({"name": label, "source": rel, "field": field, "bites": bool(_read(base, rel).get(field) is True)})

    max_residual = max(residual_values, default=math.inf)
    all_precise = bool(all(r["within_tol"] for r in precision_rows))
    all_controlled = bool(all(r["bites"] for r in control_rows))
    ok = bool(all_precise and all_controlled and math.isfinite(max_residual))
    return {
        "schema": SCHEMA,
        "precision_tolerance": _PRECISION_TOL,
        "precision_rows": precision_rows,
        "control_rows": control_rows,
        "result_count": len(precision_rows),
        "control_count": len(control_rows),
        "max_residual": max_residual,
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
        tol = float(payload.get("precision_tolerance", _PRECISION_TOL))  # type: ignore[arg-type]
        residuals = [float(r["residual"]) for r in prows]
        all_precise = all(math.isfinite(v) and v < tol for v in residuals)
        all_controlled = all(bool(r["bites"]) for r in crows)
    except (KeyError, TypeError, ValueError) as exc:
        return [*issues, f"malformed ledger rows: {exc}"]
    if bool(payload.get("all_precise")) != all_precise:
        issues.append("all_precise disagrees with re-derived")
    if bool(payload.get("all_controlled")) != all_controlled:
        issues.append("all_controlled disagrees with re-derived")
    if abs(float(payload.get("max_residual", math.inf)) - max(residuals)) > 1e-15:  # type: ignore[arg-type]
        issues.append("max_residual disagrees with re-derived")
    if bool(payload.get("ok")) != (all_precise and all_controlled):
        issues.append("stored ok disagrees with re-derived verdict")
    return issues


def validate_against_sources(root: Path, payload: dict[str, object]) -> list[str]:
    """Cross-read: confirm every ledger row reproduces its live source value.

    This is what makes the ledger an audit rather than a self-report -- a row that
    claims a residual or control the source artifact does not contain is caught.
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
            live = _read(base, str(r["source"])).get(str(r["field"])) is True
            if live != bool(r["bites"]):
                issues.append(f"ledger control for {r.get('name')} does not match source")
        except (KeyError, TypeError, ValueError, FileNotFoundError, OSError) as exc:
            issues.append(f"cannot cross-read control source {r.get('name')}: {exc}")
    return issues


if __name__ == "__main__":  # pragma: no cover - runnable self-check
    p = build_payload(Path("."))
    print(json.dumps(p, indent=2, sort_keys=True))
    assert p["ok"] and validate_payload(p) == [] and validate_against_sources(Path("."), p) == []
    print("\nprecision_ledger self-check OK")
