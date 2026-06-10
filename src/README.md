# Source Modules

Reusable logic for the on-policy-distillation = active-inference research project (multi-track sheaf manuscript). Scripts under `../scripts/` are thin orchestrators that
import from here.

- `analytical/` — closed-form Active Inference math (free energy, Bernoulli toy,
  coupling, decomposition, joint distributions, hyperparameters).
- `firstprinciples/` — OPD/Active-Inference correspondence artifacts,
  divergence geometry, reward-tilting, exposure-bias, SDPG, taxonomy, statistics,
  and the two-agent pymdp classroom.
- `gnn/` — Generalized Notation Notation (GNN) model parsing, the model object,
  and cross-track concordance checks.
- `simulation/` — pymdp sophisticated-inference T-maze model, deterministic runner, policy-comparison artifacts, and scoped JAX/pymdp runtime diagnostics.
- `manuscript/` — sheaf composition and run-derived manuscript variable hydration.
- `validation_spine/` — canonical artifact producers (`CORE_ARTIFACT_PRODUCERS`), replay matrix, provenance, diffoscope, and attestation builders.
- `artifact_contracts.py` — typed artifact-contract declarations shared by gates and the validation spine.
- `ontology/` — shared ontology-term bindings used to keep tracks consistent.
- `orchestration/` — pipeline manifest describing the analysis stages.
- `gates/` — validation gates over generated outputs.
- `visualizations/` — deterministic figure generation.
- `roadmap_tracks/` — promoted toy sweep, formal interop, canonical sheaf-track, and integration-audit artifacts.
- `analysis.py`, `invariants.py` — top-level analysis entry points and invariant checks.
