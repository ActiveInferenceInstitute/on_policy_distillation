# Extending the project

A task-oriented quickstart for the four most common extensions. The full,
verified-against-the-tree reference is
[`../reference/configuration-and-extension.md`](../reference/configuration-and-extension.md)
— this page links into it rather than restating it. Read that reference before a
non-trivial change; the surfaces below cascade test failures if one is missed.

## Choosing where a knob goes

New behavioural knobs go in exactly one place:

- simulation → [`../../pymdp.yaml`](../../pymdp.yaml)
- visualization → [`../../figures.yaml`](../../figures.yaml)
- methods hyperparameters → a frozen dataclass field in `src/firstprinciples/`
  (never a buried literal)

The advisory files (`domain_profile.yaml`, `experiment_plan.yaml`,
`tasks.yaml`) are human-readable planning metadata, **not** switches — see the
[configuration map](../reference/configuration-and-extension.md#configuration-map-every-knob-and-its-consumer).

## Add a figure

A figure that misses one surface cascades ~10 failures
(`all_figures_mapped=false` propagates). The six surfaces, in order, are:
generator → registry dict → `figures.yaml` entry → section binding → source map
→ prose. Each is spelled out with the exact module and dict names in
[Add a figure (the six surfaces)](../reference/configuration-and-extension.md#add-a-figure-the-six-surfaces).

Quick rules of thumb:

- Generator (`figure_<id>(project_root) -> Path`) reads **only** from generated
  artifacts, derives any "shown N of M" counts from the loaded rows, and saves
  via `save_styled_figure` / `save_figure_png`.
- Captions and alt text use `{{token}}` hydration — no hand-typed numbers. Check
  any new format spec against `_TOKEN_RE` in `src/manuscript/hydrate.py`; a spec
  the regex does not match is silently left unsubstituted.

Then regenerate and verify:

```bash
uv run python scripts/generate_figures.py
uv run python scripts/generate_integration_audit.py
uv run python scripts/z_generate_manuscript_variables.py
uv run --extra dev python -m pytest tests/test_figures.py --no-cov -q
```

## Add a sheaf track / manuscript section

1. Declare the track in
   [`../../manuscript/sheaf/tracks.yaml`](../../manuscript/sheaf/tracks.yaml)
   (order, renderer — usually `markdown`, label, `optional` flag).
2. Bind fragments per section in
   [`../../manuscript/sheaf/manifest.yaml`](../../manuscript/sheaf/manifest.yaml).
3. Author the fragments; hydrate all numbers via `{{tokens}}`.
4. If the track has a generated artifact, follow the promotion rule in
   [`../../TODO.md`](../../TODO.md): producer script, deterministic artifact,
   manuscript consumer, typed claim, semantic restriction, validation gate, and a
   negative control. Artifact contracts live in `src/artifact_contracts.py`.
5. Keep compose green:

```bash
uv run python scripts/compose_manuscript.py --validate-only --strict
```

Full step list: [Add a sheaf track](../reference/configuration-and-extension.md#add-a-sheaf-track).

## Add a model / track to the pipeline

Pipeline tracks, gates, and extension artifacts are declared in
[`../../tracks.yaml`](../../tracks.yaml); update it when a track gains artifacts
or scripts (per [`../../AGENTS.md`](../../AGENTS.md)). Keep the analytical,
first-principles, simulation/pymdp, GNN, ontology, Lean, visualization, and
validation-spine tracks concordant — same objects, notation, and claims — using
`gnn/concordance.py`, `src/validation_spine/`, and `src/gates/validation.py`.

Do **not** add network calls or LLM calls to the default exemplar path, and do
not claim non-toy graph-world SI or empirical biological behavior in prose.

## After editing X

Use the canonical *what to run after editing X* table in the reference:
[What to run after editing X](../reference/configuration-and-extension.md#what-to-run-after-editing-x).
When unsure, run the convergent one-command chain:

```bash
uv run python scripts/run_full_chain.py
```

It encodes the canonical producer order and converges the attestation fixed
point with bounded retry — see
[`../reproducibility/artifacts.md`](../reproducibility/artifacts.md) and the
[producer order](../reference/rendering-reproducibility.md#producer-order).

## See also

- [`../reference/configuration-and-extension.md`](../reference/configuration-and-extension.md) — authoritative reference (knobs, surfaces, troubleshooting).
- [`conventions.md`](conventions.md) — thin-orchestrator and writer/validator rules every extension must obey.
- [`../reproducibility/rendering.md`](../reproducibility/rendering.md) — how the composed manuscript becomes a PDF.
