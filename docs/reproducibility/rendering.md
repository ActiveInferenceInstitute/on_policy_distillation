# Rendering quickstart

There are two ways to produce the PDF. The portable standalone renderer is all a
copy-out checkout needs; the sibling template path adds full-polish bookends and
post-processing. The authoritative contract for both is
[`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md);
this page is the quickstart.

Render only after the analysis tree is generated and validated — see
[`artifacts.md`](artifacts.md). The simplest correct sequence is
`uv run python scripts/run_full_chain.py --render`.

## Path 1 — standalone (portable)

`scripts/render_pdf.py` composes, hydrates, and renders the manuscript to
`output/pdf/on_policy_distillation.pdf` using only this project's code plus the
external `pandoc` and `xelatex` tools.

```bash
uv run python scripts/render_pdf.py
```

Typography is read from project-owned sources: margins from
[`../../manuscript/config.yaml`](../../manuscript/config.yaml)
(`metadata.geometry`), the dense 9 pt body from
[`../../manuscript/preamble.md`](../../manuscript/preamble.md), and red
hyperlinks from pandoc `colorlinks` variables set by the renderer. No
`infrastructure/` import is involved (see
[`standalone-vs-template.md`](standalone-vs-template.md)).

## Path 2 — through the sibling template checkout

The monorepo pipeline (`scripts/03_render_pdf.py` in the template repo, which
*does* use `infrastructure/`) adds transmission bookends, QR strips, and LaTeX
post-processing. This is the full-polish path and is **not** required to build
the PDF standalone. It needs the project linked into the template first:

```bash
cd ../../../template
uv run python -m infrastructure.orchestration link-projects
uv run python scripts/03_render_pdf.py --project working/active_inference_on_policy_distillation
```

After a root pipeline run, verify copied root output parity from both sides:

```bash
cd ../projects/working/active_inference_on_policy_distillation
uv run python scripts/validate_outputs.py
```

Project-local `output/**` is authoritative during generation; the template root
copies it to `output/working/active_inference_on_policy_distillation/**`. Final
acceptance inspects both. The semantic and release-bundle reports allow
render-deferred PDF/web rows before copy, but a root copy that fails to
hash-match is drift and fails the release-bundle check.

## Figure rendering contract (why a figure shows up at all)

Every figure id must exist in [`../../figures.yaml`](../../figures.yaml), have a
generator in `src/visualizations/figures.py`, write through
`figure_io.save_figure_png`, and appear in `output/figures/figure_registry.json`.
Captions and alt text may use hydration tokens, but figure *numbering* belongs to
pandoc-crossref. Reused figures must use unlabeled references rather than
duplicate labels. To add one, follow
[`../development/extending.md`](../development/extending.md#add-a-figure).

## Common failure modes

- **Dangling `??` in the PDF** — a cross-reference points at a figure or equation
  whose *definition* is missing or appears after its first reference. A figure
  reference without the figure's labelled definition (or a forward reference)
  renders as `??`. Ensure the figure id is fully wired (all six surfaces) and
  defined before it is referenced.
- **`{{token}}` appears literally in output** — either the token is not produced
  by `src/manuscript/variables.py`, or its format spec is outside `_TOKEN_RE` in
  `src/manuscript/hydrate.py`. The fail-closed collector cannot flag a spec it
  cannot parse, so check the regex before inventing new format specs. Numbers
  must enter through hydration, never hand-typed prose — missing tokens fail
  closed rather than silently rendering a wrong or blank value.
- **Gray cells on the coverage page** — a manifest binding points at a missing
  fragment path; check the section's `tracks:` block in
  `manuscript/sheaf/manifest.yaml` against the filesystem.
- **Validation red after a partial regen** — the attestation binds the validation
  report by hash, so a half-regenerated tree fails on staleness. Re-run the
  spine → audit → sheaf → variables chain and validate again (or just use
  `run_full_chain.py`).
- **Missing external tools** — the standalone renderer needs `pandoc` and
  `xelatex` on `PATH`; the project code itself does not provide them.

## See also

- [`artifacts.md`](artifacts.md) — generate and validate the tree before rendering.
- [`standalone-vs-template.md`](standalone-vs-template.md) — which render path applies.
- [`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md) — authoritative contract.
