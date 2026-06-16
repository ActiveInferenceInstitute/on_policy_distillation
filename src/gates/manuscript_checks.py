"""Manuscript and sheaf structure validation."""

from __future__ import annotations

import re
from pathlib import Path

from gates.claim_ledger import validate_claim_ledger, verify_claim_bindings

_SHEAF_TRACK_MARKER_RE = re.compile(r"^<!--\s*sheaf-track:([a-z_]+)\s*-->\s*$", re.MULTILINE)
_BIB_ENTRY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
_CITATION_KEY_RE = re.compile(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_:\-]+)")
_CROSSREF_PREFIXES = ("sec:", "fig:", "eq:", "tbl:", "lst:", "lem:", "thm:")
_EXCLUDED_CITATION_FILES = {
    "99_references.md",
    "SYNTAX.md",
    "README.md",
    "AGENTS.md",
}
SUPPORTED_SELECTED_MANUSCRIPT_CHECKS = {
    "sheaf_manifest",
    "sheaf_registry",
    "figure_registry_yaml",
    "generated_figure_registry",
    "sheaf_coverage_page",
    "sheaf_coverage_json",
    "sheaf_coverage_heatmap",
    "sheaf_valid",
    "coverage_matrix_valid",
    "full_sheaf_appendix_tracks",
    "imrad_groups_present",
    "composed_sections",
    "methods_sheaf_layers",
    "promoted_sheaf_tracks_bound",
    "blocked_empirical_adapter",
    "claim_ledger_valid",
    "claim_bindings_satisfied",
    "manuscript_tokens_registered",
    "citation_keys_resolved",
    "no_duplicate_sheaf_track_markers",
    "resolved_manuscript_hydrated",
    "gnn_concordance",
    "semantic_sheaf_gluing",
    "integration_audit_artifacts",
    "canonical_sheaf_tracks",
}


def _duplicate_track_markers(manuscript_dir: Path) -> list[str]:
    """Composed sections in which the same sheaf-track marker appears more than once.

    The composer emits exactly one ``<!-- sheaf-track:X -->`` per (section, track) binding,
    so a track id appearing twice in one composed flat file means a fragment self-emitted a
    marker the composer also emits (a doubled stutter). Matches standalone marker lines only,
    so an inline prose mention of the marker syntax is not counted.
    """
    duplicates: list[str] = []
    for md_file in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        counts: dict[str, int] = {}
        for tid in _SHEAF_TRACK_MARKER_RE.findall(md_file.read_text(encoding="utf-8")):
            counts[tid] = counts.get(tid, 0) + 1
        duplicates.extend(f"{md_file.name}:{tid}={count}" for tid, count in sorted(counts.items()) if count > 1)
    return duplicates


def _bib_keys(root: Path) -> set[str]:
    path = root / "manuscript" / "references.bib"
    if not path.is_file():
        return set()
    return {match.group(1).strip() for match in _BIB_ENTRY_RE.finditer(path.read_text(encoding="utf-8"))}


def _citation_source_paths(root: Path) -> list[Path]:
    section_paths = sorted((root / "manuscript" / "sections").glob("**/*.md"))
    composed_paths = sorted(
        path
        for path in (root / "manuscript").glob("*.md")
        if path.name not in _EXCLUDED_CITATION_FILES
    )
    return [path for path in section_paths + composed_paths if path.is_file()]


def unresolved_citation_keys(project_root: Path) -> list[str]:
    """Return manuscript citation keys that have no bibliography entry.

    Cross-reference labels such as ``@fig:...`` and ``@sec:...`` are not
    bibliography citations, so they are excluded before checking the BibTeX key
    set. The check covers fragment sources and composed manuscript files.
    """
    root = project_root.resolve()
    bib = _bib_keys(root)
    cited: set[str] = set()
    for path in _citation_source_paths(root):
        text = path.read_text(encoding="utf-8")
        for key in _CITATION_KEY_RE.findall(text):
            if key.startswith(_CROSSREF_PREFIXES):
                continue
            cited.add(key)
    return sorted(cited - bib)


def citations_resolved(project_root: Path) -> bool:
    return not unresolved_citation_keys(project_root)


def validate_manuscript_selected_strict(project_root: Path, only: set[str]) -> dict[str, bool]:
    """Validate selected manuscript keys without silently dropping unknown keys."""
    selected = set(only)
    unsupported = selected - SUPPORTED_SELECTED_MANUSCRIPT_CHECKS
    if unsupported:
        raise KeyError(f"unsupported lazy manuscript check keys: {sorted(unsupported)}")
    checks = validate_manuscript(project_root, only=selected)
    missing = selected - set(checks)
    if missing:
        raise AssertionError(f"lazy manuscript checks did not return requested keys: {sorted(missing)}")
    return checks


