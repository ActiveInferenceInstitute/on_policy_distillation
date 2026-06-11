"""Read-time re-derivation of stored ``all_*`` aggregate booleans.

Closes TODO row ``AI-STALE-SUMMARY-1`` and the Run-2 cross-vendor residual
("predicates check pre-computed flags, not re-derivations"). Inner track
validators enforce flag-to-rows honesty at *write* time; nothing previously
defended the final gate against post-write mutation, staleness, or hand-edits
at *read* time. This module makes ``validate_outputs`` re-derive every covered
aggregate from its own rows, so a payload whose stored flag disagrees with its
row data fails validation no matter what wrote it.

Design rules (FirstPrinciples deconstruction, Run-4):

- A stored aggregate is a *conjecture*; the rows are the evidence. The check is
  ``stored == re-derived`` (strict equality, both directions): a flag that is
  ``True`` over failing rows is lying, and a flag that is ``False`` over passing
  rows is broken bookkeeping; both mean the artifact cannot be trusted.
- Empty or missing rows with a stored ``True`` flag re-derive to ``False`` —
  vacuous truth over ``[]`` is exactly the green-wash this layer exists to stop.
- Rules live in ONE module (this one). Do not copy the table or the evaluator
  into other validators; import them (copy-drift hazard, see Run-3 changelog).
- Only aggregates whose row-level predicate is unambiguous are covered.
  Ambiguous aggregates (cross-artifact joins, deferred-conditional semantics)
  stay with their bespoke validators.

Threat model: this layer proves FLAG-vs-ROWS consistency, not row correctness.
A payload whose rows were forged wholesale (rows and flag rewritten together)
passes here by construction; byte-level integrity of rows is the provenance /
hash-manifest layer's job (`artifact_provenance.json`, `artifact_diffoscope`).
The two layers compose: diffoscope pins the bytes, this module pins the logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "ARTIFACT_AGGREGATE_RULES",
    "aggregate_rederivation_rows",
    "aggregates_consistent",
    "rederive_aggregate",
    "rule_count",
]

# A predicate spec is a tuple mini-language evaluated per row:
#   ("true", field)              -> row[field] is True
#   ("nonempty", field)          -> row[field] is a non-empty str/list/dict/number-or-bool-present
#   ("empty", field)             -> row[field] is an empty list/dict/str or None
#   ("equals", field, value)     -> row[field] == value
#   ("positive", field)          -> row[field] is a number > 0
#   ("fields_equal", a, b)       -> row[a] == row[b] and both non-empty
#   ("all", spec, ...)           -> conjunction
#   ("any", spec, ...)           -> disjunction
#   ("implies", cond, then)      -> (not cond(row)) or then(row)
#   ("recompute_ok", field)      -> row[field] == ((not forbidden) or negated or allowed)
Spec = tuple[Any, ...]


def _eval_spec(spec: Spec, row: dict[str, Any]) -> bool:
    kind = spec[0]
    if kind == "true":
        return row.get(spec[1]) is True
    if kind == "nonempty":
        value = row.get(spec[1])
        if value is None:
            return False
        if isinstance(value, (str, list, dict, tuple)):
            return len(value) > 0
        return True
    if kind == "empty":
        value = row.get(spec[1])
        return value is None or (isinstance(value, (str, list, dict, tuple)) and len(value) == 0)
    if kind == "equals":
        return bool(row.get(spec[1]) == spec[2])
    if kind == "positive":
        value = row.get(spec[1])
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0
    if kind == "fields_equal":
        left, right = row.get(spec[1]), row.get(spec[2])
        return left is not None and left != "" and left == right
    if kind == "all":
        return all(_eval_spec(sub, row) for sub in spec[1:])
    if kind == "any":
        return any(_eval_spec(sub, row) for sub in spec[1:])
    if kind == "implies":
        return (not _eval_spec(spec[1], row)) or _eval_spec(spec[2], row)
    if kind == "recompute_ok":
        # A row missing any classification flag cannot vacuously pass: require all
        # three flag fields present, else the re-derivation fails closed.
        if not all(field in row for field in ("has_forbidden_wording", "is_negated", "allowed")):
            return row.get(spec[1]) is False
        expected = (not bool(row.get("has_forbidden_wording"))) or row.get("is_negated") is True or row.get("allowed") is True
        return row.get(spec[1]) is expected
    raise ValueError(f"unknown predicate spec kind: {kind!r}")


# rel artifact path -> tuple of (aggregate_field, row predicate spec)
ARTIFACT_AGGREGATE_RULES: dict[str, tuple[tuple[str, Spec], ...]] = {
    "output/data/analytical_assumption_index.json": (
        ("all_equations_indexed", ("all", ("nonempty", "equation_id"), ("nonempty", "assumptions"))),
    ),
    "output/data/animation_frame_deltas.json": (
        ("all_nonzero", ("true", "nonzero")),
        ("all_hashes_distinct", ("true", "hashes_differ")),
    ),
    "output/data/artifact_provenance.json": (
        ("all_records_complete", ("true", "complete")),
        # cycle-excluded artifacts (provenance of provenance) legitimately skip hashing
        ("all_hashed", ("any", ("true", "hash_checked"), ("true", "cycle_excluded"))),
        ("all_producers_configured", ("true", "producer_configured")),
        ("all_config_digests", ("nonempty", "config_digest")),
        ("all_source_commits", ("nonempty", "source_commit")),
    ),
    "output/data/causal_ablation_matrix.json": (("all_deterministic", ("true", "deterministic")),),
    "output/data/cross_track_symbol_table.json": (
        ("all_consistent", ("true", "consistent")),
        ("all_dtypes_declared", ("true", "dtype_declared")),
        ("all_shapes_declared", ("true", "shape_declared")),
        ("all_ontology_terms_declared", ("true", "ontology_declared")),
        ("all_section_terms_declared", ("true", "section_ontology_declared")),
    ),
    "output/data/evidence_field_index.json": (("all_fields_mapped", ("true", "field_present")),),
    "output/data/figure_source_map.json": (
        ("all_figures_mapped", ("true", "mapped")),
        ("all_figure_metadata_complete", ("true", "metadata_complete")),
    ),
    "output/data/gnn_roundtrip_report.json": (("all_lossless", ("true", "lossless")),),
    "output/data/interop_roundtrip_report.json": (
        ("all_lossless", ("true", "lossless")),
        ("all_shape_diffs_empty", ("empty", "shape_diff")),
    ),
    "output/data/ontology_profile_matrix.json": (("all_mapped_once", ("true", "mapped_once")),),
    "output/data/proof_extraction_index.json": (
        ("all_extracted", ("true", "extracted")),
        ("all_constructive", ("empty", "forbidden_tokens")),
    ),
    "output/data/pymdp_policy_posterior_grid.json": (
        ("all_available_posteriors_normalized", ("implies", ("true", "posterior_available"), ("true", "normalized"))),
        (
            "all_unavailable_rows_explained",
            ("implies", ("equals", "posterior_available", False), ("nonempty", "fallback_reason")),
        ),
    ),
    "output/data/scholarship_source_matrix.json": (("all_sources_connected", ("true", "connected")),),
    "output/data/sensitivity_sweep.json": (("all_finite_bounds_ok", ("true", "finite_bound_ok")),),
    "output/data/si_efe_terms.json": (
        (
            "all_rows_explained",
            (
                "any",
                ("all", ("true", "terms_available"), ("nonempty", "terms")),
                ("all", ("equals", "terms_available", False), ("nonempty", "fallback_reason")),
            ),
        ),
    ),
    "output/data/si_graph_world_topology_sweep.json": (
        ("all_summary_trace_agree", ("true", "summary_trace_agreement")),
    ),
    "output/data/si_graph_world_topology_traces.json": (
        ("all_trace_summary_agree", ("true", "trace_summary_agree")),
    ),
    "output/data/state_space_catalog.json": (
        ("all_finite", ("true", "finite")),
        # writer semantics (toy_sweep.py): state_count > 0 and policy_count >= 1;
        # action_count may be 0 for the static bernoulli_ising toy
        (
            "all_counts_positive",
            ("all", ("positive", "state_count"), ("positive", "policy_count")),
        ),
    ),
    "output/data/state_transition_table.json": (
        ("all_transitions_deterministic", ("true", "deterministic")),
        ("all_reachable_states_covered", ("true", "reachable")),
    ),
    "output/data/theorem_traceability_matrix.json": (("all_theorems_linked", ("true", "linked")),),
    "output/data/uncertainty_summary.json": (("all_normalized", ("true", "normalized")),),
    "output/data/validation_gate_index.json": (("all_indexed", ("true", "indexed")),),
    "output/reports/ablation_sensitivity_report.json": (
        ("all_effects_source_backed", ("true", "source_backed")),
    ),
    "output/reports/adversarial_audit.json": (
        # writer (sheaf_tracks_builders.py): expected_failure and known_bad_should_fail
        (
            "all_expected_failures_documented",
            ("all", ("true", "expected_failure"), ("true", "known_bad_should_fail")),
        ),
        # writer: expected_failure and observed == "expected_failure" (literal status string)
        (
            "all_expected_failures_observed",
            ("all", ("true", "expected_failure"), ("equals", "observed", "expected_failure")),
        ),
    ),
    "output/reports/artifact_diffoscope.json": (("all_equal", ("true", "equal")),),
    "output/reports/artifact_license_audit.json": (("all_license_safe", ("true", "license_safe")),),
    "output/reports/claim_evidence_audit.json": (
        ("all_claims_typed", ("all", ("true", "has_evidence"), ("true", "has_tracks"))),
    ),
    "output/reports/counterexample_matrix.json": (
        # writer: expected_failure and gate and test and mutation all non-empty
        (
            "all_expected_failures_documented",
            (
                "all",
                ("nonempty", "expected_failure"),
                ("nonempty", "gate"),
                ("nonempty", "test"),
                ("nonempty", "mutation"),
            ),
        ),
        # writer: fixture replay actually reproduced the expected failure
        (
            "all_expected_failures_observed",
            ("equals", "fixture_replay_status", "expected_failure_observed"),
        ),
    ),
    "output/reports/figure_hash_manifest.json": (
        ("all_hashes_present", ("all", ("nonempty", "sha256"), ("true", "fresh"))),
    ),
    "output/reports/gnn_lint_report.json": (
        ("all_variables_mapped_once", ("true", "ok")),
        ("all_round_trip_ok", ("true", "round_trip_ok")),
    ),
    "output/reports/graph_world_invariants.json": (("all_passed", ("true", "passed")),),
    "output/reports/lean_graph_world_inventory.json": (
        ("all_policy_witnesses_present", ("true", "present")),
    ),
    "output/reports/lean_theorem_inventory.json": (("all_proved", ("equals", "status", "proved")),),
    "output/reports/manuscript_hardcoded_variable_audit.json": (
        ("all_values_auto_injected", ("true", "auto_injected")),
    ),
    "output/reports/manuscript_staleness_report.json": (("all_fresh", ("true", "fresh")),),
    "output/reports/model_checking_witnesses.json": (
        ("all_passed", ("true", "passed")),
        ("all_exhaustive", ("true", "exhaustive")),
    ),
    "output/reports/producer_completeness.json": (
        ("all_complete", ("all", ("true", "configured"), ("true", "exists"))),
    ),
    "output/reports/release_bundle_manifest.json": (
        # pre-render deliverables (PDF/web) are explicitly deferred until render
        (
            "all_required_sources_present",
            ("any", ("true", "source_exists"), ("true", "deferred_until_render")),
        ),
    ),
    "output/reports/replay_matrix.json": (("all_replay_rows_matched", ("true", "matched")),),
    "output/reports/scope_boundary_audit.json": (("all_current_claims_toy", ("recompute_ok", "ok")),),
    "output/reports/stale_artifact_report.json": (("all_fresh", ("true", "fresh")),),
}


def rederive_aggregate(payload: dict[str, Any], spec: Spec) -> bool:
    """Re-derive an aggregate from ``payload['rows']``; vacuous truth is False."""
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        return False
    if not all(isinstance(row, dict) for row in rows):
        return False
    return all(_eval_spec(spec, row) for row in rows)


def aggregate_rederivation_rows(project_root: Path) -> list[dict[str, Any]]:
    """One row per covered (artifact, aggregate): stored vs re-derived."""
    root = project_root.resolve()
    out: list[dict[str, Any]] = []
    for rel, rules in sorted(ARTIFACT_AGGREGATE_RULES.items()):
        path = root / rel
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            payload = None
        for aggregate_field, spec in rules:
            if not isinstance(payload, dict):
                out.append(
                    {
                        "artifact": rel,
                        "aggregate": aggregate_field,
                        "stored": None,
                        "rederived": False,
                        "consistent": False,
                        "reason": "artifact missing or unreadable",
                    }
                )
                continue
            stored = payload.get(aggregate_field)
            rederived = rederive_aggregate(payload, spec)
            consistent = isinstance(stored, bool) and stored == rederived
            row: dict[str, Any] = {
                "artifact": rel,
                "aggregate": aggregate_field,
                "stored": stored,
                "rederived": rederived,
                "consistent": consistent,
            }
            if not consistent:
                row["reason"] = "stored flag disagrees with row-level re-derivation"
            out.append(row)
    return out


def aggregates_consistent(project_root: Path) -> bool:
    """True iff every covered stored aggregate equals its row-level re-derivation."""
    return all(row["consistent"] for row in aggregate_rederivation_rows(project_root))


def rule_count() -> int:
    """Number of (artifact, aggregate) pairs re-derived at validation time."""
    return sum(len(rules) for rules in ARTIFACT_AGGREGATE_RULES.values())
