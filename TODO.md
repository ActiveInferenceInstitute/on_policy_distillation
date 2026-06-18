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

The project is a mature, validated multi-track toy Active Inference exemplar and
is **green**: `validate_outputs` ALL TRUE, `compose_manuscript --validate-only
--strict` clean, `lake build` green, the PDF renders with zero dangling
cross-references, and the full test suite passes.

The active-inference ↔ on-policy-distillation correspondence is built on both
halves and synthesised:

- **Passive (VFE):** the per-token reverse-KL distillation loss is variational
  free energy up to the evidence constant — an algebraic identity of the declared
  finite objects, two-route verified.
- **Active (EFE):** EFE-driven rollout selection closes the distillation gap; the
  toy-exact identity `gap_closed(pi) = H(r) - E_o[H(r|o)] = I(o;r) = epistemic`,
  a precision-weighted policy posterior, multi-state generality (`n,k in {3,4}`),
  a horizon-scaling sequential result, and the analytical↔pymdp bridge that
  predicts the sophisticated-inference agent's belief-entropy trajectory.
- **Formal + synthesis:** a sorry-free Lean finite chain-rule skeleton of the
  complement identity, and a result-integrity ledger that certifies the whole
  set is precise (tier-aware tolerances) and controlled (every result has a
  measured-margin negative control), cross-read against the live source
  artifacts.

Each result is a first-class audited artifact (re-derive-never-trust validator +
typed claim-ledger evidence + biting negative control), narrated in the
manuscript with hydrated tokens, and visualised. Live proofs belong in the
registry, project docs, generated certificates,
`output/data/track_improvement_scope.json`, and output reports rather than as
completed TODO work here.

## What remains

Everything below is **optional future deepening or externally-gated** — nothing
is blocking. In priority order:

1. **Owed verification:** `OPD-ACTIVE-XVENDOR-1` — the GPT-5.4/codex cross-vendor
   audit of the active-selection family (math + integration). Opus-family
   adversarial probes have stood in (PASS, proven not green-by-construction), but
   the cross-vendor blind-spot reduction is not yet present.
2. **Optional formal deepening:** `OPD-LEAN-REAL-IDENTITY-1` — promote the Lean
   witness from the integer chain-rule skeleton to the real-valued
   `I + H_b(sigma) = log 2` entropy identity. Requires adding a Mathlib toolchain
   (heavyweight; the current pinned Lean ships without it). Until then the
   real-valued form remains the two-route numerical witness.
3. **Human decision / external input (cannot proceed unilaterally):**
   - *Publish decision* — this exemplar is LOCAL-ONLY by design; if publishing,
     the release path is reserve-DOI-first → GitHub release → Zenodo.
   - *Venue/submission decisions* → unblock `REVIEW-FIGURE-RELOCATION-1` and
     `TMAZE-MATRIX-TABLE-1` (the paper is deliberately an auditable-artifact
     paper, so these are deferred to a venue choice).
4. **Environment-gated maintenance:** `AI-TEST-ISOLATION-1` — a fresh idle-host
   isolation soak with `complete_soak: true`.
