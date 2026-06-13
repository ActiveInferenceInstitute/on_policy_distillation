# Pipeline and Artifact Regeneration Order

The scripts under [`../../scripts/`](../../scripts/) are **thin orchestrators**:
they import from [`../../src/`](../../src/) and handle I/O only (see
[`../../scripts/README.md`](../../scripts/README.md)). Each writes typed JSON
artifacts under `output/`, and the order is load-bearing — running generators out
of order silently re-stales downstream certificates.

For the authored regeneration contract (authored vs generated surfaces,
hydration boundary, figure registry, root output parity) see
[`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md).
This page documents what each script *is* and *produces*.

## The canonical order

The single source of truth for the order is `analysis.scripts` in
[`../../manuscript/config.yaml`](../../manuscript/config.yaml).
[`run_full_chain.py`](../../scripts/run_full_chain.py) reads that list — nothing
is hard-coded in the runner — executes it, validates, then re-runs the
convergence tail and re-validates to a bounded fixed point. Prefer it over
invoking generators by hand:

```bash
uv run python scripts/run_full_chain.py             # full chain + converge
uv run python scripts/run_full_chain.py --tail-only # convergence tail only
uv run python scripts/run_full_chain.py --render     # + render the PDF
uv run python scripts/run_full_chain.py --dry-run    # print the plan
```

The order published in the rendering contract is:

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/run_analytical_sweep.py
uv run python scripts/simulate_si_tmaze.py
uv run python scripts/simulate_si_graph_world.py
uv run python scripts/compute_statistics.py
uv run python scripts/generate_firstprinciples.py
uv run python scripts/generate_validation_spine.py
uv run python scripts/generate_toy_sweep_tracks.py
uv run python scripts/generate_formal_interop_tracks.py
uv run python scripts/generate_integration_audit.py
uv run python scripts/generate_sheaf_tracks.py
uv run python scripts/generate_figures.py
uv run python scripts/render_animation.py
uv run python scripts/z_generate_manuscript_variables.py
uv run python scripts/generate_method_inventory.py
```

Two ordering invariants matter most (from
[`../../scripts/README.md`](../../scripts/README.md)):
`generate_sheaf_tracks.py` must precede `z_generate_manuscript_variables.py`, and
the validation spine must precede the audits.

## What each script produces

| Script | Layer | Writes (selected) |
| --- | --- | --- |
| [`compose_manuscript.py`](../../scripts/compose_manuscript.py) | sheaf compose | flat `manuscript/NN_*.md`, `output/data/sheaf_coverage_matrix.json`, regenerated `manuscript/00_00_sheaf_coverage.md` |
| [`run_analytical_sweep.py`](../../scripts/run_analytical_sweep.py) | analytical | closed-form hyperparameter sweep (`output/data/parameter_sweep.csv`, analytical sweep JSON) |
| [`simulate_si_tmaze.py`](../../scripts/simulate_si_tmaze.py) | pymdp | `si_tmaze_summary.json`, `si_tmaze_trace.json`, `si_tmaze_model_matrices.json`, `si_policy_comparison.json`, `pymdp_policy_posterior_grid.json`, `pymdp_runtime_diagnostics.json` |
| [`simulate_si_graph_world.py`](../../scripts/simulate_si_graph_world.py) | pymdp (extension) | deterministic `si_graph_world_summary.json`, `si_graph_world_trace.json` |
| [`compute_statistics.py`](../../scripts/compute_statistics.py) | analytical + sim | combined `output/data/analysis_statistics.json` |
| [`generate_firstprinciples.py`](../../scripts/generate_firstprinciples.py) | firstprinciples | correspondence map, divergence/exposure/energy demos, sequential-shift witness and sensitivity sweep, the two-agent pymdp classroom (default; `--no-classroom` to skip), classroom-derived statistics under `output/data/firstprinciples/` |
| [`generate_validation_spine.py`](../../scripts/generate_validation_spine.py) | gates / spine | `artifact_provenance.json`, deterministic `replay_matrix.json` / `reproducibility_replay.json`, `counterexample_matrix.json` |
| [`generate_toy_sweep_tracks.py`](../../scripts/generate_toy_sweep_tracks.py) | roadmap | sensitivity, uncertainty, benchmark, measured policy grid, EFE terms, analytical-observable, graph-world topology trace/invariants, state-space catalog, causal-ablation artifacts |
| [`generate_formal_interop_tracks.py`](../../scripts/generate_formal_interop_tracks.py) | formal | `model_checking_witnesses.json`, `gnn_roundtrip_report.json`, `gnn_lint_report.json`, ontology alias/profile indices, `interop_roundtrip_report.json`, `lean_theorem_inventory.json`, `proof_extraction_index.json` |
| [`generate_integration_audit.py`](../../scripts/generate_integration_audit.py) | audit | producer/stale/token/figure/scope/claim/adversarial audits, `artifact_diffoscope.json`, `artifact_license_audit.json`, `release_notes_evidence.json` |
| [`generate_sheaf_tracks.py`](../../scripts/generate_sheaf_tracks.py) | consolidation | the canonical semantic certificate, dependency graph, evidence-field index, release-bundle manifest, theorem-traceability matrix, gate index, diffoscope, proof-extraction index, state-space catalog, causal-ablation matrix, license audit, release-note evidence, track-improvement scope, blocked-scope manifest, section-status, render-log |
| [`generate_figures.py`](../../scripts/generate_figures.py) | figures | `output/figures/*` (through `figure_io.save_figure_png`), `output/figures/figure_registry.json`, the sheaf coverage heatmap and layers overview PNGs |
| [`render_animation.py`](../../scripts/render_animation.py) | figures | trace-derived belief-trajectory GIF + `animation_frame_deltas.json` |
| [`z_generate_manuscript_variables.py`](../../scripts/z_generate_manuscript_variables.py) | hydration | `output/data/manuscript_variables.json` and hydrated `output/manuscript/*.md` — the **single hydration boundary** |
| [`generate_method_inventory.py`](../../scripts/generate_method_inventory.py) | docs | regenerates `docs/reference/method-inventory.md` from the live `src/`/`scripts/` AST |

`generate_sheaf_tracks.py` is the canonical consolidation pass: it rewrites the
large family of certificate, audit, and traceability artifacts in one place, so a
single generator owns those IDs (the rendering contract enumerates them).

## The convergence tail

Because the release attestation attests the *previous* validation report, the
runner re-executes a fixed subset after the first validate, in this order
(from [`run_full_chain.py`](../../scripts/run_full_chain.py)):

```text
generate_validation_spine.py
generate_toy_sweep_tracks.py
generate_formal_interop_tracks.py
generate_integration_audit.py
generate_sheaf_tracks.py
z_generate_manuscript_variables.py
```

It then re-runs `validate_outputs.py`. The loop is bounded by `--max-passes`
(default 3) and exits 0 only when the final validate is green.

## Rendering and root output parity

`render_pdf.py` renders the standalone PDF; PDF and web outputs are render
results, not sources of truth. After a root-pipeline run, project-local
`output/**` is authoritative during generation, and the copied
`../../../template/output/working/active_inference_on_policy_distillation/**`
tree must be checked for parity. The exact commands are in the
[rendering-reproducibility contract](../reference/rendering-reproducibility.md).

## Running the suite under load

A single long `pytest` process can be killed under resource pressure (observed
exit 144). [`run_tests_chunked.py`](../../scripts/run_tests_chunked.py) runs the
suite as small per-process chunks that survive, covering the same files; it exits
0 only when every chunk is clean. `--shuffle-seed N` shuffles file order
deterministically — a red shuffled run is a finding, never a seed to re-roll.
