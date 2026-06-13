# Figures: Inventory and Provenance

How figures are declared, generated, captioned, and bound to their source data. Derived
from [`../../figures.yaml`](../../figures.yaml) (structure only — it is large),
[`../../scripts/generate_figures.py`](../../scripts/generate_figures.py),
[`../../src/visualizations/figure_registry.py`](../../src/visualizations/figure_registry.py),
the figure-source / hash gates in
[`../../src/gates/output_checks.py`](../../src/gates/output_checks.py) and
[`../../src/roadmap_tracks/integration_audit_artifacts.py`](../../src/roadmap_tracks/integration_audit_artifacts.py),
and the figure tables in [`../../manuscript/SYNTAX.md`](../../manuscript/SYNTAX.md).

## Source of truth

[`../../figures.yaml`](../../figures.yaml) is the single source of truth for figure ids,
captions, alt text, widths, and section bindings (echoed in
[`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md):
the stale second registry `manuscript/refs/labels.yaml` is intentionally absent). Its
top-level structure is:

- **style block** — `dpi`, `transparent: false`, `font_scale`, `grid`, and a named
  `palette` (pass/fail/proved/sorry colors, etc.), loaded by
  `src/visualizations/figure_style.py`.
- **`figures:`** — one entry per registry figure id. Each entry carries `filename`,
  `alt` (verbose accessibility description), `caption` (the numbered figure caption), and
  `width` (fractional page width).
- **`section_figures:`** — binds figure ids to IMRAD sections (e.g. `results_invariants`
  → `invariant_dashboard`, `diversity_tradeoff`). An entry may set `labeled: false` for a
  deliberate repeated embedding (e.g. `si_tmaze_model_matrices` reappears in
  `results_si_tmaze`); prefer one canonical labeled occurrence per result figure.

## Generation

[`../../scripts/generate_figures.py`](../../scripts/generate_figures.py) is a thin
orchestrator: it calls `generate_all_figures(PROJECT_ROOT)` from
`src/visualizations/figures.py` and prints each output path. Generators are organized by
module — `figures`, `figures_interpretability`, `figures_diagrams`, `figures_sheaf`,
`figures_validation`, `figures_abstract` — and the id→generator mapping is tabulated in
[`../../manuscript/SYNTAX.md`](../../manuscript/SYNTAX.md) (e.g.
`figure_ising_mi_curve`, `figures_interpretability.figure_correspondence_map`).

Figures are **deterministic**: no sampling, fixed inputs. Captions say so explicitly
(e.g. "Both curves are deterministic closed forms, so no uncertainty intervals apply"),
which is itself a scope guardrail — a deterministic figure cannot carry an implied
statistical claim.

## Where figures land

PNGs are written to `output/figures/` (referenced in the section markdown as
`../output/figures/<filename>.png`). `output/figures/figure_registry.json` materializes
the registry. As with all of `output/`, these are **regeneratable artifacts**, not
sources of truth — never hand-edit a PNG or its embedded numbers to make a claim pass;
regenerate the producer.

## Figure → source-map discipline

Every figure is bound to the data artifact(s) that produced it. `build_figure_source_map()`
in
[`../../src/roadmap_tracks/integration_audit_artifacts.py`](../../src/roadmap_tracks/integration_audit_artifacts.py)
emits `output/data/figure_source_map.json` (schema
`template_active_inference.figure_source_map.v1`) with, per registry figure: its
`sources` (relative data paths), whether those `source_paths_exist`, its caption/alt
tokens, image dimensions, and a `mapped` flag. The gate
`_figure_source_map_ok()` in
[`../../src/gates/output_checks.py`](../../src/gates/output_checks.py) passes **only**
when the schema matches, `all_figures_mapped is True`, and every row's source rows are
complete. Captions reinforce this by naming their source inline — e.g.
`distillation_divergence_geometry` cites
`output/data/firstprinciples/divergence_demo.json`,
`sequential_shift_sensitivity` cites
`output/data/firstprinciples/sequential_shift_sensitivity.json`,
`policy_posterior_grid` cites `output/data/pymdp_policy_posterior_grid.json`.

A companion **hash manifest** (`build_figure_hash_manifest()` →
`output/reports/figure_hash_manifest.json`, schema
`template_active_inference.figure_hash_manifest.v1`) records verified per-figure hashes;
`_figure_hash_manifest_ok()` fails if hashes are not verified. The generated
`visualization_quality_audit.json` adds a third row-level guard over readable image
bytes, nonblank pixels, source binding, caption scope terms, and overclaim phrases.
Together the source-map, hash, and quality-audit gates bind each figure to its inputs,
content fingerprint, and claim boundary.

## Caption discipline

Captions are not free prose. They:

- **State determinism and scope guardrails.** They flag closed-form / no-sampling
  status, and repeatedly scope claims to the toy ("illustrating objective geometry
  rather than asserting a universal KL outcome"; "not a performance comparison").
- **Carry hydrated numbers, never literals.** Caption text in `figures.yaml` uses
  `{{token}}` and `{{token:.spec}}` placeholders (e.g.
  `{{param_sweep_grid_points}}`, `{{sweep_max_residual:.1e}}`,
  `{{free_energy_mean_field_gap_max:.3f}}`). They are resolved at render time by
  `render_figure_markdown()` in
  [`../../src/visualizations/figure_registry.py`](../../src/visualizations/figure_registry.py)
  using the same `substitute_snake_case_tokens()` as the prose hydrator, so a caption
  number can never drift from its artifact. See [`hydration-tokens.md`](hydration-tokens.md).
- **Name their source artifact** so the provenance is readable in the figure itself.

## Alt-text requirement

Every figure entry in `figures.yaml` has an `alt` field (a verbose, self-contained
description of axes, panels, and what the figure shows). `render_figure_markdown()` emits
the caption as the pandoc-crossref caption (one numbered "Figure N: …") and rides the
verbose `alt` along as `fig-alt` for accessibility, so there is exactly one numbered
caption and a separate screen-reader description. Alt text is token-substituted on the
same path as captions, and double quotes are normalized to single quotes for the
`fig-alt` attribute.

## Audit gates binding figures to data

The figure-binding gates run before the PDF can render and fail closed:

| Gate (in `src/gates/output_checks.py`) | Binds | Fails when |
| --- | --- | --- |
| `figure_source_map_schema` | each figure → its source data paths | schema wrong, not all figures mapped, or a source row incomplete/missing |
| `figure_hash_manifest_schema` | each figure → a verified content hash | schema wrong or hashes unverified |
| `visualization_quality_audit_schema` | each figure → readable pixels, source binding, and caption scope | any row is unreadable, blank, unbound, missing a required scope guard, or overclaiming |

These sit alongside the manuscript token gates (unresolved/malformed tokens) and the
integration audit, which also emits `manuscript_token_provenance.json` and the
`manuscript_hardcoded_variable_audit.json` feeding `{{token_provenance_count}}` and
`{{hardcoded_variable_issue_count}}`. The net effect: a figure cannot enter the PDF
unless its id is registered, its source data exists, its hash verifies, its pixels are
readable/nonblank, its scope language is present where required, and every number in its
caption/alt resolves from a generated artifact.

## Registry reference

The full figure id → PNG → generator table lives in
[`../../manuscript/SYNTAX.md`](../../manuscript/SYNTAX.md) ("Figure label registry"); the
id → section bindings live in `figures.yaml` → `section_figures`. Reference a figure in
prose as `[@fig:<registry-id>]` (e.g. `[@fig:ising_mi_curve]`), never with a literal
placeholder.
