# Configuration and extension guide

This reference answers the three questions a reader actually has when working on
this project: **which knob changes what** (and which module consumes it), **how
to add a new track or figure** without tripping the integration gates, and
**what to run after editing X**. Everything documented here was verified against
the live tree on 2026-06-10; commands are copy-pasteable from the project root.

## Configuration map: every knob and its consumer

| Config file | Consumed by | What it controls | Status |
| --- | --- | --- | --- |
| `pymdp.yaml` | `src/simulation/pymdp_config.py::load_pymdp_config()` (used by `si_runner`, `si_loop`, `si_artifacts`, `manuscript/variables.py`, claim ledger) | Canonical planner/profile, SI search horizon, rollout timesteps, cue validity, agent gamma, seeds, graph-world topology, logging | **Live** — every key read |
| `figures.yaml` | `src/visualizations/figure_registry.py::load_figure_registry()` / `load_section_figures()`; `figure_style.py` for the `style:` block | Figure captions, alt text, widths, filenames, per-section figure bindings, palette/DPI/font roles | **Live** |
| `manuscript/sheaf/tracks.yaml` | `src/manuscript/sheaf/compose.py`, `status.py`, `laws.py` | Fragment-type registry: compose order, renderer, optional flag per track | **Live** |
| `manuscript/sheaf/manifest.yaml` | `src/manuscript/sheaf/compose.py` | IMRAD section rows and their track→fragment-path bindings | **Live** |
| `tracks.yaml` (root) | `src/manuscript/variables.py` (track counts), pipeline gates | Required pipeline tracks and the artifact contract surface | **Live** |
| `manuscript/config.yaml` | `src/manuscript/pdf_render.py`, `render_helpers.py` | Paper title/authors, margins, DOI/repository fields, transmission bookends | **Live** (read with fallbacks) |
| `data/claim_ledger.yaml` | `src/gates/claim_ledger.py` | Typed claims: artifact path + predicate (equals/min/set_equals/approx/re-derivation forms) | **Live** |
| `domain_profile.yaml` | nothing in `src/` or `scripts/` | Figure-type / artifact-expectation inventory | **Advisory only** — documentation metadata, not code-consumed |
| `experiment_plan.yaml` | nothing reads the YAML (the `experiment_plan_metrics` validate check is computed from artifact checks, not from this file) | Conditions/metrics narrative | **Advisory only** |
| `tasks.yaml` | external taskboard tooling only | Task/Gantt metadata | **Advisory only** |

The three advisory files are deliberately retained as human-readable planning
metadata; treat them as documentation, not as switches. If you need a new
behavioural knob, put it in `pymdp.yaml` (simulation), `figures.yaml`
(visualization), or a frozen dataclass config in `src/firstprinciples/`
(methods) — every methods hyperparameter is a dataclass field, never a buried
literal.

## Validation knobs that are not in YAML

- **Aggregate re-derivation rules** — `src/gates/aggregate_rederivation.py`
  (`ARTIFACT_AGGREGATE_RULES`). One declarative table maps each artifact's
  stored `all_*` flags to row-level predicates; `validate_outputs` fails when a
  stored flag disagrees with its rows. Add a rule when you add an aggregate;
  never copy the evaluator elsewhere.
- **Observable routes** — `src/roadmap_tracks/toy_sweep.py`
  (`_OBSERVABLE_ROUTES`). Each analytical observable has a closed-form route
  and an independent enumeration route; the validator re-derives the residual
  bound from rows and pins the observable set.
- **Gate index** — `src/roadmap_tracks/integration_audit_builders.py`
  (`GATE_INDEX_ROWS` + `build_validation_gate_index`). One declarative
  `(gate id, required inputs)` row per promoted gate; `indexed` is derived
  from on-disk input existence, and `validate_outputs` re-derives a live
  binding (`validation_gate_index_binding`) requiring every row id to match
  a check key this run produced (or a known external gate: the validate
  runner itself, the manuscript CLI, `lake build`). Phantom rows fail
  validation (`tests/test_gate_index_binding.py`).
