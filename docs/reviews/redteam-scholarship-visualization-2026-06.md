# RedTeam Scholarship and Visualization Hardening, 2026-06

## Disposition

| Finding | Status | Binding |
| --- | --- | --- |
| Sequential-shift evidence could pass as a single chosen correction level | **LANDED** | `firstprinciples.sequential_shift_sensitivity.v1` varies correction fraction over finite policy mixtures and requires monotone induced-test-loss and shift-mass reductions. |
| Figure provenance needed to cover the broader sensitivity artifact, not only the base witness | **LANDED** | `sequential_shift_sensitivity` is registered in `figures.yaml`, rendered from `output/data/firstprinciples/sequential_shift_sensitivity.json`, and guarded by `figure_source_map_schema`. |
| Scholarship context for train/test visitation mismatch should name distribution-shift risk weighting explicitly | **LANDED** | `shimodaira2000covariate_shift` is added to the scholarship matrix as external context only; local evidence remains the generated finite artifact. |
| Caption/prose could overread the new sensitivity sweep as empirical OPD evidence | **LANDED** | Manuscript and caption text state deterministic finite correction-dose sweep, toy-only scope, and no production-LLM benchmark claim. |

## Boundary

This pass does not add empirical OPD evidence, production-language-model measurements,
biological claims, or release/archive claims. It strengthens the local finite witness
and the validator surface that keeps the witness source-bound.
