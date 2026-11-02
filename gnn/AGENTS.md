# GNN Specification Notes

These `.gnn.md` files are the single source of truth for model structure. When a
model changes, edit the spec here first, then re-run the parser and concordance
checks so the analytical, numeric, pymdp, and Lean tracks stay aligned.

- Use the canonical `## ActInfOntologyAnnotation` heading; the spaced variant is
  a historical alias the project parser still accepts (and the upstream parser
  normalizes), but new specs must not use it.
- `upstream.json` is a custody pin, not a version hint: it records the upstream
  repository, the exact commit, the upstream `version` from that revision's
  `pyproject.toml`, and `date_recorded`, with `tag` and the parser entry point as
  optional convenience fields (`tag` must name the same release as `version`).
  Re-pinning is a deliberate change — move the recorded commit, version, and
  date, then re-run the conformance test.
- Never import upstream GNN code from `src/`; the conformance test runs the real
  pinned parser out-of-process against the pinned tree.
- Keep the conformance check non-vacuous: the spaced-heading mutant in the test
  must diverge.
