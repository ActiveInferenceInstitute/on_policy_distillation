# active_inference_on_policy_distillation TODO

This roadmap tracks remaining or externally-gated work only. It is not the
current artifact contract and it does not create publication claims. Current
publication claims remain deterministic, public, locally reproducible, and
toy-only. The live system uses stable canonical track IDs; future work should
deepen canonical tracks such as `provenance`, `replay_matrix`, `sensitivity`,
`uncertainty`, `model_checking`, `interop`, `adversarial_audit`,
`evidence_fields`, `release_bundle`, `theorem_traceability`, `gate_ergonomics`,
`artifact_diffoscope`, `proof_extraction`, `state_space_catalog`,
`causal_ablation`, `artifact_license`, and `release_notes` rather than adding
`_vN` siblings.

## Current baseline

The current system is a validated multi-track toy Active Inference exemplar with
canonical sheaf tracks, semantic gluing, dependency graph, typed claim evidence,
manuscript hydration, Lean/GNN/ontology checks, graph-world and animation
artifacts, and a blocked empirical boundary. Live proofs belong in the registry,
project docs, generated certificates, `output/data/track_improvement_scope.json`,
and output reports rather than repeated here as completed TODO work.

## Status & what's needed from here (2026-06-13, after verifier-first hardening)

**The project is mature and green — nothing here is blocking.** Full suite
validation is `validate_outputs` ALL TRUE after the Run-12 fixed-point tail;
compose strict and PDF rendering are green. Runs 10–12 landed the canonical
promotion chains that used to occupy this file as active TODO rows. They have
been removed from the active roadmap and now live in README/docs, generated
certificates, validation reports, and tests.

What remains is **optional future deepening or externally-gated**, in priority order:

1. **Needs a human decision / external input (cannot proceed unilaterally):**
   - *Venue/submission decision* → unblocks `REVIEW-FIGURE-RELOCATION-1` (move dense
     dashboard figures to a supplement) and `TMAZE-MATRIX-TABLE-1` (typeset table vs
     figure). Deliberately not done: current genre is an auditable artifact paper.
   - *Publish decision* — this exemplar is LOCAL-ONLY by design; if publishing, the
     release path is reserve-DOI-first → GitHub release → Zenodo (out of TODO scope).
2. **Additive deepening (doable in a future session, medium value, under the promotion rule):**
   - Live canonical artifacts now include `proof_dependency_graph`,
     `state_transition_table`, `ablation_sensitivity_report`, and
     `release_attestation`; the current verifier-first tranche deepens those
     same stable surfaces with edge, transition, join, and attestation checks.
     Future work should continue deepening these IDs rather than creating
     versioned siblings.
   - Remaining optional work is mostly venue- or release-process polish.
3. **Environment-gated maintenance:** `AI-TEST-ISOLATION-1` — the durable soak
   runner now writes and validates `output/reports/test_isolation_soak.json`
   from repeated deterministic shuffled chunked runs. A local diagnostic
   five-run soak on 2026-06-13 exposed order-sensitive stale-artifact failures
   under seeds 61300, 61301, and 61302; the reported failing chunk groups and a
   full same-seed 61300 rerun now pass after gate-surface refresh hardening. A
   loaded-host 2026-06-14 five-run transcript then produced green seeds 61300,
   61301, and 61302, followed by SIGTERM-style red rows at seed 61303 chunk 8
   and seed 61304 chunk 4 (`EXIT -15`, no pytest failures, `complete_soak: false`).
   The remaining closure item is still a fresh 5-consecutive-run
   idle-host transcript with `complete_soak: true`.
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

## Active roadmap

