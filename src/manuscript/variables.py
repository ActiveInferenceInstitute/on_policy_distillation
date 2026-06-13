"""Manuscript variable generation from measured project outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from analytical.hyperparameters import load_hyperparameters
from analytical.sweep_io import read_parameter_sweep
from gnn.concordance import BERNOULLI_EXPECTED_TERMS
from manuscript.invariant_counts import load_invariant_counts
from simulation.pymdp_config import load_pymdp_config


def _rederived_aggregate_rule_count() -> int:
    """Count of (artifact, aggregate) pairs re-derived from rows at validation time."""
    from gates.aggregate_rederivation import rule_count

    return rule_count()


def _ising_mi_saturation_from_sweep(sweep_rows: list[dict[str, float]]) -> float:
    """Maximum closed-form MI on the measured λ grid (nats)."""
    if not sweep_rows:
        return 0.0
    return max(row["closed_form_mi"] for row in sweep_rows)


def _free_energy_sweep_summary(hp: Any) -> dict[str, float]:
    """Summary for the exact-target and mean-field free-energy comparison.

    The exact entangled target gives zero variational free energy because the
    posterior equals its own normalized prior on the sweep. The reader-facing
    curve therefore plots that zero reference beside the mean-field gap
    ``D_KL(q_lambda || q_0)``, which equals total correlation / mutual
    information in the symmetric Bernoulli-Ising toy.
    """
    import numpy as np

    from analytical.bernoulli_toy import (
        ising_coupling,
        ising_joint_posterior,
        ising_mutual_information,
        symmetric_mean_field_prior,
    )
    from analytical.decomposition import free_energy_against_entangled_prior
    from analytical.free_energy import kl_divergence, total_correlation
    from analytical.hyperparameters import lambda_grid
    from analytical.joint_dist import mean_field_to_joint

    lambdas = lambda_grid(hp)
    if not lambdas:
        return {
            "argmin_lambda": 0.0,
            "mean_field_gap_max": 0.0,
            "exact_target_max_abs": 0.0,
            "gap_equals_mi_max_abs": 0.0,
        }
    mf = symmetric_mean_field_prior()
    mf_joint = mean_field_to_joint(mf)
    g0 = [np.zeros(2), np.zeros(2)]
    j = ising_coupling()
    kc = np.zeros((2, 2))
    exact_values: list[float] = []
    mean_field_gaps: list[float] = []
    gap_mi_deltas: list[float] = []
    for lam in lambdas:
        q = ising_joint_posterior(float(lam))
        exact = free_energy_against_entangled_prior(q, mf, g0, j, kc, gamma=1.0, lam=float(lam))
        gap = kl_divergence(q, mf_joint)
        mi = ising_mutual_information(float(lam))
        exact_values.append(float(exact))
        mean_field_gaps.append(float(gap))
        gap_mi_deltas.append(abs(float(gap) - float(mi)))
        gap_mi_deltas.append(abs(float(gap) - float(total_correlation(q))))
    return {
        "argmin_lambda": round(float(lambdas[int(np.argmin(mean_field_gaps))]), 4),
        "mean_field_gap_max": float(max(mean_field_gaps)),
        "exact_target_max_abs": float(max(abs(value) for value in exact_values)),
        "gap_equals_mi_max_abs": float(max(gap_mi_deltas)),
    }


def _free_energy_argmin_lambda(hp: Any) -> float:
    """λ minimizing the mean-field free-energy gap on the configured sweep."""
    return _free_energy_sweep_summary(hp)["argmin_lambda"]


def _policy_goal_counts_by_planner(policy_data: dict[str, Any]) -> dict[str, int]:
    """Goal-reaching counts split by planner from comparison-only rows."""
    counts = {"sophisticated_inference": 0, "vanilla": 0}
    for run in policy_data.get("runs") or []:
        planner = run.get("planner")
        if planner in counts and bool(run.get("goal_reached")):
            counts[planner] += 1
    return counts


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data


def _pipeline_track_count(project_root: Path) -> int:
    """Required pipeline tracks from ``tracks.yaml`` (distinct from ``sheaf_track_count``)."""
    tracks_path = project_root / "tracks.yaml"
    if not tracks_path.is_file():
        return 0
    raw = yaml.safe_load(tracks_path.read_text(encoding="utf-8")) or {}
    tracks = raw.get("tracks") or []
    return sum(1 for track in tracks if track.get("required", True))


def _gnn_spec_version(project_root: Path) -> str:
    path = project_root / "gnn" / "bernoulli_toy.gnn.md"
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines):
        if line.strip() != "## GNNVersionAndFlags":
            continue
        for follow in lines[idx + 1 :]:
            text = follow.strip()
            if not text:
                continue
            return text
    return ""


def generate_variables(project_root: Path, *, require_analysis_outputs: bool = True) -> dict[str, Any]:
    root = project_root.resolve()
    hp = load_hyperparameters()
    pymdp_cfg = load_pymdp_config(root)
    sweep_path = root / "output" / "data" / "parameter_sweep.csv"
    si_summary = root / "output" / "data" / "si_tmaze_summary.json"
    stats_path = root / "output" / "data" / "analysis_statistics.json"
    inv_passed, inv_total = load_invariant_counts(root)

    if require_analysis_outputs and not sweep_path.exists():
        raise FileNotFoundError(f"missing analysis artifact: {sweep_path}")

    sweep_rows = read_parameter_sweep(sweep_path)
    si_data = _load_json(si_summary)
    stats_data = _load_json(stats_path)
    policy_data = _load_json(root / "output" / "data" / "si_policy_comparison.json")
    posterior_data = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    matrices_data = _load_json(root / "output" / "data" / "si_tmaze_model_matrices.json")
    runtime_data = _load_json(root / "output" / "reports" / "pymdp_runtime_diagnostics.json")
    graph_data = _load_json(root / "output" / "data" / "si_graph_world_summary.json")
    graph_topology_traces = _load_json(root / "output" / "data" / "si_graph_world_topology_traces.json")
    provenance_data = _load_json(root / "output" / "data" / "artifact_provenance.json")
    replay_data = _load_json(root / "output" / "reports" / "reproducibility_replay.json")
    counterexample_data = _load_json(root / "output" / "reports" / "counterexample_matrix.json")
    sensitivity_data = _load_json(root / "output" / "data" / "sensitivity_sweep.json")
    uncertainty_data = _load_json(root / "output" / "data" / "uncertainty_summary.json")
    benchmark_data = _load_json(root / "output" / "data" / "toy_benchmark_matrix.json")
    model_checking_data = _load_json(root / "output" / "reports" / "model_checking_witnesses.json")
    lean_graph_data = _load_json(root / "output" / "reports" / "lean_graph_world_inventory.json")
    interop_data = _load_json(root / "output" / "data" / "interop_roundtrip_report.json")
    adversarial_data = _load_json(root / "output" / "reports" / "adversarial_audit.json")
    semantic_data = _load_json(root / "output" / "data" / "sheaf_gluing_certificate.json")
    dependency_data = _load_json(root / "output" / "data" / "validation_dependency_graph.json")
    stale_data = _load_json(root / "output" / "reports" / "stale_artifact_report.json")
    manuscript_staleness_data = _load_json(root / "output" / "reports" / "manuscript_staleness_report.json")
    figure_source_data = _load_json(root / "output" / "data" / "figure_source_map.json")
    scope_data = _load_json(root / "output" / "reports" / "scope_boundary_audit.json")
    gate_index_data = _load_json(root / "output" / "data" / "validation_gate_index.json")
    section_status_data = _load_json(root / "output" / "data" / "sheaf_section_status_matrix.json")
    render_log_data = _load_json(root / "output" / "reports" / "sheaf_render_log.json")
    claim_audit_data = _load_json(root / "output" / "reports" / "claim_evidence_audit.json")
    token_provenance_data = _load_json(root / "output" / "data" / "manuscript_token_provenance.json")
    hardcoded_variable_data = _load_json(root / "output" / "reports" / "manuscript_hardcoded_variable_audit.json")
    cross_symbol_data = _load_json(root / "output" / "data" / "cross_track_symbol_table.json")
    assumption_data = _load_json(root / "output" / "data" / "analytical_assumption_index.json")
    animation_delta_data = _load_json(root / "output" / "data" / "animation_frame_deltas.json")
    replay_matrix_data = _load_json(root / "output" / "reports" / "replay_matrix.json")
    track_scope_data = _load_json(root / "output" / "data" / "track_improvement_scope.json")
    blocked_scope_data = _load_json(root / "output" / "reports" / "blocked_scope_manifest.json")
    evidence_fields_data = _load_json(root / "output" / "data" / "evidence_field_index.json")
    release_bundle_data = _load_json(root / "output" / "reports" / "release_bundle_manifest.json")
    theorem_traceability_data = _load_json(root / "output" / "data" / "theorem_traceability_matrix.json")
    artifact_diffoscope_data = _load_json(root / "output" / "reports" / "artifact_diffoscope.json")
    proof_extraction_data = _load_json(root / "output" / "data" / "proof_extraction_index.json")
    state_space_catalog_data = _load_json(root / "output" / "data" / "state_space_catalog.json")
    causal_ablation_data = _load_json(root / "output" / "data" / "causal_ablation_matrix.json")
    artifact_license_data = _load_json(root / "output" / "reports" / "artifact_license_audit.json")
    release_notes_data = _load_json(root / "output" / "reports" / "release_notes_evidence.json")
    scholarship_data = _load_json(root / "output" / "data" / "scholarship_source_matrix.json")
    divergence_data = _load_json(root / "output" / "data" / "firstprinciples" / "divergence_demo.json")
    exposure_bias_data = _load_json(root / "output" / "data" / "firstprinciples" / "exposure_bias_demo.json")
    taxonomy_data = _load_json(root / "output" / "data" / "firstprinciples" / "opd_taxonomy.json")
    correspondence_data = _load_json(root / "output" / "data" / "firstprinciples" / "correspondence_map.json")
    posterior_grid_data = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    observable_sweep_data = _load_json(root / "output" / "data" / "analytical_observable_sweep.json")
    proof_dependency_data = _load_json(root / "output" / "data" / "proof_dependency_graph.json")
    state_transition_data = _load_json(root / "output" / "data" / "state_transition_table.json")
    ablation_sensitivity_data = _load_json(root / "output" / "reports" / "ablation_sensitivity_report.json")
    release_attestation_data = _load_json(root / "output" / "reports" / "release_attestation.json")
    classroom_data = _load_json(root / "output" / "data" / "firstprinciples" / "classroom.json")
    sequential_shift_data = _load_json(root / "output" / "data" / "firstprinciples" / "sequential_shift.json")
    sequential_sensitivity_data = _load_json(
        root / "output" / "data" / "firstprinciples" / "sequential_shift_sensitivity.json"
    )
    energy_data = _load_json(root / "output" / "data" / "firstprinciples" / "energy_demo.json")
    energy_vfe_prior = energy_data.get("vfe_at_prior") or {}
    energy_efe = energy_data.get("efe") or {}
    gkd_data = _load_json(root / "output" / "data" / "firstprinciples" / "gkd_demo.json")
    gkd_gap = gkd_data.get("reverse_kl") or {}
    diversity_data = _load_json(root / "output" / "data" / "firstprinciples" / "diversity_demo.json")
    privilege_data = _load_json(root / "output" / "data" / "firstprinciples" / "privilege_sweep.json")
    privilege_levels = privilege_data.get("levels") or []
    _flat = [row for row in privilege_levels if abs(float(row.get("entropy_gap", 0.0))) <= 1e-9]
    # "Appreciable" floor: rollout float noise produces ~1e-7-nat reverse-KL
    # values at low privilege; only signals above 1e-3 nats count as detection.
    _nonzero_kl = [row for row in privilege_levels if float(row.get("mean_reverse_kl", 0.0)) > 1e-3]
    em_data = _load_json(root / "output" / "data" / "firstprinciples" / "variational_em_demo.json")
    adaptive_data = _load_json(root / "output" / "data" / "firstprinciples" / "adaptive_demo.json")
    statistics_data = _load_json(root / "output" / "data" / "firstprinciples" / "statistics_demo.json")
    statistics_ci = statistics_data.get("advantage_bootstrap_ci") or {}
    statistics_perm = statistics_data.get("paired_permutation") or {}
    empirical_data = _load_json(root / "output" / "data" / "firstprinciples" / "empirical_benchmark.json")
    empirical_gain = empirical_data.get("accuracy_gain") or {}
    empirical_replication = empirical_data.get("thinking_machines_replication") or {}
    parallel_data = _load_json(root / "output" / "data" / "firstprinciples" / "parallel_demo.json")
    exposure_gap = exposure_bias_data.get("gap") or {}
    si_stats = stats_data.get("si_tmaze") or {}
    sweep_stats = stats_data.get("sweep") or {}
    if require_analysis_outputs and not (
        "max_residual" in sweep_stats and "rmse_mi" in sweep_stats
    ):
        # Fail closed: defaulting these to 0.0 would hydrate the *strongest
        # possible* agreement claim ("residual 0") exactly when the statistics
        # artifact is missing or corrupt.
        raise KeyError(
            "analysis_statistics.json lacks sweep.max_residual / sweep.rmse_mi; "
            "rerun compute_statistics before hydrating the manuscript"
        )
    policy_summary = policy_data.get("summary") or {}
    policy_goal_by_planner = _policy_goal_counts_by_planner(policy_data)
    q_pi_rows = si_data.get("q_pi_by_step") or []
    action_probability_rows = si_data.get("action_probabilities") or []
    observations_by_modality = si_data.get("observations_by_modality") or {}
    first_action_probabilities = (
        (si_data.get("action_probabilities") or [{}])[0] if si_data.get("action_probabilities") else {}
    )
    cue_probability = float(first_action_probabilities.get("move_to_cue", 0.0) or 0.0)
    matrix_a_shapes = matrices_data.get("A_shapes") or []
    matrix_b_shapes = matrices_data.get("B_shapes") or []
    matrix_shape_summary = f"A={matrix_a_shapes}; B={matrix_b_shapes}" if matrix_a_shapes and matrix_b_shapes else ""

    mean_entropy = float(si_data.get("mean_belief_entropy", si_stats.get("entropy_mean", 0.0)))
    free_energy_summary = _free_energy_sweep_summary(hp)
    from manuscript.sheaf.counts import structural_counts

    counts = structural_counts(root)
    return {
        "project_name": root.name,
        "lambda_grid_points": hp.lambda_grid_points,
        "lambda_max": hp.lambda_max,
        "bernoulli_state_count": hp.bernoulli_state_count,
        "gnn_spec_version": _gnn_spec_version(root),
        "pymdp_horizon": pymdp_cfg.planning_horizon,
        "pymdp_profile": si_data.get("profile", pymdp_cfg.profile),
        "pymdp_planner": stats_data.get("pymdp_planner", si_data.get("planner", pymdp_cfg.planner)),
        "random_seed": pymdp_cfg.random_seed,
        "param_sweep_grid_points": len(sweep_rows) or hp.lambda_grid_points,
        "ising_mi_saturation": _ising_mi_saturation_from_sweep(sweep_rows),
        "free_energy_argmin_lambda": free_energy_summary["argmin_lambda"],
        "free_energy_mean_field_gap_max": free_energy_summary["mean_field_gap_max"],
        "free_energy_exact_target_max_abs": free_energy_summary["exact_target_max_abs"],
        "free_energy_gap_equals_mi_max_abs": free_energy_summary["gap_equals_mi_max_abs"],
        "bernoulli_ontology_term_count": len(BERNOULLI_EXPECTED_TERMS),
        "invariants_passed": inv_passed,
        "invariants_total": inv_total,
        "si_tmaze_steps": si_data.get("steps", si_stats.get("steps", 0)),
        "si_tmaze_rollout_timestep_count": si_data.get("rollout_timestep_count", 0),
        "si_tmaze_planning_horizon": si_data.get("planning_horizon", pymdp_cfg.planning_horizon),
        "si_tmaze_policy_len": si_data.get("policy_len", pymdp_cfg.policy_len),
        "si_tmaze_num_policies": si_data.get("num_policies", 0),
        "si_tmaze_profile": si_data.get("profile", pymdp_cfg.profile),
        "si_tmaze_planner": stats_data.get("pymdp_planner", si_data.get("planner", pymdp_cfg.planner)),
        "si_tmaze_config_hash": stats_data.get("pymdp_config_hash", si_data.get("config_hash", "")),
        "si_tmaze_q_pi_row_count": stats_data.get("si_tmaze_q_pi_row_count", len(q_pi_rows)),
        "si_tmaze_action_probability_row_count": stats_data.get(
            "si_tmaze_action_probability_row_count", len(action_probability_rows)
        ),
        "si_tmaze_observation_modality_count": stats_data.get(
            "si_tmaze_observation_modality_count", len(observations_by_modality)
        ),
        "si_tmaze_mean_belief_entropy": mean_entropy,
        "si_tmaze_mean_belief_entropy_formatted": f"{mean_entropy:.4f}",
        "si_tmaze_policy_entropy_min": si_stats.get("policy_entropy_min", 0.0),
        "si_tmaze_policy_entropy_max": si_stats.get("policy_entropy_max", 0.0),
        "si_tmaze_policy_entropy_mean": si_stats.get("policy_entropy_mean", 0.0),
        "si_tmaze_policy_entropy_drop_after_cue": si_stats.get("policy_entropy_drop_after_cue", 0.0),
        "si_tmaze_policy_entropy_mean_formatted": f"{float(si_stats.get('policy_entropy_mean', 0.0)):.4f}",
        "si_tmaze_policy_entropy_drop_after_cue_formatted": (
            f"{float(si_stats.get('policy_entropy_drop_after_cue', 0.0)):.4f}"
        ),
        "si_goal_reached": int(bool(si_data.get("goal_reached", si_stats.get("goal_reached", False)))),
        "si_action_diversity": si_data.get("action_diversity", si_stats.get("action_diversity", 0)),
        "si_tree_available": int(bool(si_data.get("tree_available", False))),
        "si_tree_known_max_node_warning_count": (si_data.get("expected_known_warnings") or {}).get("tree_max_nodes", 0),
        "si_tmaze_first_action_cue_probability": cue_probability,
        "si_tmaze_initial_selected_action_name": si_stats.get("initial_selected_action_name", ""),
        "si_tmaze_initial_cue_probability_from_stats": si_stats.get("initial_cue_probability", cue_probability),
        "si_tmaze_cue_observed_step": si_stats.get("cue_observed_step", ""),
        "si_tmaze_reward_observed_step": si_stats.get("reward_observed_step", ""),
        "si_tmaze_cue_before_reward": si_stats.get("cue_before_reward", False),
        "si_tmaze_action_space_count": len((matrices_data.get("labels") or {}).get("actions") or {}),
        "si_tmaze_location_state_count": 5,
        "si_tmaze_reward_location_state_count": 2,
        "si_tmaze_matrix_shape_summary": matrix_shape_summary,
        "si_tmaze_A_shapes": matrix_a_shapes,
        "si_tmaze_B_shapes": matrix_b_shapes,
        "si_tmaze_cue_validity": (matrices_data.get("environment") or {}).get(
            "cue_validity", pymdp_cfg.environment.cue_validity
        ),
        "si_tmaze_reward_condition": (matrices_data.get("environment") or {}).get(
            "reward_condition", pymdp_cfg.environment.reward_condition
        ),
        "si_entropy_min": si_stats.get("entropy_min", 0.0),
        "si_entropy_max": si_stats.get("entropy_max", 0.0),
        "sweep_max_residual": sweep_stats.get("max_residual", 0.0),
        "sweep_rmse_mi": sweep_stats.get("rmse_mi", 0.0),
        "pymdp_config_hash": stats_data.get("pymdp_config_hash", si_data.get("config_hash", "")),
        "si_policy_comparison_run_count": policy_summary.get("run_count", 0),
        "si_policy_comparison_goal_reached_count": policy_summary.get("goal_reached_count", 0),
        "si_policy_comparison_vanilla_role": policy_summary.get("vanilla_role", "comparison_only"),
        "si_policy_comparison_si_goal_count": policy_goal_by_planner["sophisticated_inference"],
        "si_policy_comparison_vanilla_goal_count": policy_goal_by_planner["vanilla"],
        "si_policy_comparison_state_goal_count": 0,
        "si_policy_comparison_policy_goal_count": policy_goal_by_planner["sophisticated_inference"],
        "si_policy_comparison_complete_grid": int(bool(policy_summary.get("complete_grid", False))),
        "si_policy_efe_rows_explained": int(bool(policy_summary.get("all_efe_rows_explained", False))),
        "pymdp_policy_posterior_row_count": posterior_data.get("row_count", 0),
        "pymdp_policy_posterior_available_count": posterior_data.get("available_row_count", 0),
        "pymdp_policy_posteriors_normalized": int(
            bool(posterior_data.get("all_available_posteriors_normalized", False))
        ),
        "pymdp_runtime_known_warning_count": runtime_data.get("known_warning_count", 0),
        "pymdp_runtime_unexpected_warning_count": runtime_data.get("unexpected_warning_count", 0),
        "pymdp_runtime_construction_count": runtime_data.get("construction_count", 0),
        "si_graph_world_steps": graph_data.get("steps", 0),
        "si_graph_world_node_count": graph_data.get("node_count", 0),
        "si_graph_world_goal_reached": int(bool(graph_data.get("goal_reached", False))),
        "si_graph_world_topology_trace_count": graph_topology_traces.get("topology_count", 0),
        "si_graph_world_topology_traces_agree": int(bool(graph_topology_traces.get("all_trace_summary_agree", False))),
        "validation_spine_artifact_count": provenance_data.get("artifact_count", 0),
        "provenance_seeded_count": sum(
            1
            for row in (provenance_data.get("artifacts") or {}).values()
            if isinstance(row.get("deterministic_seed"), int) and row.get("config_digest")
        ),
        "provenance_all_seeded": bool(provenance_data.get("all_seeded", False)),
        "provenance_all_config_digests": bool(provenance_data.get("all_config_digests", False)),
        "provenance_all_source_commits": bool(provenance_data.get("all_source_commits", False)),
        "reproducibility_check_count": replay_data.get("check_count", 0),
        "reproducibility_all_passed": int(bool(replay_data.get("all_passed", False))),
        "counterexample_count": counterexample_data.get("counterexample_count", 0),
        "counterexample_all_known_bad_fail": int(
            bool(counterexample_data.get("all_expected_failures_observed", False))
        ),
        "sensitivity_cell_count": sensitivity_data.get("row_count", 0),
        "sensitivity_complete_grid": bool(sensitivity_data.get("complete_grid", False)),
        "analytical_assumption_count": assumption_data.get("row_count", 0),
        "analytical_equation_count": len(assumption_data.get("equation_ids") or []),
        "analytical_assumptions_indexed": bool(assumption_data.get("all_equations_indexed", False)),
        "uncertainty_row_count": uncertainty_data.get("row_count", 0),
        "uncertainty_all_normalized": bool(uncertainty_data.get("all_normalized", False)),
        "benchmark_model_count": len(benchmark_data.get("models") or []),
        "benchmark_all_models_complete": bool(benchmark_data.get("all_models_complete", False)),
        "model_checking_witness_count": model_checking_data.get("witness_count", 0),
        "model_checking_all_passed": bool(model_checking_data.get("all_passed", False)),
        "lean_graph_world_topology_witness_count": sum(
            1 for row in lean_graph_data.get("rows", []) if row.get("kind") == "topology"
        ),
        "lean_graph_world_all_topologies_witnessed": bool(lean_graph_data.get("all_topologies_witnessed", False)),
        "interop_check_count": interop_data.get("check_count", 0),
        "interop_all_lossless": bool(interop_data.get("all_lossless", False)),
        "adversarial_audit_count": adversarial_data.get("audit_count", 0),
        "adversarial_audit_all_documented": bool(adversarial_data.get("all_expected_failures_documented", False)),
        "adversarial_known_bad_passed": adversarial_data.get("known_bad_rows_passed", 0),
        "animation_delta_count": animation_delta_data.get("delta_count", 0),
        "animation_deltas_all_nonzero": bool(animation_delta_data.get("all_nonzero", False)),
        "semantic_restriction_count": len(semantic_data.get("restrictions") or {}),
        "semantic_ok": bool(semantic_data.get("ok", False)),
        "dependency_edge_type_count": len(dependency_data.get("edge_types") or []),
        "dependency_edge_types_ok": bool(dependency_data.get("all_required_edge_types_present", False)),
        "stale_artifact_fresh_count": sum(1 for row in stale_data.get("rows") or [] if row.get("fresh")),
        "stale_artifact_all_fresh": bool(stale_data.get("all_fresh", False)),
        "manuscript_staleness_row_count": manuscript_staleness_data.get("row_count", 0),
        "manuscript_staleness_all_fresh": bool(manuscript_staleness_data.get("all_fresh", False)),
        "figure_source_coverage_count": sum(1 for row in figure_source_data.get("rows") or [] if row.get("mapped")),
        "figure_source_all_mapped": bool(figure_source_data.get("all_figures_mapped", False)),
        "scope_boundary_status": "toy_only_pass" if scope_data.get("all_current_claims_toy") else "scope_leak",
        "validation_gate_index_count": gate_index_data.get("gate_count", 0),
        "sheaf_section_status_cell_count": section_status_data.get("cell_count", 0),
        "sheaf_section_status_bound_count": section_status_data.get("bound_cell_count", 0),
        "sheaf_section_status_validated_count": section_status_data.get("validated_cell_count", 0),
        "sheaf_section_status_missing_count": section_status_data.get("missing_required_count", 0),
        "sheaf_section_status_fully_sheafed_count": section_status_data.get("fully_sheafed_section_count", 0),
        "sheaf_section_status_composable_count": section_status_data.get("composable_section_count", 0),
        "sheaf_section_status_all_bound_present": bool(section_status_data.get("all_bound_fragments_present", False)),
        "sheaf_render_log_event_count": render_log_data.get("event_count", 0),
        "sheaf_render_log_all_events_ok": bool(render_log_data.get("all_events_ok", False)),
        "claim_evidence_audit_count": claim_audit_data.get("claim_count", 0),
        "token_provenance_count": token_provenance_data.get("token_count", 0),
        "hardcoded_variable_guarded_count": hardcoded_variable_data.get("guarded_token_count", 0),
        "hardcoded_variable_issue_count": hardcoded_variable_data.get("issue_count", 0),
        "hardcoded_variables_all_auto_injected": bool(hardcoded_variable_data.get("all_values_auto_injected", False)),
        "cross_track_symbol_count": cross_symbol_data.get("symbol_count", 0),
        "cross_track_symbols_consistent": int(bool(cross_symbol_data.get("all_consistent", False))),
        "provenance_bundle_count": provenance_data.get("bundle_count", 0),
        "provenance_bundle_complete": bool(provenance_data.get("all_bundles_complete", False)),
        "replay_matrix_check_count": replay_matrix_data.get("check_count", replay_matrix_data.get("row_count", 0)),
        "replay_matrix_row_count": replay_matrix_data.get("row_count", replay_matrix_data.get("check_count", 0)),
        "replay_matrix_all_replayed": bool(replay_matrix_data.get("all_replayed", False)),
        "replay_matrix_all_matched": bool(replay_matrix_data.get("all_replay_rows_matched", False)),
        "uncertainty_bin_count": uncertainty_data.get("bin_count", 0),
        "track_improvement_row_count": track_scope_data.get("improvement_row_count", 0),
        "track_improvement_all_live_valid": bool(track_scope_data.get("all_live_tracks_valid", False)),
        "blocked_scope_status": "blocked" if blocked_scope_data.get("all_blocked") else "scope_leak",
        "evidence_field_count": evidence_fields_data.get("field_count", 0),
        "evidence_fields_mapped": bool(evidence_fields_data.get("all_fields_mapped", False)),
        "release_bundle_artifact_count": release_bundle_data.get("artifact_count", 0),
        "release_bundle_sources_present": bool(release_bundle_data.get("all_required_sources_present", False)),
        "theorem_traceability_row_count": theorem_traceability_data.get("row_count", 0),
        "theorem_traceability_linked": bool(theorem_traceability_data.get("all_theorems_linked", False)),
        "artifact_diffoscope_row_count": artifact_diffoscope_data.get("row_count", 0),
        "artifact_diffoscope_all_equal": bool(artifact_diffoscope_data.get("all_equal", False)),
        "proof_extraction_theorem_count": proof_extraction_data.get("theorem_count", 0),
        "proof_extraction_all_constructive": bool(proof_extraction_data.get("all_constructive", False)),
        "state_space_catalog_row_count": state_space_catalog_data.get("row_count", 0),
        "state_space_catalog_all_finite": bool(state_space_catalog_data.get("all_finite", False)),
        "causal_ablation_row_count": causal_ablation_data.get("row_count", 0),
        "causal_ablation_complete_grid": bool(causal_ablation_data.get("complete_grid", False)),
        "artifact_license_row_count": artifact_license_data.get("row_count", 0),
        "artifact_license_all_safe": bool(artifact_license_data.get("all_license_safe", False)),
        "release_notes_row_count": release_notes_data.get("row_count", 0),
        "release_notes_source_backed": bool(release_notes_data.get("all_notes_source_backed", False)),
        "scholarship_source_count": scholarship_data.get("source_count", 0),
        "scholarship_method_role_count": scholarship_data.get("method_role_count", 0),
        "scholarship_source_family_count": scholarship_data.get("source_family_count", 0),
        "scholarship_primary_source_count": scholarship_data.get("primary_source_count", 0),
        "scholarship_sources_connected": bool(scholarship_data.get("all_sources_connected", False)),
        "opd_taxonomy_method_count": taxonomy_data.get("method_count", 0),
        "opd_taxonomy_on_policy_count": taxonomy_data.get("on_policy_count", 0),
        "opd_taxonomy_privileged_info_count": taxonomy_data.get("privileged_info_count", 0),
        "correspondence_row_count": correspondence_data.get("row_count", 0),
        "posterior_grid_row_count": posterior_grid_data.get("row_count", 0),
        "posterior_grid_available_count": posterior_grid_data.get("available_row_count", 0),
        "observable_sweep_row_count": observable_sweep_data.get("row_count", 0),
        "observable_sweep_max_residual": float(observable_sweep_data.get("max_abs_residual", 0.0)),
        "rederived_aggregate_rule_count": _rederived_aggregate_rule_count(),
        "divergence_reverse_kl": divergence_data.get("reverse_kl", 0.0),
        "divergence_forward_kl": divergence_data.get("forward_kl", 0.0),
        "divergence_jensen_shannon": divergence_data.get("jensen_shannon", 0.0),
        "divergence_clipped_reverse_kl": divergence_data.get("clipped_reverse_kl", 0.0),
        "divergence_alpha_0_5": divergence_data.get("alpha_divergence_0_5", 0.0),
        "exposure_bias_terminal_gap": exposure_gap.get("terminal_gap", 0.0),
        "exposure_bias_on_policy_final": exposure_gap.get("on_policy_final", 0.0),
        "exposure_bias_off_policy_final": exposure_gap.get("off_policy_final", 0.0),
        "energy_complexity": float(energy_vfe_prior.get("complexity", 0.0)),
        "energy_accuracy": float(energy_vfe_prior.get("accuracy", 0.0)),
        "energy_log_evidence": float(energy_data.get("log_evidence", 0.0)),
        "efe_risk": float(energy_efe.get("risk", 0.0)),
        "efe_ambiguity": float(energy_efe.get("ambiguity", 0.0)),
        "efe_epistemic": float(energy_efe.get("epistemic_value", 0.0)),
        "efe_pragmatic": float(energy_efe.get("pragmatic_value", 0.0)),
        "gkd_on_policy_loss": float(gkd_gap.get("on_policy_loss", 0.0)),
        "gkd_off_policy_loss": float(gkd_gap.get("off_policy_loss", 0.0)),
        "gkd_exposure_gap": float(gkd_gap.get("exposure_gap", 0.0)),
        "privilege_sweep_level_count": len(privilege_levels),
        "privilege_sweep_student_cue_validity": privilege_data.get("student_cue_validity", 0.0),
        "privilege_sweep_baseline_gap": float(privilege_data.get("baseline_gap") or 0.0),
        "privilege_sweep_gap_rank_correlation": float(privilege_data.get("gap_rank_correlation", 0.0)),
        "privilege_sweep_last_flat_validity": (
            max(float(row["teacher_cue_validity"]) for row in _flat) if _flat else 0.0
        ),
        "privilege_sweep_top_validity": (
            float(privilege_levels[-1]["teacher_cue_validity"]) if privilege_levels else 0.0
        ),
        "privilege_sweep_top_gap": float(privilege_levels[-1]["entropy_gap"]) if privilege_levels else 0.0,
        "privilege_sweep_top_kl": float(privilege_levels[-1]["mean_reverse_kl"]) if privilege_levels else 0.0,
        "privilege_sweep_first_nonzero_validity": (
            float(_nonzero_kl[0]["teacher_cue_validity"]) if _nonzero_kl else 0.0
        ),
        "privilege_sweep_first_nonzero_kl": float(_nonzero_kl[0]["mean_reverse_kl"]) if _nonzero_kl else 0.0,
        "diversity_sharpest_pass_at_k": float(diversity_data.get("sharpest_pass_at_k", 0.0)),
        "diversity_flattest_pass_at_k": float(diversity_data.get("flattest_pass_at_k", 0.0)),
        "diversity_greedy_pass_at_1": float(diversity_data.get("greedy_pass_at_1", 0.0)),
        "em_iterations": int(em_data.get("iterations", 0)),
        "em_final_gap": float(em_data.get("final_gap_to_target", 0.0)),
        "em_monotone_descent": bool(em_data.get("monotone_descent", False)),
        "adaptive_reverse_fraction": float(adaptive_data.get("reverse_fraction", 0.0)),
        "adaptive_total": float(adaptive_data.get("adaptive_total", 0.0)),
        "statistics_advantage_ci_low": float(statistics_ci.get("ci_low", 0.0)),
        "statistics_advantage_ci_high": float(statistics_ci.get("ci_high", 0.0)),
        "statistics_advantage_point": float(statistics_ci.get("point", 0.0)),
        "statistics_cohens_d": float(statistics_data.get("cohens_d_student_minus_teacher", 0.0)),
        "statistics_permutation_p": float(statistics_perm.get("p_value", 1.0)),
        "statistics_sample_size": int(statistics_data.get("sample_size", statistics_perm.get("n", 0)) or 0),
        "statistics_permutation_count": int(statistics_perm.get("n_perm", 0) or 0),
        "statistics_paired_test": statistics_data.get("paired_test", ""),
        "statistics_pair_deltas": ", ".join(
            f"{float(v):+.3f}" for v in (statistics_data.get("paired_difference") or [])
        ),
        "statistics_effect_size": statistics_data.get("effect_size", ""),
        "statistics_claim_scope": statistics_data.get("claim_scope", ""),
        "empirical_opd_aime24": float(empirical_data.get("opd_aime24", 0.0)),
        "empirical_rl_aime24": float(empirical_data.get("rl_aime24", 0.0)),
        "empirical_opd_gpu_hours": float(empirical_data.get("opd_gpu_hours", 0.0) or 0.0),
        "empirical_rl_gpu_hours": float(empirical_data.get("rl_gpu_hours", 0.0) or 0.0),
        "empirical_compute_reduction": float(empirical_data.get("compute_reduction_factor", 0.0)),
        "empirical_aime24_gain_over_rl": float(empirical_gain.get("aime24_over_rl", 0.0)),
        "empirical_direct_bibkey": empirical_data.get("direct_bibkey", empirical_data.get("bibkey", "")),
        "empirical_relay_bibkey": empirical_data.get("relayed_by_bibkey", ""),
        "empirical_tm_replication_aime24": float(empirical_replication.get("aime24_accuracy", 0.0)),
        "empirical_tm_replication_steps": int(empirical_replication.get("training_steps", 0) or 0),
        "empirical_tm_efficiency_min": float(empirical_replication.get("efficiency_range_min", 0.0)),
        "empirical_tm_efficiency_max": float(empirical_replication.get("efficiency_range_max", 0.0)),
        "qwen_table_number": 21,
        "parallel_max_abs_difference": float(parallel_data.get("max_abs_difference", 0.0)),
        "parallel_student_free_energy": float(parallel_data.get("student_free_energy", 0.0)),
        "parallel_neg_log_evidence": float(parallel_data.get("neg_log_evidence", 0.0)),
        "parallel_frameworks_agree": bool(parallel_data.get("frameworks_agree", False)),
        "parallel_opt_learning_rate": float((parallel_data.get("optimizer") or {}).get("learning_rate", 0.0)),
        "parallel_opt_max_steps": int((parallel_data.get("optimizer") or {}).get("max_steps", 0)),
        "parallel_opt_stop_tolerance": float((parallel_data.get("optimizer") or {}).get("stop_tolerance", 0.0)),
        "classroom_teacher_cue_validity": classroom_data.get("teacher_cue_validity", 0.0),
        "classroom_student_cue_validity": classroom_data.get("student_cue_validity", 0.0),
        "classroom_teacher_belief_entropy": classroom_data.get("teacher_mean_belief_entropy", 0.0),
        "classroom_student_belief_entropy": classroom_data.get("student_mean_belief_entropy", 0.0),
        "classroom_teacher_belief_entropy_formatted": f"{float(classroom_data.get('teacher_mean_belief_entropy', 0.0)):.3f}",
        "classroom_student_belief_entropy_formatted": f"{float(classroom_data.get('student_mean_belief_entropy', 0.0)):.3f}",
        "classroom_mean_reverse_kl": classroom_data.get("mean_reverse_kl", 0.0),
        "classroom_mean_forward_kl": classroom_data.get("mean_forward_kl", 0.0),
        "classroom_mean_jensen_shannon": classroom_data.get("mean_jensen_shannon", 0.0),
        "classroom_mean_reverse_kl_formatted": f"{float(classroom_data.get('mean_reverse_kl', 0.0)):.2f}",
        "classroom_step_count": len(classroom_data.get("per_step") or []),
        "classroom_agreement_count": sum(1 for row in classroom_data.get("per_step") or [] if row.get("agreement")),
        "classroom_privileged_advantage": bool(classroom_data.get("privileged_advantage", False)),
        "classroom_teacher_goal_reached": str(bool(classroom_data.get("teacher_goal_reached", False))).lower(),
        "classroom_student_goal_reached": str(bool(classroom_data.get("student_goal_reached", False))).lower(),
        "sequential_shift_state_count": int(sequential_shift_data.get("state_count", 0) or 0),
        "sequential_shift_action_count": int(sequential_shift_data.get("action_count", 0) or 0),
        "sequential_shift_horizon": int(sequential_shift_data.get("horizon", 0) or 0),
        "sequential_shift_mass": float(sequential_shift_data.get("shift_mass", 0.0)),
        "sequential_train_loss": float(sequential_shift_data.get("train_loss", 0.0)),
        "sequential_test_loss_before": float(sequential_shift_data.get("test_loss_before", 0.0)),
        "sequential_test_loss_after": float(sequential_shift_data.get("test_loss_after", 0.0)),
        "sequential_gap_closed": float(sequential_shift_data.get("gap_closed", 0.0)),
        "sequential_shift_ok": bool(sequential_shift_data.get("ok", False)),
        "sequential_sensitivity_row_count": int(sequential_sensitivity_data.get("row_count", 0) or 0),
        "sequential_sensitivity_baseline_loss": float(
            sequential_sensitivity_data.get("baseline_test_loss", 0.0)
        ),
        "sequential_sensitivity_final_loss": float(sequential_sensitivity_data.get("final_test_loss", 0.0)),
        "sequential_sensitivity_test_loss_reduction": float(
            sequential_sensitivity_data.get("test_loss_reduction", 0.0)
        ),
        "sequential_sensitivity_baseline_shift": float(
            sequential_sensitivity_data.get("baseline_shift_mass", 0.0)
        ),
        "sequential_sensitivity_final_shift": float(sequential_sensitivity_data.get("final_shift_mass", 0.0)),
        "sequential_sensitivity_shift_reduction": float(
            sequential_sensitivity_data.get("shift_mass_reduction", 0.0)
        ),
        "sequential_sensitivity_ok": bool(sequential_sensitivity_data.get("ok", False)),
        "proof_dependency_edge_count": proof_dependency_data.get("edge_count", 0),
        "proof_dependency_all_resolved": bool(proof_dependency_data.get("all_edges_resolved", False)),
        "state_transition_row_count": state_transition_data.get("row_count", 0),
        "state_transition_all_covered": bool(state_transition_data.get("all_reachable_states_covered", False)),
        "ablation_sensitivity_row_count": ablation_sensitivity_data.get("row_count", 0),
        "ablation_sensitivity_source_backed": bool(ablation_sensitivity_data.get("all_effects_source_backed", False)),
        "release_attestation_row_count": release_attestation_data.get("row_count", 0),
        "release_attestation_all_attested": bool(release_attestation_data.get("all_attested", False)),
        "pipeline_track_count": _pipeline_track_count(root),
        **counts,
    }
