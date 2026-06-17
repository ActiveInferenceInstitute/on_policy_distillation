"""Artifact, figure, license, and semantic-snapshot integration-audit builders.

Split out of :mod:`roadmap_tracks.integration_audit` alongside
:mod:`roadmap_tracks.integration_audit_builders` to keep each module under the
line-count gate. The public ``integration_audit`` module re-exports every name
defined here, so existing imports continue to resolve unchanged.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from .integration_audit_builders import (
    LATE_HYDRATION_PRODUCER,
    SELF_PRODUCER,
    SHEAF_TRACK_PRODUCER,
    _load_json,
    _sha256,
    build_claim_evidence_audit,
    build_integration_dependency_graph,
    build_manuscript_staleness_report,
    build_manuscript_token_provenance,
    build_stale_artifact_report,
)

# The fixed-point check set and its membership test live in supplemental.py —
# a duplicated copy here drifted from the canonical set once already.
from roadmap_tracks.supplemental import (  # noqa: E402
    _validation_failures_within_fixed_point,
)


def build_artifact_diffoscope(project_root: Path) -> dict[str, Any]:
    """Build the artifact_diffoscope.v1 payload comparing saved provenance sha256 digests against live file hashes, skipping cycle-excluded producers."""
    root = project_root.resolve()
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    rows = []
    cycle_producers = {SELF_PRODUCER, LATE_HYDRATION_PRODUCER, SHEAF_TRACK_PRODUCER}
    for row in provenance.get("rows") or []:
        rel = str(row.get("artifact") or "")
        if row.get("cycle_excluded") or row.get("producer") in cycle_producers:
            continue
        path = root / rel
        live_hash = _sha256(path) if path.is_file() else ""
        saved_hash = str(row.get("sha256") or "")
        rows.append(
            {
                "artifact": rel,
                "jsonpath": "$",
                "saved_sha256": saved_hash,
                "live_sha256": live_hash,
                "equal": bool(saved_hash) and saved_hash == live_hash,
                "source": "output/data/artifact_provenance.json",
            }
        )
    return {
        "schema": "template_active_inference.artifact_diffoscope.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_equal": bool(rows) and all(row["equal"] for row in rows),
    }


def build_artifact_license_audit(project_root: Path) -> dict[str, Any]:
    """Build the artifact_license_audit.v1 payload labeling each provenance artifact with the project license and a license_safe flag."""
    root = project_root.resolve()
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    project_license = "MIT"
    import yaml

    config = yaml.safe_load((root / "manuscript" / "config.yaml").read_text(encoding="utf-8")) or {}
    project_license = str((config.get("metadata") or {}).get("license") or project_license)
    rows = []
    for row in provenance.get("rows") or []:
        rel = str(row.get("artifact") or "")
        generated = rel.startswith("output/")
        rows.append(
            {
                "artifact": rel,
                "license": project_license,
                "source_kind": "generated_local" if generated else "project_source",
                "license_safe": generated or rel.startswith(("manuscript/", "src/", "data/", "lean/", "gnn/")),
                "producer": row.get("producer", ""),
            }
        )
    return {
        "schema": "template_active_inference.artifact_license_audit.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_license_safe": bool(rows) and all(row["license_safe"] and row["license"] for row in rows),
    }


def build_release_notes_evidence(project_root: Path) -> dict[str, Any]:
    """Build the release_notes_evidence.v1 payload: three source-backed release notes (validation report, bundle sources, semantic certificate), deferring rows whose source artifact does not exist yet."""
    root = project_root.resolve()
    release_bundle = _load_json(root / "output" / "reports" / "release_bundle_manifest.json")
    semantic = _load_json(root / "output" / "data" / "sheaf_gluing_certificate.json")
    validation_path = root / "output" / "reports" / "validation_report.json"
    semantic_path = root / "output" / "data" / "sheaf_gluing_certificate.json"
    rows = [
        {
            "note_id": "validation_report_all_passed",
            "source": "output/reports/validation_report.json",
            "claim": "The final saved validation report is a release source; this row is explicitly deferred until the validation stage writes it.",
            # Bound to content with the attestation self-row carve-out: a red
            # report fails this note UNLESS the only failures are the bounded
            # release fixed-point checks that cannot be green until the tail is
            # rebuilt after validation.
            "passed": (
                _validation_failures_within_fixed_point(_load_json(validation_path))
                if validation_path.exists()
                else False
            ),
            "deferred_until_validation": not validation_path.exists(),
        },
        {
            "note_id": "release_bundle_sources_present",
            "source": "output/reports/release_bundle_manifest.json",
            "claim": "Required release bundle sources are present or render-deferred.",
            "passed": release_bundle.get("all_required_sources_present") is True,
            "deferred_until_validation": False,
        },
        {
            "note_id": "semantic_certificate_ok",
            "source": "output/data/sheaf_gluing_certificate.json",
            "claim": "The semantic certificate is the source for the release note; semantic correctness is enforced by the semantic gate.",
            "passed": (not semantic_path.exists()) or bool(semantic.get("schema")),
            "deferred_until_validation": not semantic_path.exists(),
        },
    ]
    return {
        "schema": "template_active_inference.release_notes_evidence.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_notes_source_backed": all(row["source"] and row["passed"] for row in rows),
    }


def build_figure_source_map(project_root: Path) -> dict[str, Any]:
    """Build the figure_source_map.v1 payload: per-registry-figure sources, source fields, validation gates, caption/alt tokens, and image dimensions."""
    root = project_root.resolve()
    from visualizations.figure_registry import load_figure_registry

    token_re = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)")

    def _image_dimensions(rel: str) -> dict[str, int | None]:
        path = root / rel
        if not path.is_file():
            return {"width_px": None, "height_px": None}
        try:
            from PIL import Image

            with Image.open(path) as img:
                width, height = img.size
        except Exception:
            return {"width_px": None, "height_px": None}
        return {"width_px": int(width), "height_px": int(height)}

    sources = {
        "ising_mi_curve": ["output/data/parameter_sweep.csv"],
        "free_energy_curve": [
            "output/data/parameter_sweep.csv",
            "src/analytical/decomposition.py",
            "src/analytical/free_energy.py",
        ],
        "si_belief_entropy_curve": ["output/data/si_tmaze_trace.json"],
        "si_obs_action_trace": ["output/data/si_tmaze_summary.json"],
        "si_tmaze_actions": ["output/data/si_tmaze_summary.json"],
        "si_tmaze_model_matrices": ["output/data/si_tmaze_model_matrices.json"],
        "distillation_divergence_geometry": ["output/data/firstprinciples/divergence_demo.json"],
        "exposure_bias_recovery": ["output/data/firstprinciples/exposure_bias_demo.json"],
        "classroom_distillation_signal": ["output/data/firstprinciples/classroom.json"],
        "sequential_shift_recovery": ["output/data/firstprinciples/sequential_shift.json"],
        "sequential_shift_sensitivity": ["output/data/firstprinciples/sequential_shift_sensitivity.json"],
        "energy_decomposition": ["output/data/firstprinciples/energy_demo.json"],
        "parallel_convergence": ["output/data/firstprinciples/parallel_demo.json"],
        "diversity_tradeoff": ["output/data/firstprinciples/diversity_demo.json"],
        "privilege_dose_response": ["output/data/firstprinciples/privilege_sweep.json"],
        "correspondence_map": ["output/data/firstprinciples/correspondence_map.json"],
        "policy_posterior_grid": ["output/data/pymdp_policy_posterior_grid.json"],
        "opd_taxonomy_landscape": ["output/data/firstprinciples/opd_taxonomy.json"],
        "active_selection_landscape": ["output/data/firstprinciples/active_selection_demo.json"],
        "sheaf_layers_overview": ["output/data/sheaf_coverage_matrix.json"],
        "sheaf_coverage_heatmap": ["output/data/sheaf_coverage_matrix.json"],
        "invariant_dashboard": ["output/reports/invariants.json"],
        "tmaze_schematic": [
            "pymdp.yaml",
            "output/data/si_tmaze_summary.json",
            "output/data/si_tmaze_model_matrices.json",
        ],
        "multi_track_architecture": [
            "tracks.yaml",
            "manuscript/sheaf/tracks.yaml",
            "output/data/manuscript_variables.json",
        ],
        "lean_boundary_status": ["lean/OnPolicyDistillation"],
        "gnn_ontology_concordance": ["gnn", "manuscript/sections/imrad"],
        "semantic_gluing_graph": [
            "output/data/validation_dependency_graph.json",
            "output/data/sheaf_gluing_certificate.json",
            "output/data/evidence_field_index.json",
        ],
        "theorem_traceability_graph": [
            "output/data/theorem_traceability_matrix.json",
            "output/data/proof_dependency_graph.json",
        ],
        "causal_ablation_heatmap": [
            "output/data/causal_ablation_matrix.json",
            "output/reports/ablation_sensitivity_report.json",
        ],
        "scholarship_source_map": ["output/data/scholarship_source_matrix.json", "manuscript/references.bib"],
        "graphical_abstract": [
            "manuscript/sheaf/tracks.yaml",
            "output/data/firstprinciples/classroom.json",
            "output/data/firstprinciples/energy_demo.json",
            "output/data/firstprinciples/sequential_shift.json",
            "output/data/validation_dependency_graph.json",
        ],
        "opd_reader_map": [
            "output/data/firstprinciples/correspondence_map.json",
            "output/data/firstprinciples/exposure_bias_demo.json",
            "output/data/firstprinciples/sequential_shift.json",
            "output/data/validation_dependency_graph.json",
        ],
        "opd_situational_awareness": [
            "output/data/firstprinciples/correspondence_map.json",
            "output/data/firstprinciples/sequential_shift.json",
            "output/data/firstprinciples/classroom.json",
            "output/data/firstprinciples/energy_demo.json",
            "output/data/firstprinciples/opd_taxonomy.json",
            "output/data/validation_dependency_graph.json",
            "output/data/manuscript_variables.json",
        ],
    }
    source_fields = {
        "ising_mi_curve": [
            "parameter_sweep.csv:lambda",
            "parameter_sweep.csv:closed_form_mi",
            "parameter_sweep.csv:empirical_mi",
        ],
        "free_energy_curve": [
            "decomposition.free_energy_against_entangled_prior",
            "free_energy.kl_divergence",
            "free_energy.total_correlation",
            "parameter_sweep.csv:lambda",
            "analytical.hyperparameters.lambda_grid",
        ],
        "si_belief_entropy_curve": ["$.steps[*].belief_entropy"],
        "si_obs_action_trace": ["$.observations_by_modality", "$.actions", "$.action_names"],
        "si_tmaze_actions": ["$.actions", "$.action_probabilities", "$.planning_horizon", "$.expected_known_warnings"],
        "si_tmaze_model_matrices": [
            "$.A_shapes",
            "$.B_shapes",
            "$.dependencies",
            "$.normalization_checks",
            "$.environment",
        ],
        "distillation_divergence_geometry": [
            "$.teacher",
            "$.student",
            "$.reverse_kl",
            "$.forward_kl",
            "$.jensen_shannon",
        ],
        "exposure_bias_recovery": ["$.curves.off_policy", "$.curves.on_policy", "$.gap.terminal_gap"],
        "classroom_distillation_signal": [
            "$.per_step[*].teacher",
            "$.per_step[*].student",
            "$.per_step[*].reverse_kl",
            "$.mean_reverse_kl",
        ],
        "sequential_shift_recovery": [
            "$.train_visitation",
            "$.student_test_visitation_before",
            "$.student_test_visitation_after",
            "$.train_loss",
            "$.test_loss_before",
            "$.test_loss_after",
            "$.gap_closed",
        ],
        "sequential_shift_sensitivity": [
            "$.rows[*].correction_fraction",
            "$.rows[*].train_loss",
            "$.rows[*].test_loss",
            "$.rows[*].shift_mass",
            "$.rows[*].student_drift_visitation",
            "$.monotone_test_loss_decrease",
            "$.monotone_shift_mass_decrease",
        ],
        "energy_decomposition": [
            "$.vfe_at_prior.complexity",
            "$.vfe_at_prior.accuracy",
            "$.efe.risk",
            "$.efe.ambiguity",
            "$.log_evidence",
        ],
        "parallel_convergence": [
            "$.loss_trajectory",
            "$.active_inference_teacher_posterior",
            "$.ml_distilled_student",
            "$.max_abs_difference",
        ],
        "diversity_tradeoff": [
            "$.temperatures",
            "$.pass_at_k",
            "$.greedy_pass_at_1",
        ],
        "privilege_dose_response": [
            "$.levels",
            "$.baseline_gap",
            "$.gap_rank_correlation",
        ],
        "correspondence_map": [
            "$.rows",
            "$.row_count",
            "$.ok",
        ],
        "policy_posterior_grid": [
            "$.rows",
            "$.available_row_count",
            "$.all_available_posteriors_normalized",
        ],
        "opd_taxonomy_landscape": [
            "$.methods",
            "$.method_count",
            "$.on_policy_count",
            "$.privileged_info_count",
        ],
        "active_selection_landscape": [
            "$.policies",
            "$.validity_sweep",
            "$.prior_entropy_nats",
            "$.efe_selected_policy",
        ],
        "sheaf_layers_overview": ["$.tracks", "$.layers", "$.bound_cell_count", "$.validated_cell_count"],
        "sheaf_coverage_heatmap": ["$.tracks", "$.sections"],
        "invariant_dashboard": ["$.invariants", "$.simulation", "$.all_pass"],
        "tmaze_schematic": [
            "pymdp.yaml:planning_horizon",
            "pymdp.yaml:agent.si_policy_len",
            "output/data/si_tmaze_summary.json:$.planning_horizon",
            "output/data/si_tmaze_summary.json:$.policy_len",
            "output/data/si_tmaze_model_matrices.json:$.A_shapes",
            "output/data/si_tmaze_model_matrices.json:$.B_shapes",
            "output/data/si_tmaze_model_matrices.json:$.environment",
        ],
        "multi_track_architecture": [
            "tracks.yaml:tracks",
            "manuscript/sheaf/tracks.yaml:tracks",
            "$.free_energy_mean_field_gap_max",
            "$.si_tmaze_policy_entropy_drop_after_cue",
            "$.proof_extraction_theorem_count",
        ],
        "lean_boundary_status": ["lean/OnPolicyDistillation/*.lean"],
        "gnn_ontology_concordance": ["gnn/*.gnn.md", "manuscript/sections/imrad/*/ontology.yaml"],
        "semantic_gluing_graph": [
            "$.artifacts",
            "$.edges",
            "$.restrictions",
        ],
        "theorem_traceability_graph": ["$.rows[*].theorem", "$.edges", "$.all_edges_resolved"],
        "causal_ablation_heatmap": ["$.rows[*].topology", "$.rows[*].perturbation", "$.rows[*].effect"],
        "scholarship_source_map": ["$.rows[*].citation_key", "$.rows[*].method_role", "$.rows[*].artifact"],
        "graphical_abstract": [
            "manuscript/sheaf/tracks.yaml:tracks",
            "output/data/firstprinciples/classroom.json:schema",
            "output/data/firstprinciples/energy_demo.json:schema",
            "output/data/firstprinciples/sequential_shift.json:schema",
            "output/data/validation_dependency_graph.json:producer_consumer_spine",
        ],
        "opd_reader_map": [
            "$.rows",
            "$.curves.off_policy",
            "$.student_test_visitation_after",
            "output/data/validation_dependency_graph.json:$.edges",
        ],
        "opd_situational_awareness": [
            "output/data/firstprinciples/correspondence_map.json:$.rows",
            "output/data/firstprinciples/sequential_shift.json:$.schema",
            "output/data/firstprinciples/classroom.json:$.schema",
            "output/data/firstprinciples/energy_demo.json:$.schema",
            "output/data/firstprinciples/opd_taxonomy.json:$.methods",
            "output/data/validation_dependency_graph.json:$.edges",
            "output/data/manuscript_variables.json:$.sheaf_track_count",
        ],
    }
    validation_gates = {
        "ising_mi_curve": ["validate_outputs.output/data/parameter_sweep.csv", "test_figures.nonblank_png"],
        "free_energy_curve": ["test_manuscript_variables.free_energy_argmin_lambda", "test_figures.nonblank_png"],
        "si_belief_entropy_curve": ["validate_outputs.si_summary_schema", "test_figures.nonblank_png"],
        "si_obs_action_trace": ["validate_outputs.si_trace_present", "test_figures.nonblank_png"],
        "si_tmaze_actions": ["validate_outputs.si_summary_schema", "test_figures.nonblank_png"],
        "si_tmaze_model_matrices": ["validate_outputs.si_tmaze_model_matrices_schema", "test_figures.nonblank_png"],
        "distillation_divergence_geometry": [
            "validate_outputs.firstprinciples_divergence_schema",
            "test_figures.nonblank_png",
        ],
        "exposure_bias_recovery": [
            "validate_outputs.firstprinciples_exposure_bias_schema",
            "test_figures.nonblank_png",
        ],
        "classroom_distillation_signal": [
            "validate_outputs.firstprinciples_classroom_schema",
            "test_figures.nonblank_png",
        ],
        "sequential_shift_recovery": [
            "validate_outputs.firstprinciples_sequential_shift_schema",
            "test_figures.nonblank_png",
        ],
        "sequential_shift_sensitivity": [
            "validate_outputs.firstprinciples_sequential_shift_sensitivity_schema",
            "test_figures.nonblank_png",
        ],
        "energy_decomposition": [
            "test_firstprinciples_energy.decompositions_agree",
            "test_figures.nonblank_png",
        ],
        "parallel_convergence": [
            "test_firstprinciples_parallel.test_parallel_payload_frameworks_agree",
            "test_figures.nonblank_png",
        ],
        "diversity_tradeoff": [
            "test_firstprinciples_dynamics.test_diversity_tradeoff_payload",
            "test_figures.nonblank_png",
        ],
        "privilege_dose_response": [
            "test_firstprinciples_stats.test_privilege_sweep_payload_contract",
            "test_figures.nonblank_png",
        ],
        "correspondence_map": [
            "test_firstprinciples_artifacts.test_correspondence_and_taxonomy_payloads",
            "test_figures.nonblank_png",
        ],
        "policy_posterior_grid": [
            "validate_outputs.pymdp_policy_posterior_grid_schema",
            "validate_outputs.aggregate_rederivation",
            "test_figures.nonblank_png",
        ],
        "opd_taxonomy_landscape": [
            "validate_outputs.firstprinciples_taxonomy_schema",
            "test_figures.nonblank_png",
        ],
        "active_selection_landscape": [
            "validate_outputs.firstprinciples_active_selection_schema",
            "test_figures.nonblank_png",
        ],
        "sheaf_layers_overview": ["validate_outputs.canonical_sheaf_track_schemas", "test_figures.nonblank_png"],
        "sheaf_coverage_heatmap": [
            "validate_outputs.output/data/sheaf_coverage_matrix.json",
            "test_figures.nonblank_png",
        ],
        "invariant_dashboard": ["validate_outputs.invariants_all_pass", "test_figures.nonblank_png"],
        "tmaze_schematic": [
            "validate_outputs.si_summary_schema",
            "validate_outputs.si_tmaze_model_matrices_schema",
            "test_figures.tmaze_schematic_uses_configured_horizon",
            "test_figures.nonblank_png",
        ],
        "multi_track_architecture": ["validate_outputs.track_improvement_scope_schema", "test_figures.nonblank_png"],
        "lean_boundary_status": ["validate_outputs.lean_theorem_inventory_schema", "test_figures.nonblank_png"],
        "gnn_ontology_concordance": ["validate_outputs.gnn_lint_schema", "test_figures.nonblank_png"],
        "semantic_gluing_graph": ["validate_outputs.validation_dependency_graph_schema", "test_figures.nonblank_png"],
        "theorem_traceability_graph": [
            "validate_outputs.theorem_traceability_matrix_schema",
            "test_figures.nonblank_png",
        ],
        "causal_ablation_heatmap": ["validate_outputs.causal_ablation_matrix_schema", "test_figures.nonblank_png"],
        "scholarship_source_map": ["validate_outputs.scholarship_source_matrix_schema", "test_figures.nonblank_png"],
        "graphical_abstract": [
            "validate_outputs.figure_source_map_schema",
            "test_figures.graphical_abstract_is_cover_quality_near_square_png",
            "test_figures.graphical_abstract_represents_artifact_validation_spine",
        ],
        "opd_reader_map": [
            "validate_outputs.figure_source_map_schema",
            "test_figures.opd_reader_map_is_intro_bound_and_source_backed",
            "test_figures.nonblank_png",
        ],
        "opd_situational_awareness": [
            "validate_outputs.figure_source_map_schema",
            "test_figures.opd_situational_awareness_is_intro_bound_and_source_backed",
            "test_figures.nonblank_png",
        ],
    }
    registry = load_figure_registry(root)
    rows = []
    for figure_id, spec in sorted(registry.items()):
        row_sources = sources.get(figure_id, [])
        source_exists = {rel: (root / rel).exists() for rel in row_sources}
        row_fields = source_fields.get(figure_id, [])
        row_gates = validation_gates.get(figure_id, [])
        output_rel = f"output/figures/{spec.filename}"
        caption_tokens = sorted(set(token_re.findall(spec.caption)))
        alt_tokens = sorted(set(token_re.findall(spec.alt)))
        dimensions = _image_dimensions(output_rel)
        caption_claims = _figure_caption_claim_payloads(spec)
        text = f"{spec.caption} {spec.alt}"
        caption_claims_source_bound = _caption_claims_source_bound(caption_claims, row_sources, row_fields)
        caption_claim_fields_resolved = _caption_claim_fields_resolved(caption_claims, row_sources, root)
        caption_claim_terms_present = _caption_claim_terms_present(text, caption_claims)
        caption_claim_scope_ok = _caption_claim_scope_ok(figure_id, caption_claims)
        caption_claim_display_transform_ok = _caption_claim_display_transform_ok(text, caption_claims)
        caption_claims_ok = bool(
            caption_claims
            and caption_claims_source_bound
            and caption_claim_fields_resolved
            and caption_claim_terms_present
            and caption_claim_scope_ok
            and caption_claim_display_transform_ok
        )
        metadata_complete = bool(spec.caption.strip()) and bool(spec.alt.strip()) and spec.width > 0
        rows.append(
            {
                "figure_id": figure_id,
                "label": f"fig:{figure_id}",
                "output": output_rel,
                "generator": f"visualizations.figures::{figure_id}",
                "caption": spec.caption,
                "alt": spec.alt,
                "caption_claims": caption_claims,
                "caption_claim_count": len(caption_claims),
                "caption_claims_source_bound": caption_claims_source_bound,
                "caption_claim_fields_resolved": caption_claim_fields_resolved,
                "caption_claim_terms_present": caption_claim_terms_present,
                "caption_claim_scope_ok": caption_claim_scope_ok,
                "caption_claim_display_transform_ok": caption_claim_display_transform_ok,
                "caption_claims_ok": caption_claims_ok,
                "caption_token_count": len(caption_tokens),
                "alt_token_count": len(alt_tokens),
                "variable_tokens": sorted(set(caption_tokens + alt_tokens)),
                "width": spec.width,
                "image_width_px": dimensions["width_px"],
                "image_height_px": dimensions["height_px"],
                "metadata_complete": metadata_complete
                and dimensions["width_px"] is not None
                and dimensions["height_px"] is not None,
                "sources": row_sources,
                "source_fields": row_fields,
                "source_field_count": len(row_fields),
                "source_path_status": source_exists,
                "source_paths_exist": bool(row_sources) and all(source_exists.values()),
                "validation_gates": row_gates,
                "validation_gate_count": len(row_gates),
                "mapped": bool(row_sources)
                and bool(row_fields)
                and bool(row_gates)
                and caption_claims_ok
                and bool(row_sources)
                and all(source_exists.values()),
            }
        )
    return {
        "schema": "template_active_inference.figure_source_map.v1",
        "rows": rows,
        "figure_count": len(rows),
        "registry_figure_ids": sorted(registry),
        "all_figures_mapped": all(row["mapped"] for row in rows),
        "all_figure_metadata_complete": all(row["metadata_complete"] for row in rows),
        "all_caption_claims_ok": bool(rows) and all(row["caption_claims_ok"] for row in rows),
    }


_FIGURE_IMAGE_SUFFIXES = {".png", ".gif"}
_DECLARED_NONREGISTRY_IMAGE_PATHS = {"output/figures/si_belief_trajectory.gif"}


def _actual_figure_image_paths(root: Path) -> set[str]:
    figures_dir = root / "output" / "figures"
    if not figures_dir.is_dir():
        return set()
    return {
        path.relative_to(root).as_posix()
        for path in figures_dir.iterdir()
        if path.is_file() and path.suffix.lower() in _FIGURE_IMAGE_SUFFIXES
    }


def _expected_figure_image_paths(root: Path) -> set[str]:
    from visualizations.figure_registry import load_figure_registry

    registry_paths = {f"output/figures/{spec.filename}" for spec in load_figure_registry(root).values()}
    return registry_paths | _DECLARED_NONREGISTRY_IMAGE_PATHS


def build_figure_hash_manifest(project_root: Path) -> dict[str, Any]:
    """Build the figure_hash_manifest.v1 payload for declared figure/animation images."""
    root = project_root.resolve()
    expected_paths = _expected_figure_image_paths(root)
    actual_paths = _actual_figure_image_paths(root)
    unexpected = sorted(actual_paths - expected_paths)
    rows = []
    for rel in sorted(expected_paths):
        path = root / rel
        exists = path.is_file()
        rows.append(
            {
                "path": rel,
                "exists": exists,
                "sha256": _sha256(path) if exists else "",
                "size_bytes": path.stat().st_size if exists else 0,
                "fresh": exists,
            }
        )
    all_expected_present = bool(rows) and all(row["exists"] and row["sha256"] for row in rows)
    return {
        "schema": "template_active_inference.figure_hash_manifest.v1",
        "rows": rows,
        "figure_count": len(rows),
        "declared_nonregistry_image_paths": sorted(_DECLARED_NONREGISTRY_IMAGE_PATHS),
        "unexpected_image_paths": unexpected,
        "unexpected_image_count": len(unexpected),
        "all_expected_images_present": all_expected_present,
        "no_unexpected_image_artifacts": not unexpected,
        "all_hashes_present": all_expected_present and not unexpected,
    }


_FIGURE_SCOPE_REQUIRED = {
    "distillation_divergence_geometry",
    "exposure_bias_recovery",
    "classroom_distillation_signal",
    "sequential_shift_recovery",
    "sequential_shift_sensitivity",
    "energy_decomposition",
    "parallel_convergence",
    "diversity_tradeoff",
    "privilege_dose_response",
    "correspondence_map",
    "opd_taxonomy_landscape",
    "active_selection_landscape",
    "causal_ablation_heatmap",
    "scholarship_source_map",
    "graphical_abstract",
    "opd_reader_map",
    "opd_situational_awareness",
}

_FIGURE_SCOPE_TERMS = (
    "deterministic",
    "finite",
    "toy",
    "closed-form",
    "no sampling",
    "not an empirical",
    "not local evidence",
    "not evidence",
    "not a benchmark",
    "not a performance comparison",
    "not a rhetorical analogy",
    "not asserting",
    "no uncertainty intervals",
    "scope guardrail",
    "print-condensed",
)

_FIGURE_FORBIDDEN_OVERCLAIMS = (
    "opd = active inference",
    "opd is active inference",
    "on-policy distillation is active inference",
    "production-scale causal effects",
    "empirical opd benchmark",
    "production llm optimization",
    "production-scale proof",
    "universal kl law",
    "universal llm law",
    "biological mechanism",
    "field-wide theorem",
)

_NEGATED_OVERCLAIMS = (
    "not an empirical opd benchmark",
    "not local evidence about production llm optimization",
    "not evidence about production llm optimization",
    "not a production-scale proof",
    "not a universal kl law",
    "not a universal llm law",
    "no biological mechanism",
    "not a field-wide theorem",
)


def _caption_overclaim_free(text: str) -> bool:
    lower = " ".join(text.lower().split())
    for phrase in _FIGURE_FORBIDDEN_OVERCLAIMS:
        if phrase in lower and not any(negated in lower for negated in _NEGATED_OVERCLAIMS):
            return False
    return True


def _figure_claim_wording_ok(figure_id: str, text: str) -> bool:
    lower = " ".join(text.lower().split())
    obsolete_cover_phrases = (
        "opd = active inference",
        "opd is active inference",
        "on-policy distillation is active inference",
    )
    if any(phrase in lower for phrase in obsolete_cover_phrases):
        return False
    if figure_id != "graphical_abstract":
        return True
    required_cover_terms = ("finite", "reading", "correspondence")
    return all(term in lower for term in required_cover_terms) and "universal identity" in lower


_COVER_FORBIDDEN_QUANT_PHRASES = (
    "nats",
    "cue observed",
    "teacher cue",
    "policy entropy drop",
    "mean reverse kl",
    "test loss",
    "train loss",
    "gap nats",
    "rmse",
    "gpu-hours",
    "aime",
)

_COVER_FORBIDDEN_COUNT_BADGES = (
    "tracks",
    "claim rows",
    "lean proofs",
    "source-bound figures",
)


def _cover_quantitative_free(figure_id: str, text: str) -> bool:
    """Reject metric-dashboard language only on the graphical abstract."""
    if figure_id != "graphical_abstract":
        return True
    lower = " ".join(text.lower().split())
    if any(phrase in lower for phrase in _COVER_FORBIDDEN_QUANT_PHRASES):
        return False
    if re.search(r"\b\d+\.\d+\b", lower):
        return False
    for badge in _COVER_FORBIDDEN_COUNT_BADGES:
        if re.search(rf"\b\d+\s+{re.escape(badge)}\b", lower):
            return False
    return True


_ALLOWED_CAPTION_CLAIM_TYPES = {"local_deterministic", "external_context", "schematic"}
_EXTERNAL_CONTEXT_FIGURES = {"opd_taxonomy_landscape", "scholarship_source_map"}
_SCHEMATIC_CLAIM_FIGURES = {"graphical_abstract", "opd_reader_map", "opd_situational_awareness"}
_ALLOWED_DISPLAY_TRANSFORMS = {
    "full",
    "schematic",
    "matrix_overview",
    "aggregate",
    "compacted",
    "compacted_subset",
    "compacted_aggregate",
    "compacted_label_key",
}
_COMPRESSED_DISPLAY_TRANSFORMS = _ALLOWED_DISPLAY_TRANSFORMS - {"full"}
_COMPRESSED_TEXT_TERMS = (
    "print-condensed",
    "compacted",
    "aggregated",
    "aggregate",
    "subset",
    "omitted",
    "right-side label key",
    "+n counts",
    "collapsed",
)


# `{{token}}` spans render to substituted *values* (usually numbers) after
# hydration, so the token name never appears in the published caption. Strip those
# spans before term-matching so a `caption_term` must occur in the authored prose,
# not merely inside a token name (e.g. the term "sweep_max_residual" matching
# `{{sweep_max_residual:.1e}}`). This is the verifier the contract claims: terms are
# validated against the hydrated caption, not the raw template.
_CAPTION_TOKEN_SPAN = re.compile(r"\{\{[^{}]*\}\}")

# Anti-overclaim: a compressed/aggregated figure must not assert it shows the
# complete row set. Match a completeness quantifier and a display verb adjacent to
# "row(s)" in either order ("all rows are displayed" / "displays every row"), plus
# negated-omission completeness ("no rows are omitted"). A denylist is inherently
# incomplete, so a compressed transform must ALSO positively disclose its compaction
# (see _REQUIRES_DISCLOSURE below) — the two together close the enumerable gap.
# A display verb anywhere in the caption, plus a non-negated completeness phrase
# (below), is what marks a compressed figure as overclaiming it shows every row.
# Decoupling the two (rather than a windowed adjacency) catches cross-sentence and
# far-split phrasings while a verb-less "each row maps to a family" stays legal.
_DISPLAY_VERB = re.compile(
    r"\b(shows?|displays?|draws?|renders?|plots?|visualizes?|graphs?|includes?|contains?"
    r"|displayed|drawn|rendered|plotted|visualized|graphed|shown|appears?|visible)\b"
)
# The row unit is the figure's per-record vocabulary. "rows" is the canonical word,
# but the same overclaim is honest-sounding with synonyms ("all entries are shown",
# "no record is omitted", "each line of the ledger appears") — the claim-ledger figure
# literally renders "claims". Match the whole family so a synonym can't evade the gate.
_ROW_UNIT = r"(?:rows?|entr(?:y|ies)|records?|lines?|claims?|items?)"
# Negated-completeness overclaim: "no rows are omitted".
_NO_ROWS_OMITTED_PATTERNS = (
    re.compile(rf"\bno\b.{{0,30}}\b{_ROW_UNIT}\b.{{0,30}}\b(omitted|dropped|hidden|excluded|left\s+out)\b"),
    re.compile(rf"\b(omitted|dropped|hidden|excluded)\b.{{0,20}}\bno\b.{{0,20}}\b{_ROW_UNIT}\b"),
)
# Transforms that actively drop/aggregate rows must affirmatively disclose it; a
# schematic or matrix-overview is not a row-truncation and is exempt.
_REQUIRES_DISCLOSURE = {"compacted", "compacted_subset", "compacted_aggregate", "compacted_label_key", "aggregate"}

# A non-negated "(all|every|each) … UNIT" phrase is a completeness assertion that a
# compressed figure must not make, at ANY distance (catches cross-sentence/far-split
# overclaims). Loose intervening-word fillers cover "all 51 rows" and adjective forms
# ("every single record"); the whole _ROW_UNIT family (rows/entries/records/lines/
# claims/items) is matched so a synonym cannot evade. "full row" is intentionally NOT a
# quantifier — real disclosures say "the full row-level contract remains in …".
_ROWS_COMPLETENESS_PHRASE = re.compile(
    rf"\b(all|every|each)\b(?:\s+[\w-]+){{0,3}}\s+{_ROW_UNIT}\b"
    # "(the) entire/complete/full/whole set|collection|list of [...] UNIT" — requires the
    # "… of" frame, so the honest "the full row-level contract remains in …" does NOT match.
    rf"|\b(?:the\s+)?(?:entire|complete|full|whole)\s+(?:set|collection|list)\s+of\s+(?:[\w-]+\s+){{0,2}}{_ROW_UNIT}\b"
)
_COMPLETENESS_NEGATION = re.compile(r"\b(not|no|only|fewer|without|aside\s+from|rather\s+than)\b")
# Several synonyms ("records", "claims", "lines") are also verbs. When the matched unit
# is immediately followed by a determiner that opens a direct object ("each edge records
# A declared link", "the model claims A result") it is a verb, not the row noun — skip
# it. The completeness assertion ("all rows ARE shown") never puts a determiner-object
# right after the unit, so this guard removes the verb collisions without weakening the
# overclaim detection. Pairs with the gate's global display-verb requirement, which is
# what catches cross-sentence "All rows. Displayed." phrasings.
_UNIT_AS_VERB = re.compile(
    r"^\s+(?:a|an|the|its|their|his|her|our|your|my|some|any|this|that|these|those|each|every|no)\b"
)


def _asserts_complete_rows(lower: str) -> bool:
    # A negation only defuses the overclaim when it governs the SAME clause as the
    # completeness phrase ("not all rows are shown" is honest disclosure). A fixed
    # character window let an unrelated negation in a neighbouring clause ("aside from
    # styling, all rows are shown") suppress a real overclaim, so scope the lookback to
    # the clause: back to the previous sentence/clause boundary, not a raw char count.
    for match in _ROWS_COMPLETENESS_PHRASE.finditer(lower):
        clause_start = max((lower.rfind(sep, 0, match.start()) for sep in ".;,:"), default=-1) + 1
        if _COMPLETENESS_NEGATION.search(lower[clause_start : match.start()]):
            continue
        if _UNIT_AS_VERB.match(lower[match.end() :]):  # synonym used as a verb, not the unit noun
            continue
        return True
    return False


def _normalize_claim_text(text: str) -> str:
    without_tokens = _CAPTION_TOKEN_SPAN.sub(" ", text)
    return " ".join(without_tokens.lower().replace("–", "-").replace("—", "-").split())


def _term_in_text(term: str, lower: str) -> bool:
    """Word-boundary containment so an opposite-sense substring cannot satisfy a term
    (e.g. "aggregate" must not match inside "disaggregate")."""
    return re.search(rf"(?<!\w){re.escape(term.lower())}(?!\w)", lower) is not None


def _figure_caption_claim_payloads(spec: Any) -> list[dict[str, Any]]:
    claims = []
    for claim in getattr(spec, "claims", ()) or ():
        claims.append(
            {
                "id": str(getattr(claim, "claim_id", "")),
                "claim_type": str(getattr(claim, "claim_type", "")),
                "caption_terms": [str(term) for term in getattr(claim, "caption_terms", ())],
                "sources": [str(source) for source in getattr(claim, "sources", ())],
                "source_fields": [str(field) for field in getattr(claim, "source_fields", ())],
                "scope": str(getattr(claim, "scope", "")),
                "display_transform": str(getattr(claim, "display_transform", "full")),
            }
        )
    return claims


def _caption_claims_source_bound(
    caption_claims: list[dict[str, Any]],
    row_sources: list[str],
    row_fields: list[str],
) -> bool:
    source_set = set(row_sources)
    field_set = set(row_fields)
    if not caption_claims:
        return False
    for claim in caption_claims:
        claim_sources = set(claim.get("sources") or [])
        claim_fields = set(claim.get("source_fields") or [])
        if not (
            claim.get("id")
            and claim_sources
            and claim_fields
            and claim_sources <= source_set
            and claim_fields <= field_set
        ):
            return False
    return True


def _load_structured_artifact(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        if path.suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if path.suffix in (".yaml", ".yml"):
            import yaml

            return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — a malformed artifact is an unresolved field, not a crash
        return None
    return None


def _nonempty_node(node: Any) -> bool:
    """A resolved node carries content iff it is not None and not an empty
    container/string. ``0`` and ``False`` are legitimate resolved values and are kept;
    only ``None``/``[]``/``{}``/``""`` count as "key present but empty" — a stale or
    zeroed artifact whose key exists but holds nothing the figure could have drawn."""
    return node is not None and node != [] and node != {} and node != ""


def _jsonpath_present(obj: Any, path: str) -> bool:
    """Return True iff a `$.a.b[*].c` / `$.a[0].b` JSONPath resolves to ≥1 *non-empty*
    node. A key that exists but holds ``[]``/``{}``/``None``/``""`` is rejected: the
    generators raise on empty source rows, so the verifier must too (else a zeroed
    stale artifact resolves a claim the figure could not honestly depict)."""
    parts = re.findall(r"\[\*\]|\[\d+\]|[^.\[\]]+", path[1:].lstrip("."))
    if not parts:
        return False  # a bare "$" selects the document root and binds nothing
    nodes = [obj]
    for part in parts:
        nxt: list[Any] = []
        if part == "[*]":
            for node in nodes:
                if isinstance(node, list):
                    nxt.extend(node)
        elif part.startswith("[") and part.endswith("]"):
            index = int(part[1:-1])
            for node in nodes:
                if isinstance(node, list) and -len(node) <= index < len(node):
                    nxt.append(node[index])
        else:
            for node in nodes:
                if isinstance(node, dict) and part in node:
                    nxt.append(node[part])
                elif isinstance(node, list):
                    nxt.extend(item[part] for item in node if isinstance(item, dict) and part in item)
        nodes = nxt
        if not nodes:
            return False
    return any(_nonempty_node(node) for node in nodes)


def _nested_key_present(obj: Any, dotted: str) -> bool:
    node = obj
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return False
    return True


def _source_field_resolves(field: str, row_sources: list[str], root: Path) -> bool:
    """Resolve a caption-claim ``source_field`` against the figure's artifacts.

    The contract previously only checked that a field string was *declared* on the
    row; a row could cite ``$.totally_made_up`` and pass. This binds the declared
    field to artifact *content* across the claim grammar: bare ``$.jsonpath``
    (against the row's structured sources), ``relpath:column`` (CSV header),
    ``relpath:$.jsonpath`` / ``relpath:dotted.key`` (file-scoped), globs, and plain
    paths. A field that resolves to no node is rejected.
    """
    field = str(field)
    if field.startswith("$"):
        if field.strip().rstrip(".") == "$":
            return False  # a bare "$" / "$." selects the whole document and binds nothing
        return any(
            (obj := _load_structured_artifact(root / source)) is not None and _jsonpath_present(obj, field)
            for source in row_sources
        )
    if ":" in field:
        rel, selector = field.split(":", 1)
        # The reference may name the artifact by a bare filename (e.g.
        # "parameter_sweep.csv:col") while the row source is a full path
        # ("output/data/parameter_sweep.csv"); resolve against the row sources by
        # basename, falling back to the literal repo-relative path.
        candidates = [s for s in row_sources if Path(s).name == Path(rel).name or s.endswith(rel)]
        candidates.append(rel)
        for candidate in candidates:
            path = root / candidate
            if path.suffix == ".csv":
                if not path.is_file():
                    continue
                with path.open(encoding="utf-8", newline="") as handle:
                    header = next(csv.reader(handle), [])
                if selector in header:
                    return True
                continue
            obj = _load_structured_artifact(path)
            if obj is None:
                continue
            if selector.startswith("$") and _jsonpath_present(obj, selector):
                return True
            if not selector.startswith("$") and _nested_key_present(obj, selector):
                return True
        return False
    if "*" in field:
        matches = [path for path in root.glob(field) if path.is_file()]
        if not matches:
            return False
        if not row_sources:
            return True
        # Bind the glob to a declared source: a matched file must live under one of
        # the row's sources, not merely exist somewhere in the repo.
        rels = {path.relative_to(root).as_posix() for path in matches}
        return any(rel == src or rel.startswith(f"{src.rstrip('/')}/") for rel in rels for src in row_sources)
    return (root / field).is_file()


def _caption_claim_fields_resolved(caption_claims: list[dict[str, Any]], row_sources: list[str], root: Path) -> bool:
    if not caption_claims:
        return False
    for claim in caption_claims:
        fields = claim.get("source_fields") or []
        # Resolve a field against the claim's OWN declared sources, not the row-wide
        # source set — otherwise a claim could cite source A for "$.metric" while the
        # value actually lives in a sibling source B, masking a stale claim.
        claim_sources = [str(source) for source in (claim.get("sources") or [])] or list(row_sources)
        if not fields or not all(_source_field_resolves(str(field), claim_sources, root) for field in fields):
            return False
    return True


def _caption_claim_terms_present(text: str, caption_claims: list[dict[str, Any]]) -> bool:
    lower = _normalize_claim_text(text)
    if not caption_claims:
        return False
    for claim in caption_claims:
        terms = [str(term) for term in claim.get("caption_terms") or []]
        # Word-boundary match so a term is not satisfied by an opposite-sense
        # substring (e.g. "measured" inside "unmeasured", "finite" inside "infinite").
        if not terms or not all(_term_in_text(term, lower) for term in terms):
            return False
    return True


def _caption_claim_scope_ok(figure_id: str, caption_claims: list[dict[str, Any]]) -> bool:
    if not caption_claims:
        return False
    claim_ids = [str(claim.get("id") or "") for claim in caption_claims]
    if not all(claim_ids) or len(set(claim_ids)) != len(claim_ids):
        return False  # empty or duplicate claim ids must not pass silently
    if figure_id and not all(cid.startswith(f"{figure_id}_") for cid in claim_ids):
        return False  # a claim id must name its figure (convention: {figure_id}_caption_claim)
    for claim in caption_claims:
        claim_type = str(claim.get("claim_type") or "")
        display_transform = str(claim.get("display_transform") or "")
        scope = str(claim.get("scope") or "").strip()
        if (
            claim_type not in _ALLOWED_CAPTION_CLAIM_TYPES
            or display_transform not in _ALLOWED_DISPLAY_TRANSFORMS
            or not scope
        ):
            return False
        if claim_type == "external_context" and figure_id not in _EXTERNAL_CONTEXT_FIGURES:
            return False
        if figure_id in _EXTERNAL_CONTEXT_FIGURES and claim_type != "external_context":
            return False
        if claim_type == "schematic" and figure_id not in _SCHEMATIC_CLAIM_FIGURES:
            return False
        if figure_id in _SCHEMATIC_CLAIM_FIGURES and claim_type != "schematic":
            return False
    return True


def _caption_claim_display_transform_ok(text: str, caption_claims: list[dict[str, Any]]) -> bool:
    if not caption_claims:
        return False
    lower = _normalize_claim_text(text)
    transforms = {str(claim.get("display_transform") or "") for claim in caption_claims}
    discloses_compression = any(_term_in_text(term, lower) for term in _COMPRESSED_TEXT_TERMS)
    if discloses_compression and not (transforms & _COMPRESSED_DISPLAY_TRANSFORMS):
        return False
    if (transforms & _COMPRESSED_DISPLAY_TRANSFORMS) and (
        (_asserts_complete_rows(lower) and _DISPLAY_VERB.search(lower) is not None)
        or any(pattern.search(lower) for pattern in _NO_ROWS_OMITTED_PATTERNS)
    ):
        return False
    # Positive disclosure: a row-dropping/aggregating transform must affirmatively
    # say so. This is the allowlist half — it cannot be evaded by avoiding the
    # (necessarily incomplete) overclaim denylist above.
    if (transforms & _REQUIRES_DISCLOSURE) and not discloses_compression:
        return False
    return True


def build_visualization_quality_audit(project_root: Path) -> dict[str, Any]:
    """Build a verifier-facing audit over figure readability, provenance, and caption scope."""
    root = project_root.resolve()
    from visualizations.figure_style import load_figure_style

    style = load_figure_style(root)
    palette_contrast_report = style.palette_contrast_report()
    font_role_report = style.font_role_report()
    palette_contrast_ok = bool(palette_contrast_report) and all(
        row.get("passes_aa") is True for row in palette_contrast_report.values()
    )
    font_roles_ok = bool(font_role_report) and all(row.get("meets_minimum") is True for row in font_role_report.values())
    source_map = build_figure_source_map(root)
    registry_outputs = {str(row.get("output") or "") for row in source_map.get("rows") or []}
    expected_images = _expected_figure_image_paths(root)
    actual_images = _actual_figure_image_paths(root)
    unexpected_images = sorted(actual_images - expected_images)
    rows = []
    for row in source_map.get("rows") or []:
        figure_id = str(row.get("figure_id") or "")
        output = str(row.get("output") or "")
        path = root / output
        readable = False
        nonblank = False
        width = 0
        height = 0
        if path.is_file():
            try:
                from PIL import Image

                with Image.open(path) as img:
                    img.load()
                    width, height = img.size
                    extrema = img.convert("L").getextrema()
                readable = True
                nonblank = bool(extrema[0] < extrema[1])
            except (OSError, ValueError):
                readable = False
        text = f"{row.get('caption', '')} {row.get('alt', '')}"
        lower = text.lower()
        scope_guard_required = figure_id in _FIGURE_SCOPE_REQUIRED
        scope_guard_present = (not scope_guard_required) or any(term in lower for term in _FIGURE_SCOPE_TERMS)
        caption_overclaim_free = _caption_overclaim_free(text)
        claim_wording_ok = _figure_claim_wording_ok(figure_id, text)
        cover_quantitative_free = _cover_quantitative_free(figure_id, text)
        source_bound = (
            row.get("mapped") is True
            and row.get("source_paths_exist") is True
            and bool(row.get("sources"))
            and bool(row.get("source_fields"))
            and bool(row.get("validation_gates"))
        )
        caption_claims_ok = bool(
            row.get("caption_claim_count", 0)
            and row.get("caption_claims_source_bound") is True
            and row.get("caption_claim_fields_resolved") is True
            and row.get("caption_claim_terms_present") is True
            and row.get("caption_claim_scope_ok") is True
            and row.get("caption_claim_display_transform_ok") is True
            and row.get("caption_claims_ok") is True
        )
        metadata_complete = row.get("metadata_complete") is True and bool(row.get("caption")) and bool(row.get("alt"))
        dimensions_ok = readable and nonblank and width >= 400 and height >= 200
        accessibility_ok = bool(metadata_complete and dimensions_ok and claim_wording_ok)
        ok = bool(
            source_bound
            and caption_claims_ok
            and metadata_complete
            and dimensions_ok
            and scope_guard_present
            and caption_overclaim_free
            and claim_wording_ok
            and cover_quantitative_free
            and accessibility_ok
        )
        rows.append(
            {
                "figure_id": figure_id,
                "output": output,
                "readable": readable,
                "nonblank": nonblank,
                "image_width_px": width,
                "image_height_px": height,
                "source_bound": source_bound,
                "caption_claims": row.get("caption_claims") or [],
                "caption_claim_count": int(row.get("caption_claim_count", 0) or 0),
                "caption_claims_source_bound": row.get("caption_claims_source_bound") is True,
                "caption_claim_fields_resolved": row.get("caption_claim_fields_resolved") is True,
                "caption_claim_terms_present": row.get("caption_claim_terms_present") is True,
                "caption_claim_scope_ok": row.get("caption_claim_scope_ok") is True,
                "caption_claim_display_transform_ok": row.get("caption_claim_display_transform_ok") is True,
                "caption_claims_ok": caption_claims_ok,
                "metadata_complete": metadata_complete,
                "scope_guard_required": scope_guard_required,
                "scope_guard_present": scope_guard_present,
                "caption_overclaim_free": caption_overclaim_free,
                "claim_wording_ok": claim_wording_ok,
                "cover_quantitative_free": cover_quantitative_free,
                "accessibility_ok": accessibility_ok,
                "ok": ok,
            }
        )
    return {
        "schema": "template_active_inference.visualization_quality_audit.v1",
        "rows": rows,
        "figure_count": len(rows),
        "palette_contrast_report": palette_contrast_report,
        "font_role_report": font_role_report,
        "palette_contrast_ok": palette_contrast_ok,
        "font_roles_ok": font_roles_ok,
        "declared_nonregistry_image_paths": sorted(expected_images - registry_outputs),
        "unexpected_image_paths": unexpected_images,
        "unexpected_image_count": len(unexpected_images),
        "all_figures_readable": bool(rows) and all(row["readable"] for row in rows),
        "all_figures_nonblank": bool(rows) and all(row["nonblank"] for row in rows),
        "all_figures_source_bound": bool(rows) and all(row["source_bound"] for row in rows),
        "all_caption_claims_ok": bool(rows) and all(row["caption_claims_ok"] for row in rows),
        "all_scope_guards_present": bool(rows) and all(row["scope_guard_present"] for row in rows),
        "all_caption_overclaims_free": bool(rows) and all(row["caption_overclaim_free"] for row in rows),
        "all_claim_wording_ok": bool(rows) and all(row["claim_wording_ok"] for row in rows),
        "all_cover_quantitative_free": bool(rows) and all(row["cover_quantitative_free"] for row in rows),
        "all_accessibility_metadata_ok": bool(rows) and all(row["accessibility_ok"] for row in rows),
        "no_unexpected_image_artifacts": not unexpected_images,
        "all_rows_ok": bool(rows)
        and palette_contrast_ok
        and font_roles_ok
        and not unexpected_images
        and all(row["ok"] for row in rows),
    }


def _figure_source_rows_complete(project_root: Path, payload: dict[str, Any]) -> bool:
    root = project_root.resolve()
    from visualizations.figure_registry import load_figure_registry

    registry = load_figure_registry(root)
    registry_ids = set(registry)
    rows = payload.get("rows") or []
    row_ids = {str(row.get("figure_id", "")) for row in rows}
    if (
        not rows
        or row_ids != registry_ids
        or int(payload.get("figure_count", 0) or 0) != len(registry_ids)
        or payload.get("all_figure_metadata_complete") is not True
        or payload.get("all_caption_claims_ok") is not True
    ):
        return False
    for row in rows:
        output = str(row.get("output", ""))
        sources = row.get("sources") or []
        source_fields = row.get("source_fields") or []
        source_status = row.get("source_path_status") or {}
        gates = row.get("validation_gates") or []
        # Registry is authoritative for caption text and claim payloads: a forged
        # figure_source_map.json cannot rewrite the prose to satisfy the term check
        # or swap in a benign claim — the stored values must equal the registry's.
        spec = registry.get(str(row.get("figure_id", "")))
        if spec is None:
            return False
        caption_claims = _figure_caption_claim_payloads(spec)
        if (
            (row.get("caption_claims") or []) != caption_claims
            or str(row.get("caption", "")) != spec.caption
            or str(row.get("alt", "")) != spec.alt
        ):
            return False
        row_text = f"{spec.caption}\n{spec.alt}"
        if not (
            row.get("mapped") is True
            and row.get("metadata_complete") is True
            and row.get("source_paths_exist") is True
            and str(row.get("label", "")) == f"fig:{row.get('figure_id')}"
            and str(row.get("generator", "")).startswith("visualizations.figures::")
            and output.startswith("output/figures/")
            and (root / output).is_file()
            and int(row.get("image_width_px", 0) or 0) > 0
            and int(row.get("image_height_px", 0) or 0) > 0
            and float(row.get("width", 0.0) or 0.0) > 0
            and sources
            and source_fields
            and int(row.get("source_field_count", 0) or 0) == len(source_fields)
            and gates
            and int(row.get("validation_gate_count", 0) or 0) == len(gates)
            and caption_claims
            and int(row.get("caption_claim_count", 0) or 0) == len(caption_claims)
            and row.get("caption_claims_source_bound") is True
            and row.get("caption_claim_fields_resolved") is True
            and row.get("caption_claim_terms_present") is True
            and row.get("caption_claim_scope_ok") is True
            and row.get("caption_claim_display_transform_ok") is True
            and row.get("caption_claims_ok") is True
            and _caption_claims_source_bound(caption_claims, sources, source_fields)
            and _caption_claim_fields_resolved(caption_claims, sources, root)
            and _caption_claim_terms_present(row_text, caption_claims)
            and _caption_claim_scope_ok(str(row.get("figure_id", "")), caption_claims)
            and _caption_claim_display_transform_ok(row_text, caption_claims)
        ):
            return False
        if set(source_status) != set(sources):
            return False
        for rel, recorded_exists in source_status.items():
            if recorded_exists is not True or not (root / str(rel)).exists():
                return False
        if row.get("figure_id") == "tmaze_schematic":
            required_sources = {
                "pymdp.yaml",
                "output/data/si_tmaze_summary.json",
                "output/data/si_tmaze_model_matrices.json",
            }
            required_fields = {
                "pymdp.yaml:planning_horizon",
                "pymdp.yaml:agent.si_policy_len",
                "output/data/si_tmaze_summary.json:$.planning_horizon",
                "output/data/si_tmaze_summary.json:$.policy_len",
                "output/data/si_tmaze_model_matrices.json:$.A_shapes",
                "output/data/si_tmaze_model_matrices.json:$.B_shapes",
                "output/data/si_tmaze_model_matrices.json:$.environment",
            }
            required_gates = {
                "validate_outputs.si_summary_schema",
                "validate_outputs.si_tmaze_model_matrices_schema",
                "test_figures.tmaze_schematic_uses_configured_horizon",
            }
            if not (
                required_sources.issubset(set(sources))
                and required_fields.issubset(set(row.get("source_fields") or []))
                and required_gates.issubset(set(gates))
            ):
                return False
        if row.get("figure_id") == "sequential_shift_sensitivity":
            required_sources = {"output/data/firstprinciples/sequential_shift_sensitivity.json"}
            required_fields = {
                "$.rows[*].correction_fraction",
                "$.rows[*].test_loss",
                "$.rows[*].shift_mass",
                "$.monotone_test_loss_decrease",
                "$.monotone_shift_mass_decrease",
            }
            required_gates = {
                "validate_outputs.firstprinciples_sequential_shift_sensitivity_schema",
                "test_figures.nonblank_png",
            }
            if not (
                required_sources.issubset(set(sources))
                and required_fields.issubset(set(row.get("source_fields") or []))
                and required_gates.issubset(set(gates))
            ):
                return False
    return True


def _rederive_image_facts(path: Path) -> tuple[bool, bool, int, int]:
    """Re-open a figure PNG and recompute (readable, nonblank, width, height).

    Mirrors ``build_visualization_quality_audit``'s image probe so the read-time gate
    can re-derive image facts from disk instead of trusting the stored audit booleans.
    A blank or deleted PNG returns falsy facts regardless of what the JSON claims."""
    if not path.is_file():
        return (False, False, 0, 0)
    try:
        from PIL import Image

        with Image.open(path) as img:
            img.load()
            width, height = img.size
            extrema = img.convert("L").getextrema()
        return (True, bool(extrema[0] < extrema[1]), int(width), int(height))
    except (OSError, ValueError):
        return (False, False, 0, 0)


def _visualization_quality_caption_claims_rederived(project_root: Path, payload: dict[str, Any]) -> bool:
    """Re-derive the visualization audit's caption-claim AND image booleans from source.

    The audit gate otherwise trusts the stored row booleans; a fully self-consistent
    forged audit could flip every caption-claim boolean green over a bad claim, or claim
    a blank/missing PNG is readable and nonblank. This rebuilds the authoritative figure
    sources/fields and the registry claim payloads, re-runs the claim helpers, re-opens
    each PNG, and requires the stored row booleans to agree and be True. The single
    source of truth is the registry, the source-map builder, and the image files on
    disk — not the on-disk audit JSON.
    """
    root = project_root.resolve()
    from visualizations.figure_registry import load_figure_registry

    registry = load_figure_registry(root)
    rows = payload.get("rows") or []
    if not rows or {str(row.get("figure_id", "")) for row in rows} != set(registry):
        return False
    if payload.get("all_caption_claims_ok") is not True:
        return False
    fsm_by_id = {str(row.get("figure_id", "")): row for row in build_figure_source_map(root).get("rows") or []}
    for row in rows:
        fid = str(row.get("figure_id", ""))
        spec = registry.get(fid)
        fsm = fsm_by_id.get(fid)
        if spec is None or fsm is None:
            return False
        caption_claims = _figure_caption_claim_payloads(spec)
        if not caption_claims or int(row.get("caption_claim_count", 0) or 0) != len(caption_claims):
            return False
        sources = fsm.get("sources") or []
        source_fields = fsm.get("source_fields") or []
        text = f"{spec.caption}\n{spec.alt}"
        derived = {
            "caption_claims_source_bound": _caption_claims_source_bound(caption_claims, sources, source_fields),
            "caption_claim_fields_resolved": _caption_claim_fields_resolved(caption_claims, sources, root),
            "caption_claim_terms_present": _caption_claim_terms_present(text, caption_claims),
            "caption_claim_scope_ok": _caption_claim_scope_ok(fid, caption_claims),
            "caption_claim_display_transform_ok": _caption_claim_display_transform_ok(text, caption_claims),
        }
        for key, value in derived.items():
            if value is not True or row.get(key) is not True:
                return False
        if row.get("caption_claims_ok") is not True:
            return False
        # Re-derive image facts from the PNG on disk and require the stored booleans to
        # agree — a blank or deleted image cannot pass on stored values alone, and this
        # holds even when only `visualization_quality_audit_schema` is selected (the
        # sibling figure-integrity gate that incidentally re-opens files is not run).
        readable, nonblank, width, height = _rederive_image_facts(root / str(row.get("output", "")))
        if not (readable and nonblank and width >= 400 and height >= 200):
            return False
        if (
            row.get("readable") is not True
            or row.get("nonblank") is not True
            or int(row.get("image_width_px", 0) or 0) != width
            or int(row.get("image_height_px", 0) or 0) != height
        ):
            return False
    return True


def _figure_hash_rows_complete(project_root: Path, payload: dict[str, Any]) -> bool:
    root = project_root.resolve()
    expected_paths = _expected_figure_image_paths(root)
    unexpected_paths = sorted(_actual_figure_image_paths(root) - expected_paths)
    rows = payload.get("rows") or []
    row_paths = {str(row.get("path", "")) for row in rows}
    if (
        not rows
        or row_paths != expected_paths
        or unexpected_paths
        or payload.get("unexpected_image_paths") not in ([], None)
        or int(payload.get("unexpected_image_count", 0) or 0) != 0
        or payload.get("no_unexpected_image_artifacts") is not True
        or payload.get("all_expected_images_present") is not True
    ):
        return False
    for row in rows:
        path = root / str(row.get("path", ""))
        digest = str(row.get("sha256", ""))
        if not (
            path.is_file()
            and row.get("exists") is True
            and len(digest) == 64
            and digest == _sha256(path)
            and int(row.get("size_bytes", 0) or 0) == path.stat().st_size
            and row.get("fresh") is True
        ):
            return False
    return True


_SCOPE_FORBIDDEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "equality_slogan": re.compile(r"\bopd\s*=\s*active inference\b"),
    "universal_theorem": re.compile(
        r"\b(proves?|establishes?|certif(?:y|ies)|demonstrates?)\s+(a\s+)?"
        r"(universal|general)\s+theorem\b|\b(universal|general)\s+theorem\b"
    ),
    "production_llm_result": re.compile(
        r"\b(qwen|thinking machines|production[- ](?:llms?|language models?|opd)|llms?)\b"
        r"[^.\n;:]{0,120}\b(reproduce[sd]?|measure[sd]?|benchmark(?:ed)?|validate[sd]?|confirm(?:ed)?)\b|"
        r"\b(reproduce[sd]?|measure[sd]?|benchmark(?:ed)?|validate[sd]?|confirm(?:ed)?)\b"
        r"[^.\n;:]{0,120}\b(qwen|thinking machines|production[- ](?:llms?|language models?|opd)|llms?)\b"
    ),
    "biological_markov_blanket": re.compile(
        r"\b(markov blanket|blanket)\b[^.\n;:]{0,120}\b(biological|cortical|physical)\b|"
        r"\b(biological|cortical|physical)\b[^.\n;:]{0,120}\b(markov blanket|blanket|boundary)\b"
    ),
    "empirical_biological": re.compile(r"\b(empirical biological|biological data)\b"),
}

_SCOPE_NEGATION_TERMS = (
    "not ",
    "no ",
    "never ",
    "rather than",
    "external context",
    "not reproduced",
    "not a",
    "not an",
    "without claiming",
    "does not",
    "do not",
    "outside",
    "future",
    "blocked",
    "scope",
    "limited",
    "toy",
    "finite",
)


def _scope_forbidden_hits(text: str) -> list[dict[str, Any]]:
    """Return scoped-overclaim hits by line, preserving negated guardrail mentions."""
    hits: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        for rule, pattern in _SCOPE_FORBIDDEN_PATTERNS.items():
            if pattern.search(lowered):
                hits.append(
                    {
                        "line": line_no,
                        "rule": rule,
                        "negated": any(term in lowered for term in _SCOPE_NEGATION_TERMS),
                        "excerpt": line.strip()[:240],
                    }
                )
    return hits


def build_scope_boundary_audit(project_root: Path) -> dict[str, Any]:
    """Build the scope_boundary_audit.v1 payload scanning numbered manuscript sections for scope leaks."""
    root = project_root.resolve()
    rows = []
    violations: list[str] = []
    allowed_future_files = {"15_discussion_outlook.md", "17_conclusion.md"}
    for path in sorted((root / "manuscript").glob("[0-9][0-9]_*.md")):
        text = path.read_text(encoding="utf-8")
        all_hits = _scope_forbidden_hits(text)
        forbidden_hits = [hit for hit in all_hits if not hit["negated"]]
        forbidden = bool(forbidden_hits)
        negated = bool(all_hits) and not forbidden_hits
        allowed = path.name in allowed_future_files
        ok = not forbidden or negated or allowed
        rows.append(
            {
                "section": path.name,
                "classification": "toy_or_future",
                "has_forbidden_wording": forbidden,
                "is_negated": negated,
                "allowed": allowed,
                "forbidden_hits": forbidden_hits,
                "negated_hits": [hit for hit in all_hits if hit["negated"]],
                "ok": ok,
            }
        )
        if not ok:
            for hit in forbidden_hits:
                violations.append(f"{path.name}:{hit['line']}:{hit['rule']}")
    return {
        "schema": "template_active_inference.scope_boundary_audit.v1",
        "rows": rows,
        "violations": violations,
        "all_current_claims_toy": not violations,
        "empirical_adapter_enabled": False,
        "scope_boundary_status": "toy_only_pass" if not violations else "scope_leak",
    }


def build_manuscript_evidence_tables(project_root: Path) -> dict[str, Any]:
    """Build the manuscript_evidence_tables.v1 payload: an id/row_count/source index over twenty evidence artifacts."""
    root = project_root.resolve()
    claims = build_claim_evidence_audit(root)
    graph = build_integration_dependency_graph(root)
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    staleness = build_manuscript_staleness_report(root)
    posterior = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    runtime = _load_json(root / "output" / "reports" / "pymdp_runtime_diagnostics.json")
    semantic = _load_json(root / "output" / "data" / "sheaf_gluing_certificate.json")
    track_scope = _load_json(root / "output" / "data" / "track_improvement_scope.json")
    replay_matrix = _load_json(root / "output" / "reports" / "replay_matrix.json")
    diffoscope = _load_json(root / "output" / "reports" / "artifact_diffoscope.json")
    proof = _load_json(root / "output" / "data" / "proof_extraction_index.json")
    catalog = _load_json(root / "output" / "data" / "state_space_catalog.json")
    ablation = _load_json(root / "output" / "data" / "causal_ablation_matrix.json")
    license_audit = _load_json(root / "output" / "reports" / "artifact_license_audit.json")
    release_notes = _load_json(root / "output" / "reports" / "release_notes_evidence.json")
    scholarship = _load_json(root / "output" / "data" / "scholarship_source_matrix.json")
    proof_dependency = _load_json(root / "output" / "data" / "proof_dependency_graph.json")
    transition_table = _load_json(root / "output" / "data" / "state_transition_table.json")
    ablation_sensitivity = _load_json(root / "output" / "reports" / "ablation_sensitivity_report.json")
    release_attestation = _load_json(root / "output" / "reports" / "release_attestation.json")
    tables = [
        {
            "id": "claim_evidence",
            "row_count": claims["claim_count"],
            "source": "output/reports/claim_evidence_audit.json",
        },
        {
            "id": "artifact_producers",
            "row_count": len(graph.get("artifacts") or {}),
            "source": "output/data/validation_dependency_graph.json",
        },
        {
            "id": "artifact_provenance",
            "row_count": int(provenance.get("artifact_count", 0)),
            "source": "output/data/artifact_provenance.json",
        },
        {
            "id": "manuscript_staleness",
            "row_count": int(staleness.get("row_count", 0)),
            "source": "output/reports/manuscript_staleness_report.json",
        },
        {
            "id": "pymdp_policy_posterior",
            "row_count": int(posterior.get("row_count", 0)),
            "source": "output/data/pymdp_policy_posterior_grid.json",
        },
        {
            "id": "pymdp_runtime_diagnostics",
            "row_count": int(runtime.get("construction_count", 0)),
            "source": "output/reports/pymdp_runtime_diagnostics.json",
        },
        {
            "id": "semantic_restrictions",
            "row_count": len(semantic.get("restrictions") or {}),
            "source": "output/data/sheaf_gluing_certificate.json",
        },
        {
            "id": "track_improvement_scope",
            "row_count": int(track_scope.get("improvement_row_count", 0)),
            "source": "output/data/track_improvement_scope.json",
        },
        {
            "id": "replay_matrix",
            "row_count": int(replay_matrix.get("check_count", 0)),
            "source": "output/reports/replay_matrix.json",
        },
        {
            "id": "artifact_diffoscope",
            "row_count": int(diffoscope.get("row_count", 0)),
            "source": "output/reports/artifact_diffoscope.json",
        },
        {
            "id": "proof_extraction",
            "row_count": int(proof.get("theorem_count", 0)),
            "source": "output/data/proof_extraction_index.json",
        },
        {
            "id": "state_space_catalog",
            "row_count": int(catalog.get("row_count", 0)),
            "source": "output/data/state_space_catalog.json",
        },
        {
            "id": "causal_ablation",
            "row_count": int(ablation.get("row_count", 0)),
            "source": "output/data/causal_ablation_matrix.json",
        },
        {
            "id": "artifact_license",
            "row_count": int(license_audit.get("row_count", 0)),
            "source": "output/reports/artifact_license_audit.json",
        },
        {
            "id": "release_notes",
            "row_count": int(release_notes.get("row_count", 0)),
            "source": "output/reports/release_notes_evidence.json",
        },
        {
            "id": "scholarship_sources",
            "row_count": int(scholarship.get("source_count", 0)),
            "source": "output/data/scholarship_source_matrix.json",
        },
        {
            "id": "proof_dependency_graph",
            "row_count": int(proof_dependency.get("edge_count", 0)),
            "source": "output/data/proof_dependency_graph.json",
        },
        {
            "id": "state_transition_table",
            "row_count": int(transition_table.get("row_count", 0)),
            "source": "output/data/state_transition_table.json",
        },
        {
            "id": "ablation_sensitivity",
            "row_count": int(ablation_sensitivity.get("row_count", 0)),
            "source": "output/reports/ablation_sensitivity_report.json",
        },
        {
            "id": "release_attestation",
            "row_count": int(release_attestation.get("row_count", 0)),
            "source": "output/reports/release_attestation.json",
        },
    ]
    return {
        "schema": "template_active_inference.manuscript_evidence_tables.v1",
        "tables": tables,
        "table_count": len(tables),
        "all_source_backed": all(table["row_count"] > 0 and table["source"] for table in tables),
    }


def build_adversarial_audit(project_root: Path) -> dict[str, Any]:
    """Return a copy of the canonical adversarial audit from roadmap_tracks.sheaf_tracks."""
    from roadmap_tracks.sheaf_tracks import build_adversarial_audit as build_canonical_adversarial_audit

    return dict(build_canonical_adversarial_audit(project_root))


def build_integration_semantic_snapshot(project_root: Path) -> dict[str, Any]:
    """Build the integration_semantic_snapshot.v1 payload: ~30 boolean restrictions over the saved artifacts plus structural/semantic/artifact/manuscript section rollups."""
    root = project_root.resolve()
    toy = _load_json(root / "output" / "data" / "sensitivity_sweep.json")
    assumptions = _load_json(root / "output" / "data" / "analytical_assumption_index.json")
    policy = _load_json(root / "output" / "data" / "si_policy_comparison.json")
    posterior = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    runtime = _load_json(root / "output" / "reports" / "pymdp_runtime_diagnostics.json")
    topology_traces = _load_json(root / "output" / "data" / "si_graph_world_topology_traces.json")
    uncertainty = _load_json(root / "output" / "data" / "uncertainty_summary.json")
    benchmark = _load_json(root / "output" / "data" / "toy_benchmark_matrix.json")
    model_checking = _load_json(root / "output" / "reports" / "model_checking_witnesses.json")
    lean_theorems = _load_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    lean_graph = _load_json(root / "output" / "reports" / "lean_graph_world_inventory.json")
    interop = _load_json(root / "output" / "data" / "interop_roundtrip_report.json")
    adversarial = build_adversarial_audit(root)
    dependency = build_integration_dependency_graph(root)
    stale = build_stale_artifact_report(root)
    tokens = build_manuscript_token_provenance(root)
    figures = build_figure_source_map(root)
    scope = build_scope_boundary_audit(root)
    staleness = build_manuscript_staleness_report(root)
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    animation = _load_json(root / "output" / "data" / "animation_frame_deltas.json")
    diffoscope = _load_json(root / "output" / "reports" / "artifact_diffoscope.json")
    proof = _load_json(root / "output" / "data" / "proof_extraction_index.json")
    catalog = _load_json(root / "output" / "data" / "state_space_catalog.json")
    ablation = _load_json(root / "output" / "data" / "causal_ablation_matrix.json")
    license_audit = _load_json(root / "output" / "reports" / "artifact_license_audit.json")
    release_notes = _load_json(root / "output" / "reports" / "release_notes_evidence.json")
    scholarship = _load_json(root / "output" / "data" / "scholarship_source_matrix.json")
    restrictions = {
        "analytical_assumptions_indexed": assumptions.get("all_equations_indexed") is True,
        "pymdp_runtime_diagnostics_ok": runtime.get("ok") is True
        and int(runtime.get("unexpected_warning_count", 0) or 0) == 0,
        "policy_comparison_grid_complete": (policy.get("summary") or {}).get("complete_grid") is True,
        "policy_posterior_normalized": posterior.get("all_available_posteriors_normalized") is True
        and posterior.get("all_unavailable_rows_explained") is True,
        "efe_availability_or_fallback_complete": (policy.get("summary") or {}).get("all_efe_rows_explained") is True,
        "topology_trace_consistency": topology_traces.get("all_trace_summary_agree") is True,
        "sensitivity_grid_complete": toy.get("complete_grid") is True,
        "uncertainty_rows_normalized": uncertainty.get("all_normalized") is True,
        "benchmark_rows_complete": benchmark.get("all_models_complete") is True,
        "model_checking_all_passed": model_checking.get("all_passed") is True,
        "lean_theorem_inventory_proved": lean_theorems.get("all_proved") is True,
        "lean_graph_world_topologies_witnessed": lean_graph.get("all_topologies_witnessed") is True
        and lean_graph.get("all_policy_witnesses_present") is True,
        "interop_lossless": interop.get("all_lossless") is True,
        "adversarial_expected_failures_documented": adversarial["all_expected_failures_documented"],
        "dependency_edge_types_ok": dependency["all_required_edge_types_present"],
        "stale_flags_clear": stale["all_fresh"],
        "token_provenance_complete": tokens["all_tokens_mapped"],
        "figure_source_coverage": figures["all_figures_mapped"],
        "animation_deltas_nonzero": animation.get("all_nonzero") is True,
        "scope_boundary_toy_only": scope["all_current_claims_toy"],
        "manuscript_staleness_fresh": staleness["all_fresh"],
        "artifact_provenance_seed_config_complete": provenance.get("all_seeded") is True
        and provenance.get("all_config_digests") is True,
        "artifact_diffoscope_equal": diffoscope.get("all_equal") is True,
        "proof_extraction_constructive": proof.get("all_extracted") is True and proof.get("all_constructive") is True,
        "state_space_catalog_finite": catalog.get("all_finite") is True and catalog.get("all_counts_positive") is True,
        "causal_ablation_complete": ablation.get("complete_grid") is True and ablation.get("all_deterministic") is True,
        "artifact_license_safe": license_audit.get("all_license_safe") is True,
        "release_notes_source_backed": (
            release_notes.get("all_notes_source_backed")
            == (
                bool(release_notes.get("rows"))
                and all(row.get("source") and row.get("passed") for row in release_notes.get("rows") or [])
            )
        ),  # consistency; greenness at validate gate
        "scholarship_sources_connected": scholarship.get("all_sources_connected") is True,
    }
    return {
        "schema": "template_active_inference.integration_semantic_snapshot.v1",
        "ok": all(restrictions.values()),
        "restrictions": restrictions,
        "sections": {
            "structural": {"ok": dependency["all_required_edge_types_present"]},
            "semantic": {"ok": restrictions["interop_lossless"] and restrictions["scope_boundary_toy_only"]},
            "artifact": {"ok": restrictions["stale_flags_clear"] and restrictions["figure_source_coverage"]},
            "manuscript_variable": {
                "ok": restrictions["token_provenance_complete"] and restrictions["manuscript_staleness_fresh"]
            },
        },
    }
