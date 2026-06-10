# scholarship — source-backed literature traceability matrix

Split in Run-6 (2026-06-10) from a 1471-line single module into focused modules;
every pre-split import path still works via the package `__init__`, and the
emitted artifact is byte-identical.

| Module | Contents |
| --- | --- |
| `schema.py` | `SCHOLARSHIP_SCHEMA` + `EXPECTED_SCHOLARSHIP_KEYS` (closed citation-key set) |
| `sources_base.py` | `_BASE_SCHOLARSHIP_SOURCES` — original authorship batch (pure data, 72 rows) |
| `sources_review.py` | `_REDTEAM_REVIEW_SOURCES` (39) + `_RUN5_REVIEW_SOURCES` (6) — review batches (pure data) |
| `matrix.py` | `SCHOLARSHIP_SOURCES` merge + build / write / validate logic |

The matrix (`output/data/scholarship_source_matrix.json`) maps every expected
citation key to: bib entry presence + locator, manuscript citation sites,
backing artifact existence, registered tracks, bound sections, and a claim
boundary. `validate_scholarship_source_matrix` re-derives connectivity; the
expected-key set and row connectivity are negative-controlled in
`tests/test_roadmap_promotion.py`.

Adding a source: append the dict to the appropriate batch in
`sources_review.py` (new sources are review-vintage by definition), add the
citation key to `EXPECTED_SCHOLARSHIP_KEYS`, add the bib entry with a locator,
cite it in a manuscript section, and re-run the sheaf-tracks generator.
Live-verify the reference (arXiv abs page or DOI redirect) before inclusion.
