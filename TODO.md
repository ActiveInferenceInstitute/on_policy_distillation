# active_inference_on_policy_distillation TODO

This roadmap is future-only. It is not the current artifact contract and it does
not create publication claims. Current publication claims remain deterministic,
public, locally reproducible, and toy-only. The live system uses stable canonical
track IDs; future work should deepen canonical tracks such as `provenance`,
`replay_matrix`, `sensitivity`, `uncertainty`, `model_checking`, `interop`,
`adversarial_audit`, `evidence_fields`, `release_bundle`,
`theorem_traceability`, `gate_ergonomics`, `artifact_diffoscope`,
`proof_extraction`, `state_space_catalog`, `causal_ablation`,
`artifact_license`, and `release_notes` rather than adding `_vN` siblings.

## Current baseline

The current system is a validated multi-track toy Active Inference exemplar with
canonical sheaf tracks, semantic gluing, dependency graph, typed claim evidence,
manuscript hydration, Lean/GNN/ontology checks, graph-world and animation
artifacts, and a blocked empirical boundary. Live proofs belong in the registry,
project docs, generated certificates, `output/data/track_improvement_scope.json`,
and output reports rather than repeated here as completed TODO work.

## Status & what's needed from here (2026-06-11, after Runs 10–11)

**The project is mature and green — nothing here is blocking.** Full suite
`483 passed / 0 failed` across the chunked runner; `validate_outputs` ALL TRUE
(reproduced across two independent clean regenerations); eleven hardening runs.
Runs 10–11 landed **7 promotion chains** (each: production-path gate in
`_validate_outputs_full` + a biting negative control + write-path verification +
Forge GPT-5.4 cross-vendor PASS): `AI-PYMDP-POLICY-3`, `AI-PYMDP-RUNTIME-3`,
`AI-GNN-SHAPE-3`, `AI-ANIMATION-HASH-2`, `AI-CLAIM-PREDICATE-3`, `AI-SCOPE-ROWS-1`,
`AI-GATE-INDEX-3` (see their LANDED notes below).

What remains is **optional future deepening or externally-gated**, in priority order:

1. **Needs a human decision / external input (cannot proceed unilaterally):**
   - *Venue/submission decision* → unblocks `REVIEW-FIGURE-RELOCATION-1` (move dense
     dashboard figures to a supplement) and `TMAZE-MATRIX-TABLE-1` (typeset table vs
     figure). Deliberately not done: current genre is an auditable artifact paper.
   - *Primary Qwen3 report PDF* → `QWEN-TABLE-PIN-1` (pin the external OPD-vs-RL values
     to an exact table/figure locator; must be verified against the source PDF, never
     fabricated).
   - *Publish decision* — this exemplar is LOCAL-ONLY by design; if publishing, the
     release path is reserve-DOI-first → GitHub release → Zenodo (out of TODO scope).
2. **Additive deepening (doable in a future session, medium value, under the promotion rule):**
   - Integration field-level rows: `AI-DEPENDENCY-FIELDS-1`, `AI-PROVENANCE-FIELDS-1`,
     `AI-EVIDENCE-FIELDS-1` (JSONPath/prose-span edges, field-level lineage),
     `AI-SYMBOL-SPINE-3` (manuscript-variable + figure-label + Lean-name joins),
     `AI-SEMANTIC-CLASSIFIED-1` (typed restriction classes + proof obligations).
   - `AI-MANUSCRIPT-TOKEN-3` (rendered↔provenance token `set_equals`),
     `AI-RELEASE-PARITY-1` (post-root-pipeline live drift exercise).
   - `AI-ONTOLOGY-PROFILE-3` — **low value / high risk** (needs a graph-world GNN +
     true uniqueness check; current artifact is a name-matched shell). Consider
     descoping rather than building.
   - Future sheaf tracks (`proof_dependency_graph`, `state_transition_table`,
     `ablation_sensitivity_report`, `release_attestation`) — some artifacts already
     exist; promotion needs the full 7-part chain + manuscript binding before going live.
