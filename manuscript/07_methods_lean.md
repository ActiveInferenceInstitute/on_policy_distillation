# Machine-checked correspondence (Lean) {#sec:methods_lean}

<!-- sheaf-track:prose -->

The Lean track is a boundary layer, not a proof of the full OPD=AI thesis. Its role is to make the finite assumptions used by the executable artifacts explicit: the centered Ising coupling witness, T-maze reachability and absorbing-goal witnesses, graph-world reachability witnesses, finite policy enumeration, finite belief-weight normalization, finite policy-posterior normalization, the positive-horizon witness for sophisticated inference, and the finite-channel chain-rule skeleton for the mutual-information complement identity. These are checked by `lake build` and extracted into `output/data/proof_extraction_index.json`, where {{proof_extraction_theorem_count}} theorem rows must match the Lean theorem inventory and constructive-token status is `{{proof_extraction_all_constructive}}`. The validation gates also fail if a theorem statement is dropped, if `sorry`, `axiom`, or `native_decide` appears, or if the generated theorem index diverges from `output/reports/lean_theorem_inventory.json`.

The central correspondence still lives in the analytical and simulation artifacts: the reverse-KL/variational-free-energy analogy is derived in [@sec:methods_analytical], while the positive-horizon on-policy sampling interpretation is exercised in the pymdp T-maze and graph-world traces. The Lean layer certifies the small finite boundaries those arguments depend on, including the parameterized `tmaze_goal_absorbing` witness, the `sophisticated_requires_horizon` witness, and the `mi_chain_rule` skeleton (with its `pragmatic_leaves_gap` negative control) that machine-checks the *algebraic structure* of the mutual-information complement identity the active-selection result rests on — `I(o;r) + E_o[H(r\mid o)] = H(r)` over the integers, with a strictly positive residual provably transferring strictly less than the prior entropy. This is deliberately the finite chain-rule skeleton, **not** the real-valued entropy identity `I + H_b(\sigma) = \log 2`, which remains the two-route numerical witness in [@sec:methods_analytical] (the Lean toolchain here ships without Mathlib's real-valued entropy). It does *not* prove a general theorem about pymdp's $q_\pi$ posterior, production language models, or all sophisticated-inference planners. The paper therefore treats Lean as a checked finite-witness interface: it binds the toy state machines and horizon assumptions to named theorem rows, then the Python gates bind those theorem rows to generated artifacts and manuscript claims.

That interface is intentionally redundant with the non-Lean finite checks rather than a replacement for them. `output/reports/model_checking_witnesses.json` contributes {{model_checking_witness_count}} exhaustive toy witnesses with all-pass status `{{model_checking_all_passed}}`; `output/data/theorem_traceability_matrix.json` contributes {{theorem_traceability_row_count}} linked theorem rows; and the Lean graph-world inventory witnesses {{lean_graph_world_topology_witness_count}} generated topology ids with all-topologies-witnessed flag `{{lean_graph_world_all_topologies_witnessed}}`. [@fig:lean_boundary_status] summarizes this proved-versus-deferred boundary without duplicating proof scripts in prose.

<!-- sheaf-track:visualization -->

![Lean formalization boundary: a table of modules, declaration kinds, names, and proved-versus-sorry status under `lean/OnPolicyDistillation/`, each row a witness checked by `lake build`. Proved rows mark the finite boundary claims in this inventory that are machine-verified, while any sorry row honestly demarcates the edge of what is formally established. The figure makes the trust boundary explicit: the compiled core is the declared finite witness set, not a general proof about all OPD or active-inference systems.](../output/figures/lean_boundary_status.png){#fig:lean_boundary_status width=90% fig-alt="Table figure listing Lean modules, declaration kinds, names, and proved versus sorry status under lean/OnPolicyDistillation/."}

<!-- sheaf-track:lean -->

The Lean `SophisticatedInference` boundary module declares the finite planning-horizon witness used to mirror the pymdp SI search horizon {{si_tmaze_planning_horizon}}, alongside finite T-maze boundary witnesses such as `tmaze_two_forward_steps_reach_goal` and `tmaze_goal_absorbing`. It also contains constructive finite witnesses for graph-world reachability, finite policy enumeration, belief weights, and policy-posterior weights. These theorems formalize small finite boundaries shared with generated artifacts; they do *not* prove that the pymdp $q_\pi$ posterior is a general model of sophisticated inference. Axioms are audited with `#print axioms` (the gate whitelists only `propext`, `Classical.choice`, `Quot.sound`); see the Lean track gate.

Build via `lake build` under `lean/`.

<!-- sheaf-track:model_checking -->

The `model_checking` fragment complements Lean with finite exhaustive witnesses. `output/reports/model_checking_witnesses.json` records {{model_checking_witness_count}} toy-state witnesses and reports `{{model_checking_all_passed}}` only when no counterexample is found in the enumerated state/action space.

This is deliberately narrower than a semantic proof of all Active Inference programs. It checks the finite T-maze and graph-world boundary objects used by this manuscript and exposes the witness inventory to the same artifact and claim gates as the Lean theorem inventory. The Lean graph-world inventory witnesses {{lean_graph_world_topology_witness_count}} generated toy topology ids, with all-topologies-witnessed flag `{{lean_graph_world_all_topologies_witnessed}}`; theorem traceability contributes {{theorem_traceability_row_count}} linked rows.

<!-- sheaf-track:theorem_traceability -->

The `theorem_traceability` fragment binds Lean theorem inventory rows to finite model-checking witnesses, manuscript claims, and evidence fields. `output/data/theorem_traceability_matrix.json` records {{theorem_traceability_row_count}} traceability rows and passes only when every theorem row is linked (`{{theorem_traceability_linked}}`).

<!-- sheaf-track:proof_extraction -->

### Proof extraction track

The `proof_extraction` track extracts Lean theorem statements and proof-source
metadata into `output/data/proof_extraction_index.json`. The index currently
contains {{proof_extraction_theorem_count}} extracted theorem rows, with
constructive-token status `{{proof_extraction_all_constructive}}`.

The extracted rows are checked against `output/reports/lean_theorem_inventory.json`
before the manuscript can render. This catches a false-green case where `lake build`
passes but a theorem silently falls out of the generated proof index; the gate requires
the theorem inventory and extracted proof rows to agree exactly.
