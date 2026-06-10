# First-Principles Module Notes

This package is the executable OPD/Active-Inference correspondence layer. Keep
modules deterministic and dependency-light; generated artifacts belong under
`output/data/firstprinciples/` via `scripts/generate_firstprinciples.py`.

- Keep correspondence, divergence, reward-tilting, exposure-bias, SDPG,
  taxonomy, statistics, and classroom claims scoped to the toy artifacts they
  generate.
- Preserve public module names; manuscript fragments, figure generators, and
  semantic gates import these modules directly.
- The classroom path may use pymdp, but the metric helpers should remain pure
  and testable without live I/O.

- `empirical.py` - curated literature-reported OPD benchmark rows (bibkey-bound).
