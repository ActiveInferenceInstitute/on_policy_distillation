# Analysis scripts

Thin orchestrators that import from `../src/` and handle I/O only.

- `run_analytical_sweep.py` — closed-form sweep over hyperparameters.
- `compute_statistics.py` — write the combined analytical + simulation statistics JSON.
- `generate_firstprinciples.py` — emit the OPD<->active-inference first-principles
  artifacts (correspondence map, divergence/exposure/energy demos, the two-agent
  pymdp classroom by default, and the classroom-derived inferential statistics).
- `render_pdf.py` — render the standalone manuscript PDF (cover, hyperlinked
  citations, abstract-first ordering).
- `simulate_si_tmaze.py` — run the pymdp sophisticated-inference T-maze, policy comparison, posterior grid, and runtime diagnostics.
- `simulate_si_graph_world.py` — write deterministic graph-world summary/trace artifacts.
- `generate_figures.py` — render figures from generated data.
- `render_animation.py` — render the trace-derived belief trajectory GIF.
- `generate_validation_spine.py` — write provenance, deterministic replay,
  and counterexample matrix artifacts.
- `generate_toy_sweep_tracks.py` — write sensitivity, uncertainty, benchmark,
  measured policy-grid, EFE, analytical-observable, graph-world topology-trace,
  graph-world invariant, state-space catalog, and causal-ablation artifacts.
- `generate_formal_interop_tracks.py` — write model-checking, GNN, ontology,
  interop, Lean theorem inventory, and proof-extraction artifacts.
- `generate_integration_audit.py` — write producer/stale/token/figure/scope/claim/adversarial, visualization-quality, diffoscope, license, and release-note audit artifacts.
- `generate_sheaf_tracks.py` — write the canonical semantic certificate,
  dependency graph, evidence-field index, release-bundle manifest, theorem
  traceability matrix, gate index, artifact diffoscope, proof extraction index,
  state-space catalog, causal-ablation matrix, artifact license audit,
  release-note evidence, track-improvement scope, blocked-scope manifest, and
  consolidated promoted track artifacts.
- `generate_method_inventory.py` — regenerate `docs/reference/method-inventory.md`
  from the live `src/` and `scripts/` AST so every `def` and `class` has a
  documented reference entry.
- `inject_variables.py` / `z_generate_manuscript_variables.py` — hydrate
  manuscript variables from run outputs.
- `compose_manuscript.py` — sheaf-compose the multi-track sections.
- `validate_outputs.py` — run the validation gates over generated outputs.
- `run_full_chain.py` — **one-command convergent runner**: executes the canonical
  `analysis.scripts` order from `manuscript/config.yaml`, validates, and — because
  `release_attestation.json` attests the *previous* `validation_report.json` —
  re-runs the attestation/figure-hash tail and re-validates to a bounded fixed
  point (`--max-passes`, default 3). Use `--tail-only` after editing manuscript
  fragments, ledger claims, tokens, or figure sources; `--render` to also
  produce the PDF; `--dry-run` to print the plan. Exit 0 only when the final
  validate is green and the release attestation pins that validation report.
- `run_tests_chunked.py` — run the test suite as small per-process chunks.
  On a loaded machine a single long pytest process is reliably killed by
  resource pressure (observed exit 144); per-chunk subprocesses survive and
  cover the same files. Exit 0 only when every chunk is clean.
  `--shuffle-seed N` shuffles file order deterministically (same seed = same
  order) for isolation soaks; a red shuffled run is a finding to report,
  never a seed to re-roll.
- `run_test_isolation_soak.py` — run repeated deterministic shuffled
  `run_tests_chunked.py` passes and write
  `output/reports/test_isolation_soak.json`. The default is the
  `AI-TEST-ISOLATION-1` five-run evidence collection contract; a partial run is
  useful diagnostics but does not set `complete_soak`. The report is rewritten
  after every executed run so red or interrupted soaks preserve the failing seed
  and bounded tail. Use `--validate-report PATH` to validate an existing
  transcript, and add `--require-complete` only when checking closure evidence.
- `audit_roadmap_tasks.py` — check that `TODO.md` future-work rows and
  `tasks.yaml` taskboard metadata agree on active status, progress,
  proof-artifact notes, and blocked/deferred semantics.

## Order matters

Running generators out of order silently restales downstream certificates
(`generate_sheaf_tracks.py` must precede `z_generate_manuscript_variables.py`;
the validation spine must precede the audits). `run_full_chain.py` encodes the
canonical order — prefer it over invoking generators by hand.
