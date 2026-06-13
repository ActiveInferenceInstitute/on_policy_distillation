# Section Guide

Per-section map of the composed manuscript. For each section file: its IMRAD role,
the claim it carries, the key hydration tokens it uses (a representative subset —
see [`hydration-tokens.md`](hydration-tokens.md) for the system), and which sheaf
fragment tracks feed it. Track names are the keys declared in
[`../../manuscript/sheaf/tracks.yaml`](../../manuscript/sheaf/tracks.yaml).

Numbered files are composed outputs of
[`../../scripts/compose_manuscript.py`](../../scripts/compose_manuscript.py).
`00_abstract.md`, `17_conclusion.md`, and `99_references.md` are hand-authored.
Section labels (`{#sec:…}`) follow [`../../manuscript/SYNTAX.md`](../../manuscript/SYNTAX.md).

## The three scientific tracks

The manuscript repeatedly frames its evidence as three lanes (see
[`../../manuscript/02_intro_motivation.md`](../../manuscript/02_intro_motivation.md)):

- **Analytical** — the Bernoulli–Ising coupling oracle (closed-form MI and free energy).
- **pymdp** — the on-policy active-inference T-maze rollout and classroom.
- **Formal/publication** — Lean witnesses, sheaf composition, GNN/ontology, provenance.

The fragment tracks below are the finer-grained machinery that carries these lanes
into each section.

## Front matter

### `00_abstract.md` — `{#sec:abstract}`
- **IMRAD role:** Abstract (hand-authored).
- **Claim carried:** The full scoped thesis in miniature — teacher↔generative model
  `p(o,s)`, student↔posterior `q(s)`, per-token reverse-KL loss = variational free
  energy `F = D_KL(q‖p) − log p(o)`, on-policy rollouts = active sampling; exact only
  in the finite models studied. States the VFE/EFE separation up front.
- **Key tokens:** `{{classroom_teacher_cue_validity}}`, `{{classroom_student_cue_validity}}`,
  `{{classroom_mean_reverse_kl_formatted}}`, `{{sheaf_track_count}}`, `{{sheaf_law_count}}`,
  `{{counterexample_count}}`, `{{invariants_passed}}`, `{{invariants_total}}`,
  `{{sweep_rmse_mi:.1e}}`.
- **Feeding tracks:** prose (single hand-authored fragment; no sheaf-track markers).

### `00_00_sheaf_coverage.md` — `{#sec:sheaf_coverage}`
- **IMRAD role:** Front-matter coverage page (regenerated at compose time from
  `src/manuscript/sheaf/report.py` + `manuscript/sheaf/coverage.yaml`).
- **Claim carried:** Which fragment tracks are present/absent/missing per IMRAD row —
  the gluing record that licenses composing local fragments into one argument.
- **Key tokens:** `{{coverage_present}}`, `{{coverage_bound}}`, `{{coverage_missing}}`,
  `{{imrad_manifest_rows}}`, `{{sheaf_track_count}}`, `{{appendix_sheaf_track_count}}`.
- **Feeding tracks:** generated coverage report + `visualization` (figure `sheaf_coverage_heatmap`).

## Introduction

### `02_intro_motivation.md` — `{#sec:intro_motivation}`
- **IMRAD role:** Introduction — motivation and scope.
- **Claim carried:** The exposure-bias / induced-distribution problem motivates OPD;
  active inference's act-to-sample correction is the parallel mechanism. Names the
  model surface (Bernoulli–Ising, pymdp T-maze, classroom, graph-world; **no gridworld**)
  and scopes the thesis to formal objects, not biology or production LLMs.
- **Key tokens:** `{{sheaf_track_count}}`, `{{pipeline_track_count}}`,
  `{{si_tmaze_planning_horizon}}`, `{{si_tmaze_policy_len}}`.
- **Feeding tracks:** prose.

### `03_intro_contributions.md` — `{#sec:intro_contributions}`
- **IMRAD role:** Introduction — contributions.
- **Claim carried:** The five contributions: (1) audited correspondence map,
  (2) shared divergence geometry, (3) reward-tilted-target unification, (4) two-agent
  pymdp classroom, (5) sheaf-indexed composition. States the correspondence is exact
  only for the constructed finite objects, pinned as the Proposition in `methods_analytical`.
