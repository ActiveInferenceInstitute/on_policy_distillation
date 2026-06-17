# active_inference_on_policy_distillation

**On-Policy Distillation as Active Inference in Finite Variational Models** — *reverse-KL free energy, student-induced sampling, and deterministic toy witnesses.*

This project formalises a scoped active-inference reading from first principles and demonstrates it on auditable minimal models. The intellectual core is the [`firstprinciples`](src/firstprinciples/) package — an audited active-inference ↔ on-policy-distillation correspondence map, the shared divergence geometry (forward/reverse KL, JSD, skew, α-divergence, OPSD per-token clipping), the reward-tilted-target unification of RL-as-inference / active inference / distillation, the SDPG privileged-context self-distillation objective, an exposure-bias model, a deterministic sequential-shift witness with a correction-dose sensitivity sweep, a structured OPD-literature taxonomy, and a **two-agent pymdp classroom** that pits a privileged teacher against an on-policy student and measures the reverse-KL distillation signal. See the integrated [notation & formalism supplement](docs/reference/notation-supplement.md).

The manuscript is a **sheaf-composed** multi-track document with configurable sections (analytical, pymdp, GNN, ontology, Lean, visualizations, provenance, replay matrix, counterexamples, sensitivity, uncertainty, benchmark, model-checking, interop, adversarial audit, evidence fields, scholarship, release bundle, theorem traceability, gate ergonomics, assumption indexing, animation deltas, and manuscript staleness). Every reported number is hydrated from a generated artifact and machine-checked before rendering.

## Quick start

The canonical readiness command is the convergent full chain. It regenerates the
declared analysis artifacts, refreshes manuscript variables and validation
certificates, validates the outputs, and renders the PDF:

```bash
uv sync --directory working/active_inference_on_policy_distillation --extra dev
cd working/active_inference_on_policy_distillation
uv run python scripts/run_full_chain.py --render
```

The individual scripts remain available for debugging or narrow development.
Their order is declared in `manuscript/config.yaml` and should not be
hand-reordered:

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/run_analytical_sweep.py
uv run python scripts/simulate_si_tmaze.py
uv run python scripts/simulate_si_graph_world.py
uv run python scripts/compute_statistics.py
uv run python scripts/generate_firstprinciples.py        # OPD<->AI artifacts; classroom rollout runs by default (--no-classroom to skip)
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

Validation and tests:

```bash
uv run python scripts/compose_manuscript.py --validate-only --strict
uv run python scripts/validate_outputs.py
uv run python -m pytest tests/ --cov=src --cov-fail-under=90
# On a loaded machine use scripts/run_tests_chunked.py — a single pytest process
# can be killed under resource pressure (exit 144); chunks survive.
```

For local iteration that does not need the full fixed-point artifact writers,
use the fast lane:

```bash
uv run --extra dev python -m pytest tests/ -m "not artifact_slow" --no-cov
```

For the tighter daily edit loop that also skips full figure rendering, animation,
pymdp rollout, and large manuscript-compose checks:

```bash
uv run --extra dev python -m pytest tests/ -m "not artifact_slow and not render_slow" --no-cov
```

The coverage command above remains the release gate; `artifact_slow` covers
full artifact writes, fixed-point validation, and tests that mutate shared
generated artifacts. `render_slow` covers read-only but expensive render,
animation, rollout, and large-compose checks.

From the sibling `../template` checkout after linking sidecar projects:

```bash
uv run python -m infrastructure.orchestration link-projects
uv run python scripts/01_run_tests.py --project working/active_inference_on_policy_distillation
./run.sh --project working/active_inference_on_policy_distillation --pipeline --core-only
```

## Sheaf composition