def validate_manuscript(project_root: Path, *, only: set[str] | None = None) -> dict[str, bool]:
    root = project_root.resolve()
    requested = set(only) if only is not None else None
    if requested is not None:
        unsupported = requested - SUPPORTED_SELECTED_MANUSCRIPT_CHECKS
        if unsupported:
            raise KeyError(f"unsupported manuscript check keys: {sorted(unsupported)}")

    def _wants(*keys: str) -> bool:
        return requested is None or any(key in requested for key in keys)

    checks: dict[str, bool] = {}
    manuscript_dir = root / "manuscript"
    manifest_path = root / "manuscript" / "sheaf" / "manifest.yaml"
    json_path = root / "output" / "data" / "sheaf_coverage_matrix.json"
    heatmap_path = root / "output" / "figures" / "sheaf_coverage_heatmap.png"
    figure_registry_yaml = root / "figures.yaml"
    generated_figure_registry = root / "output" / "figures" / "figure_registry.json"

    if _wants("sheaf_manifest"):
        checks["sheaf_manifest"] = manifest_path.exists()
    if _wants("sheaf_registry"):
        checks["sheaf_registry"] = (root / "manuscript" / "sheaf" / "tracks.yaml").exists()
    if _wants("figure_registry_yaml"):
        checks["figure_registry_yaml"] = figure_registry_yaml.exists()
    if _wants("generated_figure_registry"):
        checks["generated_figure_registry"] = generated_figure_registry.exists()
    if _wants("sheaf_coverage_page"):
        checks["sheaf_coverage_page"] = (root / "manuscript" / "00_00_sheaf_coverage.md").exists()
    if _wants("sheaf_coverage_json"):
        checks["sheaf_coverage_json"] = json_path.exists()
    if _wants("sheaf_coverage_heatmap"):
        checks["sheaf_coverage_heatmap"] = heatmap_path.exists()

    manifest_keys = {
        "sheaf_valid",
        "coverage_matrix_valid",
        "full_sheaf_appendix_tracks",
        "imrad_groups_present",
        "composed_sections",
        "methods_sheaf_layers",
        "promoted_sheaf_tracks_bound",
        "blocked_empirical_adapter",
    }
    if _wants(*manifest_keys):
        from manuscript.sheaf import (
            load_coverage_json,
            load_sheaf_coverage_context,
            validate_coverage_json_data,
            validate_manifest,
        )

        ctx = load_sheaf_coverage_context(root)
        manifest = ctx.manifest
        registry = ctx.registry

        if _wants("sheaf_valid"):
            sheaf_issues = validate_manifest(manifest, root, registry=registry, strict_coverage=True)
            checks["sheaf_valid"] = not any(i.level == "error" for i in sheaf_issues)

        if _wants("coverage_matrix_valid"):
            coverage_matrix_valid = False
            if json_path.exists():
                data = load_coverage_json(json_path)
                json_issues = validate_coverage_json_data(data, manifest, registry)
                coverage_matrix_valid = not any(i.level == "error" for i in json_issues)
            checks["coverage_matrix_valid"] = coverage_matrix_valid

        def _section_path(section_id: str) -> Path:
            section = next(s for s in manifest.sections if s.id == section_id)
            return root / "manuscript" / section.output_name

        if _wants("full_sheaf_appendix_tracks"):
            full_sheaf_path = _section_path("appendix_full_sheaf")
            full_sheaf_appendix_tracks = False
            if full_sheaf_path.exists():
                text = full_sheaf_path.read_text(encoding="utf-8")
                appendix = next((s for s in manifest.sections if s.id == "appendix_full_sheaf"), None)
                if appendix is not None:
                    full_sheaf_appendix_tracks = all(f"sheaf-track:{tid}" in text for tid in appendix.tracks)
            checks["full_sheaf_appendix_tracks"] = full_sheaf_appendix_tracks

        if _wants("imrad_groups_present"):
            checks["imrad_groups_present"] = sum(1 for s in manifest.sections if s.kind == "group") >= 4

        if _wants("composed_sections"):
            composed = list(manuscript_dir.glob("[0-9][0-9]_*.md"))
            composed_leaf_count = sum(1 for s in manifest.sections if s.should_compose())
            checks["composed_sections"] = len(composed) >= composed_leaf_count

        if _wants("methods_sheaf_layers"):
            methods_sheaf_path = _section_path("methods_sheaf")
            methods_sheaf_layers = False
            if methods_sheaf_path.exists():
                sheaf_text = methods_sheaf_path.read_text(encoding="utf-8")
                methods_sheaf_layers = (
                    "sheaf_layers_overview.png" in sheaf_text
                    and "<!-- sheaf-layers:registry -->" in sheaf_text
                    and "<!-- sheaf-layers:binding-matrix -->" in sheaf_text
                    and "<!-- sheaf-layers:legend -->" in sheaf_text
                    and "<!-- sheaf-layers:section-status -->" in sheaf_text
                    and "<!-- sheaf-layers:track-status -->" in sheaf_text
                    and "<!-- sheaf-layers:render-log -->" in sheaf_text
                )
            checks["methods_sheaf_layers"] = methods_sheaf_layers

        if _wants("promoted_sheaf_tracks_bound", "blocked_empirical_adapter"):
            promoted_tracks = {
                "sensitivity",
                "uncertainty",
                "benchmark",
                "model_checking",
                "interop",
                "adversarial_audit",
                "assumption_index",
                "animation_delta",
                "manuscript_staleness",
                "provenance",
                "replay_matrix",
                "counterexample",
                "evidence_fields",
                "release_bundle",
                "theorem_traceability",
                "gate_ergonomics",
                "artifact_diffoscope",
                "proof_extraction",
                "state_space_catalog",
                "causal_ablation",
                "artifact_license",
                "release_notes",
            }
            bound_tracks = {track_id for section in manifest.sections for track_id in section.tracks}
            if _wants("promoted_sheaf_tracks_bound"):
                checks["promoted_sheaf_tracks_bound"] = promoted_tracks <= set(registry.tracks) and promoted_tracks <= bound_tracks
            if _wants("blocked_empirical_adapter"):
                checks["blocked_empirical_adapter"] = (
                    "empirical_adapter" not in set(registry.tracks) and "empirical_adapter" not in bound_tracks
                )

    if _wants("claim_ledger_valid"):
        checks["claim_ledger_valid"] = validate_claim_ledger(root)
    if _wants("claim_bindings_satisfied"):
        checks["claim_bindings_satisfied"] = not verify_claim_bindings(root)

    if _wants("manuscript_tokens_registered"):
        from manuscript.hydrate import EXCLUDED_DOC_FILENAMES, collect_malformed_token_names, validate_manuscript_tokens
        from manuscript.variables import generate_variables

        variable_keys = set(generate_variables(root, require_analysis_outputs=False))
        unknown_tokens = validate_manuscript_tokens(manuscript_dir, variable_keys)
        malformed_tokens: list[str] = []
        for md_file in sorted(manuscript_dir.glob("*.md")):
            if md_file.name in EXCLUDED_DOC_FILENAMES:
                continue
            malformed_tokens.extend(collect_malformed_token_names(md_file.read_text(encoding="utf-8")))
        checks["manuscript_tokens_registered"] = not unknown_tokens and not malformed_tokens

    if _wants("citation_keys_resolved"):
        checks["citation_keys_resolved"] = citations_resolved(root)
    if _wants("no_duplicate_sheaf_track_markers"):
        checks["no_duplicate_sheaf_track_markers"] = not _duplicate_track_markers(manuscript_dir)

    if _wants("resolved_manuscript_hydrated"):
        from manuscript.hydrate import EXCLUDED_DOC_FILENAMES

        resolved_dir = root / "output" / "manuscript"
        checks["resolved_manuscript_hydrated"] = (
            resolved_dir.is_dir()
            and any(resolved_dir.glob("*.md"))
            and all(
                "{{" not in md.read_text(encoding="utf-8")
                for md in resolved_dir.glob("*.md")
                if md.name not in EXCLUDED_DOC_FILENAMES
            )
        )

    if _wants("gnn_concordance"):
        from ontology.bindings import validate_all_gnn_ontology

        checks["gnn_concordance"] = not validate_all_gnn_ontology(root)
    if _wants("semantic_sheaf_gluing"):
        from manuscript.sheaf.semantic import validate_semantic_gluing

        checks["semantic_sheaf_gluing"] = not validate_semantic_gluing(root)
    if _wants("integration_audit_artifacts"):
        from roadmap_tracks import validate_integration_audit_artifacts

        checks["integration_audit_artifacts"] = not validate_integration_audit_artifacts(root)
    if _wants("canonical_sheaf_tracks"):
        from roadmap_tracks import validate_sheaf_track_artifacts

        checks["canonical_sheaf_tracks"] = not validate_sheaf_track_artifacts(root)

    return checks