| ID | Area | Remaining improvement | Proving artifact | Gate or predicate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AI-TEST-ISOLATION-1` | Test infra | Complete the 5-consecutive-run idle-host soak. `run_test_isolation_soak.py` records repeated deterministic shuffled chunked runs incrementally, and `--validate-report --require-complete` verifies seed continuity, failed chunk ids, failed tests, diagnostic completeness, and `complete_soak`. The 2026-06-13 diagnostic soak exposed stale-artifact order failures that were hardened; the 2026-06-14 loaded-host transcript then failed only through SIGTERM-style chunk exits at seeds 61303 and 61304 with no pytest failures. A fresh idle-host completion transcript is still needed. | `output/reports/test_isolation_soak.json` | five green consecutive runs with fixed or reported shuffle seeds and `complete_soak: true` | Red shuffled run is reported with its seed and tail, not re-rolled |
| `REVIEW-FIGURE-RELOCATION-1` | Visualization | At venue-submission time, decide whether dense dashboard figures should move to the supplement with simplified main-text replacements. Deliberately deferred because the current paper is an auditable artifact paper. | `figures.yaml` `section_figures` | compose and figure-source gates stay green | Figure lacks source artifact |
| `TMAZE-MATRIX-TABLE-1` | Visualization | At venue-submission time, convert `si_tmaze_model_matrices` into a generated table or move it fully to the supplement. Do not hand-typeset values; bind them to the matrix artifact. | generated table binding + matrix artifact | compose and figure gates stay green | Typeset values diverge from matrix artifact |
| `OPD-ACTIVE-INTEGRATE-1` | Correspondence / sheaf | Promote the committed `firstprinciples.active_selection` result (EFE epistemic value = closeable distillation gap; commit `80053f5`) to a first-class audited artifact: register `active_selection_demo.json` in `artifacts.py write_all` + `artifact_contracts.py` (4 lists) + an `output_checks.py` read-time re-derivation validator + a `claim_ledger.py` typed predicate + `manuscript/variables.py` hydration tokens + a methods/results fragment + a `figures.yaml` figure (validity sweep + per-policy EFE/residual), and update the EFE row of `mapping.py` from "not minimized" to cite this result. | `output/data/firstprinciples/active_selection_demo.json` + bound fragment + figure | `validate_outputs` ALL TRUE + claim-ledger predicate + compose strict + PDF render, all six surfaces | Mutate a residual/epistemic row leaving `ok` true ⇒ re-derivation gate fails; blinded-cue control reopens gap |
| `OPD-ACTIVE-XVENDOR-1` | Verification | Disposition the Forge GPT-5.4 cross-vendor audit of the active-selection math/claim (launched 2026-06-17). | Forge verdict + any fixes | no unaddressed CRITICAL/HIGH | n/a |

`tasks.yaml` is the taskboard metadata surface. `scripts/audit_roadmap_tasks.py`
keeps the open TODO rows, task status/progress, and blocked/deferred semantics in
agreement without making completed proof claims active roadmap work again.

## Completed hardening removed from active scope

The following roadmap IDs are implemented and no longer active TODO work:
`AI-ANALYTICAL-OBS-4`, `AI-PYMDP-EFE-3`, `AI-GRAPH-TOPOLOGY-3`,
`AI-VIZ-PIXEL-2`, `AI-LEAN-BELIEF-3`, `AI-THEOREM-LINKS-1`,
`AI-STALE-LIVE-1`, `AI-PYMDP-POLICY-3`, `AI-PYMDP-RUNTIME-3`,
`AI-GNN-SHAPE-3`, `AI-ANIMATION-HASH-2`, `AI-CLAIM-PREDICATE-3`,
`AI-SCOPE-ROWS-1`, `AI-GATE-INDEX-3`, `AI-ONTOLOGY-PROFILE-3`,
`AI-MANUSCRIPT-TOKEN-3`, `AI-SEMANTIC-CLASSIFIED-1`,
`AI-DEPENDENCY-FIELDS-1`, `AI-PROVENANCE-FIELDS-1`,
`AI-RELEASE-PARITY-1`, `AI-EVIDENCE-FIELDS-1`, `AI-SYMBOL-SPINE-3`,
`AI-STALE-SUMMARY-1`, `AI-EFE-NONVACUOUS-1`, `AI-STUB-DEPTH-1`,
`AI-APPENDIX-HYDRATE-1`, `AI-APPENDIX-FIGURES-1`, `AI-HYGIENE-1`,
and `QWEN-TABLE-PIN-1`.

The proof surface for completed rows is the live artifact contract:
`validate_outputs.py`, `compose_manuscript.py --validate-only --strict`,
the generated semantic/provenance/dependency/evidence/release artifacts, and
their negative-control tests. Do not re-open completed IDs without a new
failure, changed venue requirement, or changed artifact contract.

## Live canonical supplemental artifacts

The IDs below are now live canonical artifacts. They are intentionally not
versioned `_vN` tracks; future work should deepen these stable surfaces and keep
the promotion rule intact.

| Canonical id | Purpose | Artifact | Manuscript binding | Gate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `proof_dependency_graph` | Expand extracted Lean proof dependencies into theorem-to-definition and witness edges | `output/data/proof_dependency_graph.json` | `methods_lean/proof_dependency_graph.md` | proof dependency validator plus `lake build`; requires unique edges, required edge types, and no orphan targets | Theorem dependency edge is dropped, duplicated, or pointed at an orphan target |
| `state_transition_table` | Emit explicit finite transition tables for every toy topology and T-maze action | `output/data/state_transition_table.json` | `results_invariants/state_transition_table.md` | transition-table validator; requires unique transition keys, outgoing coverage for every reachable state, and terminal self-transition coverage | Transition table omits a reachable state, duplicate key, outgoing transition, or terminal self-transition |
| `ablation_sensitivity_report` | Summarize causal-ablation effects against sensitivity and uncertainty rows | `output/reports/ablation_sensitivity_report.json` | `results_invariants/ablation_sensitivity_report.md` | ablation-sensitivity validator; requires explicit source join keys and source row-count agreement | Ablation effect is reported without source row or join key |
| `release_attestation` | Generate a compact attestation over validation report, bundle hash, license audit, and blocked scope | `output/reports/release_attestation.json` | `discussion_outlook/release_attestation.md` | release-attestation validator; requires attested source counts and validation check ids/counts to match the current report | Attestation claims a failed gate passed or reports stale attestation counts |

## Future sheaf tracks

The proposed ID below is not live. Do not add it to `manuscript/sheaf/tracks.yaml`,
`tracks.yaml`, manuscript fragments, or public claims until the promotion rule is
fully satisfied.

| Proposed id | Purpose | First artifact | First manuscript binding | First gate | Negative control |
| --- | --- | --- | --- | --- | --- |
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

1. Keep this roadmap limited to remaining work; completed live tracks belong in
   README, AGENTS, registries, generated outputs, and tests.
2. Deepen canonical semantic/dependency/provenance/evidence-field rows before
   adding another live track.
3. Prefer finite toy evidence, negative controls, and typed claim predicates
   over broader prose claims.
4. Leave `empirical_adapter` blocked until the unblock artifacts and gates above
   exist and fail closed.

## Known residual: idle-host isolation soak

Historical full-suite artifact-isolation races have been narrowed by symmetric
gate-cache eviction, file-chunk isolation, deterministic shuffle support, and
machine validation for persisted soak reports.
The remaining evidence task is a five-run idle-host soak. A loaded-host chunked
run on 2026-06-11 produced one red chunk followed by two exact chunk reruns that
passed. A diagnostic five-run local soak on 2026-06-13 recorded red seeds
61300, 61301, and 61302, then green seeds 61303 and 61304; the failing chunk
groups and a full same-seed 61300 rerun now pass after refresh hardening. A
loaded-host five-run soak on 2026-06-14 recorded green seeds 61300, 61301, and
61302, then red rows for seed 61303 chunk 8 and seed 61304 chunk 4; both were
`EXIT -15` with no pytest failures in the emitted tail, so `complete_soak`
remains false. Treat any future red shuffled run as evidence to report with the
seed and emitted failure tail.

| ID | Area | Improvement | Proving artifact | Gate or predicate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AI-TEST-ISOLATION-1` | Test infra | **PARTIAL:** chain-A stale-trust race closed; `run_tests_chunked.py --shuffle-seed N` provides deterministic file-order coverage; failure tails are emitted for red chunks; `run_test_isolation_soak.py` writes an incremental repeated-run report; the 2026-06-13 red diagnostic chunks and full same-seed 61300 rerun are now green after refresh hardening; the 2026-06-14 loaded-host five-run transcript preserved new SIGTERM-style red rows at seeds 61303 and 61304. Remaining: the 5-consecutive-run idle-host soak with `complete_soak: true` | `output/reports/test_isolation_soak.json` | chunked equivalent green across 5 consecutive idle-host runs | shuffled chunk order (`--shuffle-seed`) is reported with exact seed and tail if red |
