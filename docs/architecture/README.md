# Architecture documentation

Reader-facing architecture notes for the Active Inference on-policy-distillation
exemplar. These pages describe how the system is structured and how an authored
number becomes a machine-checked PDF — they do not duplicate the API-level
[`../reference/`](../reference/) contracts, which remain authoritative for the
rendering/reproducibility, method-inventory, and notation surfaces.

| Page | Summary |
| --- | --- |
| [`overview.md`](overview.md) | The system at a glance: the six layers (analytical oracle, pymdp simulation, firstprinciples classroom, sheaf compose, gates/validation, formal Lean/GNN/ontology) and how one number travels generator → `output/data/*.json` → hydration token → composed section → PDF. |
| [`pipeline.md`](pipeline.md) | The artifact regeneration order: every script under [`../../scripts/`](../../scripts/), what each produces under `output/`, and why [`run_full_chain.py`](../../scripts/run_full_chain.py) is the canonical convergent runner. |
| [`sheaf-compose-contract.md`](sheaf-compose-contract.md) | The sheaf track system: registry, manifest, the six verified sheaf laws, negative controls, and how per-section track fragments glue into flat IMRAD sections. |
| [`gates-and-validation.md`](gates-and-validation.md) | The fail-closed gate system: what is re-derived at read time vs trusted, schema validators, and the analytical/simulation invariant checks. |
| [`formal-layers.md`](formal-layers.md) | Lean witnesses, GNN concordance, ontology bindings, and model-checking interop — and, critically, what each layer does **not** prove. |

## Conventions

- Implementation lives in [`../../src/`](../../src/), orchestration in
  [`../../scripts/`](../../scripts/), generated artifacts under
  [`../../output/`](../../output/). These pages are documentation only.
- Counts and guarantees stated here are sourced from files in the repository.
  When a number is volatile (track count, theorem count), the manuscript reads
  it from a generated artifact, never from prose — see
  [`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md).

## Verification

```bash
uv run python scripts/run_full_chain.py
uv run python scripts/validate_outputs.py
```
