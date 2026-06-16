```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Appendix}
\section*{Appendix}
```

# Supplementary material: full coverage and concordance {#sec:appendix_full_sheaf}

<!-- sheaf-track:prose -->

This section is the **composability proof** for the manifest-indexed sheaf model that carries the on-policy-distillation-as-active-inference argument: all {{appendix_sheaf_track_count}} appendix-bound fragment tracks render into one flat manuscript section without section-specific compose branches. It is intentionally a coverage and concordance supplement, not the operational reproducibility-methods section; the latter follows in [@sec:methods_sheaf]. Just as the thesis holds that one variational free-energy functional governs both the generative model (the teacher policy) and the approximate posterior (the student policy) [@friston2006fep; @friston2010fep; @agarwal2024gkd], one registry governs every fragment type here. The registry defines {{sheaf_track_count}} composable types, and this row binds every registered fragment slot, including the generated `layers` tables and optional `animation` fragment, alongside the live proof, simulation, formal, notation, validation-spine, integration, audit, finite-catalog, ablation, license, release-evidence, scholarship, assumption-index, delta, and staleness tracks. The heterogeneous fragments are the manuscript-level analogue of the correspondence's heterogeneous terms — the Bernoulli–Ising coupling toy, the pymdp sophisticated-inference rollout, and the two-agent classroom run [@parr2022active] — each carrying a distinct piece of evidence under a single composition law. The sheaf language follows a finite local-to-global and composition-contract discipline [@curry2014sheaves; @speranzon2018contracts; @robinson2014topological; @robinson2017sensor_sheaf; @phillips2019sheaving; @fong2019applied_category; @rosiak2022sheaf_examples; @cox2026fragmented_risk_sheaf], not an unmeasured cohomological claim.

**Supplemental concordance and metadata tables.** To keep the main body prose-led, the large concordance and metadata tables are kept as separate, single-source markdown files rather than inlined: the active-inference $\leftrightarrow$ on-policy-distillation correspondence map (`output/data/firstprinciples/correspondence_table.md`), the on-policy-distillation method taxonomy (`output/data/firstprinciples/taxonomy_table.md`), the literature-reported empirical benchmark (`output/data/firstprinciples/benchmark_table.md`), and the integrated notation/formalism supplement (`docs/reference/notation-supplement.md`). Each is regenerated from the `firstprinciples` package and the manuscript variables, so the supplemental tables never drift from the artifacts that produced them. The GNN $\leftrightarrow$ ontology concordance and the sheaf coverage/scholarship matrices remain in their generated form under `output/data/`.

The proof is a publication-systems check ([@eq:appendix_track_count]). It demonstrates that heterogeneous fragments share one registry, manifest, renderer dispatch path, coverage matrix, and hydration boundary; it does not assert that every track carries equal scientific weight, nor that the analytical and T-maze demonstrations [@dacosta2020discrete] license claims beyond these minimal models and artifacts. The machinery guarantees only that the structural mapping - variational free energy to reverse-KL distillation loss, active sampling to on-policy student rollouts [@gu2024minillm], and privileged information to teacher-side conditioning across a statistical boundary - is rendered coherently across tracks, leaving the scientific weight of each correspondence to the sections that carry it.

### Supplemental table: energy decomposition

The full variational- and expected-free-energy decomposition for the minimal model (referenced from [@sec:energy_decompositions]) is tabulated here. As elsewhere, these are nats from a faithful minimal-model demonstration, not production measurements.

| Functional | Stream A | A (nats) | Stream B | B (nats) | Scalar (nats) |
| --- | --- | --- | --- | --- | --- |
| VFE ($F$) | complexity | {{energy_complexity:.3f}} | accuracy | {{energy_accuracy:.3f}} | log-evidence {{energy_log_evidence:.3f}} |
| EFE (risk/ambiguity) | risk | {{efe_risk:.3f}} | ambiguity | {{efe_ambiguity:.3f}} | — |
| EFE (epistemic/pragmatic) | epistemic | {{efe_epistemic:.3f}} | pragmatic | {{efe_pragmatic:.3f}} | — |

### Supplemental table: empirical OPD-vs-RL benchmark (literature-reported)

The literature-reported AIME-24 benchmark (referenced from the discussion) is tabulated here. These are external empirical results from Table {{qwen_table_number}} of the Qwen3 technical report [@qwen2025technical_report], relayed and discussed by Thinking Machines [@thinkingmachines2025opd], not measured in this manuscript; only the toy-model statistics reported elsewhere here are hydrated from our own generated artifacts.