- **Numeric tolerances** — writer-side constants live in
  `src/analytical/hyperparameters.py` (`BERNOULLI_VERIFICATION_TOLERANCE`)
  and `src/simulation/numerics.py` (`STEP_POSTERIOR_ATOL`,
  `POLICY_POSTERIOR_ATOL`). Validator-side literals in `src/gates/` are
  DELIBERATELY independent copies: across the writer/validator trust
  boundary, duplication is the verification mechanism — do not "consolidate"
  them into a shared constant.
- **Scholarship registry** — `src/roadmap_tracks/scholarship/` (split from a
  1471-line module in Run-6): `schema.py` (schema id + expected citation
  keys), `sources_base.py` / `sources_review.py` (pure-data source batches by
  provenance), `matrix.py` (build/write/validate logic). Every pre-split
  import path still works via the package `__init__`; the emitted
  `scholarship_source_matrix.json` is byte-identical to the pre-split output.
- **Release parity** — `src/roadmap_tracks/sheaf_tracks_support.py`
  (`_copied_parity`). Deferral means pre-copy or render-source-absent ONLY;
  an existing root copy that fails to hash-match is drift and fails the
  `release_bundle_manifest_schema` check (`tests/test_release_parity.py`).
- **Ontology profile matrix** — `src/roadmap_tracks/formal_interop.py`
  (`build_ontology_profile_matrix`). Rows cover `bernoulli_toy`, `si_tmaze`,
  the graph-world GNN surface, and toy benchmark models. `mapped_once` is a
  uniqueness check, not a presence check; duplicate aliases, missing graph-world
  rows, and unused/unmapped terms fail validation.
- **Cross-track symbol spine** — `src/roadmap_tracks/integration_audit_builders.py`
  (`build_cross_track_symbol_table`). Required domains are GNN variables,
  ontology terms, Lean theorem names, manuscript variables, JSON fields, figure
  labels, and rendered-manuscript consumers; the validator re-derives exact
  domain coverage and per-row consistency.
- **Semantic proof obligations** — `src/manuscript/sheaf/semantic.py`.
  `sheaf_gluing_certificate.json` includes typed `restriction_classes` and
  `proof_obligations`; every boolean restriction must have an obligation with
  source artifacts, a gate, a semantic restriction, a negative control, and
  `passed=true`.
- **Fixed-point release/provenance tail** —
  `src/orchestration/artifact_pipeline.py`. The tail refreshes sheaf artifacts,
  rewrites variables and hydrated manuscript, refreshes staleness/provenance
  currency, then emits semantic/release artifacts so `validate_outputs.py`
  sees current hashes and the current validation report.

## Add a figure (the six surfaces)

A figure that misses one of these surfaces cascades ~10 test failures
(`all_figures_mapped=false` propagates). In order:

1. **Generator** — a `figure_<id>(project_root) -> Path` function in a
   `src/visualizations/figures_*.py` module (≤500 lines per module; create a
   new module rather than growing one past the cap). Read ONLY from generated
   artifacts; derive any "shown N of M" counts from the loaded rows; save via
   `save_styled_figure` (or `save_figure_png` when a colorbar manages layout).
2. **Registry dict** — add the id to `FIGURE_GENERATORS` in
   `src/visualizations/figures.py` (import + `__all__` too).
   `tests/test_figures.py::test_figure_generators_match_registry` requires this
   dict and `figures.yaml` to match exactly.
3. **`figures.yaml` entry** — filename, self-contained `alt`, quantitative
   `caption` using `{{token}}` hydration (no hand-typed numbers; check any new
   format spec against `_TOKEN_RE` in `src/manuscript/hydrate.py` — a spec the
   regex does not match is silently left unsubstituted), and `width`.
4. **Section binding** — add the id under `figures.yaml` `section_figures.<section>`.
   The section must bind the `visualization` track in
   `manuscript/sheaf/manifest.yaml` (a one-line placeholder fragment under
   `manuscript/sections/imrad/<section>/visualization.md` plus the manifest
   `visualization:` entry).
