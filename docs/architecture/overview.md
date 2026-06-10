# System Overview

This exemplar proves a *scoped* correspondence — on-policy distillation is active
inference where the variational posterior generates its own observations and the
generative model is conditioned on privileged beliefs — and then refuses to let
any reported number escape machine checking. The system has one job beyond the
science: every figure, count, and claim in the PDF must trace back to a
deterministic generator, through a typed artifact, through a single hydration
boundary, before it is allowed onto the page.

## The six layers

The repository is organized as six cooperating layers. The first three produce
evidence; the last three compose, hydrate, and check it.

| Layer | Home | Produces | Role |
| --- | --- | --- | --- |
| Analytical oracle | [`src/analytical/`](../../src/analytical/) | closed-form sweeps, the free-energy decomposition identity, core invariants | The hard-to-vary mathematical ground truth (Ising/Bernoulli toy, mutual information, decomposition). |
| pymdp simulation | [`src/simulation/`](../../src/simulation/) | T-maze sophisticated-inference rollout, policy comparison, posterior grid, runtime diagnostics | The on-policy student: a real pymdp `sophisticated_inference` planner, logged step by step. |
| firstprinciples classroom | [`src/firstprinciples/`](../../src/firstprinciples/) | correspondence map, divergence geometry, reward-tilted target, SDPG/exposure-bias demos, two-agent classroom | The intellectual core — the audited active-inference ↔ OPD dictionary and the executable teacher/student classroom. |
| Sheaf manuscript compose | [`src/manuscript/sheaf/`](../../src/manuscript/sheaf/) | flat `manuscript/NN_*.md`, coverage matrix, layers report | Glues per-section track fragments into flat IMRAD sections, verifying the sheaf axioms first. |
| Gates / validation | [`src/gates/`](../../src/gates/), [`src/validation_spine/`](../../src/validation_spine/) | `output/reports/validation_report.json`, invariants, schema checks | The fail-closed acceptance surface — re-derives aggregates, validates schemas, checks invariants. |
| Formal layers | [`lean/`](../../lean/), [`src/gnn/`](../../src/gnn/), [`src/ontology/`](../../src/ontology/), [`src/roadmap_tracks/formal_interop.py`](../../src/roadmap_tracks/formal_interop.py) | Lean theorem inventory, GNN round-trip, ontology concordance, model-checking witnesses | Machine-checked *boundary* witnesses and cross-track notation agreement. |

Layer detail lives in the focused pages: the compose layer in
[`sheaf-compose-contract.md`](sheaf-compose-contract.md), the gate layer in
[`gates-and-validation.md`](gates-and-validation.md), and the formal layer in
[`formal-layers.md`](formal-layers.md). The producer layers and their scripts are
documented in [`pipeline.md`](pipeline.md).

## How a number travels to the page

The defining property of this exemplar is that no volatile number is typed into
prose. Follow one value — say a T-maze rollout statistic — through the whole
chain:

1. **Generator script.** A thin orchestrator under
   [`scripts/`](../../scripts/) (here `simulate_si_tmaze.py`) imports the tested
   code in `src/simulation/`, runs the deterministic rollout, and writes a typed
   JSON artifact. Scripts do I/O and orchestration only; the algorithm lives in
   `src/`.
2. **`output/data/*.json` artifact.** The run lands in a schema-tagged file such
   as `output/data/si_tmaze_summary.json`. The artifact is the unit of evidence —
   downstream layers read it, never the script's stdout.
3. **Hydration token.** Composed sections may carry `{{token}}` placeholders.
   The **single hydration boundary** is
   [`scripts/z_generate_manuscript_variables.py`](../../scripts/z_generate_manuscript_variables.py),
   which resolves tokens from `output/data/manuscript_variables.json`. Per the
   [rendering contract](../reference/rendering-reproducibility.md), composition
   may *emit* placeholders but only hydration *substitutes* them; unknown
   placeholders and single-brace typos fail closed.
4. **Composed section.** Before any of this, the sheaf composer
   ([`scripts/compose_manuscript.py`](../../scripts/compose_manuscript.py)) glued
   the section's per-track fragments — prose, formalism, pymdp, visualization —
   into a flat `manuscript/NN_*.md`, after verifying the sheaf laws.
5. **PDF.** The render step produces `output/pdf/*`. Per the contract, PDF and
   web outputs are render results, not sources of truth; figure numbering belongs
   to pandoc-crossref.

Between steps 2 and 5 the gate layer runs: `validate_outputs` re-derives stored
aggregate booleans from their own rows (so a hand-edited flag cannot lie),
validates artifact schemas, and checks the analytical and simulation invariants.
A red gate stops the chain.

```bash
# Run the producers, converge the attestation fixed point, validate.
uv run python scripts/run_full_chain.py
```

## Why a convergent runner exists

The release attestation attests the *previous* `validation_report.json`, so a
single linear pass can leave the attestation one step stale. Rather than ask the
operator to "re-run the tail and validate again" by hand,
[`scripts/run_full_chain.py`](../../scripts/run_full_chain.py) encodes the
canonical script order from `manuscript/config.yaml`, then re-runs the
convergence tail and re-validates to a bounded fixed point (`--max-passes`,
default 3). Its exit code is honest: 0 only when the final `validate_outputs`
pass is green. See [`pipeline.md`](pipeline.md) for the full order.

## What the system deliberately does not do

- It does not claim non-toy graph-world sophisticated inference or empirical
  biological behavior; the graph-world track writes deterministic summary/trace
  artifacts only (see [`../AGENTS.md`](../AGENTS.md)).
- It does not make network or LLM calls on the default path.
- The formal layers prove *boundary* facts and manuscript consistency, **not**
  the scientific thesis itself — see [`formal-layers.md`](formal-layers.md).
