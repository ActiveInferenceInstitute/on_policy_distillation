# active_inference_on_policy_distillation docs

Documentation for the public Active Inference multi-track exemplar (analytical,
pymdp, sheaf manuscript, Lean/GNN/ontology, provenance, replay matrix,
counterexamples, toy sweeps, uncertainty, benchmark, model-checking, interop,
semantic gluing, dependency graph, evidence fields, release bundle, theorem
traceability, gate ergonomics, generated track-improvement scope, blocked-scope,
and adversarial audit) composed into a sheaf manuscript.

- `reference/method-inventory.md` — generated coverage for every Python `def`
  and `class` under `src/` and `scripts/`; refresh with
  `uv run python scripts/generate_method_inventory.py`.
- `reference/rendering-reproducibility.md` — authored contract for sheaf
  composition, hydration, figure rendering, artifact regeneration order, and
  root output parity.
- See the project root `README.md` for the overview and `AGENTS.md` for agent
  guidance; per-directory `README.md`/`AGENTS.md` pairs document each component.

Run the project:

```bash
uv run --extra dev python -m pytest tests/ -m "not artifact_slow and not render_slow" --no-cov
uv run --extra dev python -m pytest tests/ -m "not artifact_slow" --no-cov
uv run python -m pytest tests -q
uv run python scripts/validate_outputs.py
```

The fast lane excludes tests that perform full fixed-point artifact writes or
mutate shared generated artifacts. The tighter edit loop also excludes expensive
rendering, animation, rollout, and large-compose checks. The full coverage gate
remains authoritative.

Render through the sibling template checkout after linking sidecar projects:

```bash
cd ../../../template
uv run python -m infrastructure.orchestration link-projects
uv run python scripts/03_render_pdf.py --project working/active_inference_on_policy_distillation
```