3. **Environment-gated maintenance:** `AI-TEST-ISOLATION-1` — the 5-consecutive-run
   idle-host soak needs an idle host (the codex co-actor's continuous short pytest
   bursts make the host non-idle); the chunked runner already isolates the
   `mutates_artifacts` class, so this is confirmation, not a fix.
4. **Intentionally blocked (do NOT build without the unblock artifacts + gates):** all
   rows under "Blocked scope" — empirical/biological, private data, network-dependent,
   LLM-generated evidence, non-toy claims.

## Promotion rule

A future capability becomes live only after every row below is satisfied in the
repository and passes under the core pipeline. Each roadmap row must identify a
proving artifact, a gate or typed predicate, and a negative control before
implementation begins.

| Requirement | Minimum proof before promotion |
| --- | --- |
| Producer | Configured script or renderer in the analysis DAG |
| Artifact | Deterministic file under `output/data/`, `output/reports/`, or `output/figures/` |
| Manuscript consumer | Bound IMRAD fragment or generated evidence table |
| Typed claim evidence | Claim-ledger predicate with explicit field, expected value, tolerance, or list predicate |
| Semantic restriction | Certificate field that catches disagreement, missing evidence, or stale output |
| Validation gate | `validate_outputs`, `validate_manuscript`, `lake build`, or project test |
| Negative control | Test that mutates artifact/config/claim text and proves the gate fails |

## Within-track roadmap

