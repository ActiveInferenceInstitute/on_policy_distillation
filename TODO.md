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

## Before first publication

The science is publication-grade: the full chain renders green, `validate_outputs`
is ALL TRUE, every reported number is hydrated from an audited artifact, the result
set is RedTeam-checked with no surviving overclaim, and the Lean layer is sorry-free
with every theorem axiom-audited. **Nothing in the science blocks a first release.**
What remains is release mechanics plus a few judgment calls.

**Metadata fixed in this pass (no longer open):**
- `LICENSE` file added (MIT, matching `config.yaml`, `CITATION.cff`, `.zenodo.json`).
- `CITATION.cff` + `.zenodo.json` version synced `0.4.0` → `1.0.0` to match
  `pyproject.toml` and `config.yaml` (the M1 gate only checks pyproject↔config, so
  this drift was real but un-gated).

**Decisions only the author can make (do not set unilaterally):**
- *Title* — `CITATION.cff` / `.zenodo.json` use the short "On-Policy Distillation is
  Active Inference"; `config.yaml` / `README` use the full "On-Policy Distillation as
  Active Inference in Finite Variational Models". Keep the short citation title or
  align to the full paper title.
- *License intent* — the project declares MIT in all three metadata files, but the
  umbrella template repo is Apache-2.0. Confirm MIT is intended for the standalone
  release.
- *Target repo* — `config.yaml` `github_repository: docxology/on_policy` (CITATION /
  .zenodo agree). Confirm owner + name (`docxology` vs `ActiveInferenceInstitute`)
  before the repo is created.

**Release mechanics (at publish time — needs credentials + an explicit go-ahead):**
- Reserve a Zenodo DOI first, bake `publication.doi` + `publication.version_doi` +
  the final `paper.date` into `config.yaml`, then **deterministically re-render** the
  DOI-stamped PDF before deposit (`scripts/publish_project_release.py`, or
  `09_archive_publication.py`). `CITATION.cff` `date-released` is re-stamped to the
  real release date at deposit.
- **Confidentiality:** this project lives under `projects/working/` — LOCAL-ONLY and
  gitignored in the template repo. Publishing means its **own** public repo; it must
  never be committed into the template (the `check_tracked_projects.py` gate enforces
  this).

**Recommended before tagging 1.0.0 (not a hard blocker):**
- `OPD-ACTIVE-XVENDOR-1` — the GPT-5.4/codex cross-vendor audit of the
  active-selection family (quota-gated; Opus-family adversarial probes have stood in
  and PASSED, but the cross-vendor blind-spot reduction is not yet present).

**Deferred to post-publication / venue time (not blockers):**
`OPD-LEAN-REAL-IDENTITY-1` (real-valued Lean identity, needs Mathlib),
`REVIEW-FIGURE-RELOCATION-1`, `TMAZE-MATRIX-TABLE-1` (venue-dependent figure
choices), `AI-TEST-ISOLATION-1` (idle-host soak). Detail in the Active roadmap below.
Everything under "Blocked scope" stays out of scope until its unblock gates exist.

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
