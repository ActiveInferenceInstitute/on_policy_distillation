# RedTeam Scholarship and Visualization Hardening, 2026-06

## Disposition

| Finding | Status | Binding |
| --- | --- | --- |
| Sequential-shift evidence could pass as a single chosen correction level | **LANDED** | `firstprinciples.sequential_shift_sensitivity.v1` varies correction fraction over finite policy mixtures and requires monotone induced-test-loss and shift-mass reductions. |
| Figure provenance needed to cover the broader sensitivity artifact, not only the base witness | **LANDED** | `sequential_shift_sensitivity` is registered in `figures.yaml`, rendered from `output/data/firstprinciples/sequential_shift_sensitivity.json`, and guarded by `figure_source_map_schema`. |
| Scholarship context for train/test visitation mismatch should name distribution-shift risk weighting explicitly | **LANDED** | `shimodaira2000covariate_shift` is added to the scholarship matrix as external context only; local evidence remains the generated finite artifact. |
| DAgger context was cited in the paper but not bound to the new sequential-shift artifact | **LANDED** | `ross2011dagger` now points to `output/data/firstprinciples/sequential_shift_sensitivity.json` with PMLR locator metadata and remains external context only. |
| Figure quality gates checked source maps and hashes but not a single generated row-level readability/scope audit | **LANDED** | `output/reports/visualization_quality_audit.json` now records readable/nonblank pixels, source binding, caption scope guardrails, overclaim checks, and unexpected-image absence for every registered figure. |
| Stray ignored images under `output/figures` could be hashed without source-map or caption binding | **LANDED** | `figure_hash_manifest.v1`, `figure_output_integrity`, and `visualization_quality_audit.v1` now reject undeclared visible image artifacts; only registry PNGs plus the explicit animation GIF are declared. |
| Caption/prose could overread the new sensitivity sweep as empirical OPD evidence | **LANDED** | Manuscript and caption text state deterministic finite correction-dose sweep, toy-only scope, and no production-LLM benchmark claim. |
| Teacher-token reliability scholarship lagged the newest OPD reliability pressure case | **LANDED** | `liu2026pwopsd` is added as a primary-preprint scholarship row and OPD taxonomy method; it is cited only as external teacher-token reliability context, not as reproduced evidence. |

## Boundary

This pass does not add empirical OPD evidence, production-language-model measurements,
biological claims, or release/archive claims. It strengthens the local finite witness
and the validator surface that keeps the witness source-bound.
