# development/ — Agent Notes

## Purpose

Task-oriented developer guidance: the test system, code conventions, and
extension recipes for this project. Documentation only.

## Local Rules

- Keep this directory documentation-only. Implementation belongs in
  [`../../src/`](../../src/), orchestration in [`../../scripts/`](../../scripts/),
  and generated outputs in [`../../output/`](../../output/).
- These pages are a developer-facing companion to the reference contracts; do
  not duplicate [`../reference/configuration-and-extension.md`](../reference/configuration-and-extension.md)
  or [`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md)
  wholesale — link to them as the authoritative source.
- Do not hand-author volatile counts (test totals, coverage percentages, track
  counts). State the gate floor, not a snapshot number, and let generated
  artifacts or the manuscript variable generator own the live values.
- Preserve the writer/validator trust boundary when describing it: validators
  re-derive from rows rather than trusting stored booleans, and duplicated
  numeric tolerances across that boundary are deliberate, not redundant.

## Verification

```bash
uv run --extra dev python -m pytest tests/ -m "not artifact_slow and not render_slow" --no-cov
uv run python -m pytest tests -q
```
