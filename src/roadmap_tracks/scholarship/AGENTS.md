# AGENTS — scholarship package

- **Data modules are append-only registries.** `sources_base.py` and
  `sources_review.py` are pure flat data (no logic); new sources go to
  `sources_review.py`. Do not reorder existing rows — row order feeds the
  deterministic artifact (diffoscope-tracked).
- **Logic lives only in `matrix.py`.** `__init__.py` is re-exports only
  (the method-inventory generator skips `__init__.py`, so logic parked there
  vanishes from `docs/reference/method-inventory.md`).
- **The self-referential bootstrap special case** in `matrix.py`
  (`friston2010fep`, `biehl2020critique` declare the matrix itself as their
  artifact; path-equality branch prevents a first-clean-build deadlock) must
  survive any refactor verbatim.
- **Schema string is frozen.** `template_active_inference.scholarship_source_matrix.v1`
  is pinned by `gates/output_checks.py` as a literal (deliberate
  validator-side independence) — renaming it invalidates saved artifacts and
  pinned tests for zero gain (ISA Out-of-Scope).
- **Byte-stability contract:** any change here must either leave
  `output/data/scholarship_source_matrix.json` byte-identical (refactor) or
  regenerate it through `scripts/run_full_chain.py` (content change) so the
  hash/diffoscope/attestation gates re-converge.
- Every new citation key needs: expected-key entry, bib entry with locator,
  manuscript citation, backing artifact, tracks, sections, claim boundary —
  the connectivity validator fails closed on any missing leg.
