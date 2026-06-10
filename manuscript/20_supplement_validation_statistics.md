# Supplementary material: validation invariants and statistics {#sec:results_invariants}

<!-- sheaf-track:prose -->

Because the central claim is a formal correspondence rather than a metaphor, every quantity that instantiates the teacher--student mapping is guarded by an invariant that runs before PDF rendering ([@sec:methods_analytical]). These gates assert that the analytical free energy, the coupling-mediated mutual information $I(\lambda)$, and the reverse- versus forward-KL limits behave as the distillation objective predicts, and that the on-policy student rollout reported by the pymdp harness reproduces the privileged-information advantage. On a clean checkout **{{invariants_passed}} / {{invariants_total}}** checks pass in the merged validation report, which records the sophisticated-inference simulation invariants whenever the pymdp harness ran ([@sec:results_si_tmaze]).

The full registry, binding-matrix, and track-status layer tables appear once, in the reproducibility supplement ([@sec:methods_sheaf]); this section reports only the validation statistics layered on top of them. [@fig:invariant_dashboard] lists each analytical and simulation gate; a failure on any correspondence check blocks publication artifacts, so a broken claim about the variational-posterior-as-student mapping cannot pass silently. This validation supplement follows the reproducibility-methodology supplement ([@sec:methods_sheaf]) because the invariant counts depend on the same hydration and source-map boundary: the numbers are generated first, injected second, and only then rendered. As with the rest of this work, the guarantees are scoped to the analytical Bernoulli--Ising model and the T-maze rollout: they certify that these minimal artifacts demonstrate the on-policy-distillation correspondence faithfully, not that the same numbers hold for production-scale language-model distillation.

Beyond the binary pass/fail gates, the privileged-information asymmetry that defines the teacher--student Markov blanket admits a quantitative inferential test. Under the correspondence, the teacher conditions its generative model on privileged context the student cannot observe, so the teacher should hold a sharper posterior --- lower belief entropy --- than the on-policy student that must generate its own observations and update from them. We measure this gap directly in the two-agent pymdp classroom: `statistics_demo.json` is derived from the per-decision belief-entropy series persisted in `classroom.json`, giving {{statistics_sample_size}} matched per-decision teacher/student pairs, and we report interval, effect size, and permutation $p$ rather than a single point estimate. By construction the mean paired difference equals the classroom's reported entropy gap. The privileged-teacher advantage is {{statistics_advantage_point:.3f}} nats (student minus teacher belief entropy), with a bootstrap 95% confidence interval of [{{statistics_advantage_ci_low:.3f}}, {{statistics_advantage_ci_high:.3f}}] nats. At this sample size the raw data say more than any interval, so we print all {{statistics_sample_size}} paired student-minus-teacher deltas directly: {{statistics_pair_deltas}} nats. The standardized effect size is Cohen's $d = {{statistics_cohens_d:.2f}}$ using {{statistics_effect_size}} [@cohen1988power], and {{statistics_paired_test}} with {{statistics_permutation_count}} seeded permutations returns $p = {{statistics_permutation_p:.3f}}$. With only {{statistics_sample_size}} matched conditions, these are descriptive inferential summaries over a deterministic toy classroom: the effect size is useful for scale, the permutation test is intentionally finite and seeded, and with {{statistics_sample_size}} pairs it is underpowered to the point of being uninformative — $p = {{statistics_permutation_p:.3f}}$ here means the test cannot distinguish this gap from sign-flip noise at all, which we state plainly rather than dressing as near-significance. The *sign* of the point estimate is the prediction the active-inference reading makes — a generative model conditioned on privileged beliefs (the teacher) should resolve more uncertainty per step than a variational posterior generating its own observations [@friston2013life; @kirchhoff2018markov; @parr2020markov_blankets_thermo; @zhao2026opsd; @jin2026entropy_opd] — and the measured mean gap is positive. We state plainly what the interval shows: at this sample size the confidence interval includes zero and the permutation test cannot reject the null, so the per-decision series demonstrates the direction of the effect and the honesty of the reporting machinery, not statistical significance. The thesis does not rest on this inferential summary: the correspondence is carried by the analytical identities, the executable models, and the deterministic mean entropy gap; this small-sample analysis is illustrative of honest reporting machinery, not confirmatory evidence. We frame these numbers as {{statistics_claim_scope}}: the confidence interval, effect size, and permutation $p$ characterize sampling uncertainty within this toy classroom rather than asserting that the same advantage transfers to language-model distillation [@qwen2025technical_report; @thinkingmachines2025opd].

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

<!-- sheaf-track:manuscript_staleness -->

The appendix `manuscript_staleness` row points to
`output/reports/manuscript_staleness_report.json`. It checks
{{manuscript_staleness_row_count}} token bindings after hydration, including late
audit variables, and the pass flag is `{{manuscript_staleness_all_fresh}}`.

This is the rendered-output side of the sheaf contract. Source fragments may
contain hydration placeholders, but the public manuscript must not; the staleness report
compares each token's generated value against the resolved markdown so stale
counts are caught after composition, not only during source-file linting.

<!-- sheaf-track:visualization -->

