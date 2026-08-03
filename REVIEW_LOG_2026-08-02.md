# Docs-deep review log — 2026-08-02

Repo: `ActiveInferenceInstitute/on_policy_distillation` (public standalone
submodule). Scope: mega-deep documentation review + implementation. All work
confined to this repo; pushed to `origin/main`.

## Phase 0 — Preflight

- Fetched origin; working tree was on `main` (fast-forward clean). Pre-existing
  uncommitted `uv.lock` change left untouched (not staged, not committed).
- Inventory: 240 tracked markdown files across `docs/` (architecture,
  development, manuscript, models, reference, reproducibility, reviews),
  `manuscript/`, per-directory `README.md`/`AGENTS.md`, root `README.md`,
  `AGENTS.md`, `ISA.md`, `STANDALONE.md`, `TODO.md`, `.aii/`, `gnn/`, `lean/`,
  `tests/`. Metadata surfaces (`CITATION.cff`, `.zenodo.json`, `codemeta.json`,
  `LICENSE`, `pyproject.toml`) cross-checked consistent.
- HEAD at start: `586332b` (main). Branch pushed to: `main`.

## Phase 1 — Mega-deep docs review

Method: repo-wide relational scanner (`/tmp/mdscan.py`, read-only) over all 240
tracked markdown files for broken links, dead anchors, invalid backticked
paths, and stub markers; plus three parallel review subagents for
content-vs-code cross-checks (one subagent failed on provider billing — its
file family, `docs/architecture/` + `docs/development/`, was reviewed directly
instead); plus manual verification of every contested fact against the tree
(bib counts, manifest bindings, config keys, script flags, Lean theorems,
metadata surfaces).

Key verified facts:
- `manuscript/references.bib` holds 133 `@` entries (docs claimed 117).
- `appendix_full_sheaf` binds 22 of 33 registry tracks (docs claimed "all
  registered" / "full proof row except layers"); `layers` binds in
  `methods_sheaf`, `animation`/`lean`/`gnn`/`model_checking`/etc. bind in
  `results_invariants`.
- `analysis.scripts` in `manuscript/config.yaml` (mirrored by
  `DEFAULT_ANALYSIS_SCRIPTS`) puts `generate_firstprinciples.py` AFTER
  `generate_toy_sweep_tracks.py`; three docs showed the pre-fix order.
  `run_full_chain.py` does not run `generate_method_inventory.py`.
- `scripts/run_test_isolation_soak.py --validate-report`,
  `--require-complete`, `tests/gates/`, root `conftest.py`,
  `test_figure_generators_match_registry`, `--no-classroom`,
  `--list-tracks`/`--validate-only`/`--strict` all exist as documented.
- v1.0.2 release state: tags `v1.0.0`–`v1.0.2`; concept and version DOIs
  resolve; `manuscript/config.yaml` carries populated `doi`/`version_doi`.

## Phase 2 — Scoped findings (in TODO.md)

Added "Docs-deep review (2026-08-02)" section to `TODO.md` with
Minor/Medium/Major entries, each marked completed with its commit, plus an
open/deferred list. See `TODO.md`.

## Phase 3 — Implemented

8 commits, 27 files changed (+284/−103); details in TODO.md and commit
messages:

1. `3e09402` docs: pipeline order aligned with `manuscript/config.yaml`
   (README, pipeline.md, rendering-reproducibility.md).
2. `0b744d7` docs: appendix/supplement track-binding claims corrected
   (AGENTS.md, section-guide.md, sheaf-compose-contract.md).
3. `e544747` docs: snapshot bibliography counts replaced with live
   verification commands (citation-map.md, manuscript README, deep-review).
4. `ad05833` docs: template-relative paths fixed for the standalone checkout
   (AGENTS.md, SYNTAX.md, rendering.md).
5. `ea0e345` docs: stale module/artifact paths corrected (config map,
   extending.md, ISA.md, tmaze-pymdp.md, formal-layers.md).
6. `ab72197` docs: gnn README registry list, `.aii` DOI typo, glossary anchor
   (gnn/README.md, .aii/config.yaml, glossary.md, faq.md).
7. `16ad4a1` docs: review ledgers updated to file-backed evidence and current
   state (critical-review, redteam, notation-supplement).
8. review log, scoped TODO section, and the last `src/`-less path fix
   (REVIEW_LOG_2026-08-02.md, TODO.md, src/manuscript/AGENTS.md) — the
   commit carrying this file.

Total: 8 commits, 27 files changed (+284/−103).

Cheap validations run after edits: `uvx ruff check src tests scripts` (clean),
repo-wide link/anchor/path re-scan (no new findings), targeted
`test_review_ledgers.py` / `test_documentation_contracts.py` — see Phase 4
notes in TODO.md. Heavy suites (full pytest, Lean `lake build`, full PDF
render) intentionally not run: no code changed in this pass.

## Phase 4 — Verification & push

- Final scanner re-run clean for touched files; `git status` contains only
  intended changes (plus pre-existing untouched `uv.lock`).
- Pushed to `origin/main`; verified up to date.
