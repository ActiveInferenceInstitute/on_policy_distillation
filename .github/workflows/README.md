# Workflows

`ci.yml` is the release gate. It runs on pushes to `main` and on every pull
request, and it is the only workflow in this directory.

The gate is deliberately one job; its check steps invoke
[`../../scripts/gate.py`](../../scripts/gate.py): one locked environment, then
`lint`, `docs`, `gnn`, `chain`, and `full`. The suite reads generated artifacts,
so the `chain` arm is required on a clean checkout. `pandoc` is installed because
the typography contract test renders the combined `.tex`.

Local equivalent — the same arms, in the same order, in the same interpreter
environment (`python scripts/gate.py --list` prints each arm's argv):

```bash
uv sync --locked --extra dev
uv run --extra dev python scripts/gate.py all
```

`all` is `lint, docs, gnn, chain, full`. The `render` arm is not part of CI.
