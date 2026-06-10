# models/ — agent guidance

- This directory is documentation-only. The models live in
  [`../../src/`](../../src/); orchestration lives in
  [`../../scripts/`](../../scripts/); generated numbers live in
  [`../../output/`](../../output/).
- Never hard-code measured values here. The manuscript hydrates tokens from
  `output/data/manuscript_variables.json`; these pages cite artifact paths
  instead. If you need a number, name the artifact, not the digits.
- Quote real module paths, function/class names, and config keys — verify them
  against the source before editing, the same discipline as
  [`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md).
- Keep each model's scope honest: state both what it witnesses and what it does
  *not* claim. These are minimal-model demonstrations, not production results.
- After touching a model, regenerate its artifacts via the producer order in
  the rendering-reproducibility contract, then `uv run python scripts/validate_outputs.py`.
