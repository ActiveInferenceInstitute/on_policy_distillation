# Code conventions

These conventions are enforced by tests and the lint gates, not just by habit.
Sources: [`../../src/AGENTS.md`](../../src/AGENTS.md),
[`../../scripts/AGENTS.md`](../../scripts/AGENTS.md),
[`../../AGENTS.md`](../../AGENTS.md), and the lint config in
[`../../pyproject.toml`](../../pyproject.toml).

## Thin orchestrator pattern

All reusable, tested logic lives in [`../../src/`](../../src/).
[`../../scripts/`](../../scripts/) contains **no business logic** — scripts parse
arguments, resolve paths, call `src/` functions, and print output paths to
stdout for manifest collection. Computation stays deterministic: fixed seeds,
`MPLBACKEND=Agg`, no network, no runtime downloads.

```python
# scripts/<name>.py — orchestration only
from analytical.invariants import check_invariants   # tested src/ function
result = check_invariants(project_root)              # logic lives in src/
print(output_path)                                   # for manifest collection
```

The `z_`-prefixed script (`z_generate_manuscript_variables.py`) runs last in
lexicographic analysis order because it depends on prior outputs. Extension
scripts delegate to `src/` too (e.g. `render_animation.py` →
`src/visualizations/animation.py`, `simulate_si_graph_world.py` →
`src/simulation/graph_world.py`).

This separation is what keeps the project copy-out-and-run standalone — see
[`../reproducibility/standalone-vs-template.md`](../reproducibility/standalone-vs-template.md).

## Type hints and docstrings

- Public `src/` functions carry type hints; the project uses
  `from __future__ import annotations` and targets `py310`.
- Module and public-function docstrings state role and contract. Scripts open
  with a one-line purpose docstring and a `Usage:` block (see
  `run_tests_chunked.py`, `run_full_chain.py` for the house style).
- Use nearby `WHY:` comments only for surprising local choices, per
  [`../../AGENTS.md`](../../AGENTS.md) — not as narration of obvious code.

## ruff + mypy gates

The project `[tool.ruff]` mirrors the template-root gate: `line-length = 120`,
`select = ["E", "F"]`, `ignore = ["E741"]`, `target-version = "py310"`. Per-file
ignores match root semantics — `scripts/*` allow `E402`/`E501` (sys.path
bootstrap before imports, long CLI strings), `tests/**` add `E712`,
`src/**` allow `E501`, and `__init__.py` allows `F401` (re-exports).

```bash
uvx ruff check src tests scripts          # mirrors the template-root gate
```

A bare `uvx ruff check src tests scripts` inside this project matches the root
gate by design. mypy is run over the same source set in the template-root CI
scope; keep public APIs typed so it stays green.

## Module size

Keep `src/` modules at or under ~500 lines. Create a new module rather than
growing one past the cap — for example, add a `figures_*.py` module rather than
extending an existing one. When you split a module, **preserve public exports**:
tests import from the established paths, and facades (e.g. `invariants.py`,
`si_runner.py`, `gates/validation.py`) exist precisely to keep those paths
stable after a split.

## Writer/validator separation

The single most important convention: **validators re-derive rather than trust
stored booleans.**

- A producer script writes an artifact that may include aggregate flags such as
  `all_figures_mapped` or `all_*` summaries.
- The validator does **not** trust those flags. `src/gates/aggregate_rederivation.py`
  (`ARTIFACT_AGGREGATE_RULES`) maps each artifact's stored `all_*` flag to
  row-level predicates and fails when a stored flag disagrees with its rows. A
  hand-edited or stale artifact is caught because the rows no longer support the
  summary.
- Numeric tolerances are **deliberately duplicated** across the boundary:
  writer-side constants live in `src/analytical/hyperparameters.py` and
  `src/simulation/numerics.py`; validator-side literals in `src/gates/` are
  independent copies. Across the writer/validator trust boundary, duplication is
  the verification mechanism — do not "consolidate" them into a shared constant.
- The gate index (`src/roadmap_tracks/integration_audit_builders.py`) derives
  `indexed` from on-disk input existence and re-derives a live binding requiring
  every declared gate row to match a check key the run actually produced;
  phantom rows fail validation (`tests/test_gate_index_binding.py`).

The corollary for every new verifier-like gate is the promotion rule in
[`../../TODO.md`](../../TODO.md): a producer, a deterministic artifact, a
manuscript consumer, a typed claim, a validation restriction, **and a negative
control** that proves the gate bites.

## See also

- [`extending.md`](extending.md) — how to add a track/model/figure/section.
- [`testing.md`](testing.md) — suites, markers, coverage floor, chunked runner.
- [`../reference/configuration-and-extension.md`](../reference/configuration-and-extension.md) — every config knob and its consumer.
