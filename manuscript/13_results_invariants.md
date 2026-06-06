# Validation invariants and statistics {#sec:results_invariants}

<!-- sheaf-track:prose -->

Because the central claim is a formal correspondence rather than a metaphor, every quantity that instantiates the teacher--student mapping is guarded by an invariant that runs before PDF rendering ([@sec:methods_analytical]). These gates assert that the analytical free energy, the coupling-mediated mutual information $I(\lambda)$, and the reverse- versus forward-KL limits behave as the distillation objective predicts, and that the on-policy student rollout reported by the pymdp harness reproduces the privileged-information advantage. On a clean checkout **{{invariants_passed}} / {{invariants_total}}** checks pass in the merged validation report, which records the sophisticated-inference simulation invariants whenever the pymdp harness ran ([@sec:results_si_tmaze]).

[@fig:invariant_dashboard] lists each analytical and simulation gate; a failure on any correspondence check blocks publication artifacts, so a broken claim about the variational-posterior-as-student mapping cannot pass silently. See [@sec:methods_sheaf] for how these invariant counts hydrate the manuscript tokens. As with the rest of this work, the guarantees are scoped to the analytical Bernoulli--Ising model and the T-maze rollout: they certify that these minimal artifacts demonstrate the on-policy-distillation correspondence faithfully, not that the same numbers hold for production-scale language-model distillation.

Beyond the binary pass/fail gates, the privileged-information asymmetry that defines the teacher--student Markov blanket admits a quantitative inferential test. Under the correspondence, the teacher conditions its generative model on privileged context the student cannot observe, so the teacher should hold a sharper posterior --- lower belief entropy --- than the on-policy student that must generate its own observations and update from them. We measure this gap directly in the two-agent pymdp classroom as the paired difference between student and teacher belief entropy across matched rollout steps, then report it with full inferential honesty rather than a single point estimate. The privileged-teacher advantage is {{statistics_advantage_point:.3f}} nats (student minus teacher belief entropy), with a bootstrap 95% confidence interval of [{{statistics_advantage_ci_low:.3f}}, {{statistics_advantage_ci_high:.3f}}] nats. The standardized effect size is Cohen's $d = {{statistics_cohens_d:.2f}}$, and a paired permutation test of the same matched differences returns $p = {{statistics_permutation_p:.3f}}$. The sign and magnitude are the prediction the active-inference reading makes: a generative model conditioned on privileged beliefs (the teacher) resolves more uncertainty per step than a variational posterior generating its own observations (the on-policy student), exactly the Markov-blanket asymmetry that on-policy distillation exploits @zhao2026opsd. We frame these numbers as an inferential demonstration on a minimal two-agent model, not a production claim: the confidence interval and permutation $p$ characterize sampling uncertainty within this toy classroom, and the effect-size convention follows standard paired reporting @parr2022active rather than asserting that the same advantage transfers to language-model distillation @thinkingmachines2025opd.

<!-- sheaf-track:simulation -->

Simulation invariants merge into the analytical report after the pymdp harness runs ([@sec:results_si_tmaze]). [@fig:invariant_dashboard] summarizes pass/fail status for both domains on the clean tree.

<!-- sheaf-track:replay_matrix -->

The replay matrix exposes deterministic rerun comparison as table data rather than prose. It contains {{replay_matrix_row_count}} producer rows, uses explicit replay-or-fingerprint methods, and every row must match its saved artifact hash (`{{replay_matrix_all_matched}}`).

<!-- sheaf-track:sensitivity -->

The `sensitivity` fragment binds the deterministic toy sweep to the canonical sheaf track. `output/data/sensitivity_sweep.json` contains {{sensitivity_cell_count}} cells across toy parameters, planner labels, seeds, horizons, and graph topologies; the hydrated flag `{{sensitivity_complete_grid}}` is the only manuscript claim about coverage.

