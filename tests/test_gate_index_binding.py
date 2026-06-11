"""Negative controls for the validation gate index (AI-GATE-INDEX-3).

Before Run-6 the gate-index builder was a hardcoded list that ignored
``project_root`` (``indexed: True`` asserted, never derived) and nothing tied
row ids to the validator surface. These tests pin the honest semantics:
``indexed`` derives from on-disk inputs, and every row id must bind to a live
check key (exact/prefix/alias) or a known external gate.
"""

from __future__ import annotations

from pathlib import Path

from gates.output_checks import _gate_index_binding
from roadmap_tracks.integration_audit_builders import GATE_INDEX_ROWS, _rows_fully_specified, build_validation_gate_index

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LIVE_CHECK_KEYS = {
    "aggregate_rederivation",
    "canonical_sheaf_track_schemas",
    "claim_evidence_audit_schema",
    "manuscript_staleness_report_schema",
    "animation_frame_deltas_schema",
    "pymdp_runtime_diagnostics_schema",
    "pymdp_policy_posterior_grid_schema",
    "analytical_assumption_index_schema",
    "release_bundle_manifest_schema",
    "evidence_field_index_schema",
    "theorem_traceability_matrix_schema",
    "artifact_diffoscope_schema",
    "proof_extraction_index_schema",
    "state_space_catalog_schema",
    "causal_ablation_matrix_schema",
    "artifact_license_audit_schema",
    "release_notes_evidence_schema",
    "proof_dependency_graph_schema",
    "state_transition_table_schema",
    "ablation_sensitivity_report_schema",
    "release_attestation_schema",
    "track_improvement_scope_schema",
    "blocked_scope_manifest_schema",
}


def _index_payload() -> dict:
    return build_validation_gate_index(PROJECT_ROOT)


def test_gate_index_derives_indexed_from_disk() -> None:
    payload = _index_payload()
    assert payload["all_indexed"] is True
    assert payload["all_rows_fully_specified"] is True
    assert all(row["inputs_exist"] for row in payload["rows"])


def test_gate_index_fails_when_inputs_missing() -> None:
    """The pre-Run-6 stub returned all_indexed=True for ANY root, even an empty one."""
    payload = build_validation_gate_index(Path("/nonexistent-gate-index-root"))
    assert payload["all_indexed"] is False
    assert all(row["indexed"] is False for row in payload["rows"])


def test_registry_rows_all_bind_to_live_surface() -> None:
    payload = _index_payload()
    assert _gate_index_binding(payload, LIVE_CHECK_KEYS) is True


def test_phantom_gate_row_fails_binding() -> None:
    payload = _index_payload()
    payload["rows"].append(
        {"id": "phantom_gate_never_implemented", "inputs": [], "inputs_exist": True, "indexed": True}
    )
    assert _gate_index_binding(payload, LIVE_CHECK_KEYS) is False


def test_unindexed_row_fails_binding() -> None:
    payload = _index_payload()
    payload["rows"][0]["indexed"] = False
    assert _gate_index_binding(payload, LIVE_CHECK_KEYS) is False


def test_empty_rows_fail_binding() -> None:
    assert _gate_index_binding({"rows": []}, LIVE_CHECK_KEYS) is False


def test_gate_index_empty_command_fails_full_specification() -> None:
    payload = _index_payload()
    assert payload["all_rows_fully_specified"] is True
    mutated = [dict(row) for row in payload["rows"]]
    mutated[0]["command"] = ""
    assert _rows_fully_specified(mutated) is False


def test_registry_ids_are_unique() -> None:
    ids = [gate_id for gate_id, *_ in GATE_INDEX_ROWS]
    assert len(ids) == len(set(ids))
