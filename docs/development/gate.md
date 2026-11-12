# Gate entry point

[`scripts/gate.py`](../../scripts/gate.py) owns the check commands. CI invokes
its arms rather than duplicating their argv. Run from the project root:

```bash
uv sync --locked --extra dev
uv run --extra dev python scripts/gate.py          # default: fast
uv run --extra dev python scripts/gate.py --list   # authoritative command listing
uv run --extra dev python scripts/gate.py all      # CI sequence (includes the long full lane)
```

## Arms

| Arm | Contract |
| --- | --- |
| `lint` | Locked Ruff 0.17.4 and byte-compilation of `src`, `scripts`, and `tests`. |
| `fast` (default) | Existing `not artifact_slow and not render_slow` selection; no coverage. |
| `full` | Whole-suite coverage gate, unchanged 90% floor. Requires generated artifacts and selects the pinned GNN checkout explicitly. |
| `docs` | Relative Markdown path checks and documentation-contract tests. |
| `gnn` | Provision/select the upstream pin, then run the conformance and project-parser tests. |
| `chain` | Existing convergent artifact runner, bounded to four convergence passes. |
| `render` | Existing canonical `scripts/render_pdf.py` command. Requires generated artifacts, `pandoc`, and `xelatex`. |
| `all` | `lint`, `docs`, `gnn`, `chain`, `full`, sequentially. Rendering remains separate. |

Run one arm with `uv run --extra dev python scripts/gate.py ARM`. Run `chain`
before `full` or `render` on a fresh checkout. There is no types arm: the
repository has no configured static type checker.

Ruff now lives in the project's `dev` extra and `uv.lock`; lint no longer
creates an independent floating `uvx` environment. The upstream parser retains
its separate Python 3.12 environment, matching the pre-existing conformance
workflow. No contained/sibling repository is modified.

## GNN selection and CI

The canonical pin is [`gnn/upstream.json`](../../gnn/upstream.json), schema
`gnn-importer-pin/v1`: v5.0.3, commit
`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`. See
[`.github/GNN.md`](../../.github/GNN.md) for the exact parser and shipped models.

An explicit `ON_POLICY_DISTILLATION_GNN_ROOT` selection is final; an empty value
is refused. Otherwise a usable sibling checkout is read-only input, with
`output/gnn-pin/` as the provisioning destination. The arm never provisions into
the sibling slot. Occupied unusable destinations are refused. Provisioning
fetches the pinned commit/tag and installs `numpy`, `defusedxml`, and `psutil`
into the upstream interpreter. Both `gnn` and `full` select that checkout
explicitly, preventing a local `all` run from silently skipping conformance.

The workflow remains one job: key `release-gate`, display name
`gnn conformance (pinned)`. It performs one `uv sync --locked --extra dev`, then
invokes the arms. The redundant `uv lock --check`, inline provisioning/JSON
parsing, and separate version-report step were removed. The arm supplies the
version summary. The workflow still uses pinned `astral-sh/setup-uv`, not the
estate `setup-python-uv` composite action.

## Measured wall time — 2026-11-12

This host: macOS arm64, project Python 3.14.10. Other estate test processes were
observed concurrently. These are individual observations, not a controlled
benchmark; no speedup or causal explanation for the differences is claimed.
Before means the directly invoked existing command; after means the arm wrapper.

| Arm | Before (seconds) | After (seconds) | Evidence/limit |
| --- | ---: | ---: | --- |
| `lint` | 0.27 | 0.45 | Initial Ruff/compileall wrapper measurement, before moving Ruff into the shared lock. Final locked arm separately smoke-checked. |
| `fast` | 46.4 | 49.1 | Before: 521 passed. After: 522 passed at measurement time; a subsequently removed wiring-only test accounts for the count difference. |
| `docs` | — | 2.6 | New link checker plus then-current documentation tests; no pre-existing link-check command. |
| `gnn` | — | 14.6 | New standalone arm: fresh provisioning plus 38 passing tests. No separate pre-change local arm. |
| `chain` | 172.1 | 245.8 | Both green, zero convergence passes. |
| `render` | 70.9 | 97.5 | Historical timing observations; current exact PDF identity and renderer versions are in the [tracked render receipt](../reproducibility/render-receipt.json). |
| `full` | incomplete | not run | Attempt stopped after exceeding the requested ~10-minute bound; no completed coverage result. |

The interrupted full command was:

```bash
uv run --extra dev python -m pytest tests/ --cov=src --cov-fail-under=90 -q
```

The after `full`/`all` runs were deliberately skipped under the scope bound.
The suite had reached `test_sheaf_compose.py`; its orchestrator tests also invoke
the artifact convergence tail. Neither a release-suite pass nor 90% coverage is
claimed.

A bounded diagnostic selection was also run once:

```bash
uv run --extra dev python -m pytest tests/ -m "not artifact_slow and not render_slow" --cov=src --cov-fail-under=90 -q
```

It took 347.1 seconds, exit 1: 521 passed, one stale generated-method-inventory
failure, and 70.14% coverage (below 90%). The inventory was regenerated after
final script edits and checked narrowly. The reduced selection is **not** the
release gate and is not presented as a passing coverage substitute. The 90%
floor remains unchanged; no full/release lane was retried.

## Documentation and manuscript verification

The repository had documentation-contract tests but no mkdocs or
markdown-link-check configuration. `scripts/check_docs_links.py` checks relative
paths in tracked Markdown (or a non-Git copy's tree), including images and
reference definitions. It ignores fenced examples, URL schemes, fragments,
absolute paths, and generated/tool-owned trees. Anchor existence and remote URL
availability are outside its scope.

The existing rendering shape already matches the reference conventions: pandoc
Markdown under `manuscript/`, variables produced into
`output/data/manuscript_variables.json`, a validated `figures.yaml` registry,
and one authoritative `scripts/render_pdf.py` facade. No template or GNN
registry changes were needed. Both direct and arm renders succeeded with
pandoc, pandoc-crossref, and XeLaTeX; the current artifact path, exact bytes,
SHA-256, source commit/worktree state, and tool version output are preserved in
the [tracked render receipt](../reproducibility/render-receipt.json).
Two nonfatal oversized-float warnings remain (approximately 65 pt); no PDF
placeholder or fallback was used.

## Final bounded verification

After locking Ruff and regenerating the method inventory, a governed offline
run with a 600-second process-tree limit passed these exact project commands:

```bash
.venv/bin/python scripts/gate.py --list
.venv/bin/python scripts/gate.py lint
.venv/bin/python scripts/gate.py docs
.venv/bin/python -m pytest tests/test_method_inventory.py -q --no-cov
ON_POLICY_DISTILLATION_GNN_ROOT=/tmp/estate-gnn-pin .venv/bin/python scripts/gate.py gnn
```

Final observations: locked lint passed (0.57 s); docs passed (4.35 s,
250 Markdown files, zero broken relative paths, 10 documentation tests);
method inventory passed (five tests); pinned GNN passed (38 tests, 25.99 s,
existing checkout). Real temporary-file negative controls rejected missing
inline/reference/external-relative links and empty/occupied GNN selections.
Full coverage was deliberately excluded from this final check.