The companion `output/data/si_policy_grid.json` records measured policy-mode rows derived from `si_policy_comparison.json`, not a synthetic grid. Missing cells fail the artifact schema before they can become prose; the topology trace artifact contributes {{si_graph_world_topology_trace_count}} deterministic topology traces.

<!-- sheaf-track:uncertainty -->

The `uncertainty` fragment reports only normalized toy summaries. `output/data/uncertainty_summary.json` contains {{uncertainty_row_count}} belief and policy-posterior rows plus {{uncertainty_bin_count}} finite entropy bins, and `{{uncertainty_all_normalized}}` is false if any posterior row fails to sum to one within the deterministic tolerance.

Policy uncertainty is recorded in generated policy artifacts rather than hand-entered into the manuscript. The posterior grid contributes {{pymdp_policy_posterior_available_count}} available posterior rows; the EFE values artifact reports availability-or-measured-fallback flag {{si_policy_efe_rows_explained}}. The fragment is therefore a validation surface, not an empirical uncertainty claim.

<!-- sheaf-track:benchmark -->

The `benchmark` fragment adds a compact toy matrix over the Bernoulli, T-maze, and graph-world artifacts. `output/data/toy_benchmark_matrix.json` reports {{benchmark_model_count}} model rows and `{{benchmark_all_models_complete}}` only when each row names an artifact, metric, and passing gate.

The matrix is scoped to deterministic study models. It is useful as a cross-track smoke test, not as a performance benchmark for biological or deployed systems.

<!-- sheaf-track:visualization -->

![Invariant dashboard summarizing pass/fail status for every analytical and simulation check in the validation registry: {{invariants_passed}} of {{invariants_total}} merged checks pass on the combined report. These invariants are the machine-enforced correctness conditions -- conservation of probability mass, divergence non-negativity, free-energy bounds, and rollout consistency -- that bind the on-policy-distillation claims to the active-inference math. An all-green dashboard certifies that the executable evidence underwriting the manuscript actually satisfies the theory it reports.](../output/figures/invariant_dashboard.png){#fig:invariant_dashboard width=90% fig-alt="Horizontal bar checklist of analytical and simulation invariant names with pass or fail status. {{invariants_passed}} of {{invariants_total}} checks pass on the merged report."}

![The diversity-collapse tradeoff of mode-seeking distillation, evaluated over a problem ensemble. Greedy Pass@1 (dashed, {{diversity_greedy_pass_at_1:.3f}}) is temperature-invariant; sampling Pass@k falls from {{diversity_flattest_pass_at_k:.3f}} at the flattest temperature to {{diversity_sharpest_pass_at_k:.3f}} at the sharpest, because Pass@k is concave in the correct-answer mass. Aggressive reverse-KL sharpening therefore raises single-answer commitment while collapsing Pass@k -- the Pass@1-versus-Pass@k tension active inference frames as precision (inverse temperature). Source: `output/data/firstprinciples/diversity_demo.json`.](../output/figures/diversity_tradeoff.png){#fig:diversity_tradeoff width=90% fig-alt="Line plot of sampling Pass@k versus student temperature on a logarithmic x-axis, with a dashed horizontal line for the temperature-invariant greedy Pass@1. Pass@k rises with temperature and collapses toward the greedy ceiling as the student sharpens."}

<!-- sheaf-track:state_space_catalog -->

### State-space catalog track

The `state_space_catalog` track enumerates finite state spaces, action spaces,
and policy counts for the deterministic toy models. The catalog artifact is
`output/data/state_space_catalog.json`: it currently records
{{state_space_catalog_row_count}} rows, with finite-space status
`{{state_space_catalog_all_finite}}`.

<!-- sheaf-track:causal_ablation -->

### Causal ablation track

The `causal_ablation` track records deterministic toy ablations over finite
preferences, likelihood-noise settings, and graph-topology perturbations. The
matrix artifact is `output/data/causal_ablation_matrix.json`: it currently
records {{causal_ablation_row_count}} cells, with complete-grid status
`{{causal_ablation_complete_grid}}`.