| Quantity (literature-reported) | On-policy distillation | Reinforcement learning |
| --- | --- | --- |
| AIME-24 accuracy (percent) | {{empirical_opd_aime24:.1f}} | {{empirical_rl_aime24:.1f}} |
| Accuracy gain over RL (points) | {{empirical_aime24_gain_over_rl:.1f}} | — |
| Training cost (GPU-hours) | {{empirical_opd_gpu_hours:.0f}} | {{empirical_rl_gpu_hours:.0f}} |
| Compute reduction vs RL | {{empirical_compute_reduction:.1f}}x | 1.0x |

Table: AIME-24 accuracy and training cost for on-policy distillation versus reinforcement learning. The table cells are attributed directly to Table {{qwen_table_number}} of @qwen2025technical_report; @thinkingmachines2025opd relays those Qwen values and separately reports a {{empirical_tm_replication_aime24:.0f}} percent AIME-24 replication in about {{empirical_tm_replication_steps}} steps with a {{empirical_tm_efficiency_min:.0f}}-{{empirical_tm_efficiency_max:.0f}}x efficiency range. These are external empirical results, not measured in this manuscript; only the toy-model statistics reported elsewhere here are hydrated from our own generated artifacts.

<!-- sheaf-track:formalism -->

For each track $t \in \mathcal{T}_{\mathrm{Full}}$, the appendix row binds a fragment path $f(t)$ and the composer emits `<!-- sheaf-track:t -->` before the rendered body. Generated renderers such as `section_figures` and markdown renderers pass through the same `resolve_track_body()` dispatch, so the appendix exercises the common compose interface rather than a bespoke appendix path.

