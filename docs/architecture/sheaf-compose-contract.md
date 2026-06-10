# Sheaf Compose Contract

The manuscript is a manifest-indexed composition model. The registry declares
track semantics and renderers, the manifest binds tracks to section fragments,
and the composer writes flat `manuscript/NN_*.md` files for the PDF pipeline. The
word "sheaf" is not decoration: [`src/manuscript/sheaf/laws.py`](../../src/manuscript/sheaf/laws.py)
verifies the sheaf *axioms* the composer implicitly assumes, making the claim
runnable and falsifiable.

For the broader regeneration contract see
[`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md);
for module APIs see
[`../../src/manuscript/sheaf/AGENTS.md`](../../src/manuscript/sheaf/AGENTS.md).

## The three YAML sources

| File | Role |
| --- | --- |
| [`manuscript/sheaf/tracks.yaml`](../../manuscript/sheaf/tracks.yaml) | Fragment **registry**: each track's compose `order`, `renderer` id, `label`, and optional flag. |
| [`manuscript/sheaf/manifest.yaml`](../../manuscript/sheaf/manifest.yaml) | Section list with per-section `tracks:` map (track → fragment path) and optional `track_order`. |
| [`manuscript/sheaf/coverage.yaml`](../../manuscript/sheaf/coverage.yaml) | Heatmap styling for the coverage artifacts. |

Tracks are declared with a numeric `order` (e.g. `prose: 10`, `formalism: 20`,
`pymdp: 40`, `lean: 70`, `ontology: 90`). Two renderers are *generated* —
`section_figures` (from `figures.yaml`) and `layers_report` (registry + binding
tables) — and carry no file-type contract. Editable fragment sources live under
[`manuscript/sections/imrad/`](../../manuscript/sections/imrad/); that is where
prose is edited, never the flat composed `NN_*.md` outputs.

## The module map

| Module | Public surface |
| --- | --- |
| [`registry.py`](../../src/manuscript/sheaf/registry.py) | `load_track_registry(path)`, `track_order_for_section(...)` |
| [`manifest.py`](../../src/manuscript/sheaf/manifest.py) | `load_manifest(path, *, project_root)` |
| [`models.py`](../../src/manuscript/sheaf/models.py) | `TrackSpec`, `SheafSection`, `TrackRegistry`, `SheafManifest`, coverage symbols/colors |
| [`renderers.py`](../../src/manuscript/sheaf/renderers.py) | `RENDERERS`, `GENERATED_RENDERERS`, `resolve_track_body(...)` |
| [`compose.py`](../../src/manuscript/sheaf/compose.py) | `compose_section(...)`, `compose_all_sections(...)`, `validate_manifest(...)` |
| [`coverage.py`](../../src/manuscript/sheaf/coverage.py) | `build_coverage_matrix(...)`, `emit_coverage_artifacts(...)` |
| [`semantic.py`](../../src/manuscript/sheaf/semantic.py) | semantic gluing certificate (shared symbols, claim evidence, producers, gates, variables) |
| [`status.py`](../../src/manuscript/sheaf/status.py) | section-status reporting |
| [`laws.py`](../../src/manuscript/sheaf/laws.py) | `verify_sheaf_laws(project_root)`, `sheaf_law_violations(...)`, `SheafLaw`, `SHEAF_LAW_COUNT` |

## The base poset and the verified laws

The manuscript is modeled as a coverage sheaf over a finite base poset: the IMRAD
chain `introduction < methods < results < discussion < appendix` (the constant
`IMRAD_ORDER` in `laws.py`), with each block's *group* row containing its
*section* rows (`group ⊒ section`). `laws.py` checks six laws (`SHEAF_LAW_COUNT =
len(_CHECKERS)`, the `SheafLaw` enum), each returning concrete `LawViolation`
counter-examples rather than a bare boolean:

| Law (`SheafLaw`) | Verifies (from `laws.py`) |
| --- | --- |
| `POSET` | IMRAD blocks form a chain; compose order is monotone in block rank; if groups are used, every composing section's block has a group row. |
| `PRESHEAF` | Every bound track is in the registry; the global track order is a strict total order (no shared `order`); a section's resolved local order is the monotone restriction of the global order (a `track_order` override must be a permutation of the bound tracks). |
| `SEPARATION` | `section → output_name` is injective — distinct locals glue to distinct global positions; section ids are unique. |
| `GLUING` | Compose order is a linear extension of the poset; within each block section orders are strictly increasing; each block is contiguous (once you leave a block you never return); each section glues once. |
| `TYPING` | Each binding's renderer is registered and the fragment's suffix is in the renderer's accepted suffix set; generated renderers (`section_figures`, `layers_report`) are type-exempt. |
| `COMPOSITIONALITY` | Every fragment file is private to one section, so global composition is the coproduct (disjoint union) of per-section bodies, independent of inclusion order. |

`verify_sheaf_laws` is invoked inside `validate_manifest(...)` under `--strict`:
a violation becomes an error-level `ManifestIssue` and aborts composition.

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
uv run python scripts/compose_manuscript.py --list-tracks
```

### What the laws do *not* claim

The module verifies the sheaf axioms on a finite base; it does **not** compute
sheaf cohomology (`H^0`/`H^1`, Čech complexes, derived functors). The docstring
of `laws.py` states this scope boundary explicitly.

## Negative controls

Discipline from [`AGENTS.md`](../../src/manuscript/sheaf/AGENTS.md): every law is
paired with a negative control in
[`../../tests/test_sheaf_laws.py`](../../tests/test_sheaf_laws.py) — a single
mutation that breaks the law, proven to be caught — so the gate binds the laws'
*content*, not merely their shape.

## How fragments compose into flat sections

1. **Resolve order.** For each composing section, `track_order_for_section`
   yields the track order — the monotone restriction of the registry order, or an
   explicit `track_order` permutation (the appendix `methods_sheaf` section uses
   one).
2. **Render each track.** `compose_section` calls `resolve_track_body()` for
   every bound track — Markdown fragments are read from disk; generated renderers
   synthesize their body. There are no section-id special cases.
3. **Glue.** Bodies concatenate in resolved order into one flat
   `manuscript/NN_*.md` named by the section's `output_name`. Group rows
   (`compose: false`) emit IMRAD dividers but carry no fragments.
4. **Coverage.** `emit_coverage_artifacts` writes
   `output/data/sheaf_coverage_matrix.json` (black = present, white = absent,
   gray = missing binding). The heatmap PNG and the front coverage page come from
   `generate_figures.py`. A clean tree must have zero gray cells.
5. **Semantic certificate.** Hydration writes
   `output/data/sheaf_gluing_certificate.json` (plus the evidence crosswalk and
   validation dependency graph) binding shared GNN/ontology symbols, typed claims,
   artifact producers, validation gates, and manuscript variables — so the
   project validates semantic agreement, not only coverage shape.

## Counts are derived, never typed

Registry track count and appendix proof size are not hard-coded in prose.
Composed sections use `{{sheaf_track_count}}` and
`{{appendix_sheaf_track_count}}`; `z_generate_manuscript_variables.py` resolves
them from the live manifest and registry before PDF rendering. The appendix proof
section binds the full proof row — including the generated `layers` report and the
optional-type `animation` track — so the appendix exercises every registered
fragment renderer.
