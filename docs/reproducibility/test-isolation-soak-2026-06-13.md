# AI-TEST-ISOLATION-1 Diagnostic Soak: 2026-06-13

This note records the local diagnostic run that exercised the five-run soak
collector for `AI-TEST-ISOLATION-1`. The machine-readable transcript was written
to ignored local output:
`output/reports/test_isolation_soak.json`.

## Command

```bash
uv run python scripts/run_test_isolation_soak.py \
  --runs 5 \
  --required-runs 5 \
  --seed-base 61300 \
  --output output/reports/test_isolation_soak.json
```

## Result

The diagnostic run did not satisfy the five-run idle-host criterion:

| Run | Seed | Result | Summary |
| --- | ---: | --- | --- |
| 1 | 61300 | red | `530 passed, 2 failed, 1 skipped across 11 chunks` |
| 2 | 61301 | red | `531 passed, 1 failed, 1 skipped across 11 chunks` |
| 3 | 61302 | red | `530 passed, 2 failed, 1 skipped across 11 chunks` |
| 4 | 61303 | green | `532 passed, 0 failed, 1 skipped across 11 chunks` |
| 5 | 61304 | green | `532 passed, 0 failed, 1 skipped across 11 chunks` |

The failing rows were order-sensitive stale-artifact checks, not failures in the
new transition-key validator:

- Seed 61300, chunk 4: `tests/test_lying_flag_controls.py` honest-pass checks
  saw stale canonical sheaf artifacts.
- Seed 61301, chunk 11: `tests/test_roadmap_promotion.py` saw a stale
  `manuscript_staleness_report.json`.
- Seed 61302, chunk 10: `tests/test_lying_flag_controls.py` saw the same stale
  canonical sheaf artifact class.

## Follow-Up

The test surface was hardened so direct sheaf-payload honest-pass checks and the
promoted-roadmap honest-pass test verify/refresh the gate artifact surface before
reading generated payloads. After that patch:

```bash
uv run python -m pytest \
  tests/test_lying_flag_controls.py::test_flag4_bound_fragments_honest_passes \
  tests/test_lying_flag_controls.py::test_flag7_events_ok_honest_passes \
  tests/test_roadmap_promotion.py::test_promoted_roadmap_artifacts_are_present_and_valid \
  -q
```

passed, as did the three exact failing chunk groups. A full same-seed rerun also
passed:

```bash
uv run python scripts/run_tests_chunked.py --shuffle-seed 61300 --failure-tail-lines 120
```

Result: `532 passed, 0 failed, 1 skipped across 11 chunks`.

`AI-TEST-ISOLATION-1` remains open until a fresh five-consecutive-run idle-host
soak writes `complete_soak: true`.
