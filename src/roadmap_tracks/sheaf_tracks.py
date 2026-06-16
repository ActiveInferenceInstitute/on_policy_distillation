"""Canonical deterministic sheaf-track artifacts.

This module consolidates the former promotion waves into stable public track
ids and artifact paths.  Schema strings may evolve, but live track ids and
output paths stay canonical so the manuscript cannot accumulate parallel
``*_vN`` proof surfaces for the same concept.

The pure ``build_*`` functions and their private helpers live in
:mod:`roadmap_tracks.sheaf_tracks_builders` (split out as pure code motion).
This module is the orchestration + write facade: it re-exports every public
name (and the private helpers other modules reference via the module object)
so existing ``from roadmap_tracks.sheaf_tracks import ...`` call-sites and
``roadmap_tracks.sheaf_tracks.<name>`` attribute accesses keep working.
"""

from __future__ import annotations

from pathlib import Path

# Canonical contract constants re-exported for call-sites that read them off
# this module (e.g. tests asserting identity with sheaf_track_contracts, and
# sheaf_track_validation accessing them via the module object).
from .sheaf_track_contracts import (
    CANONICAL_ARTIFACTS,
    CANONICAL_SCHEMA,
    CANONICAL_TRACKS,
    DEPENDENCY_SCHEMA,
    LEGACY_ARTIFACTS,
    OPTIONAL_CLAIM_EXEMPT_TRACKS,
    REQUIRED_EDGE_TYPES,
    SEMANTIC_SCHEMA,
    SHEAF_TRACK_PRODUCER,
    VERSIONED_TRACK_RE,
)

# Pure builders + private helpers, split across three submodules. Re-exported
# by name so that both ``from roadmap_tracks.sheaf_tracks import build_*`` and
# ``roadmap_tracks.sheaf_tracks._private_helper`` continue to resolve.
from .sheaf_tracks_support import (
    _analysis_scripts,
    _artifact_maps,
    _bound_tracks,
    _canonical_artifact_rows,
    _claim_ids_by_path,
    _claim_ids_by_track,
    _claim_records,
    _config_digest,
    _copied_parity,
    _deterministic_seed,
    _entropy,
    _load_json,
    _load_structured,
    _load_yaml,
    _manifest_sections,
    _parse_yaml_cached,
    _refresh_hydrated_manuscript,
    _registry_tracks,
    _remove_legacy_artifacts,
    _root_output_dir,
    _sha256,
    _source_commit,
    _write_json,
)
from .sheaf_tracks_builders import (
    _artifact_bundles,
    build_adversarial_audit,
    build_artifact_provenance,
    build_blocked_scope_manifest,
    build_counterexample_matrix,
    build_interop_roundtrip_report,
    build_model_checking_witnesses,
    build_replay_matrix,
    build_sensitivity_sweep,
    build_uncertainty_summary,
)
from .sheaf_tracks_reports import (
    _canonical_restrictions,
    _field_value,
    _track_artifact,
    build_evidence_field_index,
    build_release_bundle_manifest,
    build_theorem_traceability_matrix,
    build_track_improvement_scope,
    build_validation_dependency_graph,
)