| ID | Canonical track area | Future improvement | Proving artifact | Gate or predicate | Negative control |
| --- | --- | --- | --- | --- | --- |
| ~~`AI-ANALYTICAL-OBS-4`~~ | Analytical | **DONE 2026-06-10 (Run-4):** `conditional_policy_entropy` added with closed form $H_b(\sigma(\lambda))$, equation `eq:conditional_entropy`, assumption-index row, and a genuinely independent two-route cross-check (the previous `empirical = closed_form` tautology was removed); validator re-derives the residual bound from rows and pins the observable set | `output/data/analytical_observable_sweep.json` | re-derived residual ≤ 1e-12 + observable `set_equals` | lying-row and dropped-observable controls in `test_roadmap_promotion.py` |
| `AI-PYMDP-RUNTIME-3` | PyMDP/JAX | Split runtime diagnostics into construction, inference, backend, warning, and fallback rows. *Run-6 audit: PARTIAL — construction/backend/warning rows + `unexpected_warning_count==0` gate + injected-warning negative control all live; missing only distinct "inference" and "fallback" row categories (fallback rows live in the posterior grid)* **Run-11 LANDED (2026-06-11, 2489eb5): `_categorized_rows` fans each record into construction/inference/backend(/warning/fallback) categorized rows; production gate (`_validate_outputs_full`) re-derives `_runtime_rows_explained` (every inference/fallback row carries a reason; unknown category fails closed) + keeps `unexpected_warning_count==0`; NCs (blank inference reason, unknown category) bite `validate_outputs(root)`; write-path verified; Forge cross-vendor PASS** | `output/reports/pymdp_runtime_diagnostics.json` | `equals` unexpected warning count `0` and `all` fallback rows explained | Unexpected warning is accepted |
| `AI-PYMDP-POLICY-3` | PyMDP/T-maze | Add measured policy posterior summaries for every configured mode/horizon/seed cell. *Run-6 audit: PARTIAL — 14-row grid covers the full configured planner×seed×horizon set, per-row 1e-9 normalization re-derived at validate, unnormalized negative control live; grid set_equals lives on the sibling `si_policy_comparison` artifact and no test deletes a grid cell* **Run-10 LANDED (2026-06-11, c1ca822+eecf581): production `_validate_outputs_full` re-derives the expected planner×seed grid from config + horizon check + `set_equals`; cell-deletion NC bites `validate_outputs(root)` full path (Forge GPT-5.4 cross-vendor PASS — caught+fixed an initial lazy-path-only green-wash)** | `output/data/pymdp_policy_posterior_grid.json` | `set_equals` configured grid and `all` normalized posteriors | Missing or unnormalized posterior cell passes |
| ~~`AI-PYMDP-EFE-3`~~ | PyMDP/T-maze | **DONE (verified Run-6 audit 2026-06-10):** rows carry `terms`/`terms_available`/`fallback_reason`; `_efe_values_explained` re-derives `all_rows_explained` (`output_checks.py:68-74`); `break_efe` negative control (`test_roadmap_promotion.py:650-671`). All current rows are honest fallbacks — pymdp exposes opaque arrays only (ISA Out-of-Scope); the row's "where available" wording is satisfied | `output/data/si_efe_terms.json` | `all` rows have terms or fallback reason | Row lacks both terms and fallback |
| ~~`AI-GRAPH-TOPOLOGY-3`~~ | Graph-world | **DONE (verified Run-6 audit 2026-06-10):** 4 deterministic topologies (incl. `loop5`, `diamond5`) with full traces, `trace_summary_agree` re-derivation, invariants, and per-topology Lean witnesses (`formal_interop.py:141-166`); negative control mutates `trace_steps=999` → gate fails (`test_roadmap_promotion.py:237-246`) | `output/data/si_graph_world_topology_traces.json` | `all` topology summaries agree with traces and witnesses | Summary path length disagrees with trace |
| `AI-ANIMATION-HASH-2` | Animation | Add stable per-frame perceptual hashes and frame metadata to the delta manifest. *Run-6 audit: NOT started on the headline item — rows carry bbox deltas only, no per-frame hashes or frame metadata; static-manifest negative control and GIF staleness re-derivation are live* **Run-11 LANDED (2026-06-11, 2489eb5): per-frame deterministic sha256 of frame pixel bytes + frame metadata (index/width/height) + per-row from_hash/to_hash/hashes_differ + `all_hashes_distinct` aggregate; production gate re-derives `all(row.hashes_differ)` so duplicate/static adjacent frames fail; NC (duplicate adjacent hash) bites `validate_outputs(root)`; aggregate_rederivation rule added; write-path verified; Forge cross-vendor PASS. NB: this is an EXACT content hash (sha256 of frame bytes), NOT a perceptual/near-duplicate hash — scoped to catching byte-identical duplicate/static frames, which is the row's negative control.** | `output/data/animation_frame_deltas.json` | `len_min` frames and `all` nonzero deltas/hashes | Duplicate/static frames pass |
| ~~`AI-VIZ-PIXEL-2`~~ | Visualization | **DONE (verified Run-6 audit 2026-06-10):** 28 figure rows with `sources`/`source_fields`/pixel dims/`validation_gates`; `_figure_source_rows_complete` enforces true set-equality vs the figure registry (`integration_audit_artifacts.py:479-519`); provenance-drop negative control (`test_roadmap_promotion.py:410-428`) | `output/data/figure_source_map.json` | `set_equals` figure ids against `figures.yaml` | Figure lacks source artifact |
| ~~`AI-LEAN-BELIEF-3`~~ | Lean/model-checking | **DONE (verified Run-6 audit 2026-06-10):** finite belief/posterior normalization theorems (`two_state_belief_weights_sum_to_two`, `two_policy_posterior_weights_sum_to_two`) tied to finite models via witnesses; `all_proved` + extracted==inventory set-equality + forbidden-token scan; planted-`axiom` and dropped-theorem negative controls (`test_roadmap_promotion.py:339-367`) | `output/reports/lean_theorem_inventory.json` | `set_equals` theorem names and `all` proved | `sorry`, `axiom`, `native_decide`, or missing theorem passes |
| `AI-GNN-SHAPE-3` | GNN | Require every variable to carry exactly one ontology term, dtype, shape, and round-trip row. *Run-6 audit: PARTIAL — 17 per-variable rows with dtype/shape/ontology + unused-term detection; missing per-variable round-trip rows (round-trip is per-model) and a missing-shape negative control on the lint report* **Run-11 LANDED (2026-06-11, 2489eb5): each lint row now carries `round_trip_ok` via `roundtrip_payload_lossless` on the single-variable payload (real parse→write→parse; empty dims → GNNParseError → False) + `all_round_trip_ok` aggregate; production gate requires `all(row.round_trip_ok)`; missing-shape NC bites `validate_outputs(root)`; aggregate_rederivation rule added; write-path verified; Forge cross-vendor PASS** | `output/reports/gnn_lint_report.json` | `all` variables mapped once with type and shape | Duplicate alias or missing shape passes |
| `AI-ONTOLOGY-PROFILE-3` | Ontology | Add model-specific ontology profiles for graph-world and each toy benchmark model. *Run-6 audit: NOT satisfied — artifact covers only `{bernoulli_toy, si_tmaze}` (no graph-world), `mapped_once = bool(term)` checks presence not uniqueness, and no negative control exists; treat the current artifact as a name-matched shell of this row* | `output/data/ontology_profile_matrix.json` | `all` model variables mapped once | Profile introduces unused or unmapped term |
| `AI-MANUSCRIPT-TOKEN-3` | Manuscript/hydration | Extend token provenance to generated tables, appendix fragments, and figure captions. *Run-6 audit: PARTIAL — 705 tokens incl. appendix fragments with `all_tokens_mapped` re-derived; caption/table tokens tracked by sibling artifacts, and the rendered-vs-provenance set_equals is not implemented as described* | `output/data/manuscript_token_provenance.json` | `set_equals` rendered tokens and provenance keys | Edited hydrated output hides stale value |
| `AI-CLAIM-PREDICATE-3` | Claim ledger | Improve predicate failure messages and require substantive evidence or explicit waiver for every claim. *Run-6 audit: PARTIAL — typed predicates with tolerances are live and negative-controlled, but audit rows lack `waiver`/`section`, no waiver concept exists, and the `file_exists` predicate admits exactly the path-only evidence this row's negative control forbids* **Run-10 LANDED (2026-06-11, c1ca822): `file_exists` checks on-disk existence; fieldless bare-presence evidence without a waiver is now flagged (`typed_claim_evidence_issues`) — caught a real live claim `fp_classroom_entropy_series` and added an honest waiver; path-only NC bites; all 18 waivers Forge-verified non-laundering (each sits only on a genuinely-shallow claim with substantive sibling gates). Source-ledger row, no regen dep — fully live.** | `output/reports/claim_evidence_audit.json` | `all` claims have evidence, waiver, tracks, and section | Path-only claim passes as evidence |
| `AI-GATE-INDEX-3` | Gate ergonomics | Emit one row per validator check with command, required input, output, and negative control. *Run-6 (2026-06-10) partial landing: builder no longer a hardcoded stub — `indexed` is DERIVED from on-disk inputs (`GATE_INDEX_ROWS` registry) and `validate_outputs` re-derives a live binding (`validation_gate_index_binding`: every row id must match a check key or known external gate; phantom-row, unindexed-row, and empty-rows negative controls in `tests/test_gate_index_binding.py`). Remaining for full row: per-check command/output/negative-control fields* **Run-10 LANDED (2026-06-11, c1ca822+eecf581): each row now carries `command`/`output`/`negative_control`; `validation_gate_index_schema` re-derives `all_rows_fully_specified` from rows at gate time (never trusts the stored flag — lying-flag NC bites, the Run-9 class); the builder is verified (in-memory) to emit a fully-specified index so a clean regen reads green; 2 stale `validate_manuscript.py` command strings corrected to `compose_manuscript.py --validate-only --strict`. Forge cross-vendor PASS. Live on-disk artifact REFRESHED by the Run-11 full-chain regen (retry-loop landed a co-actor gap): `validate_outputs` ALL TRUE, validation_gate_index now carries the per-check fields and reads green live.** | `output/data/validation_gate_index.json` | `set_equals` validator ids and dependency ids | Validator lacks declared artifact inputs |

