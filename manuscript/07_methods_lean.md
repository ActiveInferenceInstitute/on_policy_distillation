# Lean formalization boundary {#sec:methods_lean}

<!-- sheaf-track:prose -->

The Lean track elevates the central correspondence from prose into machine-checked guarantees about the fixed points of the distillation/inference objective. Under `lean/TemplateActiveInference/`, minimal boundary witnesses are checked by `lake build` so that the structural claims tying on-policy distillation to active inference hold not by assertion but by proof. The two load-bearing witnesses are the optimum and the planning conditions. The first formalizes that the per-token reverse-KL distillation loss—identical in form to the variational free energy contribution $D_{KL}(q\|p)$—is zero if and only if the student policy equals the teacher policy, i.e. $q(s)$ coincides with $p(o,s)$ on the relevant support; the variational posterior has nothing left to infer exactly when it reproduces the privileged generative model. The second formalizes that sophisticated inference—the teacher conditioned on the student's own verified traces, as in OPSD [@zhao2026opsd] and SDPG [@liu2026sdpg]—requires a strictly positive search horizon: with horizon zero the expected-free-energy planner collapses to a greedy posterior with no epistemic value, recovering the off-policy limit [@hinton2015distilling] rather than the on-policy regime [@agarwal2024gkd]. [@fig:lean_boundary_status] summarizes which statements are proved versus deferred; fragments cite theorem names without duplicating proof scripts in prose. These are guarantees about the minimal models only, not about production LLMs, but they pin the correspondence at exactly the points where the variational argument could otherwise smuggle in an assumption.

The horizon witnesses link back to the analytical toy ([@sec:methods_analytical]), where the reverse-KL optimum is the self-distillation mode-seeking limit of the entangled-versus-factorised free energy, and to the pymdp planning depth ([@sec:methods_pymdp]), where a positive horizon is what lets the on-policy student generate its own observations and act to minimise expected free energy. The Lean layer thus certifies, for these artifacts, the two inferential boundary conditions the rest of the manuscript reasons over.

<!-- sheaf-track:visualization -->

![Lean formalization boundary: module witnesses checked by lake build.](../output/figures/lean_boundary_status.png){#fig:lean_boundary_status width=90% fig-alt="Table figure listing Lean modules, declaration kinds, names, and proved versus sorry status under lean/TemplateActiveInference/."}

<!-- sheaf-track:lean -->

Lean module `TemplateActiveInference.SophisticatedInference` declares the finite planning-horizon witness used to mirror the pymdp SI search horizon {{si_tmaze_planning_horizon}}, alongside finite T-maze boundary witnesses such as `tmaze_two_forward_steps_reach_goal` and `tmaze_goal_absorbing`. It also contains constructive finite witnesses for graph-world reachability, finite policy enumeration, belief weights, and policy-posterior weights. These theorems formalize small finite boundaries shared with generated artifacts; they do *not* prove that the pymdp $q_\pi$ posterior is a general model of sophisticated inference. Axioms are audited with `#print axioms` (the gate whitelists only `propext`, `Classical.choice`, `Quot.sound`); see the Lean track gate.

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
