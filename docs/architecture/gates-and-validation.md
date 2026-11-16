# Gates and Validation

The gate layer is the fail-closed acceptance surface. Its governing rule, from
[`src/gates/AGENTS.md`](../../src/gates/AGENTS.md), is blunt: **a missing, empty,
or inconsistent artifact is an error, never a silent pass**, and every gate ships
with a negative-control test proving it rejects bad input, not just accepts good
input.

Model ontology symbols follow the live manifest binding. A referenced file that
is missing is an invalid binding, not an empty ontology or a fallback to the old
path. Cold consumer tests produce their real artifact prerequisites; they retain
strict rejection of claims that require absent observation or release evidence.

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
- **Source-authenticated checks.** Generic aggregate rules prove flag-versus-row
  consistency. Observation, figure-integrity, and manuscript-freshness rules
  additionally authenticate current receipts, exact absent-bookend deferrals
  and current present bytes, and complete live occurrence/section hydration
  through shared validators. Consistent red evidence is not release acceptance.

`aggregate_rederivation` is itself a supported check in `output_checks.py`'s
`SUPPORTED_SELECTED_OUTPUT_CHECKS`.

The same *re-derive, never trust the stored flag* discipline is applied a second
time by `visualization_quality_audit_schema`. Beyond checking the stored row
booleans, `_visualization_quality_caption_claims_rederived`
([`integration_audit_artifacts.py`](../../src/roadmap_tracks/integration_audit_artifacts.py))
rebuilds the authoritative figure source map and registry claim payloads and
**re-derives** each caption-claim boolean (source-bound, fields-resolve-to-content,
caption-terms-present, scope, display-transform) plus the per-figure **image
facts** (readable / non-blank / dimensions, re-opened from the PNG bytes). A field
that resolves only to an empty container (`[]`/`{}`/`null`) is rejected, and a
blanked or deleted image fails even when only this check is selected — so a forged
audit JSON, a zeroed source artifact, or a blank PNG cannot pass on stored values
alone. The caption-overclaim denylist (a compacted figure must not claim it shows
every row) is paired with a positive compaction-disclosure allowlist and is
robust to row-unit synonyms, cross-clause negation, and verb/noun homographs;
because a denylist is inherently enumerable, the disclosure allowlist is the floor.

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

- `proof_dependency_graph.json` binds live proof domains, current witness
  targets, and logical edge identities; deleting an edge and its declaration
  together still fails source authentication.
- `state_transition_table.json` requires source-derived exact finite-state and
  transition coverage, not a self-declared list of required models.
- `ablation_sensitivity_report.json` joins actual numerical ablation rows and
  their current hashes; a plausible join key is insufficient.
- `release_attestation.json` binds exactly five required companions and the
  current validation-report IDs/counts. A consistent failed report is not
  release green.

Disk and in-memory consumers use the same source-authenticating validator.
Negative controls in `tests/test_track_consolidation.py` exercise coordinated
payload edits as well as simple missing or changed rows.

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

Registered controls name exact parametrized test nodes and actual target
validators. Ordinary generation reads receipts; it never executes tests.
Explicitly invoked `scripts/record_negative_controls.py` records successful
per-case baseline acceptance, mutation rejection, and test outcomes under
artifact custody. Failed, skipped, missing, duplicate, unknown, or stale
receipts cannot satisfy observation release gates.

Structural fixed-point validation may accept authenticated unobserved state
but retains every non-observation requirement. It may explicitly defer release
evidence while validating exact live release-note contents; default integration
and release checks still require that evidence. A cold structural success
does not make a release note, observation, or publication claim green.

Output validation's explicit `require_observations=False` mode propagates this
structural contract to integration-audit checks in both selected and full
evaluations, including `experiment_plan_metrics`. Default arguments still
require release evidence; structural acceptance never supplies it.

Cold test bootstrap applies this contract to manuscript integration audits with
`validate_integration_audit_artifacts(root, require_release_evidence=False)`.
The complete structural validator still checks source, schemas, and live
contents; only the release-evidence requirement is deferred. The default
`validate_manuscript` path remains strict.

The hydration CLI adopts the full-chain runner's validated inherited artifact
lease before entering the fixed-point producer; it does not contend with its
own parent or release the parent's custody. Standalone hydration acquires the
same lease itself. Shared-root structural tests accept either authentic observed
or unobserved state. Receipt-free cold-root tests retain the strict rejection
checks, so successful production alone cannot supply observation evidence.
