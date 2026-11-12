# Workflow agent guide

- One workflow, one job: keep the release gate in `ci.yml`.
- Every Python step is an arm of `scripts/gate.py`; the workflow never restates
  an argv. Change the arm, not the step.
- Pin actions by commit SHA (`actions/checkout`, `astral-sh/setup-uv`) and keep
  the `# vX.Y.Z` comment accurate. The job uses `astral-sh/setup-uv` directly; it
  does not use the estate `setup-python-uv` composite action.
- Run every Python step through `uv run --extra dev`; a bare `uv run` syncs
  without the `dev` extra and drops pytest.
- Sync once (`uv sync --locked --extra dev`) and let the arms share that
  environment; `--locked` already refuses an out-of-date `uv.lock`.
- Install `pandoc` before the arms that run tests; `tests/test_typography_contract.py`
  fails with `RuntimeError: pandoc not found on PATH` without it.
- Set `ON_POLICY_DISTILLATION_GNN_ROOT` at job level so the `full` arm reuses the
  checkout the `gnn` arm provisioned instead of skipping the conformance half.
- Do not run `scripts/validate_outputs.py` as its own step; the chain builds and
  validates the artifact tree.
- A workflow edit is a release-gate edit: prove it in a pull request.
