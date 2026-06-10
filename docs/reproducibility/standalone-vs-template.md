# Standalone vs. template

This project is designed to live on its own. Copy
`working/active_inference_on_policy_distillation/` out of the monorepo and it is
a complete, runnable GitHub repository. The full statement is in
[`../../STANDALONE.md`](../../STANDALONE.md); this page summarizes when the
project runs standalone, when it benefits from the sibling template, and what
`infrastructure.*` imports exist (none in the shipped surface).

## No infrastructure imports in the project surface

**No code under `src/`, `scripts/`, or `tests/` imports the monorepo's
`infrastructure/` layer or any sibling project.** This is enforced, not
conventional, by `tests/test_self_contained.py`: a static AST scan plus a
clean-room import with the `infrastructure` module blocked. So the answer to
"what `infrastructure.*` imports exist?" is: none in the project's own code. The
only place `infrastructure/` appears is the *optional* full-polish render path,
which runs from inside the sibling template checkout, not from this project's
code.

## What runs standalone

Everything except the full-polish render. From the project root:

| Step | Command | Depends on |
| --- | --- | --- |
| Tests + coverage | `uv run python -m pytest tests/` | project `src/` only |
| Analytical sweep | `uv run python scripts/run_analytical_sweep.py` | numpy/scipy |
| pymdp T-maze rollout | `uv run python scripts/simulate_si_tmaze.py` | `inferactively-pymdp` |
| Statistics + figures | `uv run python scripts/compute_statistics.py && uv run python scripts/generate_figures.py` | matplotlib |
| Compose manuscript | `uv run python scripts/compose_manuscript.py` | project sheaf engine |
| Validate gates | `uv run python scripts/validate_outputs.py` | project `src/gates/` |
| **Render PDF** | `uv run python scripts/render_pdf.py` | `pandoc`, `xelatex` (external CLIs) |

The portable renderer composes, hydrates, and renders to
`output/pdf/on_policy_distillation.pdf` using only this project's code plus
`pandoc` and `xelatex`. See [`rendering.md`](rendering.md) for both render paths.

## When you need the template

Only for the full-polish render and its copied-root-output parity check. The
template pipeline (`scripts/03_render_pdf.py`, which *does* use
`infrastructure/`) adds transmission bookends, QR strips, and LaTeX
post-processing, and copies project-local `output/**` to
`output/working/active_inference_on_policy_distillation/**`. Link the project in
first:

```bash
cd ../../../template
uv run python -m infrastructure.orchestration link-projects
uv run python scripts/03_render_pdf.py --project working/active_inference_on_policy_distillation
```

That extra polish is a superset of, not a requirement for, the standalone PDF.

## The generic-engine / bespoke-registry split

The sheaf composition engine is reusable code; the bespoke binding lives in
data, which is what makes the project copy-out-and-run:

- **Engine (code)** — `src/manuscript/sheaf/` (`laws.py` sheaf-axiom oracle,
  `compose.py`, `coverage.py`, `manifest.py`, `registry.py`, `renderers.py`,
  `models.py`).
- **Bespoke registry (data)** — `manuscript/sheaf/manifest.yaml` (IMRAD rows →
  fragments), `manuscript/sheaf/tracks.yaml` (track registry),
  [`../../figures.yaml`](../../figures.yaml), [`../../pymdp.yaml`](../../pymdp.yaml).

To reuse the engine elsewhere, copy `src/manuscript/sheaf/` and supply your own
manifest/registry/figures YAML — the engine reads them and hard-codes none of
this project's content. Keeping the engine *in the project* rather than in shared
infrastructure is the deliberate choice that keeps the checkout standalone.

## See also

- [`../../STANDALONE.md`](../../STANDALONE.md) — the authoritative standalone guide.
- [`rendering.md`](rendering.md) — the two render paths in detail.
- [`../development/conventions.md`](../development/conventions.md) — the thin-orchestrator rule behind self-containment.
