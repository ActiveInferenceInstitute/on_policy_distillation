# docs/manuscript/ - Manuscript Documentation

Documentation-only. These pages describe the manuscript; they are not the manuscript.

- Do not restate scientific claims here; the scope contract is
  [`claims-and-scope.md`](claims-and-scope.md) and the sections own their claims.
- Treat numbered `manuscript/0*.md` … `manuscript/2*.md` as **composed outputs** —
  edit fragments under [`../../manuscript/sections/imrad/`](../../manuscript/sections/imrad/)
  and [`../../manuscript/sheaf/manifest.yaml`](../../manuscript/sheaf/manifest.yaml),
  then recompose via [`../../scripts/compose_manuscript.py`](../../scripts/compose_manuscript.py).
  Hand-authored exceptions: `00_abstract.md`, `17_conclusion.md`, `99_references.md`.
- Never hand-write a number in prose. Every reported value is a `{{token}}` hydrated
  from `output/data/manuscript_variables.json`; unknown or single-brace tokens fail
  closed (see [`hydration-tokens.md`](hydration-tokens.md)).
- Figure ids, captions, and alt text come only from [`../../figures.yaml`](../../figures.yaml).
- If you change a section's role, claim, tokens, or feeding tracks, update
  [`section-guide.md`](section-guide.md) in the same change.
