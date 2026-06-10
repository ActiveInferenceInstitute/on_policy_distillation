# Test Notes

No mocks — use real data, fixed RNG seeds, and `tmp_path` for I/O. Each gate and
invariant should have a negative control that proves it fails on bad input.

Gate negative controls live under `tests/gates/` (`test_output_gates.py`,
`test_manuscript_gates.py`, `test_claim_ledger.py`) plus `test_lean_gate.py`.
Small support helpers remain in `test_support_modules.py`.

Sheaf tests are split by concern: `test_sheaf_manifest.py`, `test_sheaf_registry.py`,
`test_sheaf_compose.py`, `test_sheaf_coverage.py`, `test_sheaf_cli.py`,
`test_coverage_pipeline.py`, `test_sweep_io.py` (no monolithic `test_sheaf.py`).

Daily edit loop: `uv run --extra dev python -m pytest tests/ -m "not artifact_slow and not render_slow" --no-cov`.

Fast pre-release lane: `uv run --extra dev python -m pytest tests/ -m "not artifact_slow" --no-cov`.
Tests marked `mutates_artifacts` must also be marked `artifact_slow`, so the
fast lane never edits shared generated artifacts.
Use `render_slow` for expensive figure rendering, animation/GIF generation,
pymdp rollout, and large manuscript-compose coverage that should remain in the
pre-release and release gates but stay out of the daily edit loop.

Release gate: `uv run --extra dev python -m pytest tests/ --cov=src --cov-fail-under=90`.
