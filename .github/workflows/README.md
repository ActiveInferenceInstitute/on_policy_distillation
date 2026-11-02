# Workflows

`ci.yml` is the release gate. It runs on pushes to `main` and on every pull
request, and it is the only workflow in this directory.

The gate is deliberately one job: lock check, locked sync with the `dev` extra,
byte-compile, the bounded artifact chain, and the release coverage gate. The
suite reads generated artifacts, so the chain step is required on a clean
checkout. `pandoc` is installed because the typography contract test renders the
combined `.tex`.

Local equivalent (see the repository `README.md`):

```bash
uv run --extra dev python scripts/run_full_chain.py --max-passes 4
uv run --extra dev python -m pytest tests/ --cov=src --cov-fail-under=90
```