__all__ = [
    "CANONICAL_ARTIFACTS",
    "CANONICAL_SCHEMA",
    "CANONICAL_TRACKS",
    "DEPENDENCY_SCHEMA",
    "LEGACY_ARTIFACTS",
    "OPTIONAL_CLAIM_EXEMPT_TRACKS",
    "REQUIRED_EDGE_TYPES",
    "SEMANTIC_SCHEMA",
    "SHEAF_TRACK_PRODUCER",
    "VERSIONED_TRACK_RE",
    "build_adversarial_audit",
    "build_artifact_provenance",
    "build_blocked_scope_manifest",
    "build_counterexample_matrix",
    "build_evidence_field_index",
    "build_interop_roundtrip_report",
    "build_model_checking_witnesses",
    "build_release_bundle_manifest",
    "build_replay_matrix",
    "build_sensitivity_sweep",
    "build_theorem_traceability_matrix",
    "build_track_improvement_scope",
    "build_uncertainty_summary",
    "build_validation_dependency_graph",
    "write_sheaf_track_artifacts",
    "validate_sheaf_track_artifacts",
    "load_sheaf_track_payloads",
    "validate_sheaf_track_payloads",
    # Private helpers re-exported for modules that reach them through the
    # ``roadmap_tracks.sheaf_tracks`` module object (e.g. sheaf_track_validation,
    # manuscript.sheaf.semantic). Part of the compatibility surface, not new API.
    "_analysis_scripts",
    "_artifact_bundles",
    "_artifact_maps",
    "_bound_tracks",
    "_canonical_artifact_rows",
    "_canonical_restrictions",
    "_claim_ids_by_path",
    "_claim_ids_by_track",
    "_claim_records",
    "_config_digest",
    "_copied_parity",
    "_deterministic_seed",
    "_entropy",
    "_field_value",
    "_load_json",
    "_load_structured",
    "_load_yaml",
    "_manifest_sections",
    "_parse_yaml_cached",
    "_refresh_hydrated_manuscript",
    "_registry_tracks",
    "_remove_legacy_artifacts",
    "_root_output_dir",
    "_sha256",
    "_source_commit",
    "_track_artifact",
    "_write_json",
]


