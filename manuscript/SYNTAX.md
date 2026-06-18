# Manuscript Syntax Reference (active_inference_on_policy_distillation)

Project overlay on [`docs/guides/manuscript-semantics.md`](../../../../template/docs/guides/manuscript-semantics.md). Composed sections come from `manuscript/sections/imrad/` via `scripts/compose_manuscript.py`; edit fragments and [`manuscript/sheaf/manifest.yaml`](sheaf/manifest.yaml), not numbered `02_*.md` … `16_*.md` outputs.

## Equation labels

| Label | Summary | Fragment |
| --- | --- | --- |
| `{#eq:entangled_joint}` | $q_\lambda(\pi) \propto E(\pi)\exp(\lambda J(\pi))$ | `sections/imrad/methods_analytical/formalism.md` |
| `{#eq:coverage_cell}` | $B(s,t) \in \{\mathrm{P}, \text{--}, \mathrm{M}\}$ | `sections/imrad/methods_sheaf/formalism.md` |
| `{#eq:appendix_track_count}` | $|\mathcal{T}_{\mathrm{Full}}|$ | `sections/imrad/appendix_full_sheaf/formalism.md` |

Reference with `[@eq:label]` in prose. Do not duplicate display equations across sections; cite the defining equation instead (see `results_mi_sweep/formalism.md`).

## Section labels

Composed H1 headings use `{#sec:<manifest_id>}`. IMRAD group dividers (`Introduction`, `Methods`, …) are unnumbered LaTeX `\section*` blocks injected at compose time.

| Output file | Section | Label |
| --- | --- | --- |
| `00_abstract.md` | Abstract | `{#sec:abstract}` |
| `00_00_sheaf_coverage.md` | Sheaf Track Coverage | `{#sec:sheaf_coverage}` |
| `02_intro_motivation.md` | Motivation and scope | `{#sec:intro_motivation}` |
| `03_intro_contributions.md` | Contributions | `{#sec:intro_contributions}` |
| `05_methods_analytical.md` | Bernoulli–Ising analytical model | `{#sec:methods_analytical}` |
| `06_methods_pymdp.md` | pymdp simulation harness | `{#sec:methods_pymdp}` |
| `07_methods_lean.md` | Lean formalization boundary | `{#sec:methods_lean}` |
| `19_supplement_reproducibility.md` | Supplement: reproducibility methodology | `{#sec:methods_sheaf}` |
| `10_results_mi_sweep.md` | Mutual-information parameter sweep | `{#sec:results_mi_sweep}` |
| `11_results_free_energy.md` | Free-energy decomposition | `{#sec:results_free_energy}` |
| `12_results_si_tmaze.md` | T-maze sophisticated inference | `{#sec:results_si_tmaze}` |
| `20_supplement_validation_statistics.md` | Supplement: validation invariants | `{#sec:results_invariants}` |
| `15_discussion_outlook.md` | Limitations and outlook | `{#sec:discussion_outlook}` |
| `18_supplement_full_coverage.md` | Appendix: full track coverage | `{#sec:appendix_full_sheaf}` |
| `17_conclusion.md` | Conclusion | `{#sec:conclusion}` |

## Figures

Section figures are registry-backed via `figures.yaml` and `section_figures` renderers. `render_figure_markdown()` emits pandoc-crossref labels `{#fig:<registry-id> width=…%}`. Reference with `[@fig:<registry-id>]` in prose (use the ids from the table below, not literal placeholders).

### Figure label registry

