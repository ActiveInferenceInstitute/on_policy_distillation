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
| `gnn` | Provision/select the upstream pin, run the shared reader (`gnn.importers`) from that revision, then run the conformance and project-parser tests. |
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
`gnn-importer-pin/v1`: v5.1.0, commit
`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`. See
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

## GNN-FEP cutover — adopted

The [GNN-FEP contract](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/workflows/gnn-fep.md)
gives pin reading, pin and pointer validation, and specification validation one
home: `src/gnn/importers.py` in the pinned GNN revision. This member now calls
that reader instead of carrying its own.

The pin moved from **v5.0.3 at `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`** to
**v5.1.0 at `75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`**. The old revision
predates `e6a9d3917` ("Make the downstream importer registry executable"), so
`src/gnn/importers.py` is absent there and `python -m gnn.importers` cannot run
against it; that absence was the recorded blocker in #21. The new revision
contains the module.

The `gnn` arm runs the reader from that pinned revision, before the conformance
tests:

```bash
python -m gnn.importers check --repo . --require-pointer \
    --workflow .github/workflows/ci.yml --job release-gate
```

The arm extracts `src/gnn` from the pinned commit with `git archive`, puts only
that tree on `PYTHONPATH`, and executes the command with the selected
checkout's own interpreter — the same pinned bytes and interpreter the
conformance tests use. The pin's raw revision, repository and tag are read
literally once before provisioning, because no pinned interpreter exists yet;
everything the contract makes a finding is the reader's output.

Removed in the same change: `load_upstream_pin`, `UpstreamPin`,
`UpstreamPinError` (renamed `UpstreamConformanceError`, which now only reports
malformed conformance digests), the pin regex/field tables in
`src/gnn/upstream.py`, and the four tests whose only subject was pin shape
(nineteen collected cases, including the parametrized malformed-shape matrix). The
conformance test keeps `CANONICAL_TAG`/`CANONICAL_COMMIT` as a deliberate re-pin
tripwire and reads the pin's values for its digest run; it no longer validates
the pin's shape. `.github/GNN.md` names the pin path, the new revision, `ci.yml`
and `release-gate`, which is what `--require-pointer` checks.

No manuscript-variable change was needed. `scripts/z_generate_manuscript_variables.py`
delegates to `hydrate_manuscript_fixed_point`, and the only GNN-derived variable
it produces (`gnn_spec_version`) is parsed from the specification's
`## GNNVersionAndFlags` header, not from the pin: no inline `gnn/upstream.json`
read exists in the producer chain to replace with
`gnn.importers.importer_variables`. After this change `scripts/gate.py` is the
only Python file that reads the pin, and it reads three fields to locate the
revision the reader then validates.

The non-vacuity control was re-anchored rather than dropped: v5.1.0 collapses
heading whitespace, so the previously spaced `## ActInf Ontology Annotation`
mutant is now parsed upstream and would have been vacuous. The mutant is the
doubled-space spelling, which upstream still normalizes into the ontology
section and the project parser does not; measured on this change it produces
exactly one `ontology:` divergence with the eight Bernoulli bindings populated
upstream. The shipped specs themselves still produce equal digests, so no
shipped dtype mapping (`binary` upstream versus `bool` here) diverges in this
member.

Observed when the arm was exercised on this change (this host, project Python
3.14.10, sibling GNN checkout read-only):

```text
$ python -m gnn.importers check --repo . --require-pointer --workflow .github/workflows/ci.yml --job release-gate
importer: <repository root>
  pin: gnn/upstream.json -> v5.1.0 @ 75c834bd85 (schema gnn-importer-pin/v1)
  specs: 3
  pointer: .github/GNN.md -> ok
  verdict: ok
```

That run selected an existing sibling checkout read-only; provisioning was not
exercised in it. The `gnn` arm reported 23 passed
(`tests/test_gnn_upstream_conformance.py` and `tests/test_gnn.py`, `[gnn] OK
4.9s`), and the other arms were green on the same tree, all on 2026-11-12 with
project Python 3.14.10:

| Arm | Result |
| --- | --- |
| `python scripts/gate.py` (default `fast`) | exit 0, 500 passed, 6 skipped, 137 deselected, 52.0 s |
| `lint` | exit 0, Ruff and compileall, 0.1 s |
| `docs` | exit 0, 251 Markdown files, 0 broken links, 11 tests, 1.4 s |
| `gnn` | exit 0, reader `verdict: ok`, 23 tests, 4.9 s |
| `chain` | exit 0, `OK: chain green (convergence passes used: 0)`, 122.6 s |

`chain` was run with an existing artifact tree carried over from this checkout's
prior run. With an empty `output/` the same arm stops at manuscript hydration
(`release_notes_evidence.json has unsupported notes`), because the release
bundle comes from the separate `render` arm; that is the environment, not this
change, and it is the reason the earlier `chain` attempt in this worktree
failed. `full` (coverage) was not run.

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
