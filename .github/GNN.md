# GNN conformance

`gnn conformance (pinned)` is the display name of the `release-gate` job in
`.github/workflows/ci.yml`. It reads `gnn/upstream.json` (schema
`gnn-importer-pin/v1`), which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`).

The job fetches that commit, installs the pinned parser's dependencies into a
Python 3.12 virtual environment, and runs
`uv run --extra dev python -m pytest tests/ --cov=src --cov-fail-under=90 -q`
with `ON_POLICY_DISTILLATION_GNN_ROOT` pointing at the checkout.
`tests/test_gnn_upstream_conformance.py` extracts `src/gnn` from the pinned
commit with `git archive` and runs its
`gnn.parsers.markdown_parser.MarkdownGNNParser` over every shipped
`gnn/*.gnn.md` spec (`bernoulli_toy`, `graph_world`, `si_tmaze`) plus a
leniency mutant, comparing normalized digests against the project-owned parser
in `src/gnn/parser.py`. It does not scan the rest of the repository for
`*.gnn.md`; the claim covers the three shipped specs and the pin, not any
model added elsewhere.
