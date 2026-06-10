"""Shared artifact bootstrap for gate validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from artifact_contracts import REQUIRED_OUTPUT_CHECK_KEYS
from orchestration.artifact_pipeline import hydrate_manuscript_fixed_point, refresh_gate_artifacts

_BOOTSTRAPPED_ROOTS: set[Path] = set()
_BOOTSTRAPPED_FINGERPRINTS: dict[Path, tuple[tuple[str, int, int], ...]] = {}

_REQUIRED_GATE_ARTIFACTS: tuple[str, ...] = REQUIRED_OUTPUT_CHECK_KEYS
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


def _bootstrap_current(project_root: Path) -> bool:
    root = project_root.resolve()
    return root in _BOOTSTRAPPED_ROOTS and _BOOTSTRAPPED_FINGERPRINTS.get(root) == _gate_artifact_fingerprint(root)


def _gate_artifacts_ready(project_root: Path, *, include_manuscript: bool = False) -> bool:
    """Return whether present artifacts satisfy the aggregate output gates."""
    root = project_root.resolve()
    if not (root / "manuscript" / "config.yaml").is_file():
        return True

    from gates.validation import validate_manuscript, validate_outputs

    try:
        checks = validate_outputs(root, only=set(_READY_CHECK_KEYS))
        if not all(checks.get(key) is True for key in _READY_CHECK_KEYS):
            return False
        if include_manuscript:
            manuscript_checks = validate_manuscript(root, only=set(_READY_MANUSCRIPT_CHECK_KEYS))
            return all(manuscript_checks.get(key) is True for key in _READY_MANUSCRIPT_CHECK_KEYS)
    except Exception:
        return False
    return True


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
        refresh_gate_artifacts(project_root)
    except RuntimeError as exc:
        _skip_or_fail(exc)
    _mark_bootstrapped(root)
