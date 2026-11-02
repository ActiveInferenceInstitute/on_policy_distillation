# Workflow agent guide

- One workflow, one job: keep the release gate in `ci.yml`.
- Pin actions by commit SHA (`actions/checkout`, `astral-sh/setup-uv`) and keep
  the `# vX.Y.Z` comment accurate.
- Run every Python step through `uv run --extra dev`; a bare `uv run` syncs
  without the `dev` extra and drops pytest, ruff and the type stubs.
- Install `pandoc` before the coverage gate; `tests/test_typography_contract.py`
  fails with `RuntimeError: pandoc not found on PATH` without it.
- Do not run `scripts/validate_outputs.py` as its own step; the chain builds and
  validates the artifact tree.
- A workflow edit is a release-gate edit: prove it in a pull request.
