# Gates and Validation

The gate layer is the fail-closed acceptance surface. Its governing rule, from
[`src/gates/AGENTS.md`](../../src/gates/AGENTS.md), is blunt: **a missing, empty,
or inconsistent artifact is an error, never a silent pass**, and every gate ships
with a negative-control test proving it rejects bad input, not just accepts good
input.

The entry point is [`scripts/validate_outputs.py`](../../scripts/validate_outputs.py),
which calls `validate_outputs` and `validate_manuscript`, writes
`output/reports/validation_report.json`, and exits 1 if any check failed:

```bash
uv run python scripts/validate_outputs.py
```

## Module layout

| Module | Role (from `src/gates/AGENTS.md`) |
| --- | --- |
| [`validation.py`](../../src/gates/validation.py) | Public facade: `validate_outputs`, `validate_manuscript`, `build_lean`. |
| [`artifact_manifest.py`](../../src/gates/artifact_manifest.py) | `REQUIRED_OUTPUTS` — the single source of truth for output existence checks. |
| [`output_checks.py`](../../src/gates/output_checks.py) | Pipeline artifact existence + SI schema checks. |
| [`manuscript_checks.py`](../../src/gates/manuscript_checks.py) | Sheaf manifest, tokens, hydration, layers markers. |
| [`claim_ledger.py`](../../src/gates/claim_ledger.py) | Claim ledger vs on-disk artifacts (`data/claim_ledger.yaml` required). |
| [`lean.py`](../../src/gates/lean.py) | Conditional `lake build` when `lean/lakefile.lean` exists. |
| [`method_inventory.py`](../../src/gates/method_inventory.py) | AST-backed report for every `def`/`class` under `src/` and `scripts/`. |
| [`aggregate_rederivation.py`](../../src/gates/aggregate_rederivation.py) | Read-time re-derivation of stored `all_*` aggregate booleans. |

## Re-derived vs trusted

The central design decision is *what the gate trusts*. The
[`aggregate_rederivation.py`](../../src/gates/aggregate_rederivation.py) docstring
states the threat model precisely:

- **Re-derived.** A stored aggregate boolean (`all_pass`, `all_passed`, …) is
  treated as a *conjecture*; the rows are the evidence. The check is `stored ==
  re-derived` with strict equality in both directions: a flag that is `True` over
  failing rows is lying, and a flag that is `False` over passing rows is broken
  bookkeeping — both mean the artifact cannot be trusted. Empty or missing rows
  with a stored `True` flag re-derive to `False`; vacuous truth over `[]` is
  exactly the green-wash this layer exists to stop. The re-derivation rules live
  in **one** module (no copy-drift), and only aggregates whose row-level
  predicate is unambiguous are covered.
- **Trusted (out of scope here).** This layer proves *flag-vs-rows* consistency,
  not row correctness. A payload whose rows were forged wholesale (rows and flag
  rewritten together) passes here by construction; byte-level integrity of rows
  is the provenance / hash-manifest layer's job (`artifact_provenance.json`,
  `artifact_diffoscope`). The two layers compose: diffoscope pins the bytes, this
  module pins the logic.

`aggregate_rederivation` is itself a supported check in `output_checks.py`'s
`SUPPORTED_SELECTED_OUTPUT_CHECKS`.

## Schema and existence validators

`output_checks.py` builds its supported check set from `REQUIRED_OUTPUTS` plus a
fixed family of schema and invariant keys, including (verbatim from the module):
`si_summary_schema`, `si_tmaze_model_matrices_schema`,
`pymdp_policy_posterior_grid_schema`, `figure_source_map_schema`,
`figure_hash_manifest_schema`, `visualization_quality_audit_schema`, the
`firstprinciples_*` schemas, `toy_sweep_track_schemas`,
`formal_interop_track_schemas`, `integration_audit_track_schemas`,
`canonical_sheaf_track_schemas`, and `aggregate_rederivation`. A gate-index alias table maps index ids whose live
check key differs from the row id, and three ids are explicitly *external*
commands that cannot appear in `checks` (`validate_outputs`,
`validate_manuscript`, `lake_build`). When reports exist, `validate_outputs` also
checks `invariants_all_pass`, `simulation_invariants_all_pass`,
`si_invariants_all_pass`, and `experiment_plan_metrics`.