$$
|\mathcal{T}_{\mathrm{Full}}| = {{appendix_sheaf_track_count}}
$$ {#eq:appendix_track_count}

The fragment registry defines {{sheaf_track_count}} composable track types. This appendix binds the generated `layers` report and optional `animation` fragment; the deterministic GIF artifact in `tracks.yaml` `extension_tracks` is produced by the core analysis DAG and remains separate from this fragment slot.

Because this appendix binds every registered appendix track, it is the maximal publication stalk of the coverage presheaf and exercises every publication renderer through the common `resolve_track_body()` dispatch. The same compose path is gated by the {{sheaf_law_count}} sheaf laws verified in [@sec:methods_sheaf] ({{sheaf_laws_verified}}/{{sheaf_law_count}} satisfied): the appendix section glues to a unique output (separation), occupies the terminal position of the linear extension under its own `appendix` group row (poset and gluing), binds only well-typed fragments (typing), and owns every fragment path it references (compositionality). No count in this appendix is hand-written; all are injected from the registry-backed oracle.

<!-- sheaf-track:simulation -->

Analytical sweep artifacts feed [@sec:results_mi_sweep] and [@sec:results_invariants]; simulation invariants merge after [@sec:results_si_tmaze]. No additional path listing is required beyond those Results sections.

<!-- sheaf-track:assumption_index -->

The appendix `assumption_index` row points to
`output/data/analytical_assumption_index.json`. It binds
{{analytical_assumption_count}} finite Bernoulli-Ising assumption rows to
{{analytical_equation_count}} equation identifiers and generated artifacts, with
indexed status `{{analytical_assumptions_indexed}}`.

The point is to make analytical signposting mechanical. If an equation is added
without an assumption row, or if a row loses its evidence artifact, the index
gate fails and the manuscript cannot present the equation as part of the
validated finite toy proof surface.

<!-- sheaf-track:pymdp -->

pymdp harness summary: `output/data/si_tmaze_summary.json` (mean belief entropy, action trace, $q_\pi$ rows, SI tree flag). Matrix/value audit: `output/data/si_tmaze_model_matrices.json` ({{si_tmaze_matrix_shape_summary}}). Runtime diagnostics: `output/reports/pymdp_runtime_diagnostics.json` (known warnings {{pymdp_runtime_known_warning_count}}, tree warnings {{si_tree_known_max_node_warning_count}}, unexpected warnings {{pymdp_runtime_unexpected_warning_count}}). Policy posterior grid: `output/data/pymdp_policy_posterior_grid.json` ({{pymdp_policy_posterior_row_count}} rows). Full log: `output/logs/pymdp_runs.jsonl`.

<!-- sheaf-track:interop -->

`sheaf-track:interop` binds `output/data/interop_roundtrip_report.json`, `output/data/gnn_roundtrip_report.json`, `output/reports/gnn_lint_report.json`, and ontology profile artifacts into the appendix proof row. The appendix claim is exactly {{interop_check_count}} checks with lossless status `{{interop_all_lossless}}`.

<!-- sheaf-track:provenance -->

The appendix provenance fragment points to `output/data/artifact_provenance.json`, the canonical artifact that records required toy artifact hashes, producer scripts, source commit, deterministic seeds, config digests, and {{provenance_bundle_count}} bundle rows.

<!-- sheaf-track:replay_matrix -->

`replay_matrix.json` provides the appendix proof for deterministic replay: {{replay_matrix_row_count}} producer replay/fingerprint rows with matched status `{{replay_matrix_all_matched}}`.

<!-- sheaf-track:counterexample -->

The appendix counterexample fragment points to
`output/reports/counterexample_matrix.json`, the expected-failure matrix that
keeps promoted validation gates falsifiable. It currently records
{{counterexample_count}} known-bad fixtures, and the hydrated pass flag is
`{{counterexample_all_known_bad_fail}}`, meaning those fixtures are expected to
fail rather than sneak through a positive-control gate.

This row is the negative-control ledger for the sheaf. Each counterexample names
a promoted track, target validation gate, mutation, and observed expected-failure
status. A new live track without a counterexample row is therefore visibly
incomplete in the track-improvement scope.

<!-- sheaf-track:adversarial_audit -->

`sheaf-track:adversarial_audit` binds `output/reports/adversarial_audit.json`, `output/reports/scope_boundary_audit.json`, and claim-audit outputs. The appendix claim is exactly {{adversarial_audit_count}} expected-failure rows with documented status `{{adversarial_audit_all_documented}}` and known-bad-passing count {{adversarial_known_bad_passed}}.

<!-- sheaf-track:evidence_fields -->

`evidence_field_index.json` provides the appendix proof for field-level claim evidence: {{evidence_field_count}} mapped fields with status `{{evidence_fields_mapped}}`.

<!-- sheaf-track:release_bundle -->

`release_bundle_manifest.json` provides the appendix proof for required deliverables: {{release_bundle_artifact_count}} artifacts with source-present status `{{release_bundle_sources_present}}`.

<!-- sheaf-track:gate_ergonomics -->

`validation_gate_index.json` provides the appendix proof for gate ergonomics: {{validation_gate_index_count}} indexed gates.

<!-- sheaf-track:artifact_diffoscope -->

### Appendix track: artifact diffoscope

`artifact_diffoscope` binds `output/reports/artifact_diffoscope.json` into the
full sheaf appendix. Rows: {{artifact_diffoscope_row_count}}. All equal:
`{{artifact_diffoscope_all_equal}}`.

This diffoscope is deliberately narrow and reproducibility-facing. For each
non-cyclic generated artifact, it compares the saved provenance digest to the
live file digest at validation time. The validator re-derives equality from the
rows, so a stale `all_equal: true` summary cannot hide one changed artifact.

The row count is not a decoration; it is the number of artifact fingerprints
that survived cycle exclusion and therefore can be compared directly. This
keeps the release bundle honest about mutable files while avoiding
self-referential hashes for artifacts that necessarily include their own
provenance.

<!-- sheaf-track:artifact_license -->

### Appendix track: artifact license

`artifact_license` binds `output/reports/artifact_license_audit.json` into the
full sheaf appendix. Rows: {{artifact_license_row_count}}. All safe:
`{{artifact_license_all_safe}}`.

The license audit classifies each generated or source-backed artifact under the
public study's configured license boundary. It is intentionally conservative:
generated local outputs and project-owned source files pass, while an artifact
outside those public source kinds would need an explicit provenance and license
row before it could support a manuscript claim.

This is also where the blocked empirical-adapter boundary matters. Private,
restricted, or network-derived data are not smuggled in as evidence; they remain
blocked until privacy, licensing, typed-claim, semantic, and negative-control
gates are implemented in the same artifact path.

<!-- sheaf-track:scholarship -->

`sheaf-track:scholarship` binds `output/data/scholarship_source_matrix.json` into
the appendix proof row. The appendix claim is exactly
{{scholarship_source_count}} connected source rows with connected status
`{{scholarship_sources_connected}}`; each row names a bibliography key, method
role, manuscript section, registered track set, evidence artifact, and
claim-boundary statement.

<!-- sheaf-track:sensitivity -->

`sheaf-track:sensitivity` binds `output/data/sensitivity_sweep.json`, measured `output/data/si_policy_grid.json`, compatibility-named EFE values artifact `output/data/si_efe_terms.json`, `output/data/analytical_observable_sweep.json`, and graph-world topology artifacts including `output/data/si_graph_world_topology_traces.json`. The appendix claim is exactly {{sensitivity_cell_count}} complete canonical grid cells.

<!-- sheaf-track:uncertainty -->

`sheaf-track:uncertainty` binds `output/data/uncertainty_summary.json`. The appendix claim is exactly {{uncertainty_row_count}} normalized rows across {{uncertainty_bin_count}} entropy bins with status `{{uncertainty_all_normalized}}`.

<!-- sheaf-track:benchmark -->

`sheaf-track:benchmark` binds `output/data/toy_benchmark_matrix.json`. The appendix claim is exactly {{benchmark_model_count}} complete toy-model rows with status `{{benchmark_all_models_complete}}`.

<!-- sheaf-track:visualization -->

![Theorem traceability graph generated from {{theorem_traceability_row_count}} linked theorem rows and {{proof_dependency_edge_count}} proof-dependency edges; all {{theorem_traceability_row_count}} theorem rows are drawn with their finite-witness counts, and all theorem rows have resolved dependency edges: {{proof_dependency_all_resolved}}. The graph exposes the deductive backbone of the formal track -- which lemmas each distillation/active-inference theorem rests on and which finite models witness it. Fully resolved dependencies show that each declared finite theorem row has a registered proof-dependency chain rather than appearing as an isolated assertion; they do not close formal obligations outside this inventory.](../output/figures/theorem_traceability_graph.png){#fig:theorem_traceability_graph width=95% fig-alt="Three-column graph generated from theorem traceability and proof dependency JSON. Each row links a Lean theorem to its proof-dependency edge count and finite model witness count; all theorem rows have resolved dependency edges: {{proof_dependency_all_resolved}}."}

![Causal-ablation heatmap over {{ablation_sensitivity_row_count}} source-backed rows joined to the sensitivity and uncertainty artifacts (all effects source-backed: {{ablation_sensitivity_source_backed}}). This heatmap is an aggregated max-effect view of the {{ablation_sensitivity_row_count}} source rows: rows are toy graph topologies, columns are perturbation types, and each cell reports the maximum absolute deterministic effect of that intervention. The map shows which structural assumptions of the generative model the distillation outcome is sensitive to and which it is robust against inside this toy intervention matrix, flagging where the generated on-policy behavior would shift under declared model misspecification without asserting deployment-scale effects.](../output/figures/causal_ablation_heatmap.png){#fig:causal_ablation_heatmap width=92% fig-alt="Heatmap generated from the causal ablation and sensitivity reports. Rows are toy graph topologies, columns are perturbation types, and each cell shows the maximum absolute deterministic effect sourced from generated JSON rows."}

<!-- sheaf-track:state_space_catalog -->

### Appendix track: state-space catalog

`state_space_catalog` binds `output/data/state_space_catalog.json` into the full
sheaf appendix. Rows: {{state_space_catalog_row_count}}. All finite:
`{{state_space_catalog_all_finite}}`.

The catalog is the finite-scope boundary for every toy claim in the study.
Each row records a model id, state count, action count, policy count, source
artifact, and finite flag; the validator recomputes that counts are positive
and that every row remains finite. This prevents a manuscript sentence about
exhaustive checking from silently drifting into an unbounded or empirical
setting.

`output/data/state_transition_table.json` makes the boundary operational. It
contains {{state_transition_row_count}} deterministic transition rows and covers
all reachable finite models with status `{{state_transition_all_covered}}`.
Readers can therefore audit not just the number of states, but the actual
state/action/next-state relation used by the model-checking witnesses.

<!-- sheaf-track:causal_ablation -->

### Appendix track: causal ablation

`causal_ablation` binds `output/data/causal_ablation_matrix.json` into the full
sheaf appendix. Cells: {{causal_ablation_row_count}}. Complete grid:
`{{causal_ablation_complete_grid}}`.

The matrix is a finite teaching device: every row names a topology, a coupling
value, a perturbation, a scalar effect, and the generated source row that made
the effect admissible. It is not a claim about empirical interventions. It
shows how an intervention-shaped table can be made falsifiable inside the sheaf:
delete one perturbation cell or clear one deterministic flag and the grid gate
fails before the manuscript can reuse the result.

`output/reports/ablation_sensitivity_report.json` then joins those ablation
effects to the sensitivity and uncertainty artifacts. The report contributes
{{ablation_sensitivity_row_count}} source-backed rows, with source-backed status
`{{ablation_sensitivity_source_backed}}`, so the appendix heatmap is a rendered
view of validated JSON rather than a decorative restatement.
