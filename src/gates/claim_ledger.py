"""Claim-ledger validation against sheaf coverage artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_structured(path: Path) -> Any:
    if path.suffix in {".json", ".jsonl"}:
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix in {".yaml", ".yml"}:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return path.read_text(encoding="utf-8")


def _lookup_field(data: Any, field: str) -> Any:
    value = data
    for part in field.split("."):
        if isinstance(value, dict):
            value = value[part]
        elif isinstance(value, list):
            value = value[int(part)]
        else:
            raise KeyError(field)
    return value


def _numbers_equal(left: Any, right: Any, tolerance: float) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(left) is bool(right)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) <= tolerance
    return bool(left == right)


NON_SUBSTANTIVE_PREDICATES = {"exists", "file_exists", "truthy", "non_empty"}
SUBSTANTIVE_EVIDENCE_KEYS = {
    "equals",
    "approx",
    "min",
    "max",
    "contains",
    "set_equals",
    "len_equals",
    "len_min",
    "all",
    "any",
    "equals_difference",
    "leq_field",
    "matches_artifact_field",
}


def _predicate_holds(value: Any, predicate: str, *, root: Path | None = None) -> bool:
    if predicate == "exists":
        return value is not None
    if predicate == "file_exists":
        _ = root
        return bool(value)
    if predicate == "truthy":
        return bool(value)
    if predicate == "non_empty":
        return bool(value)
    if predicate == "zero":
        try:
            return float(value) == 0.0
        except (TypeError, ValueError):
            return False
    if predicate == "positive":
        try:
            return float(value) > 0.0
        except (TypeError, ValueError):
            return False
    if predicate == "all_true":
        if isinstance(value, dict):
            return all(bool(v) for v in value.values())
        if isinstance(value, list):
            return all(bool(v) for v in value)
    if predicate == "is_true":
        return value is True
    return False


def _set_equals(left: Any, right: Any) -> bool:
    if not isinstance(left, list) or not isinstance(right, list):
        return False
    return {str(item) for item in left} == {str(item) for item in right}


def _evidence_spec_holds(value: Any, evidence: dict[str, Any], *, root: Path | None = None) -> bool:
    document = value
    if "field" in evidence:
        try:
            value = _lookup_field(value, str(evidence["field"]))
        except (KeyError, TypeError, ValueError, IndexError):
            return False
    tolerance = float(evidence.get("tolerance", 0.0))
    # --- re-derivation forms: check relations, not just stored scalars/flags ---
    if "equals_difference" in evidence:
        # value must equal lookup(document, A) - lookup(document, B): a stored
        # gap cannot silently disagree with the operands it claims to summarise.
        try:
            field_a, field_b = evidence["equals_difference"]
            derived = float(_lookup_field(document, str(field_a))) - float(_lookup_field(document, str(field_b)))
        except (KeyError, TypeError, ValueError, IndexError):
            return False
        if not _numbers_equal(value, derived, tolerance or 1e-9):
            return False
    if "leq_field" in evidence:
        # value must be <= the sibling field: orderings are re-derived, never
        # trusted from a producer-set flag.
        try:
            bound = float(_lookup_field(document, str(evidence["leq_field"])))
        except (KeyError, TypeError, ValueError, IndexError):
            return False
        try:
            if float(value) > bound + (tolerance or 1e-9):
                return False
        except (TypeError, ValueError):
            return False
    if "matches_artifact_field" in evidence:
        # Cross-artifact equality: this claim's value must be identical to a
        # field in ANOTHER generated artifact (e.g. statistics inputs == the
        # classroom series they claim to derive from).
        spec = evidence["matches_artifact_field"]
        if root is None or not isinstance(spec, dict):
            return False
        other_path = root / str(spec.get("path", ""))
        try:
            other_value = _lookup_field(_load_structured(other_path), str(spec.get("field", "")))
        except (OSError, ValueError, KeyError, TypeError, IndexError):
            return False
        if isinstance(value, list) or isinstance(other_value, list):
            if value != other_value:
                return False
        elif not _numbers_equal(value, other_value, tolerance):
            return False
    if "equals" in evidence and not _numbers_equal(value, evidence["equals"], tolerance):
        return False
    if "approx" in evidence and not _numbers_equal(value, evidence["approx"], tolerance):
        return False
    if "min" in evidence and float(value) < float(evidence["min"]):
        return False
    if "max" in evidence and float(value) > float(evidence["max"]):
        return False
    if "contains" in evidence and evidence["contains"] not in value:
        return False
    if "set_equals" in evidence and not _set_equals(value, evidence["set_equals"]):
        return False
    if "len_equals" in evidence and len(value) != int(evidence["len_equals"]):
        return False
    if "len_min" in evidence and len(value) < int(evidence["len_min"]):
        return False
    if "all" in evidence:
        nested = evidence["all"]
        if not isinstance(value, list) or not isinstance(nested, dict):
            return False
        if not all(_evidence_spec_holds(item, nested, root=root) for item in value):
            return False
    if "any" in evidence:
        nested = evidence["any"]
        if not isinstance(value, list) or not isinstance(nested, dict):
            return False
        if not any(_evidence_spec_holds(item, nested, root=root) for item in value):
            return False
    predicate = evidence.get("predicate")
    if predicate and not _predicate_holds(value, str(predicate), root=root):
        return False
    return True


def typed_claim_evidence_issues(
    project_root: Path,
    *,
    ledger_path: Path | None = None,
    allow_missing_certificate: bool = False,
    skip_paths: set[str] | None = None,
) -> list[str]:
    """Return explicit typed-evidence failures for ``claim_ledger.yaml``."""
    root = project_root.resolve()
    path = ledger_path or root / "data" / "claim_ledger.yaml"
    if not path.exists():
        return [f"claim ledger missing: {path}"]
    import yaml

    ledger = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    issues: list[str] = []
    skipped = skip_paths or set()
    for claim in ledger.get("claims") or []:
        claim_id = str(claim.get("id") or "<unknown>")
        issue_count_before_claim = len(issues)
        rel = claim.get("path")
        if not rel:
            issues.append(f"{claim_id}: missing path")
            continue
        if allow_missing_certificate and str(rel) == "output/data/sheaf_gluing_certificate.json":
            continue
        if str(rel) in skipped:
            continue
        artifact = root / str(rel)
        if not artifact.exists():
            issues.append(f"{claim_id}: missing artifact {rel}")
            continue
        evidence = claim.get("evidence")
        if evidence:
            if evidence.get("predicate") == "file_exists":
                value: Any = artifact.exists()
                spec = {k: v for k, v in evidence.items() if k != "field"}
            else:
                try:
                    value = _load_structured(artifact)
                    spec = evidence
                except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
                    issues.append(f"{claim_id}: cannot load evidence from {rel}: {exc}")
                    continue
            if not _evidence_spec_holds(value, spec, root=root):
                issues.append(f"{claim_id}: evidence predicate failed for {rel}")
        if "tracks" in claim and not claim.get("tracks"):
            issues.append(f"{claim_id}: tracks must not be empty")
        if len(issues) != issue_count_before_claim:
            continue
        evidence_dict = evidence if isinstance(evidence, dict) else {}
        predicate = str(evidence_dict.get("predicate", ""))
        has_substantive_key = any(key in evidence_dict for key in SUBSTANTIVE_EVIDENCE_KEYS)
        has_substantive_predicate = bool(predicate) and predicate not in NON_SUBSTANTIVE_PREDICATES
        waiver = claim.get("waiver")
        has_waiver = isinstance(waiver, str) and bool(waiver.strip())
        if evidence_dict and not (has_substantive_key or has_substantive_predicate or has_waiver):
            issues.append(f"{claim_id}: path-only evidence without waiver")
    return issues


def validate_typed_claim_evidence(
    project_root: Path,
    *,
    ledger_path: Path | None = None,
    allow_missing_certificate: bool = False,
    skip_paths: set[str] | None = None,
) -> bool:
    """Validate optional typed evidence declarations in ``claim_ledger.yaml``."""
    return not typed_claim_evidence_issues(
        project_root,
        ledger_path=ledger_path,
        allow_missing_certificate=allow_missing_certificate,
        skip_paths=skip_paths,
    )


def validate_claim_ledger(project_root: Path) -> bool:
    root = project_root.resolve()
    ledger_path = root / "data" / "claim_ledger.yaml"
    if not ledger_path.exists():
        return False
    import yaml

    from manuscript.sheaf import (
        gray_cell_count_from_json,
        load_coverage_json,
        load_manifest,
        load_track_registry,
        validate_coverage_json_data,
    )

    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8")) or {}
    manifest_path = root / "manuscript" / "sheaf" / "manifest.yaml"
    manifest = load_manifest(manifest_path, project_root=root) if manifest_path.exists() else None
    registry = (
        load_track_registry(root / manifest.registry_path)
        if manifest and (root / manifest.registry_path).exists()
        else None
    )
    json_path = root / "output" / "data" / "sheaf_coverage_matrix.json"
    coverage_data = load_coverage_json(json_path) if json_path.exists() else None

    for claim in ledger.get("claims") or []:
        rel = claim.get("path")
        if rel and not (root / str(rel)).exists():
            return False
        claim_id = claim.get("id")
        if claim_id == "coverage_no_gray":
            if coverage_data is None or manifest is None or registry is None:
                return False
            if gray_cell_count_from_json(coverage_data) > 0:
                return False
            json_issues = validate_coverage_json_data(coverage_data, manifest, registry)
            if any(i.level == "error" for i in json_issues):
                return False
    return validate_typed_claim_evidence(root, ledger_path=ledger_path)


def verify_claim_bindings(project_root: Path) -> list[str]:
    """Semantic claim bindings -- tie manuscript values/adjectives to their oracles."""
    import json

    import yaml as _yaml

    root = project_root.resolve()
    violations: list[str] = []

    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    summary_planner: str | None = None
    if summary_path.is_file():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            violations.append(f"si_tmaze_summary.json unreadable: {exc}")
            summary = {}
        steps = summary.get("steps")
        summary_planner = summary.get("planner")
        if not isinstance(steps, int) or steps <= 0:
            violations.append(f"si_tmaze_summary.steps must be a positive measured count, got {steps!r}")
        if summary_planner != "sophisticated_inference":
            violations.append(f"si_tmaze_summary.planner invalid: {summary_planner!r}")

    cfg_path = root / "pymdp.yaml"
    if cfg_path.is_file() and summary_planner is not None:
        try:
            cfg = _yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        except (OSError, _yaml.YAMLError) as exc:
            cfg = {}
            violations.append(f"pymdp.yaml unreadable: {exc}")
        cfg_planner = cfg.get("planner")
        if cfg_planner is None:
            violations.append("pymdp.yaml is missing the mandatory 'planner' key (planner-match bind disarmed)")
        elif cfg_planner != summary_planner:
            violations.append(
                f"pymdp planner mismatch: config planner={cfg_planner!r} "
                f"but recorded rollout planner={summary_planner!r}"
            )

    manifest_path = root / "manuscript" / "sheaf" / "manifest.yaml"
    if manifest_path.is_file():
        from manuscript.sheaf.manifest import load_manifest

        manifest = load_manifest(manifest_path, project_root=root)
        invariants_output = next(s.output_name for s in manifest.sections if s.id == "results_invariants")
    else:
        invariants_output = "20_supplement_validation_statistics.md"
    invariants_section = root / "manuscript" / invariants_output
    if invariants_section.is_file() and "merged" in invariants_section.read_text(encoding="utf-8").lower():
        from manuscript.invariant_counts import invariants_are_merged

        if not invariants_are_merged(root):
            violations.append(
                "section 13 claims a merged analytical+simulation report, but no "
                "simulation invariants are present under output/reports/"
            )

    return violations
