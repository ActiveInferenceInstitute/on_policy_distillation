"""Thin facade re-exporting publication figures from track-oriented modules.

The figure builders live in ``figures_analytical``, ``figures_si``,
``figures_firstprinciples``, ``figures_validation``, ``figures_diagrams`` and
``figures_sheaf``. This module re-exports every public name so existing
``from visualizations.figures import X`` call-sites keep working, and assembles
the ``FIGURE_GENERATORS`` registry plus the ``run_figure`` /
``generate_all_figures`` dispatchers.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .figure_registry import load_figure_registry
from .figures_analytical import (
    figure_energy_decomposition,
    figure_free_energy_curve,
    figure_ising_mi_curve,
)
from .figures_diagrams import (
    figure_gnn_ontology_concordance,
    figure_invariant_dashboard,
    figure_lean_boundary_status,
    figure_multi_track_architecture,
    figure_tmaze_schematic,
)
from .figures_firstprinciples import (
    figure_classroom_distillation_signal,
    figure_distillation_divergence_geometry,
    figure_diversity_tradeoff,
    figure_privilege_dose_response,
    figure_exposure_bias_recovery,
    figure_parallel_convergence,
    figure_sequential_shift_recovery,
    figure_sequential_shift_sensitivity,
)
from .figures_abstract import figure_graphical_abstract
from .figures_interpretability import (
    figure_correspondence_map,
    figure_opd_taxonomy_landscape,
    figure_policy_posterior_grid,
)
from .figures_sheaf import figure_sheaf_coverage_heatmap, figure_sheaf_layers_overview
from .figures_si import (
    figure_si_belief_entropy_curve,
    figure_si_obs_action_trace,
    figure_si_summary,
    figure_si_tmaze_actions,
    figure_si_tmaze_model_matrices,
)
from .figures_validation import (
    figure_causal_ablation_heatmap,
    figure_scholarship_source_map,
    figure_semantic_gluing_graph,
    figure_theorem_traceability_graph,
)

__all__ = [
    "FIGURE_GENERATORS",
    "figure_causal_ablation_heatmap",
    "figure_classroom_distillation_signal",
    "figure_correspondence_map",
    "figure_distillation_divergence_geometry",
    "figure_diversity_tradeoff",
    "figure_privilege_dose_response",
    "figure_energy_decomposition",
    "figure_exposure_bias_recovery",
    "figure_free_energy_curve",
    "figure_gnn_ontology_concordance",
    "figure_graphical_abstract",
    "figure_invariant_dashboard",
    "figure_ising_mi_curve",
    "figure_lean_boundary_status",
    "figure_multi_track_architecture",
    "figure_opd_taxonomy_landscape",
    "figure_parallel_convergence",
    "figure_policy_posterior_grid",
    "figure_scholarship_source_map",
    "figure_semantic_gluing_graph",
    "figure_sequential_shift_recovery",
    "figure_sequential_shift_sensitivity",
    "figure_sheaf_coverage_heatmap",
    "figure_sheaf_layers_overview",
    "figure_si_belief_entropy_curve",
    "figure_si_obs_action_trace",
    "figure_si_summary",
    "figure_si_tmaze_actions",
    "figure_si_tmaze_model_matrices",
    "figure_theorem_traceability_graph",
    "figure_tmaze_schematic",
    "generate_all_figures",
    "run_figure",
]


FIGURE_GENERATORS: dict[str, Callable[[Path], Path | None]] = {
    "ising_mi_curve": figure_ising_mi_curve,
    "free_energy_curve": figure_free_energy_curve,
    "si_belief_entropy_curve": figure_si_belief_entropy_curve,
    "si_obs_action_trace": figure_si_obs_action_trace,
    "si_tmaze_actions": figure_si_tmaze_actions,
    "si_tmaze_model_matrices": figure_si_tmaze_model_matrices,
    "distillation_divergence_geometry": figure_distillation_divergence_geometry,
    "exposure_bias_recovery": figure_exposure_bias_recovery,
    "classroom_distillation_signal": figure_classroom_distillation_signal,
    "sequential_shift_recovery": figure_sequential_shift_recovery,
    "sequential_shift_sensitivity": figure_sequential_shift_sensitivity,
    "energy_decomposition": figure_energy_decomposition,
    "parallel_convergence": figure_parallel_convergence,
    "diversity_tradeoff": figure_diversity_tradeoff,
    "privilege_dose_response": figure_privilege_dose_response,
    "correspondence_map": figure_correspondence_map,
    "policy_posterior_grid": figure_policy_posterior_grid,
    "opd_taxonomy_landscape": figure_opd_taxonomy_landscape,
    "sheaf_layers_overview": figure_sheaf_layers_overview,
    "sheaf_coverage_heatmap": figure_sheaf_coverage_heatmap,
    "invariant_dashboard": figure_invariant_dashboard,
    "tmaze_schematic": figure_tmaze_schematic,
    "multi_track_architecture": figure_multi_track_architecture,
    "lean_boundary_status": figure_lean_boundary_status,
    "gnn_ontology_concordance": figure_gnn_ontology_concordance,
    "semantic_gluing_graph": figure_semantic_gluing_graph,
    "theorem_traceability_graph": figure_theorem_traceability_graph,
    "causal_ablation_heatmap": figure_causal_ablation_heatmap,
    "scholarship_source_map": figure_scholarship_source_map,
    "graphical_abstract": figure_graphical_abstract,
}


def run_figure(figure_id: str, project_root: Path) -> Path:
    """Dispatch a registry figure id to its generator."""
    load_figure_registry(project_root)  # fail fast when registry missing
    try:
        generator = FIGURE_GENERATORS[figure_id]
    except KeyError as exc:
        raise KeyError(f"unknown figure id: {figure_id}") from exc
    result = generator(project_root)
    if result is None:
        raise RuntimeError(f"figure generator returned no path for {figure_id}")
    return result


def generate_all_figures(project_root: Path) -> list[Path]:
    from orchestration.coverage_pipeline import ensure_coverage_artifacts
    from .figure_registry import write_figure_registry_json

    json_path, _, page_path = ensure_coverage_artifacts(project_root, write_page=True)
    paths: list[Path] = [json_path]
    paths.extend(run_figure(figure_id, project_root) for figure_id in FIGURE_GENERATORS)
    paths.append(write_figure_registry_json(project_root))
    if page_path is not None:
        paths.append(page_path)
    return [path for path in paths if path is not None]