## Integration roadmap

| ID | Canonical integration target | Future improvement | Proving artifact | Gate or predicate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AI-SEMANTIC-CLASSIFIED-1` | Semantic certificate | Add typed restriction classes and explicit proof-obligation records inside the canonical certificate. *Run-6 audit: NOT satisfied — `restrictions` is a flat dict of named scalars with no typed classes or proof-obligation records anywhere in the artifact; only the untyped saved-vs-live restriction staleness layer exists (negative-controlled)* | `output/data/sheaf_gluing_certificate.json` | `all` proof obligations ok and typed | Saved certificate omits a required proof obligation |
| `AI-DEPENDENCY-FIELDS-1` | Dependency graph | Add field-level JSONPath edges and artifact-to-rendered-prose span links inside the canonical dependency graph. *Run-6 audit: PARTIAL — 2,579 edges across 18 kinds with required-edge-type gate and drop negative control; JSONPath field-level edges live in `evidence_field_index.json` instead, prose-span links absent* | `output/data/validation_dependency_graph.json` | `set_equals` required edge types plus field-level edge count | Artifact field appears in prose without dependency edge |
| `AI-PROVENANCE-FIELDS-1` | Provenance | Broaden source commit, config digest, seed, producer, and input-artifact lineage to field-level rows. *Run-6 audit: PARTIAL — 111 artifact-level rows with live hash/size/producer/seed/digest re-derivation and stale-hash/stale-seed negative controls (the row's own NC is fully covered); only the field-level broadening is missing* | `output/data/artifact_provenance.json` | `all` required fields have hash, producer, seed/config, and source commit | Changed artifact hash passes as current |
| `AI-RELEASE-PARITY-1` | Release bundle | Compare project-local outputs, copied root outputs, PDF/web deliverables, and required hashes after the root pipeline. ***Run-6 (2026-06-10) keystone fix:** the parity builder reclassified existing-but-drifted root copies as "deferred", so drift could NEVER fail (the row's negative-control scenario described live behavior). Fixed: deferral now means pre-copy or render-source-absent only; drift fails both `all_copied_outputs_match` and `all_copied_outputs_match_or_deferred`; synthetic-tree negative controls in `tests/test_release_parity.py`. Also corrected the required PDF/web deliverable names from the template exemplar's (`template_active_inference_combined.pdf`, never producible here) to this paper's real `on_policy_distillation.pdf` + `web/index.html`. Remaining: a post-root-pipeline live drift exercise* | `output/reports/release_bundle_manifest.json` | `all` copied outputs match or are explicitly deferred before render | Copied root output drift passes |
| `AI-EVIDENCE-FIELDS-1` | Evidence fields | Link every claim field and manuscript token to a JSONPath, validator, and semantic restriction. *Run-6 audit: PARTIAL — 103 rows with JSONPath + validators + per-row re-derivation and unmapped negative control; semantic-restriction linkage absent and the NC keys on `field_present`, not JSONPath presence* | `output/data/evidence_field_index.json` | `all` evidence fields mapped and source-backed | Claim field lacks a JSONPath edge |
| ~~`AI-THEOREM-LINKS-1`~~ | Theorem traceability | **DONE (verified Run-6 audit 2026-06-10):** 11 rows (= Lean inventory) joining theorem → claim_ids → evidence fields → model witnesses with `all_theorems_linked` re-derived; unlinked-row negative control (`test_track_consolidation.py`). Minor residual: in-row `linked` flag is the re-derivation source | `output/data/theorem_traceability_matrix.json` | `all` theorem rows linked to claims and artifacts | Theorem inventory row has no claim or artifact |
| ~~`AI-STALE-LIVE-1`~~ | Stale-artifact controls | **DONE (verified Run-6 audit 2026-06-10):** 72 rows re-hashed live at validate (`integration_audit.py:184-190`), semantic snapshot compared saved-vs-live; sha-mutation, lying-flag, stale-certificate, and upstream-mutation negative controls all present | `output/reports/stale_artifact_report.json` | `all` stale flags false and saved fields match live fields | Touching upstream JSON leaves stale report passed |
| `AI-SYMBOL-SPINE-3` | Cross-track symbols | Expand the symbol table across GNN, ontology, Lean theorem names, manuscript variables, JSON fields, and figure labels. *Run-6 audit: PARTIAL — 17 rows spanning GNN/ontology/JSON-field/Lean-namespace with 5 re-derived aggregates and an ontology-mutation negative control; manuscript-variable and figure-label columns plus Lean theorem-name joins still missing* | `output/data/cross_track_symbol_table.json` | `all` symbols have consistent type, shape, ontology, and consumer | Same symbol has incompatible meanings |
| `AI-SCOPE-ROWS-1` | Scope boundary | Make scope classification row-level for current, future, empirical, and blocked-language contexts. *Run-6 audit: PARTIAL — 16 row-level section rows but a single `toy_or_future` class via substring match over top-level sections only; flag-flip negative control exists, wording-mutation control does not* **Run-10 LANDED (2026-06-11, c1ca822+eecf581): wording-mutation negative control added; `recompute_ok` now fails closed when a row is missing any classification flag (was defaulting to pass); builder verified to emit flag-bearing rows. Forge cross-vendor PASS. Documented residual: wording flags are re-derived at write time, not re-scanned from markdown at read time (single-source; no TOCTOU).** | `output/reports/scope_boundary_audit.json` | `all` current-result rows classified toy-only | Empirical wording appears outside future/blocked context |

## Future sheaf tracks

The proposed IDs below are not live tracks. Do not add them to
`manuscript/sheaf/tracks.yaml`, `tracks.yaml`, manuscript fragments, or public
claims until the promotion rule is fully satisfied. These names are stable
non-versioned candidates; if promoted, they should remain canonical rather than
spawning tranche-numbered siblings.

| Proposed id | Purpose | First artifact | First manuscript binding | First gate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `proof_dependency_graph` | Expand extracted Lean proof dependencies into theorem-to-definition edges | `output/data/proof_dependency_graph.json` | `methods_lean/proof_dependency_graph.md` | proof dependency validator plus `lake build` | Theorem dependency edge is dropped |
| `state_transition_table` | Emit explicit finite transition tables for every toy topology and T-maze action | `output/data/state_transition_table.json` | `results_invariants/state_transition_table.md` | transition-table validator | Transition table omits a reachable state |
| `ablation_sensitivity_report` | Summarize causal-ablation effects against sensitivity and uncertainty rows | `output/reports/ablation_sensitivity_report.json` | `results_invariants/ablation_sensitivity_report.md` | ablation-sensitivity validator | Ablation effect is reported without source row |
| `release_attestation` | Generate a compact attestation over validation report, bundle hash, license audit, and blocked scope | `output/reports/release_attestation.json` | `discussion_outlook/release_attestation.md` | release-attestation validator | Attestation claims a failed gate passed |
| `empirical_adapter` | Future-only bridge for real datasets after provenance, licensing, privacy, and typed claim gates exist | `output/data/empirical_adapter_manifest.json` | `discussion_outlook/empirical_adapter.md` | blocked until explicit data gates exist | Empirical claim appears without manifest |

## Blocked scope

The following remain explicitly out of scope until a later plan promotes them
with provenance, licensing/privacy review, typed claim evidence, semantic
restrictions, gates, and negative controls.

| Blocked area | Why blocked | Required unblock artifact | Required gate | Negative control |
| --- | --- | --- | --- | --- |
| Empirical biological claims | Current artifacts are deterministic toy models, not biological data | `output/data/empirical_adapter_manifest.json` | scope-boundary and claim-ledger gates | Empirical result prose without manifest fails |
| Private or restricted data | This exemplar is public and self-contained | `output/reports/data_provenance_audit.json` | provenance and license validator | Private path or unlicensed source passes |
| Network-dependent research | Pipeline must remain locally reproducible | `output/reports/offline_reproducibility_audit.json` | offline pipeline gate | Network call required for core pipeline |
| LLM-generated evidence | Claims must come from generated local artifacts, not opaque model output | `output/reports/evidence_source_audit.json` | evidence registry and claim-ledger gates | LLM-only claim passes evidence audit |
| Non-toy model claims | Current validation covers finite pedagogical examples only | `output/reports/model_scope_audit.json` | scope-boundary validator | Non-toy generalization appears in results |

## Suggested order

1. Keep this roadmap future-only; completed live tracks belong in README,
   AGENTS, registries, and generated outputs.
2. Deepen canonical semantic/dependency/provenance/evidence-field rows before
   adding another live track.
3. Prefer finite toy evidence, negative controls, and typed claim predicates
   over broader prose claims.
4. Leave `empirical_adapter` blocked until the unblock artifacts and gates above
   exist and fail closed.

## Deferred review follow-ups (2026-06-02 deep-improvement session)

The 2026-06-02 multi-reviewer audit shipped its keystone correctness/honesty
fixes (deterministic-recompute relabel, genuine GNN round-trip, per-file proof
provenance, duplicate-marker gate, pandoc-crossref single-source figure
numbering, 4 added negative controls, enriched abstract/derivation/pymdp prose).
The rows below are the remaining, non-blocking improvements identified by that
audit. They carry no publication claim and remain future-only under the
promotion rule above.

| ID | Area | Improvement | Proving artifact | Gate or predicate | Negative control |
| --- | --- | --- | --- | --- | --- |
| ~~`AI-STALE-SUMMARY-1`~~ | Validation gates | **DONE 2026-06-10 (Run-4):** read-time re-derivation layer `src/gates/aggregate_rederivation.py` re-derives 58 stored `all_*` aggregates from their rows inside `validate_outputs` (`aggregate_rederivation` check; vacuous truth over empty rows fails closed); was also the Run-2 cross-vendor accepted residual | `validate_outputs` check + `tests/test_aggregate_rederivation.py` | stored flag == row-level re-derivation for every covered aggregate | lying-case tests: mutate one row, leave flag `true`, gate fails |
| ~~`AI-EFE-NONVACUOUS-1`~~ | PyMDP/EFE | **DONE (pre-Run-4):** `_efe_values_explained` re-derives `all_rows_explained` (terms_available ⇒ non-empty `terms.values`; fallback rows need `fallback_reason`); schema renamed to `si_efe_values.v1`; negative control in `test_roadmap_promotion.py` | `output/data/si_efe_terms.json` | `terms_available` ⇒ non-empty terms | `terms_available=true` + empty terms fails |
| ~~`AI-STUB-DEPTH-1`~~ | Fragments | **DONE (pre-Run-4):** the 6 fragments are 101–128-word hydrated teaching cells with narrative rationale (verified 2026-06-10) | composed manuscript | token gate (all `{{tokens}}` resolve) | n/a (prose) |
| ~~`AI-APPENDIX-HYDRATE-1`~~ | Integration | **DONE (pre-Run-4):** counterexample, manuscript_staleness, and assumption_index cells all carry `{{tokens}}` (verified 2026-06-10) | composed appendix | token gate | edited hydrated output hides stale value |
| ~~`AI-APPENDIX-FIGURES-1`~~ | Visualization | **DONE (pre-Run-4):** `theorem_traceability_graph` and `causal_ablation_heatmap` registered, generated, and bound in `appendix_full_sheaf` (verified 2026-06-10) | `figures.yaml` + generators | `test_figure_generators_match_registry` | figure lacks source artifact |
| ~~`AI-HYGIENE-1`~~ | Cleanup | **DONE 2026-06-10 (Run-6):** (1) tolerance SSOT scoped to trust domains — `BERNOULLI_VERIFICATION_TOLERANCE` single-defined in `analytical/hyperparameters.py` (re-exported by `bernoulli_toy`), writer-side PMF tolerances named in `simulation/numerics.py` (`STEP_POSTERIOR_ATOL`/`POLICY_POSTERIOR_ATOL`), validator-side literals in `gates/` deliberately independent (duplication across the writer/validator boundary IS the verification mechanism — documented in numerics.py); (2) duplicate `skipif` removed (`test_integrity_remediations.py`); (3) 4 direct `_parse_param_blocks` unit tests added (`tests/test_gnn.py`: happy path, unbalanced braces, empty/comment-only, comment-skip); (4) poset-law prose verified already sharp (chain + $G \sqsupseteq s$ relation stated, 6 laws each content-precise and negative-control-paired — no churn needed); (5) concordance caption now hydrates `{{bernoulli_ontology_term_count}}` | n/a | full suite + ruff/mypy | n/a |
| `REVIEW-FIGURE-RELOCATION-1` | Visualization | 2026-06-10 external review suggests moving dense dashboard figures (multi-track architecture, full correspondence dictionary, labeled taxonomy scatter) to a supplement with simplified main-text versions at venue-submission time; deliberately NOT done now — the current PDF's genre is an auditable artifact paper where provenance figures are load-bearing | figures.yaml `section_figures` | compose + figure gates stay green after any relocation | figure lacks source artifact |
| `QWEN-TABLE-PIN-1` | Scholarship | 2026-06-10 external review: pin the external OPD-vs-RL values to the exact table/figure locator in the primary Qwen3 technical report (`qwen2025technical_report`) instead of report-level citation; requires re-opening the primary PDF — do NOT insert a locator without re-verification against the source. Prose already brackets all values as literature-reported, not reproduced. **Resolution requires:** a session that fetches/opens the primary Qwen3 report PDF and quotes the table/figure heading verbatim into the scholarship source matrix | `manuscript/15_discussion_outlook.md` + supplement table | citation carries a locator verified against the primary PDF | a fabricated locator fails the source-quote check when added |
| `TMAZE-MATRIX-TABLE-1` | Visualization | 2026-06-10 external review: `si_tmaze_model_matrices` is table-like and small at print size; convert to a typeset table or move fully to supplement at venue-submission time. Deferred with `REVIEW-FIGURE-RELOCATION-1` because conversion changes the figure-source-map contract (figure rows bind to generated artifacts). **Resolution requires:** a venue decision (submission target chosen), then a generated-table binding (values hydrated from the matrix artifact, not typeset by hand) | figures.yaml + matrix artifact | compose + figure gates stay green after conversion | typeset values diverging from the matrix artifact must fail the binding gate |

## Known residual (2026-06-02): full-suite artifact-isolation flakiness

Every test passes in isolation and coverage passes at 92.03% (`fail_under = 90`),
but the full `pytest tests/` run is order/load-sensitive: the set of failing
artifact-validation tests (e.g. `test_semantic_certificate_*`,
`test_canonical_sheaf_*`, `test_validate_manuscript_contract`,
`test_promoted_roadmap_artifacts_*`) varies run-to-run (observed 1→11→2→4 across
runs at 2x normal wall-clock under machine load ~8). Root cause is the stateful
diffoscope (rows derived from `artifact_provenance.json` rows) and semantic
certificate carrying cross-test state under the run-once `ensure_gate_artifacts`
guard, exposed when artifacts regenerate concurrently. `test_integration_audit_
negative_controls` was hardened (regenerates its own diffoscope precondition).

| ID | Area | Improvement | Proving artifact | Gate or predicate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AI-TEST-ISOLATION-1` | Test infra | **PARTIAL 2026-06-10 (Run-4 + Run-6):** chain-A stale-trust race closed in Run-4 — `gate_support.evict_bootstrap` drops ROOTS **and** FINGERPRINTS symmetrically and the fingerprint surface covers the ready-only artifacts. **Run-6:** `run_tests_chunked.py --shuffle-seed N` added (deterministic file-order shuffle; unit-tested same-seed-same-order) and the first shuffled full-suite run (seed 20260610) passed 455/0/0 on a loaded host — first order-coverage evidence for chain B. Remaining: the 5-consecutive-run idle-host soak | n/a (test infra) | `pytest tests/` green across 5 consecutive runs on an idle host | shuffled chunk order (`--shuffle-seed`) stays green — first pass 2026-06-10 |
