"""Shared artifact bootstrap for gate validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from artifact_contracts import REQUIRED_OUTPUT_CHECK_KEYS
from orchestration.artifact_lock import artifact_lease
from orchestration.artifact_pipeline import refresh_gate_artifacts

_BOOTSTRAPPED_ROOTS: set[Path] = set()
_BOOTSTRAPPED_FINGERPRINTS: dict[Path, tuple[tuple[str, int, int], ...]] = {}

# The fingerprint surface must cover every artifact the readiness checks consume,
# not only REQUIRED_OUTPUT_CHECK_KEYS: a mutation to a ready-key artifact outside
# the fingerprinted set is invisible to _bootstrap_current, which lets a stale
# tree be re-blessed from cache (the AI-TEST-ISOLATION-1 order-sensitivity race).
_READY_ONLY_ARTIFACTS: tuple[str, ...] = (
    "output/reports/stale_artifact_report.json",
    "output/reports/claim_evidence_audit.json",
)
_REQUIRED_GATE_ARTIFACTS: tuple[str, ...] = REQUIRED_OUTPUT_CHECK_KEYS + tuple(
    rel for rel in _READY_ONLY_ARTIFACTS if rel not in set(REQUIRED_OUTPUT_CHECK_KEYS)
)
_READY_CHECK_KEYS: tuple[str, ...] = (
    "experiment_plan_metrics",
    "integration_audit_track_schemas",
    "canonical_sheaf_track_schemas",
    "stale_artifact_report_schema",
    "manuscript_staleness_report_schema",
    "claim_evidence_audit_schema",
    "artifact_diffoscope_schema",
)
_READY_MANUSCRIPT_CHECK_KEYS: tuple[str, ...] = (
    "claim_ledger_valid",
    "semantic_sheaf_gluing",
    "integration_audit_artifacts",
    "canonical_sheaf_tracks",
    "resolved_manuscript_hydrated",
)


def refresh_generated_gate_artifacts(project_root: Path) -> None:
    """Refresh generated manuscript/semantic artifacts after mutation tests.

    Negative-control tests restore the single file they mutated byte-for-byte in
    their own ``finally`` *before* calling this. When that restore already leaves
    the gate artifacts valid (the common case), skip the expensive regeneration and
    keep the session bootstrap cache warm so the next test reuses it instead of
    triggering a full ~80s rebuild. Only regenerate when the artifacts are actually
    stale (e.g. a test that mutated a generated ``output/`` artifact in place).
    """
    root = project_root.resolve()
    with artifact_lease(root):
        if _gate_artifacts_present(root) and _gate_artifacts_ready(root, include_manuscript=True):
            _mark_bootstrapped(root)
            return
        try:
            refresh_gate_artifacts(root, require_analysis_outputs=False)
        except RuntimeError as exc:
            _skip_or_fail(exc)
        _mark_bootstrapped(root)


def _gate_artifacts_present(project_root: Path) -> bool:
    """Return whether the gate artifact surface is available on disk.

    This is intentionally a cheap presence check. The actual gate tests call the
    validators under test; using those same validators here can recursively
    trigger full fixed-point refreshes inside per-test timeouts.
    """
    return all((project_root / rel).is_file() for rel in _REQUIRED_GATE_ARTIFACTS)


def _gate_artifact_fingerprint(project_root: Path) -> tuple[tuple[str, int, int], ...]:
    """Return a cheap change token for the generated gate artifact surface."""
    rows: list[tuple[str, int, int]] = []
    for rel in _REQUIRED_GATE_ARTIFACTS:
        path = project_root / rel
        try:
            stat = path.stat()
        except FileNotFoundError:
            rows.append((rel, -1, -1))
        else:
            rows.append((rel, stat.st_mtime_ns, stat.st_size))
    return tuple(rows)


def _mark_bootstrapped(project_root: Path) -> None:
    root = project_root.resolve()
    _BOOTSTRAPPED_ROOTS.add(root)
    _BOOTSTRAPPED_FINGERPRINTS[root] = _gate_artifact_fingerprint(root)


def evict_bootstrap(project_root: Path) -> None:
    """Symmetrically drop BOTH cache structures for a root.

    The isolate fixture must never clear only ``_BOOTSTRAPPED_ROOTS``: a dangling
    fingerprint entry lets the next ``_mark_bootstrapped`` re-couple the pair
    against a tree captured mid-mutation, silently re-blessing stale artifacts.
    """
    root = project_root.resolve()
    _BOOTSTRAPPED_ROOTS.discard(root)
    _BOOTSTRAPPED_FINGERPRINTS.pop(root, None)


def _bootstrap_current(project_root: Path) -> bool:
    root = project_root.resolve()
    return root in _BOOTSTRAPPED_ROOTS and _BOOTSTRAPPED_FINGERPRINTS.get(root) == _gate_artifact_fingerprint(root)


def _gate_artifacts_ready(project_root: Path, *, include_manuscript: bool = False) -> bool:
    """Require structural currency without inventing observation/release success."""
    import json
    import yaml

    from gates.claim_ledger import typed_claim_evidence_issues
    from gates.validation import validate_manuscript, validate_outputs
    from manuscript.sheaf.semantic import validate_semantic_gluing
    from roadmap_tracks import validate_integration_audit_artifacts, validate_sheaf_track_artifacts
    from roadmap_tracks.integration_audit_artifacts import build_release_notes_evidence
    from roadmap_tracks.negative_controls import validate_observation_payload
    from roadmap_tracks.sheaf_tracks_reports import track_improvement_scope_consistent
    from roadmap_tracks.supplemental import release_attestation_consistent_and_current

    root = project_root.resolve()
    if not (root / "manuscript" / "config.yaml").is_file():
        return True
    try:
        # Mixed experiment_plan_metrics is re-evaluated with structural leaf
        # predicates; no entire science, provenance, or render gate is skipped.
        checks = validate_outputs(root, only=set(_READY_CHECK_KEYS), require_observations=False)
        if not all(checks.get(key) is True for key in _READY_CHECK_KEYS):
            return False
        if not include_manuscript:
            return True
        if validate_sheaf_track_artifacts(root, require_observations=False):
            return False
        if validate_semantic_gluing(root, require_observations=False):
            return False
        if validate_integration_audit_artifacts(root, require_release_evidence=False):
            return False
        plain_keys = set(_READY_MANUSCRIPT_CHECK_KEYS) - {
            "claim_ledger_valid",
            "semantic_sheaf_gluing",
            "canonical_sheaf_tracks",
            "integration_audit_artifacts",
        }
        plain_keys.update({"coverage_matrix_valid", "claim_bindings_satisfied"})
        manuscript_checks = validate_manuscript(root, only=plain_keys)
        if not all(manuscript_checks.get(key) is True for key in plain_keys):
            return False

        # The existing typed validator still checks EVERY claim and operand.
        # Only a failed literal green requirement for an authenticated honest
        # red field is structurally admissible. Other fields on those same
        # artifacts, extra predicates, missing data, or malformed claims fail.
        counter_path = "output/reports/counterexample_matrix.json"
        adversarial_path = "output/reports/adversarial_audit.json"
        semantic_path = "output/data/sheaf_gluing_certificate.json"
        notes_path = "output/reports/release_notes_evidence.json"
        attestation_path = "output/reports/release_attestation.json"
        promotion_path = "output/data/track_improvement_scope.json"
        documents = {
            relative: json.loads((root / relative).read_bytes())
            for relative in (
                counter_path,
                adversarial_path,
                semantic_path,
                notes_path,
                attestation_path,
                promotion_path,
            )
        }
        authenticated = {
            (counter_path, "all_expected_failures_observed"): not validate_observation_payload(
                root, documents[counter_path], require_observations=False
            ),
            (adversarial_path, "all_expected_failures_observed"): not validate_observation_payload(
                root, documents[adversarial_path], adversarial=True, require_observations=False
            ),
            (semantic_path, "ok"): True,  # full structural semantic validation above
            (notes_path, "all_notes_source_backed"): documents[notes_path] == build_release_notes_evidence(root),
            (attestation_path, "all_attested"): release_attestation_consistent_and_current(
                root, documents[attestation_path]
            ),
            (promotion_path, "all_required_controls_observed"): track_improvement_scope_consistent(
                root, documents[promotion_path]
            ),
        }
        ledger = yaml.safe_load((root / "data/claim_ledger.yaml").read_text(encoding="utf-8"))
        allowed: set[str] = set()
        denied: set[str] = set()
        for claim in ledger.get("claims") or []:
            relative = str(claim.get("path") or "")
            evidence = claim.get("evidence")
            field = evidence.get("field") if isinstance(evidence, dict) else None
            message = f"{claim.get('id') or '<unknown>'}: evidence predicate failed for {relative}"
            if (
                isinstance(evidence, dict)
                and set(evidence) == {"field", "equals"}
                and isinstance(field, str)
                and evidence["equals"] is True
                and authenticated.get((relative, field)) is True
                and documents[relative].get(field) is False
            ):
                allowed.add(message)
            else:
                denied.add(message)
        return all(issue in allowed - denied for issue in typed_claim_evidence_issues(root))
    except Exception:
        return False


def _skip_or_fail(exc: RuntimeError) -> None:
    """Skip only for the genuine optional-dependency case; integrity failures FAIL.

    Converting every RuntimeError (including fixed-point non-convergence — an
    integrity failure) into pytest.skip green-washed the entire gate surface.
    """
    message = str(exc)
    if "pymdp" in message.lower():
        pytest.skip(message)
    pytest.fail(f"gate artifact refresh failed (not a missing-dependency skip): {message}")


def ensure_gate_artifacts(project_root: Path, *, verify: bool = False) -> None:
    """Rebuild analysis, simulation, sheaf, and figure outputs for gate checks."""
    root = project_root.resolve()
    with artifact_lease(root):
        if _gate_artifacts_present(root):
            if _bootstrap_current(root) and not verify:
                return
            if _gate_artifacts_ready(root, include_manuscript=True):
                _mark_bootstrapped(root)
                return
            try:
                refresh_gate_artifacts(root, require_analysis_outputs=False)
            except RuntimeError as exc:
                _skip_or_fail(exc)
            _mark_bootstrapped(root)
            return

        try:
            refresh_gate_artifacts(root)
        except RuntimeError as exc:
            _skip_or_fail(exc)
        _mark_bootstrapped(root)
