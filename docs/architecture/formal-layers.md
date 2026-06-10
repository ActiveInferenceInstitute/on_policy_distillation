# Formal Layers

The exemplar carries four machine-checked formal layers: Lean 4 proofs, GNN model
specifications, Active Inference Ontology bindings, and a model-checking/interop
spine that ties them together. They are the strongest checks in the project, and
also the most easily over-read. The governing caveat, stated up front:

> The formal layers prove **boundary witnesses and manuscript/notation
> consistency, not the scientific thesis**. That on-policy distillation *is*
> active inference is argued by the firstprinciples correspondence map and the
> analytical/pymdp evidence — the formal layers prove finite facts *around* that
> argument and that the tracks agree with each other.

## Lean witnesses

[`lean/`](../../lean/) is a Lean 4 project (`lakefile.lean`, pinned
`lean-toolchain`) with proof modules under
[`lean/OnPolicyDistillation/`](../../lean/OnPolicyDistillation/):
`BernoulliToy.lean` and `SophisticatedInference.lean`. The theorems are small,
decidable boundary facts about the toy models the Python harness uses — for
example (verbatim from the sources):

- `ising_coupling_sum_zero` — the centered 2×2 Ising coupling entries sum to zero
  (`by decide`).
- `sophisticated_requires_horizon` — the default policy length `3 > 1`
  (sophisticated inference needs a horizon).
- `tmaze_two_forward_steps_reach_goal` and `tmaze_goal_absorbing` — the finite
  T-maze transition reaches and absorbs at the goal (`by rfl`).
- the graph-world reachability theorems (`graph_world_three_steps_reach_goal`,
  `branch_graph_world_three_steps_reach_goal`,
  `loop_graph_world_four_steps_reach_goal`,
  `diamond_graph_world_four_steps_reach_goal`).

The generator
[`build_lean_theorem_inventory`](../../src/roadmap_tracks/formal_interop.py)
writes `output/reports/lean_theorem_inventory.json` with each theorem's name and
status, an `all_proved` flag, a `theorem_count`, and a `forbidden_tokens` scan
(`sorry`/`axiom`/`native_decide`). The gate requires `all_proved is True`.
`build_proof_extraction_index` additionally extracts each theorem's statement and
leading tactic and cross-checks the set against the inventory, so a proof-index
row with no matching Lean theorem (or vice versa) is a `proof_inventory_mismatch`.

The Lean gate runs only when `lean/lakefile.lean` is present (`build_lean`); the
build must exit 0. See [`gates-and-validation.md`](gates-and-validation.md).

**What Lean does not prove.** These are decidable finiteness/reachability/
normalization facts about the *toy boundary*. They do not establish the
active-inference ↔ OPD correspondence, nor any non-toy or empirical claim.

## GNN specifications and concordance

[`gnn/`](../../gnn/) holds the canonical, human- and machine-readable model
specs: `bernoulli_toy.gnn.md` and `si_tmaze.gnn.md`. They are parsed by
[`src/gnn/parser.py`](../../src/gnn/parser.py) and checked by
[`src/gnn/concordance.py`](../../src/gnn/concordance.py).

Concordance is a *correctness*, not merely *presence*, check. `parity_gaps`
defaults to presence (a variable is declared and carries some ontology
annotation), but with `expected_terms` supplied it requires each variable to map
to a *specific* ontology term — so a variable silently re-annotated to a
different-but-valid term is caught, not waved through. The expected maps are
pinned constants: `BERNOULLI_SYMBOL_MAP` / `BERNOULLI_EXPECTED_TERMS` in
`concordance.py` and `SI_SYMBOL_MAP` / `SI_EXPECTED_TERMS` in
[`src/ontology/bindings.py`](../../src/ontology/bindings.py).

`generate_formal_interop_tracks.py` writes `gnn_roundtrip_report.json` (the
parse → payload → re-emit → re-parse losslessness check) and
`gnn_lint_report.json`. The round-trip writer deliberately re-emits only the
structural payload (variables, dims, dtype, edge direction/label, ontology term);
non-payload content (`InitialParameterization` values, `ModelParameters`,
`Equations`) is outside the structural round-trip contract.

**What GNN does not prove.** Round-trip losslessness proves the *notation* is
internally consistent and faithfully serialized — not that the model is correct
or that it matches the running pymdp harness's numerics.

## Ontology bindings

[`src/ontology/bindings.py`](../../src/ontology/bindings.py) loads per-section
ontology YAML (`load_section_ontology`) and validates GNN ↔ ontology agreement
across both toy models (`validate_all_gnn_ontology`). The Bernoulli toy binds
symbols such as `J → CrossStreamCouplingPotential` and `lam →
EntanglementDeformationParameter`; the SI T-maze binds `loc → HiddenState`,
`obs_* → ObservationLikelihood`, `q_pi → PolicyPosterior`,
`belief_entropy → BeliefEntropy`. `generate_formal_interop_tracks.py` writes the
ontology alias index and profile matrix.

**What ontology does not prove.** Bindings prove the manuscript's vocabulary maps
onto the Active Inference Ontology consistently across tracks — a cross-track
agreement check, not a scientific validity check.

## Model-checking and interop spine

[`src/roadmap_tracks/formal_interop.py`](../../src/roadmap_tracks/formal_interop.py)
ties the layers together. `build_model_checking_witnesses` derives each witness
row from a *real* finite enumeration plus a Lean binding — never a literal
constant: graph-world reachability is established by actually walking the declared
topology trace, and **every row additionally requires its corresponding Lean
theorem to be present in the proved inventory**. T-maze normalization properties
re-derive from the generated model-matrix audit. A missing artifact, missing
theorem, or failed walk fails the row; there is no constant-`True` path. The
report (`output/reports/model_checking_witnesses.json`,
`...model_checking_witnesses.v1`) carries per-row `counterexamples`,
`finite_space_size`/`state_count`, the bound `lean_theorem`, a `witness_count`,
and an `all_passed` flag that is `True` only when every row passes with no
counterexamples. `build_interop_roundtrip_report` writes the
GNN ↔ JSON interop round-trip.

**What model-checking does not prove.** These are *finite, exhaustive*
enumerations over small toy state spaces, gated on the Lean inventory. They prove
the toy models reach/normalize as claimed and that the witnesses are anchored to
proved theorems — not anything about scaled systems, real agents, or the
correspondence thesis.

## Summary: the boundary of the boundary

| Layer | Proves | Does **not** prove |
| --- | --- | --- |
| Lean | Decidable finite facts of the toy models (reachability, absorption, normalization, horizon), zero forbidden tokens | The OPD ↔ active-inference thesis; any non-toy or empirical claim |
| GNN | Notation parses and round-trips losslessly; variables carry their expected ontology terms | Model correctness or agreement with running numerics |
| Ontology | Cross-track vocabulary maps onto the Active Inference Ontology consistently | Scientific validity |
| Model-checking / interop | Toy reachability/normalization by real finite walks, each anchored to a proved Lean theorem; interop round-trips | Behavior of scaled or empirical systems; the thesis |

The scientific argument lives in [`src/firstprinciples/`](../../src/firstprinciples/)
and the analytical/pymdp evidence; see [`overview.md`](overview.md). The formal
layers make the *scaffolding around* that argument machine-checkable and
internally consistent.