- **Key tokens:** `{{correspondence_row_count}}`, `{{sheaf_track_count}}`,
  `{{imrad_manifest_rows}}`, `{{appendix_sheaf_track_count}}`, `{{pipeline_track_count}}`,
  `{{validation_gate_index_count}}`, `{{token_provenance_count}}`,
  `{{hardcoded_variable_issue_count}}`, `{{classroom_*}}`,
  `{{exposure_bias_off_policy_final:.3f}}`, `{{exposure_bias_on_policy_final:.3f}}`,
  `{{exposure_bias_terminal_gap:.3f}}`.
- **Feeding tracks:** prose, visualization (figures `correspondence_map`,
  `multi_track_architecture`, `exposure_bias_recovery`), ontology.

## Methods

### `05_methods_analytical.md` — `{#sec:methods_analytical}`
- **IMRAD role:** Methods — the Bernoulli–Ising analytical model.
- **Claim carried:** The analytical core. Carries **the Proposition (scoped
  correspondence)** with assumptions A1–A4 (quoted verbatim in
  [`claims-and-scope.md`](claims-and-scope.md)), the entangled-joint
  ([`{#eq:entangled_joint}`]), closed-form MI ([`{#eq:mutual_information}`]),
  conditional entropy ([`{#eq:conditional_entropy}`]), and the two-route verification.
- **Key tokens:** `{{bernoulli_state_count}}`, `{{param_sweep_grid_points}}`,
  `{{lambda_max}}`, `{{observable_sweep_row_count}}`, `{{observable_sweep_max_residual:.1e}}`,
  `{{parallel_max_abs_difference:.1e}}`, `{{analytical_equation_count}}`,
  `{{analytical_assumption_count}}`, `{{analytical_assumptions_indexed}}`,
  `{{divergence_reverse_kl:.3f}}`, `{{divergence_forward_kl:.3f}}`,
  `{{gnn_spec_version}}`, `{{bernoulli_ontology_term_count}}`.
- **Feeding tracks:** prose, formalism, simulation, assumption_index, visualization
  (`distillation_divergence_geometry`, `gnn_ontology_concordance`), gnn, ontology.

### `06_methods_pymdp.md` — `{#sec:methods_pymdp}`
- **IMRAD role:** Methods — pymdp sophisticated-inference harness.
- **Claim carried:** The on-policy student is sophisticated inference — an agent that
  generates its own observations and minimizes **expected** free energy under a
  privileged cue. Includes the "one scenario, two frameworks" demonstration where a
  jax reverse-KL distilled student reproduces the AIF exact posterior.
- **Key tokens:** `{{pymdp_planner}}`, `{{pymdp_profile}}`, `{{si_tmaze_planning_horizon}}`,
  `{{si_tmaze_steps}}`, `{{si_tmaze_policy_len}}`, `{{si_tmaze_location_state_count}}`,
  `{{si_tmaze_reward_location_state_count}}`, `{{si_tmaze_observation_modality_count}}`,
  `{{si_tmaze_cue_validity}}`, `{{si_tmaze_matrix_shape_summary}}`,
  `{{parallel_max_abs_difference:.1e}}`, `{{parallel_frameworks_agree}}`,
  `{{parallel_student_free_energy:.3f}}`, `{{parallel_neg_log_evidence:.3f}}`,
  `{{interop_check_count}}`, `{{interop_all_lossless}}`, `{{pymdp_runtime_*}}`.
- **Feeding tracks:** prose, formalism, pymdp, interop, visualization
  (`tmaze_schematic`, `si_tmaze_model_matrices`, `parallel_convergence`), gnn, ontology.

### `07_methods_lean.md` — `{#sec:methods_lean}`
- **IMRAD role:** Methods — Lean formalization boundary.
- **Claim carried:** Lean is a **boundary layer**, not a proof of the full thesis. It
  certifies finite witnesses (Ising coupling, T-maze reachability/absorbing goal,
  graph-world reachability, finite policy enumeration, belief/policy normalization,
  positive-horizon SI) checked by `lake build`, with no `sorry`/`axiom`/`native_decide`.
- **Key tokens:** `{{proof_extraction_theorem_count}}`, `{{proof_extraction_all_constructive}}`,
  `{{model_checking_witness_count}}`, `{{model_checking_all_passed}}`,
  `{{theorem_traceability_row_count}}`, `{{theorem_traceability_linked}}`,
  `{{lean_graph_world_topology_witness_count}}`, `{{lean_graph_world_all_topologies_witnessed}}`,
  `{{si_tmaze_planning_horizon}}`.
- **Feeding tracks:** prose, visualization (`lean_boundary_status`), lean,
  model_checking, theorem_traceability, proof_extraction.