| Registry label / placement | PNG filename | Generator (`src/visualizations/`) |
| --- | --- | --- |
| `{#fig:ising_mi_curve}` | `ising_mi_curve.png` | `figures.figure_ising_mi_curve` |
| `{#fig:free_energy_curve}` | `free_energy_curve.png` | `figures.figure_free_energy_curve` |
| `{#fig:distillation_divergence_geometry}` | `distillation_divergence_geometry.png` | `figures.figure_distillation_divergence_geometry` |
| `{#fig:exposure_bias_recovery}` | `exposure_bias_recovery.png` | `figures.figure_exposure_bias_recovery` |
| `{#fig:active_selection_landscape}` | `active_selection_landscape.png` | `figures.figure_active_selection_landscape` |
| `{#fig:si_bridge_match}` | `si_bridge_match.png` | `figures.figure_si_bridge_match` |
| `{#fig:si_belief_entropy_trajectory}` | `si_belief_entropy_trajectory.png` | `figures.figure_si_belief_entropy_trajectory` |
| `{#fig:opd_reader_map}` | `opd_reader_map.png` | `figures_intro.figure_opd_reader_map` |
| `{#fig:opd_situational_awareness}` | `opd_situational_awareness.png` | `figures_intro.figure_opd_situational_awareness` |
| `{#fig:si_belief_entropy_curve}` | `si_belief_entropy_curve.png` | `figures.figure_si_belief_entropy_curve` |
| `{#fig:si_obs_action_trace}` | `si_obs_action_trace.png` | `figures.figure_si_obs_action_trace` |
| `{#fig:si_tmaze_actions}` | `si_tmaze_actions.png` | `figures.figure_si_tmaze_actions` |
| `{#fig:si_tmaze_model_matrices}` | `si_tmaze_model_matrices.png` | `figures.figure_si_tmaze_model_matrices` |
| `{#fig:classroom_distillation_signal}` | `classroom_distillation_signal.png` | `figures.figure_classroom_distillation_signal` |
| `{#fig:sequential_shift_recovery}` | `sequential_shift_recovery.png` | `figures.figure_sequential_shift_recovery` |
| `{#fig:sequential_shift_sensitivity}` | `sequential_shift_sensitivity.png` | `figures.figure_sequential_shift_sensitivity` |
| `{#fig:energy_decomposition}` | `energy_decomposition.png` | `figures.figure_energy_decomposition` |
| `{#fig:parallel_convergence}` | `parallel_convergence.png` | `figures.figure_parallel_convergence` |
| `{#fig:diversity_tradeoff}` | `diversity_tradeoff.png` | `figures.figure_diversity_tradeoff` |
| `{#fig:privilege_dose_response}` | `privilege_dose_response.png` | `figures.figure_privilege_dose_response` |
| `{#fig:correspondence_map}` | `correspondence_map.png` | `figures_interpretability.figure_correspondence_map` |
| `{#fig:policy_posterior_grid}` | `policy_posterior_grid.png` | `figures_interpretability.figure_policy_posterior_grid` |
| `{#fig:opd_taxonomy_landscape}` | `opd_taxonomy_landscape.png` | `figures_interpretability.figure_opd_taxonomy_landscape` |
| `{#fig:invariant_dashboard}` | `invariant_dashboard.png` | `figures_diagrams.figure_invariant_dashboard` |
| `{#fig:tmaze_schematic}` | `tmaze_schematic.png` | `figures_diagrams.figure_tmaze_schematic` |
| `{#fig:multi_track_architecture}` | `multi_track_architecture.png` | `figures_diagrams.figure_multi_track_architecture` |
| `{#fig:lean_boundary_status}` | `lean_boundary_status.png` | `figures_diagrams.figure_lean_boundary_status` |
| `{#fig:gnn_ontology_concordance}` | `gnn_ontology_concordance.png` | `figures_diagrams.figure_gnn_ontology_concordance` |
| `{#fig:sheaf_coverage_heatmap}` | `sheaf_coverage_heatmap.png` | `figures_sheaf.figure_sheaf_coverage_heatmap` |
| `{#fig:sheaf_layers_overview}` | `sheaf_layers_overview.png` | `figures_sheaf.figure_sheaf_layers_overview` |
| `{#fig:semantic_gluing_graph}` | `semantic_gluing_graph.png` | `figures.figure_semantic_gluing_graph` |
| `{#fig:theorem_traceability_graph}` | `theorem_traceability_graph.png` | `figures.figure_theorem_traceability_graph` |
| `{#fig:causal_ablation_heatmap}` | `causal_ablation_heatmap.png` | `figures.figure_causal_ablation_heatmap` |
| `{#fig:scholarship_source_map}` | `scholarship_source_map.png` | `figures.figure_scholarship_source_map` |
| `front_matter.graphical_abstract` | `graphical_abstract.png` | `figures.figure_graphical_abstract` |

Section bindings live in `figures.yaml` → `section_figures` (e.g. `results_invariants` → Figure 5 `invariant_dashboard`). Set `labeled: false` only when a repeated embedding is necessary; prefer one canonical occurrence for result figures such as `ising_mi_curve`.

## {{TOKEN}} substitution

Run-derived counts (`{{coverage_*}}`, `{{invariants_*}}`, sweep and pymdp tokens) are hydrated from `output/data/manuscript_variables.json` via `scripts/z_generate_manuscript_variables.py`. See [`src/manuscript/AGENTS.md`](../src/manuscript/AGENTS.md).