def write_sheaf_track_artifacts(
    project_root: Path,
    *,
    refresh_dependencies: bool = True,
    refresh_hydration: bool = True,
) -> dict[str, Path]:
    root = project_root.resolve()
    regeneration_errors: list[str] = []
    from roadmap_tracks.scholarship import write_scholarship_source_matrix
    from roadmap_tracks.supplemental import write_supplemental_artifacts

    semantic_cache: dict | None = None

    def _semantic_certificate() -> dict:
        nonlocal semantic_cache
        if semantic_cache is not None:
            return semantic_cache
        from manuscript.sheaf.semantic import _with_proof_obligations, build_semantic_gluing_certificate

        semantic_cache = _with_proof_obligations(root, build_semantic_gluing_certificate(root))
        return semantic_cache

    if refresh_dependencies:
        try:
            from roadmap_tracks import (
                write_formal_interop_artifacts,
                write_integration_audit_artifacts,
                write_toy_sweep_artifacts,
            )

            write_toy_sweep_artifacts(root)
            write_formal_interop_artifacts(root)
            write_integration_audit_artifacts(root)
        except (ImportError, OSError, ValueError, KeyError) as exc:
            # Never swallow generator failures silently: a skipped regeneration
            # here previously left stale artifacts that downstream gates then
            # certified as fresh.
            regeneration_errors.append(f"toy_sweep/formal_interop/integration_audit: {exc}")

    _remove_legacy_artifacts(root)
    paths: dict[str, Path] = {}

    paths["sensitivity"] = _write_json(root / CANONICAL_ARTIFACTS["sensitivity"], build_sensitivity_sweep(root))
    paths["uncertainty"] = _write_json(root / CANONICAL_ARTIFACTS["uncertainty"], build_uncertainty_summary(root))
    paths["counterexample"] = _write_json(
        root / CANONICAL_ARTIFACTS["counterexample"], build_counterexample_matrix(root)
    )
    paths["model_checking"] = _write_json(
        root / CANONICAL_ARTIFACTS["model_checking"],
        build_model_checking_witnesses(root),
    )
    paths["scholarship"] = write_scholarship_source_matrix(root)
    paths["interop"] = _write_json(root / CANONICAL_ARTIFACTS["interop"], build_interop_roundtrip_report(root))
    paths["adversarial"] = _write_json(root / CANONICAL_ARTIFACTS["adversarial_audit"], build_adversarial_audit(root))
    paths["blocked_scope"] = _write_json(
        root / CANONICAL_ARTIFACTS["blocked_scope_manifest"],
        build_blocked_scope_manifest(root),
    )
    paths["evidence_fields"] = _write_json(
        root / CANONICAL_ARTIFACTS["evidence_fields"],
        build_evidence_field_index(root),
    )
    paths["theorem_traceability"] = _write_json(
        root / CANONICAL_ARTIFACTS["theorem_traceability"],
        build_theorem_traceability_matrix(root),
    )
    paths["release_bundle"] = _write_json(
        root / CANONICAL_ARTIFACTS["release_bundle"],
        build_release_bundle_manifest(root),
    )
    paths.update(write_supplemental_artifacts(root))
    paths["artifact_diffoscope"] = root / CANONICAL_ARTIFACTS["artifact_diffoscope"]
    paths["artifact_license"] = root / CANONICAL_ARTIFACTS["artifact_license"]
    paths["release_notes"] = root / CANONICAL_ARTIFACTS["release_notes"]
    paths["proof_extraction"] = root / CANONICAL_ARTIFACTS["proof_extraction"]
    paths["state_space_catalog"] = root / CANONICAL_ARTIFACTS["state_space_catalog"]
    paths["causal_ablation"] = root / CANONICAL_ARTIFACTS["causal_ablation"]
    paths["track_improvement_scope"] = _write_json(
        root / CANONICAL_ARTIFACTS["track_improvement_scope"],
        build_track_improvement_scope(root),
    )
    paths["replay_matrix"] = _write_json(root / CANONICAL_ARTIFACTS["replay_matrix"], build_replay_matrix(root))

    if refresh_hydration:
        _refresh_hydrated_manuscript(root)

    from manuscript.sheaf.status import write_sheaf_status_outputs

    status_paths = write_sheaf_status_outputs(root)
    paths.update(status_paths)
    paths["provenance"] = _write_json(root / CANONICAL_ARTIFACTS["provenance"], build_artifact_provenance(root))
    paths["dependency"] = _write_json(root / CANONICAL_ARTIFACTS["dependency"], build_validation_dependency_graph(root))
    try:
        from manuscript.sheaf.semantic import build_evidence_crosswalk

        paths["crosswalk"] = _write_json(
            root / "output" / "data" / "sheaf_evidence_crosswalk.json", build_evidence_crosswalk(root)
        )
        paths["semantic"] = _write_json(root / CANONICAL_ARTIFACTS["semantic"], _semantic_certificate())
    except (ImportError, OSError, ValueError, KeyError) as exc:
        regeneration_errors.append(f"semantic certificate/crosswalk: {exc}")
    _remove_legacy_artifacts(root)
    if regeneration_errors:
        raise RuntimeError(
            "sheaf track regeneration failed (stale artifacts would otherwise be certified fresh): "
            + "; ".join(regeneration_errors)
        )
    return paths


def validate_sheaf_track_artifacts(project_root: Path, *, validate_saved_certificate: bool = True) -> list[str]:
    """Compatibility facade for canonical sheaf-track validation."""
    from .sheaf_track_validation import validate_sheaf_track_artifacts as _validate

    return _validate(project_root, validate_saved_certificate=validate_saved_certificate)


def load_sheaf_track_payloads(project_root: Path) -> dict[str, dict]:
    """Compatibility facade for loading canonical sheaf-track payloads once."""
    from .sheaf_track_validation import load_sheaf_track_payloads as _load

    return _load(project_root)


def validate_sheaf_track_payloads(
    project_root: Path,
    payloads: dict[str, dict],
    *,
    validate_saved_certificate: bool = True,
) -> list[str]:
    """Compatibility facade for validating preloaded canonical sheaf-track payloads."""
    from .sheaf_track_validation import validate_sheaf_track_payloads as _validate

    return _validate(project_root, payloads, validate_saved_certificate=validate_saved_certificate)