## Results

### `10_results_mi_sweep.md` — `{#sec:results_mi_sweep}`
- **IMRAD role:** Results — mutual-information parameter sweep.
- **Claim carried:** `I(λ)` is the teacher–student mutual information, rising
  monotonically; closed-form and independent exact recomputation agree to machine
  precision (a cross-implementation check, not exact zero).
- **Key tokens:** `{{param_sweep_grid_points}}`, `{{lambda_max}}`,
  `{{sweep_max_residual:.1e}}`, `{{ising_mi_saturation}}`,
  `{{free_energy_mean_field_gap_max:.3f}}`, `{{free_energy_gap_equals_mi_max_abs:.1e}}`,
  `{{free_energy_exact_target_max_abs}}`.
- **Feeding tracks:** prose, formalism, simulation, visualization (`ising_mi_curve`).

### `11_results_free_energy.md` — `{#sec:results_free_energy}`
- **IMRAD role:** Results — free-energy decomposition (incl. `{#sec:energy_decompositions}`).
- **Claim carried:** The mean-field free-energy gap equals `I(λ)`; this is the cost an
  on-policy student must close. Makes the **VFE vs EFE** split explicit: VFE =
  complexity − accuracy = the static distillation objective; EFE = risk + ambiguity =
  −(epistemic + pragmatic), the on-policy planning-side analogue.
- **Key tokens:** `{{free_energy_exact_target_max_abs:.1e}}`,
  `{{free_energy_mean_field_gap_max:.3f}}`, `{{free_energy_gap_equals_mi_max_abs:.1e}}`,
  `{{free_energy_argmin_lambda}}`, `{{ising_mi_saturation}}`,
  `{{invariants_passed}}`, `{{invariants_total}}`,
  `{{energy_complexity:.3f}}`, `{{energy_accuracy:.3f}}`, `{{energy_log_evidence:.3f}}`,
  `{{efe_risk:.3f}}`, `{{efe_ambiguity:.3f}}`, `{{efe_epistemic:.3f}}`, `{{efe_pragmatic:.3f}}`.
- **Feeding tracks:** prose, visualization (`free_energy_curve`, `energy_decomposition`).

### `12_results_si_tmaze.md` — `{#sec:results_si_tmaze}`
- **IMRAD role:** Results — T-maze sophisticated inference (the largest results section).
- **Claim carried:** The on-policy rollout sharpens its posterior because it generates
  the observations it is scored against. Privilege = differential cue reliability. The
  classroom yields a teacher/student belief-entropy gap and a mean reverse-KL signal;
  the privilege dose-response shows the entropy advantage is strongly nonlinear while
  the reverse-KL signal is the more sensitive, monotone detector above a stated noise
  floor. Four dynamic simulators (GKD, variational-EM, diversity Pass-at-k, adaptive
  divergence) plus the sequential-shift sensitivity sweep each move as the
  correspondence predicts.
- **Key tokens:** `{{pymdp_planner}}`, `{{si_tmaze_*}}` (steps, entropy, action names,
  cue/reward step, first-action prob), `{{classroom_*}}` (cue validities, entropies,
  `mean_reverse_kl_formatted`, goal-reached flags), `{{privilege_sweep_*}}`
  (level count, baseline gap, top/first-nonzero validity and KL, rank correlation),
  `{{posterior_grid_available_count}}`, `{{posterior_grid_row_count}}`,
  `{{gkd_*}}`, `{{em_*}}`, `{{diversity_*}}`, `{{adaptive_reverse_fraction:.2f}}`,
  `{{sequential_sensitivity_*}}`.
- **Feeding tracks:** prose, pymdp, visualization (`si_belief_entropy_curve`,
  `si_obs_action_trace`, `si_tmaze_actions`, `classroom_distillation_signal`,
  `sequential_shift_recovery`, `sequential_shift_sensitivity`,
  `si_tmaze_model_matrices` [labeled: false], `privilege_dose_response`,
  `policy_posterior_grid`).

## Discussion

### `15_discussion_outlook.md` — `{#sec:discussion_outlook}`
- **IMRAD role:** Discussion — limitations and outlook.
- **Claim carried:** What is demonstrated (a correspondence under verifier discipline)
  vs the limitations (toy, pedagogical, not biological/production). The OPD-vs-RL
  benchmark numbers are **literature-reported** (Qwen via Thinking Machines), not
  reproduced. Lists open problems the minimal models cannot settle.