![Invariant dashboard summarizing pass/fail status for every analytical and simulation check in the validation registry: {{invariants_passed}} of {{invariants_total}} merged checks pass on the combined report. These invariants are the machine-enforced correctness conditions -- conservation of probability mass, divergence non-negativity, free-energy bounds, and rollout consistency -- that bind the on-policy-distillation claims to the active-inference math. An all-green dashboard certifies that the executable evidence underwriting the manuscript actually satisfies the theory it reports.](../output/figures/invariant_dashboard.png){#fig:invariant_dashboard width=90% fig-alt="Horizontal bar checklist of analytical and simulation invariant names with pass or fail status. {{invariants_passed}} of {{invariants_total}} checks pass on the merged report."}

![The diversity-collapse tradeoff of mode-seeking distillation, evaluated over a problem ensemble. Greedy Pass-at-1 (dashed, {{diversity_greedy_pass_at_1:.3f}}) is temperature-invariant; sampling Pass-at-k falls from {{diversity_flattest_pass_at_k:.3f}} at the flattest temperature to {{diversity_sharpest_pass_at_k:.3f}} at the sharpest, because $Pass@k = 1-(1-p)^k$ for independent samples. Every curve is derived analytically from the declared temperature-sharpened ensemble (closed form, no sampling): this panel is an exact calculation over the toy problem ensemble, not an empirical measurement. Aggressive sharpening can raise single-answer commitment while lowering multi-sample coverage -- the Pass-at-1-versus-Pass-at-k tension active inference frames as precision (inverse temperature), adjacent to the broader generation literature on objective- and decoding-induced diversity loss. Source: `output/data/firstprinciples/diversity_demo.json`.](../output/figures/diversity_tradeoff.png){#fig:diversity_tradeoff width=90% fig-alt="Line plot of sampling Pass-at-k versus student temperature on a logarithmic x-axis, with a dashed horizontal line for the temperature-invariant greedy Pass-at-1. Pass-at-k rises with temperature and collapses toward the greedy ceiling as the student sharpens."}

<!-- sheaf-track:lean -->

The project's Lean boundary modules declare horizon and coupling witnesses. Build with `lake build` in `lean/`; [@fig:lean_boundary_status] summarizes proved versus deferred statements for this boundary fragment.

<!-- sheaf-track:model_checking -->

`sheaf-track:model_checking` binds `output/reports/model_checking_witnesses.json` and the Lean theorem inventories. The appendix claim is exactly {{model_checking_witness_count}} finite exhaustive witnesses with pass status `{{model_checking_all_passed}}`; Lean graph-world topology coverage is {{lean_graph_world_topology_witness_count}} generated topology ids with all-witnessed flag `{{lean_graph_world_all_topologies_witnessed}}`.

<!-- sheaf-track:theorem_traceability -->

`theorem_traceability_matrix.json` provides the appendix proof for theorem traceability: {{theorem_traceability_row_count}} linked rows with status `{{theorem_traceability_linked}}`.

<!-- sheaf-track:proof_extraction -->

### Appendix track: proof extraction

`proof_extraction` binds `output/data/proof_extraction_index.json` into the full
sheaf appendix. Extracted theorems: {{proof_extraction_theorem_count}}.
Constructive status: `{{proof_extraction_all_constructive}}`.

The extraction index is intentionally modest: it records theorem names,
statements, source files, leading tactics, and forbidden proof-token checks.
That makes the Lean boundary inspectable without pretending that every proof
term has been translated into a proof object. A row with a missing statement or
forbidden token fails the formal interop gate and the canonical sheaf gate.

`output/data/proof_dependency_graph.json` adds the dependency view used by the
appendix figure. It contributes {{proof_dependency_edge_count}} theorem-source,
theorem-tactic, theorem-definition, and theorem-witness edges, with resolved
edge status `{{proof_dependency_all_resolved}}`; this is the artifact that keeps
the theorem-traceability graph tied to generated Lean and model-checking rows.

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

<!-- sheaf-track:gnn -->

GNN declarations: `gnn/bernoulli_toy.gnn.md` and `gnn/si_tmaze.gnn.md` [@gnn2023]. [@fig:gnn_ontology_concordance] and [@sec:methods_analytical] document ontology concordance for the Bernoulli toy; SI notation extends the same pattern under [@sec:methods_pymdp].

<!-- sheaf-track:ontology -->

### Ontology bindings

- `belief_entropy` → **BeliefEntropy**
- `expected_free_energy` → **ExpectedFreeEnergy**
- `location` → **HiddenState**
- `observation` → **ObservationLikelihood**
- `policy` → **PolicyPosterior**
- `sheaf_track` → **SheafFragment**


<!-- sheaf-track:animation -->

Animation is an **extension** sheaf track backed by a deterministic GIF from `scripts/render_animation.py`. This appendix row documents the track binding only; default publication still uses static SI figures ([@sec:results_si_tmaze], [@fig:si_tmaze_actions]) while the GIF remains an auditable generated artifact.

<!-- sheaf-track:animation_delta -->

The appendix `animation_delta` row points to `output/data/animation_frame_deltas.json`. The manifest records {{animation_delta_count}} adjacent-frame deltas, with `{{animation_deltas_all_nonzero}}` as the hydrated evidence that the GIF is trace-derived rather than a duplicated static frame.

<!-- sheaf-track:release_notes -->

### Appendix track: release notes evidence

`release_notes` binds `output/reports/release_notes_evidence.json` into the full
sheaf appendix. Rows: {{release_notes_row_count}}. Source-backed:
`{{release_notes_source_backed}}`.

Release notes are treated as claims, not as informal changelog prose. Each row
names a source artifact and a pass/deferred status, so the release note can say
only what validation, bundle, or semantic artifacts support. The validator
re-derives support from rows; flipping the summary bit without fixing a failed
row still fails.

`output/reports/release_attestation.json` is the compact final view over the
same boundary. It records {{release_attestation_row_count}} attestation rows for
validation, release bundle hash, license audit, semantic certificate, and
blocked-scope status, with all-attested flag `{{release_attestation_all_attested}}`.