`validate_manuscript` adds the composition-side gates: `methods_sheaf_layers`
(the reproducibility section must contain `sheaf_layers_overview.png` plus the
`<!-- sheaf-layers:registry/binding-matrix/legend -->` markers),
`manuscript_tokens_registered` (every `{{token}}` maps to a
`generate_variables()` key), `resolved_manuscript_hydrated` (no unresolved `{{`
after hydration), and `full_sheaf_appendix_tracks` (the full-coverage appendix
contains every `sheaf-track:{id}` marker bound in the manifest).

## Canonical supplemental artifact validators

The canonical supplemental artifacts keep stable IDs and deepen their validation
rules in place:

- `proof_dependency_graph.json` must have linked theorem rows, resolved edges,
  unique edge keys, all required edge types, and no orphan theorem/model-witness
  targets. Negative controls live in
  `tests/test_track_consolidation.py` by dropping links, duplicating edges, and
  pointing an edge at an orphan target.
- `state_transition_table.json` must have deterministic transitions, unique
  transition keys, coverage for every required finite toy model, outgoing
  transitions for every reachable state key, and terminal self-transition
  coverage. Negative controls mutate missing models, duplicate keys, missing
  outgoing coverage, and terminal self-transition coverage.
- `ablation_sensitivity_report.json` must keep every effect source-backed, bind
  each row by an explicit source join key, and agree with the causal-ablation
  source row count. Negative controls remove source backing and join keys.
- `release_attestation.json` must agree with its row pass/fail state, pin the
  current validation-report hash, and expose attested source counts plus
  validation check ids/counts. Negative controls flip a failed gate to passed or
  stale the attested counts.

The idle-host isolation soak is intentionally not a release blocker. Its
diagnostic/completion contract is enforced by
`scripts/run_test_isolation_soak.py --validate-report`; closure requires
`--require-complete` and `complete_soak: true`.

`scripts/audit_roadmap_tasks.py` is a lightweight project-management gate, not a
publication claim gate. It fails when active `TODO.md` rows and `tasks.yaml`
disagree on status, progress, proof-artifact notes, or blocked/deferred state.

## Invariant checks

Invariants are split by track and registry-backed:

- **Analytical** —
  [`src/analytical/invariants.py`](../../src/analytical/invariants.py) (re-exported
  by [`src/invariants.py`](../../src/invariants.py)). These are computations, not
  stored flags: `inv_ising_mi_at_zero` checks the closed-form Ising mutual
  information is zero at `lambda = 0` within tolerance; `inv_ising_mi_saturates`
  checks it saturates to `ln 2` at large lambda; `inv_empirical_matches_closed_form`
  checks empirical and closed-form MI agree across the lambda grid; and
  `inv_decomposition_identity` checks the free-energy decomposition identity holds
  for the Ising joint posterior at `lambda = 1.5`.
- **Simulation** —
  [`src/simulation/invariants.py`](../../src/simulation/invariants.py) reads the
  generated T-maze artifacts. For example `inv_belief_entropy_finite` requires
  `mean_belief_entropy` in `si_tmaze_summary.json` to be finite and non-negative,
  and `inv_actions_length_matches_steps` requires the action list length to equal
  `rollout_timestep_count` and `steps + 1`.

The validation spine ([`src/validation_spine/artifacts.py`](../../src/validation_spine/artifacts.py))
writes the provenance, deterministic replay, and counterexample artifacts that
the audits and the release attestation consume; see [`pipeline.md`](pipeline.md).

## Lean gate

`build_lean(root)` runs `lake build` only when `lean/lakefile.lean` exists (it
must exit 0); a project without a Lean tree returns a clean skip message. What
the Lean layer proves — and does not — is covered in
[`formal-layers.md`](formal-layers.md).

## Negative controls

Per the AGENTS contract, gates are paired with negative controls in `tests/`,
e.g. `test_validate_outputs_negative_missing_sweep`,
`test_validate_outputs_negative_missing_sheaf_matrix`,
`test_validate_outputs_negative_si_invariants_fail`,
`test_validate_outputs_negative_analytical_invariants_fail`, and the manuscript
and Lean negatives. A new gate without a negative control is incomplete by
policy.