5. **Intentionally blocked (do NOT build without the unblock artifacts + gates):**
   everything under "Blocked scope" — empirical/biological, private data,
   network-dependent, LLM-generated evidence, non-toy claims.

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
| `OPD-ACTIVE-XVENDOR-1` | Verification | Run the GPT-5.4/codex cross-vendor audit of the active-selection math and integration once quota is available. Opus-family adversarial probes have run (PASS); the cross-vendor blind-spot pass is not yet present. | Cross-vendor verdict + any fixes | no unaddressed CRITICAL/HIGH | n/a |
| `OPD-LEAN-REAL-IDENTITY-1` | Formal | Promote the Lean witness from the integer chain-rule skeleton to the real-valued `I + H_b(sigma) = log 2` identity. Requires adding Mathlib (real-valued entropy / `Real.log`) to the Lean toolchain. | New Lean theorem over reals | `lake build` + axiom audit clean; bound to the analytical numerical witness | A wrong-definition mutation fails the elaboration gate |
| `AI-TEST-ISOLATION-1` | Test infra | Complete a 5-consecutive-run idle-host soak. `run_test_isolation_soak.py` records repeated deterministic shuffled chunked runs incrementally; `--validate-report --require-complete` verifies seed continuity, failed chunk ids, failed tests, diagnostic completeness, and `complete_soak`. Chain-A stale-trust races are closed; remaining is a clean idle-host completion transcript. | `output/reports/test_isolation_soak.json` | five green consecutive idle-host runs with reported shuffle seeds and `complete_soak: true` | A red shuffled run is reported with its seed and tail, not re-rolled |
| `REVIEW-FIGURE-RELOCATION-1` | Visualization | At venue-submission time, decide whether dense dashboard figures should move to the supplement with simplified main-text replacements. Deliberately deferred because the current paper is an auditable artifact paper. | `figures.yaml` `section_figures` | compose and figure-source gates stay green | Figure lacks source artifact |
| `TMAZE-MATRIX-TABLE-1` | Visualization | At venue-submission time, convert `si_tmaze_model_matrices` into a generated table or move it fully to the supplement. Do not hand-typeset values; bind them to the matrix artifact. | generated table binding + matrix artifact | compose and figure gates stay green | Typeset values diverge from matrix artifact |

`tasks.yaml` is the taskboard metadata surface. `scripts/audit_roadmap_tasks.py`
keeps the open TODO rows, task status/progress, and blocked/deferred semantics in
agreement without making completed proof claims active roadmap work again.

## Completed and removed from active scope

The following work is implemented, audited, and no longer active TODO. Its proof
surface is the live artifact contract (`validate_outputs.py`,
`compose_manuscript.py --validate-only --strict`, the generated
semantic/provenance/dependency/evidence/release artifacts, the Lean inventory,
and their negative-control tests). Do not re-open without a new failure, a
changed venue requirement, or a changed artifact contract.

- **Active-selection program (`OPD-ACTIVE-INTEGRATE-1` and follow-ons):** the
  active/EFE half and its extensions — EFE rollout selection, precision posterior,
  multi-state generality, sequential horizon scaling, the analytical↔pymdp bridge
  (post-cue and per-step trajectory), the Lean chain-rule skeleton, and the
  result-integrity ledger — all promoted to first-class audited artifacts with
  figures, manuscript prose, typed claim rows, and biting controls.
- **Prior canonical hardening IDs:** `AI-ANALYTICAL-OBS-4`, `AI-PYMDP-EFE-3`,
  `AI-GRAPH-TOPOLOGY-3`, `AI-VIZ-PIXEL-2`, `AI-LEAN-BELIEF-3`, `AI-THEOREM-LINKS-1`,
  `AI-STALE-LIVE-1`, `AI-PYMDP-POLICY-3`, `AI-PYMDP-RUNTIME-3`, `AI-GNN-SHAPE-3`,
  `AI-ANIMATION-HASH-2`, `AI-CLAIM-PREDICATE-3`, `AI-SCOPE-ROWS-1`, `AI-GATE-INDEX-3`,
  `AI-ONTOLOGY-PROFILE-3`, `AI-MANUSCRIPT-TOKEN-3`, `AI-SEMANTIC-CLASSIFIED-1`,
  `AI-DEPENDENCY-FIELDS-1`, `AI-PROVENANCE-FIELDS-1`, `AI-RELEASE-PARITY-1`,
  `AI-EVIDENCE-FIELDS-1`, `AI-SYMBOL-SPINE-3`, `AI-STALE-SUMMARY-1`,
  `AI-EFE-NONVACUOUS-1`, `AI-STUB-DEPTH-1`, `AI-APPENDIX-HYDRATE-1`,
  `AI-APPENDIX-FIGURES-1`, `AI-HYGIENE-1`, and `QWEN-TABLE-PIN-1`.

## Live canonical supplemental artifacts

The IDs below are live canonical artifacts. They are intentionally not versioned
`_vN` tracks; future work should deepen these stable surfaces and keep the
promotion rule intact.

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
restrictions, gates, and negative controls. The falsifiable program for testing
the correspondence at scale is written into the discussion as a future research
direction, not as work to start unilaterally here.

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
