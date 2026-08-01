# AGENTS.md — `.aii` sidecar

This directory is an InstituteOS metadata sidecar, not a research module.

Editing rules:
- Keep it metadata-only and reproducibility-neutral. No source, tests, figures,
  or generated `output/` artifacts belong here.
- Business logic, the manuscript, and all pipeline code live in the repo root /
  `src/` / `scripts/` and follow the root `AGENTS.md` and per-directory
  `AGENTS.md` files.
- Changes here must not affect the deterministic research pipeline or its gates.
