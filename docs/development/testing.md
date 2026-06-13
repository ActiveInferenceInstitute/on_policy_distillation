# Testing

The test system has one authoritative gate (the full suite under coverage) and
two faster lanes that drop the slow tests for the edit loop. Configuration lives
in [`../../pyproject.toml`](../../pyproject.toml) (`[tool.pytest.ini_options]`,
`[tool.coverage.*]`) and [`../../conftest.py`](../../conftest.py).

## Layout

All tests live under [`../../tests/`](../../tests/), discovered as `test_*.py`
(`testpaths = ["tests"]`, `python_files = ["test_*.py"]`). There is one nested
suite, [`../../tests/gates/`](../../tests/gates/), holding the output/manuscript
gate checks (`test_output_gates.py`, `test_manuscript_gates.py`,
`test_claim_ledger.py`). Shared fixtures and helpers live in
[`../../tests/conftest.py`](../../tests/conftest.py),
`tests/sheaf_fixtures.py`, and `tests/gate_support.py`.

The root [`../../conftest.py`](../../conftest.py) puts `src/` and `tests/` on
`sys.path`, sets `MPLBACKEND=Agg` for headless plotting, and prefers this
project's `.venv` site-packages so a root pytest that delegates here still finds
`inferactively-pymdp`.

## Markers

Declared in `pyproject.toml` (`addopts` includes `--strict-markers`, so an
unregistered marker is an error). The marker contract is itself tested by
`tests/test_marker_contracts.py`.

| Marker | Meaning |
| --- | --- |
| `artifact_slow` | Full fixed-point or artifact-write tests, kept out of the fast local lane. |
| `render_slow` | Figure rendering, animation, rollout, or large-compose tests, kept out of the daily edit loop. |
| `mutates_artifacts` | Tests that temporarily mutate generated or tracked artifact files. |
| `requires_pymdp` | Tests that import `inferactively-pymdp`. |
| `timeout(seconds)` | Per-test timeout for artifact write/validate isolation checks (via `pytest-timeout`). |

## Fast lanes vs. the full gate

The fast lanes (from [`../README.md`](../README.md)) trade coverage of slow
paths for turnaround speed. They are *not* a substitute for the full gate.

```bash
# tightest edit loop: no slow artifact writes, no expensive renders, no coverage
uv run --extra dev python -m pytest tests/ -m "not artifact_slow and not render_slow" --no-cov

# wider lane: keeps render/compose checks, still no full fixed-point writes
uv run --extra dev python -m pytest tests/ -m "not artifact_slow" --no-cov

# authoritative gate: whole suite under coverage
uv run python -m pytest tests -q
```

> The fast lane excludes tests that perform full fixed-point artifact writes or
> mutate shared generated artifacts; the tighter edit loop additionally excludes
> expensive rendering, animation, rollout, and large-compose checks. The full
> coverage gate remains authoritative.

## No-mocks policy

Tests use real data and real computation — no `MagicMock`, no `mocker.patch`,
no `unittest.mock`. HTTP-style boundaries use local test servers, file I/O uses
real temp files (`tmp_path`), and PDF/figure checks inspect real generated
artifacts. This is the same discipline that lets the writer/validator boundary
mean something: a validator that re-derives a result from rows is only honest if
nothing in the test path is faked (see
[`conventions.md`](conventions.md#writervalidator-separation)).

## Coverage floor

`[tool.coverage.report]` sets `fail_under = 90` with `branch = true`,
`source = ["src"]`, `show_missing = true`, and `precision = 2`; `[tool.coverage.run]`
omits `tests/*` and `*/__init__.py`. The 90% floor applies to project `src/`
and is enforced by the full gate (`uv run python -m pytest tests -q`). Do not
quote a snapshot percentage in docs — quote the floor.

## Chunked runner

On a heavily loaded machine (resident co-actor pipelines, LLM servers) a single
long-lived pytest process is reliably killed by resource pressure, observed as
exit 143/144. [`../../scripts/run_tests_chunked.py`](../../scripts/run_tests_chunked.py)
runs the suite as N-file chunks, each in its own short-lived subprocess, which
survives the same load and covers the same test files. Its exit code is honest:
0 only when every chunk reports 0 failures.

```bash
.venv/bin/python scripts/run_tests_chunked.py                 # whole suite, 6 files/chunk
.venv/bin/python scripts/run_tests_chunked.py --chunk-size 3
.venv/bin/python scripts/run_tests_chunked.py --timeout 900
```

The runner also supports a deterministic order-coverage soak (chain B of the
test-isolation work):

```bash
.venv/bin/python scripts/run_tests_chunked.py --shuffle-seed 17
```

The same seed always yields the same file order, so a red shuffled run is
exactly reproducible. Report a red seed — never re-roll to a passing one.

## Isolation soak reports

[`../../scripts/run_test_isolation_soak.py`](../../scripts/run_test_isolation_soak.py)
wraps the chunked runner for `AI-TEST-ISOLATION-1` and writes an incremental
JSON transcript after every run:

```bash
.venv/bin/python scripts/run_test_isolation_soak.py \
  --runs 5 \
  --required-runs 5 \
  --seed-base 61300 \
  --output output/reports/test_isolation_soak.json
```

A diagnostic soak may stop red or partial; it is still useful if it preserves
the seed, failed chunk ids, failed test names, and bounded failure tail. A
completion soak is stricter: validate the saved report with
`--validate-report --require-complete`, which requires consecutive seeds,
complete diagnostics for red rows, and `complete_soak: true`.

```bash
.venv/bin/python scripts/run_test_isolation_soak.py \
  --validate-report output/reports/test_isolation_soak.json \
  --require-complete
```

The same-seed policy applies to both layers. If a shuffled soak is red, rerun
the exact seed or exact failing chunk group to diagnose it; do not change seeds
to search for a green transcript.

## See also

- [`conventions.md`](conventions.md) — code conventions and the writer/validator boundary.
- [`../reference/configuration-and-extension.md`](../reference/configuration-and-extension.md) — the *what to run after editing X* table.
- [`../reference/method-inventory.md`](../reference/method-inventory.md) — generated coverage of every `def`/`class` under `src/` and `scripts/`.
