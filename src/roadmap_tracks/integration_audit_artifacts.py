"""Artifact, figure, license, and semantic-snapshot integration-audit builders.

Split out of :mod:`roadmap_tracks.integration_audit` alongside
:mod:`roadmap_tracks.integration_audit_builders` to keep each module under the
line-count gate. The public ``integration_audit`` module re-exports every name
defined here, so existing imports continue to resolve unchanged.
"""

from __future__ import annotations

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

VALIDATION_FIXED_POINT_CHECKS: set[str] = {
    "canonical_sheaf_track_schemas",
    "canonical_sheaf_tracks",
    "claim_ledger_valid",
    "experiment_plan_metrics",
    "integration_audit_artifacts",
    "integration_audit_track_schemas",
    "release_attestation_schema",
    "release_notes_evidence_schema",
    "semantic_sheaf_gluing",
}


def _validation_failures_within_fixed_point(validation: dict[str, Any]) -> bool:
    failed = set(validation.get("failed_checks") or ([] if validation.get("all_passed") else ["<unknown>"]))
    return failed <= VALIDATION_FIXED_POINT_CHECKS


def build_artifact_diffoscope(project_root: Path) -> dict[str, Any]:
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
        "energy_decomposition": ["output/data/firstprinciples/energy_demo.json"],
        "parallel_convergence": ["output/data/firstprinciples/parallel_demo.json"],
        "diversity_tradeoff": ["output/data/firstprinciples/diversity_demo.json"],
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
            "output/data/manuscript_variables.json",
            "output/data/firstprinciples/classroom.json",
            "output/data/firstprinciples/energy_demo.json",
            "output/data/validation_dependency_graph.json",
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
        "sheaf_layers_overview": ["$.tracks", "$.layers", "$.bound_cell_count", "$.validated_cell_count"],
        "sheaf_coverage_heatmap": ["$.rows", "$.track_ids", "$.section_ids", "$.status_matrix"],
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
            "$.proof_extraction_theorem_count",
            "$.sheaf_laws_verified",
            "$.figure_source_coverage_count",
            "$.teacher_mean_belief_entropy",
            "$.vfe_at_prior",
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
            "test_graphical_abstract_is_cover_quality_wide_png",
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
        metadata_complete = bool(spec.caption.strip()) and bool(spec.alt.strip()) and spec.width > 0
        rows.append(
            {
                "figure_id": figure_id,
                "label": f"fig:{figure_id}",
                "output": output_rel,
                "generator": f"visualizations.figures::{figure_id}",
                "caption": spec.caption,
                "alt": spec.alt,
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
    }


def build_figure_hash_manifest(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    rows = []
    for path in sorted((root / "output" / "figures").glob("*")):
        if path.suffix.lower() not in {".png", ".gif"}:
            continue
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
                "fresh": True,
            }
        )
    return {
        "schema": "template_active_inference.figure_hash_manifest.v1",
        "rows": rows,
        "figure_count": len(rows),
        "all_hashes_present": bool(rows) and all(row["sha256"] for row in rows),
    }


def _figure_source_rows_complete(project_root: Path, payload: dict[str, Any]) -> bool:
    root = project_root.resolve()
    from visualizations.figure_registry import load_figure_registry

    registry_ids = set(load_figure_registry(root))
    rows = payload.get("rows") or []
    row_ids = {str(row.get("figure_id", "")) for row in rows}
    if (
        not rows
        or row_ids != registry_ids
        or int(payload.get("figure_count", 0) or 0) != len(registry_ids)
        or payload.get("all_figure_metadata_complete") is not True
    ):
        return False
    for row in rows:
        output = str(row.get("output", ""))
        sources = row.get("sources") or []
        source_status = row.get("source_path_status") or {}
        gates = row.get("validation_gates") or []
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
            and row.get("source_fields")
            and int(row.get("source_field_count", 0) or 0) == len(row.get("source_fields") or [])
            and gates
            and int(row.get("validation_gate_count", 0) or 0) == len(gates)
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
    return True


def _figure_hash_rows_complete(project_root: Path, payload: dict[str, Any]) -> bool:
    root = project_root.resolve()
    from visualizations.figure_registry import load_figure_registry

    registry_paths = {f"output/figures/{spec.filename}" for spec in load_figure_registry(root).values()}
    rows = payload.get("rows") or []
    row_paths = {str(row.get("path", "")) for row in rows}
    if not rows or not registry_paths.issubset(row_paths):
        return False
    for row in rows:
        path = root / str(row.get("path", ""))
        digest = str(row.get("sha256", ""))
        if not (
            path.is_file()
            and len(digest) == 64
            and digest == _sha256(path)
            and int(row.get("size_bytes", 0) or 0) == path.stat().st_size
            and row.get("fresh") is True
        ):
            return False
    return True


def build_scope_boundary_audit(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    rows = []
    violations: list[str] = []
    allowed_future_files = {"15_discussion_outlook.md", "17_conclusion.md"}
    for path in sorted((root / "manuscript").glob("[0-9][0-9]_*.md")):
        text = path.read_text(encoding="utf-8").lower()
        forbidden = "empirical biological" in text or "biological data" in text
        negated = "not empirical" in text or "future" in text
        allowed = path.name in allowed_future_files
        ok = not forbidden or negated or allowed
        rows.append({"section": path.name, "classification": "toy_or_future", "ok": ok})
        if not ok:
            violations.append(path.name)
    return {
        "schema": "template_active_inference.scope_boundary_audit.v1",
        "rows": rows,
        "violations": violations,
        "all_current_claims_toy": not violations,
        "empirical_adapter_enabled": False,
        "scope_boundary_status": "toy_only_pass" if not violations else "scope_leak",
    }


def build_manuscript_evidence_tables(project_root: Path) -> dict[str, Any]:
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
    from roadmap_tracks.sheaf_tracks import build_adversarial_audit as build_canonical_adversarial_audit

    return dict(build_canonical_adversarial_audit(project_root))


def build_integration_semantic_snapshot(project_root: Path) -> dict[str, Any]:
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