Tracks are declared in [`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml) (order, renderer, optional). Sections bind fragments in [`manuscript/sheaf/manifest.yaml`](manuscript/sheaf/manifest.yaml). The composer merges them into flat `manuscript/0*.md` files for the PDF pipeline.

The first manuscript page ([`manuscript/00_00_sheaf_coverage.md`](manuscript/00_00_sheaf_coverage.md)) shows a **B/W/G heatmap** of section × track coverage (black = present, white = absent, gray = missing binding). Compose writes `output/data/sheaf_coverage_matrix.json` only; `generate_figures.py` renders the heatmap PNG and regenerates the coverage page via `ensure_coverage_artifacts`.

Hydration writes a semantic sheaf certificate at `output/data/sheaf_gluing_certificate.json`.
It also writes `output/data/sheaf_evidence_crosswalk.json` and
`output/data/validation_dependency_graph.json`. Together these artifacts bind shared
GNN/ontology symbols, typed claims, artifact producers, validation gates, and manuscript
variables so the project validates semantic agreement, not only coverage shape.
The certificate now carries typed `restriction_classes` and `proof_obligations`
covering scope, provenance, dependency, evidence, formal, render, release, and
blocked-scope restrictions. The ontology profile matrix covers the Bernoulli toy
model, SI T-maze, graph-world GNN surface, and toy benchmark models with true
mapped-once uniqueness checks. The cross-track symbol table validates required
domains for GNN variables, ontology terms, Lean theorem names, manuscript
variables, JSON fields, figure labels, and rendered-manuscript consumers.
The promoted validation-spine and canonical roadmap artifacts cover provenance,
replay, counterexamples, toy sweeps, uncertainty summaries, benchmark rows,
finite model-checking witnesses, interop reports, semantic gluing, dependency
graphs, evidence-field indexing, release-bundle parity, theorem traceability,
gate ergonomics, scholarship source mapping, artifact diffing, Lean proof extraction, finite state-space
catalogs, proof dependency graphs, state transition tables, causal ablations,
ablation sensitivity reports, artifact license checks, release-note evidence,
release attestation,
track-improvement scope, and adversarial/scope audits. Live track IDs are stable
canonical names; future work improves those tracks rather than adding `_vN`
siblings.

Section [`18_supplement_full_coverage.md`](manuscript/18_supplement_full_coverage.md) binds the appendix manifest row as a composability proof; live counts are injected through manuscript variables, not hand-authored in this README. Reproducibility methodology is now a standalone supplement at [`19_supplement_reproducibility.md`](manuscript/19_supplement_reproducibility.md), followed by validation statistics at [`20_supplement_validation_statistics.md`](manuscript/20_supplement_validation_statistics.md). Optional `layers` is bound in the reproducibility supplement; `animation` is bound in the full-coverage appendix row as a sheaf fragment.

The reproducible rendering contract is documented in
[`docs/reference/rendering-reproducibility.md`](docs/reference/rendering-reproducibility.md):
authored fragments/configs generate deterministic data, figures, composed
Markdown, hydrated Markdown, PDF/web outputs, and copied root outputs through one
hydration boundary.

Full modular documentation lives under [`docs/`](docs/README.md): architecture
(pipeline, sheaf compose contract, gates, formal layers), the executable model
zoo, the manuscript scope contract and citation map, external-review
disposition ledgers, development and reproducibility guides, a glossary, and an
FAQ — the map is in [`docs/README.md`](docs/README.md).

```bash
uv run python scripts/compose_manuscript.py --list-tracks
uv run python scripts/compose_manuscript.py --section methods_analytical --tracks prose,formalism
uv run python scripts/compose_manuscript.py --validate-only --strict
```

Per-section overrides: `track_order`, `include_tracks`, `exclude_tracks`. See [`AGENTS.md`](AGENTS.md).

## pymdp anchor

The pymdp anchor is the full TMaze `full_tmaze_sophisticated_inference` profile: canonical planner `sophisticated_inference`, SI search horizon 5, rollout length 6, and Agent `policy_len = 1`, all measured from `si_tmaze_summary.json` and `pymdp.yaml`. `simulate_si_tmaze.py` also writes `si_tmaze_model_matrices.json`, `si_policy_comparison.json`, `pymdp_policy_posterior_grid.json`, and `pymdp_runtime_diagnostics.json`; vanilla planning is comparison-only. Runtime diagnostics classify known pymdp/JAX warnings and fail validation on unexpected construction warnings. Reference: [pymdp sophisticated_inference examples](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference). Logs: `output/logs/pymdp_runs.jsonl`.

## Figure registry

`figures.yaml` is the source of truth for captions, alt text, source bindings, caption-claim contracts, and pandoc-crossref placement. Current registered figures are `ising_mi_curve`, `free_energy_curve`, `distillation_divergence_geometry`, `exposure_bias_recovery`, `opd_reader_map`, `opd_situational_awareness`, `si_belief_entropy_curve`, `si_obs_action_trace`, `si_tmaze_actions`, `si_tmaze_model_matrices`, `classroom_distillation_signal`, `sequential_shift_recovery`, `sequential_shift_sensitivity`, `energy_decomposition`, `parallel_convergence`, `diversity_tradeoff`, `privilege_dose_response`, `correspondence_map`, `policy_posterior_grid`, `opd_taxonomy_landscape`, `active_selection_landscape`, `si_bridge_match`, `sheaf_coverage_heatmap`, `sheaf_layers_overview`, `invariant_dashboard`, `tmaze_schematic`, `multi_track_architecture`, `lean_boundary_status`, `gnn_ontology_concordance`, `semantic_gluing_graph`, `theorem_traceability_graph`, `causal_ablation_heatmap`, `scholarship_source_map`, and `graphical_abstract`. `active_selection_landscape` plots the expected-free-energy active-selection result (the cue-validity sweep identity and per-policy EFE decomposition); `graphical_abstract` is a quantitative-free overview schematic; `opd_reader_map` is the opening source-bound mechanism map; `opd_situational_awareness` is the early concept/evidence/non-claim atlas; detailed quantitative evidence stays in body figures and tables. `output/data/figure_source_map.json` proves each row has source artifacts, source fields, generator metadata, validation gates, and `caption_claims_ok`; `output/reports/figure_hash_manifest.json` proves declared PNG/GIF bytes match live files and rejects stray images; `output/reports/visualization_quality_audit.json` rechecks readable/nonblank pixels, source binding, `all_caption_claims_ok`, caption scope guardrails, cover wording, cover quantitative-free status, declared palette contrast, font-role floors, and unexpected-image absence.

## Pipeline tracks

See [`tracks.yaml`](tracks.yaml). **Pipeline:** required tracks are declared there, including the core analytical/pymdp/formal/notation/visual tracks, validation spine, and canonical promoted roadmap tracks. **Sheaf registry:** fragment types live in [`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml); the appendix binds the full proof row except `layers`, which is methods-only. **Deterministic extension artifacts** (thin scripts -> `src/`): `simulate_si_tmaze.py` writes policy comparison, posterior-grid, and runtime-diagnostic artifacts; `simulate_si_graph_world.py` writes graph-world summary/trace artifacts; `render_animation.py` writes a trace-derived multi-frame GIF plus frame-delta manifest; `generate_validation_spine.py`, `generate_toy_sweep_tracks.py`, `generate_formal_interop_tracks.py`, `generate_integration_audit.py`, and `generate_sheaf_tracks.py` write the canonical validation spine, semantic certificate, dependency graph, evidence-field index, release-bundle manifest, theorem traceability matrix, gate index, artifact diffoscope, proof extraction index, state-space catalog, causal-ablation matrix, artifact license audit, release-note evidence, and promoted audit artifacts.

Non-blocking future work is tracked in [`TODO.md`](TODO.md); current publication claims remain confined to deterministic toy Active Inference artifacts.

## Configuration and extension

Every config knob's consumer, the six-surface add-a-figure recipe, the
add-a-track recipe, post-edit command map, and troubleshooting live in
[`docs/reference/configuration-and-extension.md`](docs/reference/configuration-and-extension.md).
Stored `all_*` aggregate flags are re-derived from their rows at validation time
by `src/gates/aggregate_rederivation.py` (the `aggregate_rederivation` check in
`validate_outputs`), so a stale or hand-edited artifact summary fails closed.

## Method inventory

Every Python `def` and `class` under `src/` and `scripts/` is documented in the
generated reference [`docs/reference/method-inventory.md`](docs/reference/method-inventory.md).
Regenerate it after method, script, or module changes:

```bash
uv run python scripts/generate_method_inventory.py
```

The inventory distinguishes inline docstrings from inventory fallbacks, so missing
docstrings remain visible without bloating internal helper code.