- **Key tokens:** `{{sheaf_law_count}}`, `{{counterexample_count}}`,
  `{{opd_taxonomy_method_count}}`, `{{opd_taxonomy_on_policy_count}}`,
  `{{opd_taxonomy_privileged_info_count}}`, `{{empirical_opd_aime24:.1f}}`,
  `{{empirical_rl_aime24:.1f}}`, `{{empirical_aime24_gain_over_rl:.1f}}`,
  `{{empirical_opd_gpu_hours:.0f}}`, `{{empirical_rl_gpu_hours:.0f}}`,
  `{{empirical_compute_reduction:.1f}}`, `{{empirical_tm_replication_aime24:.0f}}`,
  `{{pymdp_planner}}`, `{{pymdp_config_hash}}`, `{{sweep_rmse_mi}}`,
  `{{coverage_present}}`/`{{coverage_bound}}`/`{{coverage_missing}}`,
  `{{release_notes_row_count}}`.
- **Feeding tracks:** prose, simulation, scholarship, visualization
  (`opd_taxonomy_landscape`), ontology, release_notes.

## Conclusion

### `17_conclusion.md` — `{#sec:conclusion}`
- **IMRAD role:** Conclusion (hand-authored).
- **Claim carried:** Restates the scoped correspondence precisely — stronger than a
  slogan, narrower than a universal theorem; external results stay external; no
  biological claim. The engineering contribution is auditability.
- **Key tokens:** `{{pymdp_planner}}`, `{{pymdp_config_hash}}`, `{{classroom_*}}`,
  `{{sweep_rmse_mi:.1e}}`, `{{invariants_passed}}`, `{{invariants_total}}`.
- **Feeding tracks:** prose (hand-authored; no sheaf-track markers).

## Appendix / Supplements

### `18_supplement_full_coverage.md` — `{#sec:appendix_full_sheaf}`
- **IMRAD role:** Appendix — full coverage and concordance (composability proof).
- **Claim carried:** The maximal appendix row binds **all** registered fragment track
  types into one flat section without per-section compose branches; tabulates the full
  VFE/EFE decomposition and supplemental concordance/benchmark tables.
- **Key tokens:** `{{appendix_sheaf_track_count}}`, `{{sheaf_track_count}}`,
  plus the energy tokens shared with `results_free_energy`.
- **Feeding tracks:** prose plus the full registered track set (the appendix is itself
  the composability proof; equation [`{#eq:appendix_track_count}`]).

### `19_supplement_reproducibility.md` — `{#sec:methods_sheaf}`
- **IMRAD role:** Supplement — reproducibility methodology (the compose/hydration contract).
- **Claim carried:** Auditable binding: where data are generated, how variables are
  hydrated, which validators run, how failed gates block the PDF. Coverage cell semantics
  ([`{#eq:coverage_cell}`]: P present, — unbound, M missing). Records compose commands.
- **Key tokens:** `{{sheaf_track_count}}`.
- **Feeding tracks:** prose, layers (generated tables), visualization
  (`sheaf_layers_overview`, `semantic_gluing_graph`, `scholarship_source_map`).

### `20_supplement_validation_statistics.md` — `{#sec:results_invariants}`
- **IMRAD role:** Supplement — validation invariants and statistics.
- **Claim carried:** Merged analytical + simulation invariant pass counts; a deliberately
  **underpowered** small-sample inferential summary of the teacher/student entropy gap
  (CI includes zero; permutation p uninformative) — reported as honesty of machinery,
  not significance. The thesis does not rest on it.
- **Key tokens:** `{{invariants_passed}}`, `{{invariants_total}}`,
  `{{statistics_sample_size}}`, `{{statistics_advantage_point:.3f}}`,
  `{{statistics_advantage_ci_low:.3f}}`, `{{statistics_advantage_ci_high:.3f}}`,
  `{{statistics_cohens_d:.2f}}`, `{{statistics_permutation_p:.3f}}`,
  `{{statistics_pair_deltas}}`, `{{statistics_claim_scope}}`,
  `{{replay_matrix_row_count}}`, `{{sensitivity_cell_count}}`.
- **Feeding tracks:** prose, simulation, replay_matrix, sensitivity, uncertainty,
  visualization (`invariant_dashboard`, `diversity_tradeoff`).

### `99_references.md`
- **IMRAD role:** References pointer (hand-authored). Points to
  [`../../manuscript/references.bib`](../../manuscript/references.bib). See
  [`citation-map.md`](citation-map.md) for the bibliography organized by function.
