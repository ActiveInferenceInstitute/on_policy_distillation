# reproducibility/ — Agent Notes

## Purpose

Quickstart guidance for regenerating outputs and rendering the PDF. Documentation
only — the authoritative contract is
[`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md).

## Local Rules

- Keep this directory documentation-only. Producers live in
  [`../../scripts/`](../../scripts/), logic in [`../../src/`](../../src/),
  outputs in [`../../output/`](../../output/).
- Never instruct anyone to hand-edit a generated artifact to pass a claim.
  Regenerate the producer that owns the artifact; that is the whole contract.
- Do not hard-code volatile counts or numbers. Hydrated values come from
  `output/data/manuscript_variables.json` via the single hydration boundary
  (`scripts/z_generate_manuscript_variables.py`).
- Keep the two render paths distinct: the portable standalone renderer
  (`scripts/render_pdf.py`) vs. the full-polish template path
  (`scripts/03_render_pdf.py` in the sibling template checkout). Do not conflate
  them — see [`standalone-vs-template.md`](standalone-vs-template.md).
- When the producer order, hydration, figure rendering, copied-output parity, or
  sheaf reproducibility contracts change, update
  [`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md)
  first, then reconcile these quickstart pages.

## Verification

```bash
uv run python scripts/run_full_chain.py
uv run python scripts/validate_outputs.py
```