5. **Source map** — add entries to all three dicts in
   `src/roadmap_tracks/integration_audit_artifacts.py`: figure → source
   artifacts, figure → source fields (`$.jsonpath` form), and figure →
   validation gates (gate ids must name real checks/tests).
6. **Prose** — reference the figure as `[@fig:<id>]` from the relevant
   `prose.md` fragment, and add any new `{{tokens}}` to
   `src/manuscript/variables.py`.

Then regenerate and verify:

```bash
uv run python scripts/generate_figures.py
uv run python scripts/generate_integration_audit.py
uv run python scripts/z_generate_manuscript_variables.py
uv run --extra dev python -m pytest tests/test_figures.py --no-cov -q
```

## Add a sheaf track

1. Declare the track in `manuscript/sheaf/tracks.yaml` (order, renderer —
   usually `markdown`, label, `optional` flag).
2. Bind fragments per section in `manuscript/sheaf/manifest.yaml`
   (`<track>: manuscript/sections/imrad/<section>/<track>.md`).
3. Author the fragments; hydrate all numbers via `{{tokens}}`.
4. If the track has a generated artifact, follow the promotion rule in
   `TODO.md`: producer script, deterministic artifact, manuscript consumer,
   typed claim, semantic restriction, validation gate, and a negative control
   that proves the gate bites. Artifact contracts live in
   `src/artifact_contracts.py` (required-output lists, producers,
   `ARTIFACT_CONSUMERS`, `ARTIFACT_GATES` — update all sites or provenance
   rows report incomplete).
5. `uv run python scripts/compose_manuscript.py --validate-only --strict` must
   stay green (sheaf laws + coverage).

## What to run after editing X

| You edited | Run |
| --- | --- |
| `src/` methods or gates | `uv run --extra dev python -m pytest tests/ -m "not artifact_slow and not render_slow" --no-cov` |
| any generated-artifact producer | `uv run python scripts/run_full_chain.py --tail-only` after tail-only edits, or `uv run python scripts/run_full_chain.py` when producer dependencies changed |
| manuscript fragments / manifest / figures.yaml | `uv run python scripts/compose_manuscript.py && uv run python scripts/z_generate_manuscript_variables.py` |
| everything / unsure | `uv run python scripts/run_full_chain.py` (canonical convergent order with bounded retry) |
| full release gate | `uv run python scripts/run_tests_chunked.py` then `uv run python scripts/render_pdf.py` |
| isolation soak (order coverage) | `uv run python scripts/run_tests_chunked.py --shuffle-seed N` (deterministic; report a red run, never re-roll the seed) |
| lint | `uvx ruff check src tests scripts` (project `[tool.ruff]` mirrors the template root gate) |

## Troubleshooting

- **Gray cells on the coverage page** — a manifest binding points at a missing
  fragment path. Check the `tracks:` block of that section in
  `manuscript/sheaf/manifest.yaml` against the filesystem.
- **`{{token}}` appears literally in output** — either the token is not
  produced by `src/manuscript/variables.py`, or its format spec is outside
  `_TOKEN_RE` (the fail-closed collector cannot flag a spec it cannot parse —
  check the regex before inventing new specs).
- **Validation red after a partial regen** — the attestation binds the
  validation report by hash, and provenance binds terminal artifact fields by
  hash, so a half-regenerated tree fails on staleness. Run
  `uv run python scripts/z_generate_manuscript_variables.py` followed by
  `uv run python scripts/validate_outputs.py`; the fixed-point tail refreshes
  the sheaf, variables, staleness, provenance, semantic certificate, release
  notes, and attestation in the convergent order.
- **Full pytest dies with exit 143/144 under load** — the machine's resource
  killer, not a test failure. Use `scripts/run_tests_chunked.py`, which runs
  per-file chunks that survive.
- **`aggregate_rederivation` check false** — some artifact's stored `all_*`
  flag disagrees with its rows (stale or hand-edited artifact). Regenerate the
  producer for the artifact named in
  `gates.aggregate_rederivation.aggregate_rederivation_rows()` output.
