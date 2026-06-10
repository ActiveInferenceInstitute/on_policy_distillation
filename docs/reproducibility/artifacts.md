# Artifacts and determinism

Everything under [`../../output/`](../../output/) is generated and
regeneratable. Authored fragments and configuration are the only sources of
truth; the producers turn them into deterministic data, figures, composed and
hydrated Markdown, PDF, and web. The authoritative version of this contract is
[`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md);
this page is the operational tour.

## `output/` layout

| Subtree | Holds | Produced by |
| --- | --- | --- |
| `output/data/*.json`, `parameter_sweep.csv` | Analysis results, sweeps, SI/T-maze traces, sheaf coverage matrix, semantic gluing certificate, provenance, evidence/dependency graphs, and `manuscript_variables.json` (the hydration values). | Analysis + validation-spine + roadmap scripts. |
| `output/figures/*.png`, `*.gif`, `figure_registry.json` | Every figure and the figure registry. | `scripts/generate_figures.py`, `scripts/render_animation.py`. |
| `output/reports/*.json` | Validation, adversarial audit, counterexample matrix, diffoscope, license audit, hash manifests, `validation_report.json`. | Validation-spine / roadmap scripts and `scripts/validate_outputs.py`. |
| `output/manuscript/*.md` | Hydrated manuscript sections (`{{token}}` resolved). | `scripts/z_generate_manuscript_variables.py`. |
| `output/pdf/*` | The PDF (`on_policy_distillation.pdf`) plus LaTeX/pandoc intermediates and `references.bib`. | `scripts/render_pdf.py` (see [`rendering.md`](rendering.md)). |
| `output/web/*` | HTML render (`index.html`, per-section pages). | render path. |
| `output/logs/*` | Run logs. | producers. |

`output/data/*.json` and `output/reports/*.json` are produced by project
scripts and validation-spine modules. `manuscript/0*.md` (except hand-authored
front/back matter) are composed from sheaf fragments by
`scripts/compose_manuscript.py`; `output/manuscript/*.md` is then hydrated from
those plus `output/data/manuscript_variables.json`. `output/pdf/*` and
`output/web/*` are render outputs, **not** sources of truth.

## Single hydration boundary

Composition may emit `{{token}}` placeholders, but only one script substitutes
them: `scripts/z_generate_manuscript_variables.py`. Volatile counts, run facts,
semantic restrictions, and figure captions must enter through
`output/data/manuscript_variables.json`, never hard-coded prose. Unknown
placeholders and single-brace token typos **fail closed** — a number that did
not come from an artifact cannot reach the PDF.

## Determinism and seeds

Computation is deterministic: fixed seeds, headless matplotlib
(`MPLBACKEND=Agg`), no network, no runtime downloads (see
[`../development/conventions.md`](../development/conventions.md)). Seeds and
runtime knobs live in [`../../pymdp.yaml`](../../pymdp.yaml); the pymdp rollout
records a `pymdp_config_hash` so a run is pinned to its config. Re-running the
producers on a clean tree reproduces the same artifacts.

## Regenerating in order

Run the producers in the canonical order (the full list is in the
[producer order](../reference/rendering-reproducibility.md#producer-order)
section of the reference), or simply use the convergent one-command runner,
which encodes that order and converges the attestation fixed point with bounded
retry:

```bash
uv run python scripts/run_full_chain.py            # full chain + converge
uv run python scripts/run_full_chain.py --tail-only # convergence tail only
uv run python scripts/run_full_chain.py --render    # + render the PDF
uv run python scripts/run_full_chain.py --dry-run   # print the plan
```

`run_full_chain.py` reads the analysis order from `manuscript/config.yaml`
`analysis.scripts` (the single source of truth — nothing is hard-coded in the
runner), validates, and — because `release_attestation.json` attests the
*previous* `validation_report.json` — re-runs the attestation tail and
re-validates until the report is green and stable, bounded by `--max-passes`.

## Validation pass

`scripts/validate_outputs.py` runs `validate_outputs()` and
`validate_manuscript()` against the track contract, writes
`output/reports/validation_report.json`, prints the per-check map, and exits
non-zero if any check failed.

```bash
uv run python scripts/validate_outputs.py
```

Because the attestation binds the validation report by hash, a half-regenerated
tree fails on staleness — re-run the spine → audit → sheaf → variables chain and
validate **again** (one more validate pass after any red). This
attestation-circularity is exactly what `run_full_chain.py` automates.

## See also

- [`rendering.md`](rendering.md) — turning the validated tree into a PDF.
- [`standalone-vs-template.md`](standalone-vs-template.md) — project-local vs. copied root outputs.
- [`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md) — authoritative contract.
