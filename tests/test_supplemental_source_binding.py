"""Source-bound supplemental contracts over real finite temporary input trees."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

from roadmap_tracks.formal_interop import build_proof_extraction_index
from roadmap_tracks.supplemental import (
    SUPPLEMENTAL_ARTIFACTS,
    build_ablation_sensitivity_report,
    build_release_attestation,
    build_state_transition_table,
    release_attestation_consistent_and_current,
    validate_supplemental_artifacts,
    validate_supplemental_payloads,
    write_supplemental_artifacts,
)
from roadmap_tracks.toy_sweep import (
    build_causal_ablation_matrix,
    build_graph_world_topology_sweep,
    build_graph_world_topology_traces,
    build_sensitivity_sweep,
    build_state_space_catalog,
)


def _write(root: Path, relative: str, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _load(root: Path, relative: str) -> dict:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _validation_report(root: Path, *, failed: tuple[str, ...] = ()) -> None:
    outputs = {"finite_fixture_gate": True, "release_attestation_schema": True}
    manuscript = {"canonical_sheaf_tracks": True}
    for key in failed:
        (manuscript if key in manuscript else outputs)[key] = False
    _write(root, "output/reports/validation_report.json", {
        "schema": "template_active_inference.validation_report.v1",
        "outputs": outputs,
        "manuscript": manuscript,
        "failed_checks": sorted(set(failed)),
        "all_passed": not failed,
    })


@pytest.fixture
def supplemental_root(tmp_path: Path) -> Path:
    lean = tmp_path / "lean/OnPolicyDistillation/FiniteFixture.lean"
    lean.parent.mkdir(parents=True)
    lean.write_text(
        "def nextNat (n : Nat) : Nat := n + 1\n"
        "def twiceNat (n : Nat) : Nat := n + n\n"
        "theorem nextNat_zero : nextNat 0 = 1 := by\n  rfl\n"
        "theorem twiceNat_one : twiceNat 1 = 2 := by\n  rfl\n",
        encoding="utf-8",
    )
    proof = build_proof_extraction_index(tmp_path)
    _write(tmp_path, "output/data/proof_extraction_index.json", proof)
    finite_cases = [("nextNat_zero", 0 + 1, 1), ("twiceNat_one", 1 + 1, 2)]
    witnesses = [
        {"id": theorem, "model": "finite_nat", "value": value, "expected": expected,
         "passed": value == expected, "source": "lean/OnPolicyDistillation/FiniteFixture.lean"}
        for theorem, value, expected in finite_cases
    ]
    _write(tmp_path, "output/reports/model_checking_witnesses.json", {
        "rows": witnesses, "all_passed": all(row["passed"] for row in witnesses),
    })
    _write(tmp_path, "output/data/theorem_traceability_matrix.json", {
        "rows": [
            {"theorem": row["theorem"], "linked": True, "model_witnesses": [case[0] for case in finite_cases]}
            for row in proof["rows"]
        ],
    })
    _write(tmp_path, "output/data/si_graph_world_topology_traces.json", build_graph_world_topology_traces(tmp_path))
    _write(tmp_path, "output/data/si_graph_world_topology_sweep.json", build_graph_world_topology_sweep(tmp_path))
    _write(tmp_path, "output/data/state_space_catalog.json", build_state_space_catalog(tmp_path))
    _write(tmp_path, "output/data/si_tmaze_summary.json", {"model": "si_tmaze", "goal_reached": True})
    sensitivity_rows = [
        {"topology": topology, "lambda": lam, "mi": mi, "horizon": horizon, "seed": 0}
        for topology, lam, mi in (("linear4", 0.0, 0.125), ("branch4", 1.0, 0.375))
        for horizon in (2, 3)
    ]
    _write(tmp_path, "output/data/sensitivity_sweep.json", {"rows": sensitivity_rows, "row_count": 4})
    ablation_rows = [
        {"topology": topology, "lambda": lam, "perturbation": "finite_perturbation",
         "metric": "finite_delta", "effect": effect,
         "source": "output/data/si_graph_world_topology_sweep.json"}
        for topology, lam, effect in (("linear4", 0.0, -0.125), ("branch4", 1.0, 0.25))
    ]
    _write(tmp_path, "output/data/causal_ablation_matrix.json", {"rows": ablation_rows, "row_count": 2})
    uncertainty_rows = [
        {"step": step, "belief_entropy": entropy, "posterior": posterior,
         "posterior_sum": sum(posterior), "normalized": True}
        for step, entropy, posterior in ((0, 1.0, [0.5, 0.5]), (1, 0.5, [0.75, 0.25]))
    ]
    _write(tmp_path, "output/data/uncertainty_summary.json", {"rows": uncertainty_rows, "row_count": 2})
    _validation_report(tmp_path)
    _write(tmp_path, "output/reports/release_bundle_manifest.json", {
        "all_required_sources_present": True, "all_copied_outputs_match_or_deferred": True,
        "bundle_hash": hashlib.sha256(b"finite fixture bundle").hexdigest(),
    })
    _write(tmp_path, "output/reports/artifact_license_audit.json", {"all_license_safe": True})
    _write(tmp_path, "output/reports/blocked_scope_manifest.json", {"all_blocked": True})
    _write(tmp_path, "output/data/sheaf_gluing_certificate.json", {
        "ok": True, "restrictions": {"finite_fixture_scope": True, "release_attestation_complete": True},
    })
    write_supplemental_artifacts(tmp_path)
    assert validate_supplemental_payloads(tmp_path) == {key: [] for key in SUPPLEMENTAL_ARTIFACTS}
    return tmp_path


def _payload(root: Path, key: str) -> dict:
    return _load(root, SUPPLEMENTAL_ARTIFACTS[key])


def _refresh_hashes(root: Path, payload: dict) -> None:
    payload["source_hashes"] = {
        path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in payload["source_hashes"]
    }


def _assert_rejected(root: Path, key: str, payload: dict, message: str) -> None:
    before = (root / SUPPLEMENTAL_ARTIFACTS[key]).read_bytes()
    memory = validate_supplemental_payloads(root, {key: payload})
    assert any(message in issue for issue in memory[key]), memory[key]
    assert all(not issues for other, issues in memory.items() if other != key)
    assert (root / SUPPLEMENTAL_ARTIFACTS[key]).read_bytes() == before
    _write(root, SUPPLEMENTAL_ARTIFACTS[key], payload)
    assert validate_supplemental_payloads(root) == memory
    assert validate_supplemental_artifacts(root) == [issue for issues in memory.values() for issue in issues]


def _refresh_proof(payload: dict) -> None:
    edges = payload["edges"]
    payload.update({
        "theorem_count": len(payload["rows"]), "edge_count": len(edges),
        "edge_types": sorted({row["kind"] for row in edges}),
        "edge_key_count": len({row["edge_key"] for row in edges}),
        "duplicate_edge_keys": [], "orphan_edge_targets": [],
        "all_theorems_have_dependencies": True, "all_edges_resolved": True,
        "all_edge_keys_unique": True, "all_required_edge_types_present": True,
        "all_edge_targets_resolved": True,
    })


def _refresh_transitions(payload: dict) -> None:
    rows = payload["rows"]
    for row in rows:
        row["transition_key"] = "::".join(row[field] for field in ("model", "state", "action"))
        row["state_key"] = f"{row['model']}::{row['state']}"
        row["next_state_key"] = f"{row['model']}::{row['next_state']}"
    models = sorted({row["model"] for row in rows})
    states = {row[field] for row in rows for field in ("state_key", "next_state_key")}
    payload.update({
        "row_count": len(rows), "model_count": len(models), "required_models": models,
        "covered_models": models, "transition_key_count": len({row["transition_key"] for row in rows}),
        "duplicate_transition_keys": [], "reachable_state_key_count": len(states),
        "missing_outgoing_state_keys": [],
        "terminal_self_transition_models": sorted({row["model"] for row in rows if row["terminal_self_transition"]}),
        "models_without_terminal_self_transition": [], "all_transitions_deterministic": True,
        "all_transition_keys_unique": True, "all_reachable_states_covered": True,
        "all_reachable_states_have_outgoing": True, "all_terminal_states_have_self_transition": True,
    })


def _refresh_attestation(payload: dict) -> None:
    rows = payload["rows"]
    payload.update({
        "row_count": len(rows), "attested_source_count": len(rows),
        "attested_source_ids": [row["id"] for row in rows],
        "attestation_hash": hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest(),
        "all_attested": all(row["passed"] for row in rows),
        "all_attested_or_deferred": all(row["passed"] or row["deferred_until_validation"] for row in rows),
    })


def test_disk_and_memory_share_per_artifact_contract(supplemental_root: Path) -> None:
    root = supplemental_root
    payloads = {key: _payload(root, key) for key in SUPPLEMENTAL_ARTIFACTS}
    assert validate_supplemental_payloads(root, payloads) == validate_supplemental_payloads(root)
    assert validate_supplemental_artifacts(root, payloads) == []
    assert release_attestation_consistent_and_current(root, payloads["release_attestation"])
    assert set(validate_supplemental_payloads(root)) == set(SUPPLEMENTAL_ARTIFACTS)


@pytest.mark.parametrize("mutation", ["requirements_removed", "duplicate_logical_edge", "unlinked_theorem", "forged_domain"])
def test_proof_graph_uses_source_requirements(supplemental_root: Path, mutation: str) -> None:
    root = supplemental_root
    payload = _payload(root, "proof_dependency_graph")
    message = "unlinked theorem dependencies"
    if mutation == "requirements_removed":
        payload["edges"] = [edge for edge in payload["edges"] if edge["kind"] != "theorem_to_definition"]
        payload["required_edge_types"].remove("theorem_to_definition")
        message = "lacks required theorem edge types"
    elif mutation == "duplicate_logical_edge":
        duplicate = deepcopy(payload["edges"][0])
        duplicate["edge_key"] += "::different-label"
        payload["edges"].append(duplicate)
        message = "duplicate dependency edges"
    elif mutation == "unlinked_theorem":
        theorem = payload["rows"][0]["theorem"]
        payload["edges"] = [edge for edge in payload["edges"] if edge["source"] != theorem]
        assert payload["rows"][0]["linked"] is True
    else:
        edge = next(edge for edge in payload["edges"] if edge["kind"] == "theorem_to_definition")
        edge["target"] = "invented_definition"
        edge["edge_key"] = "::".join(edge[field] for field in ("source", "target", "kind"))
        row = next(row for row in payload["rows"] if row["theorem"] == edge["source"])
        row["statement_symbols"].append(edge["target"])
        row["statement_symbol_count"] = len(row["statement_symbols"])
        message = "orphan theorem dependency targets"
    _refresh_proof(payload)
    _assert_rejected(root, "proof_dependency_graph", payload, message)


def test_proof_theorem_domain_comes_from_lean_not_saved_inventories(supplemental_root: Path) -> None:
    root = supplemental_root
    payload = _payload(root, "proof_dependency_graph")
    removed = payload["rows"].pop()["theorem"]
    payload["edges"] = [edge for edge in payload["edges"] if edge["source"] != removed]
    for path in ("output/data/proof_extraction_index.json", "output/data/theorem_traceability_matrix.json"):
        source = _load(root, path)
        source["rows"] = [row for row in source["rows"] if row["theorem"] != removed]
        source["theorem_count"] = len(source["rows"])
        _write(root, path, source)
    _refresh_proof(payload)
    _refresh_hashes(root, payload)
    _assert_rejected(root, "proof_dependency_graph", payload, "unlinked theorem dependencies")


def test_proof_target_domain_is_theorem_and_kind_specific(supplemental_root: Path) -> None:
    root = supplemental_root
    payload = _payload(root, "proof_dependency_graph")
    edges = [edge for edge in payload["edges"] if edge["kind"] == "theorem_to_definition"]
    edge = edges[0]
    edge["target"] = next(other["target"] for other in edges if other["source"] != edge["source"])
    edge["edge_key"] = "::".join(edge[field] for field in ("source", "target", "kind"))
    _refresh_proof(payload)
    _assert_rejected(root, "proof_dependency_graph", payload, "orphan theorem dependency targets")


@pytest.mark.parametrize("mutation", ["whole_model", "whole_state", "false_terminal", "duplicate_logical_transition"])
def test_transition_table_uses_authoritative_coverage(supplemental_root: Path, mutation: str) -> None:
    root = supplemental_root
    payload = _payload(root, "state_transition_table")
    message = "omits a reachable finite model"
    if mutation == "whole_model":
        payload["rows"] = [row for row in payload["rows"] if row["model"] != "graph_world_loop5"]
    elif mutation == "whole_state":
        payload["rows"] = [row for row in payload["rows"] if not (row["model"] == "si_tmaze" and row["state"] == "cue")]
        for row in payload["rows"]:
            if row["model"] == "si_tmaze" and row["next_state"] == "cue":
                row["next_state"] = "goal"
        message = "omits outgoing transitions"
    elif mutation == "false_terminal":
        next(row for row in payload["rows"] if row["state"] != row["next_state"])["terminal_self_transition"] = True
        message = "omits terminal self-transition"
    else:
        payload["rows"].append(deepcopy(payload["rows"][0]))
        message = "duplicate transition keys"
    _refresh_transitions(payload)
    if mutation == "duplicate_logical_transition":
        payload["rows"][-1]["transition_key"] += "::different-label"
        payload["transition_key_count"] = len(payload["rows"])
    _assert_rejected(root, "state_transition_table", payload, message)


@pytest.mark.parametrize("mutation", ["omit_topology", "change_state", "omit_catalog_model"])
def test_transition_sources_cannot_redefine_declared_toys(supplemental_root: Path, mutation: str) -> None:
    root = supplemental_root
    if mutation == "omit_catalog_model":
        path = "output/data/state_space_catalog.json"
        source = _load(root, path)
        source["rows"] = [row for row in source["rows"] if row["model"] != "graph_world_loop5"]
        message = "source catalog omits"
    else:
        path = "output/data/si_graph_world_topology_traces.json"
        source = _load(root, path)
        if mutation == "omit_topology":
            source["rows"] = [row for row in source["rows"] if row["topology"] != "loop5"]
        else:
            source["rows"][0]["trace"][1]["node"] = "undeclared_cue"
        message = "source traces omit or change"
    _write(root, path, source)
    payload = build_state_transition_table(root)
    _assert_rejected(root, "state_transition_table", payload, message)


@pytest.mark.parametrize("field,value", [
    ("source_join_key", "unrelated::42"), ("sensitivity_row_count", 99),
    ("uncertainty_row_count", 99), ("mean_sensitivity_mi", 0.875), ("effect", 8.0),
    ("lambda", 2.0), ("topology", "unrelated_topology"),
])
def test_ablation_rows_cross_read_actual_joins_and_numerics(supplemental_root: Path, field: str, value: object) -> None:
    root = supplemental_root
    payload = _payload(root, "ablation_sensitivity_report")
    payload["rows"][0][field] = value
    _assert_rejected(root, "ablation_sensitivity_report", payload, "unsupported ablation effects")


@pytest.mark.parametrize("source,mutation", [
    ("causal_ablation_matrix", "effect"), ("causal_ablation_matrix", "remove_row"),
    ("sensitivity_sweep", "mi"), ("sensitivity_sweep", "remove_row"),
    ("uncertainty_summary", "remove_row"), ("uncertainty_summary", "posterior"),
])
def test_ablation_rejects_stale_source_rows(supplemental_root: Path, source: str, mutation: str) -> None:
    root = supplemental_root
    payload = _payload(root, "ablation_sensitivity_report")
    path = f"output/data/{source}.json"
    artifact = _load(root, path)
    if mutation == "remove_row":
        artifact["rows"].pop()
        artifact["row_count"] = len(artifact["rows"])
    elif mutation == "posterior":
        artifact["rows"][0]["posterior"] = [0.25, 0.75]
    else:
        artifact["rows"][0][mutation] = 0.875
    _write(root, path, artifact)
    if mutation != "posterior":
        # Even a refreshed hash cannot substitute for the actual source join/numerics.
        _refresh_hashes(root, payload)
    message = "stale source-derived metadata" if mutation == "posterior" else "unsupported ablation effects"
    _assert_rejected(root, "ablation_sensitivity_report", payload, message)


def test_ablation_source_counters_are_not_authority(supplemental_root: Path) -> None:
    root = supplemental_root
    path = "output/data/sensitivity_sweep.json"
    artifact = _load(root, path)
    artifact["row_count"] += 1
    _write(root, path, artifact)
    payload = build_ablation_sensitivity_report(root)
    _assert_rejected(root, "ablation_sensitivity_report", payload, "stale source joins or row counts")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), "0.25", True])
@pytest.mark.parametrize("source,field", [
    ("causal_ablation_matrix", "effect"), ("sensitivity_sweep", "mi"),
    ("uncertainty_summary", "belief_entropy"),
])
def test_ablation_rejects_nonfinite_or_non_numeric_sources(
    supplemental_root: Path, source: str, field: str, value: object,
) -> None:
    root = supplemental_root
    path = f"output/data/{source}.json"
    artifact = _load(root, path)
    artifact["rows"][0][field] = value
    _write(root, path, artifact)
    _assert_rejected(root, "ablation_sensitivity_report", _payload(root, "ablation_sensitivity_report"), "finite numbers")


def test_actual_finite_producers_share_topology_lambda_domain(supplemental_root: Path) -> None:
    root = supplemental_root
    topology = build_graph_world_topology_sweep(root)
    sensitivity = build_sensitivity_sweep(root)
    causal = build_causal_ablation_matrix(root)
    assert sensitivity["grid"]["topologies"] == [row["topology"] for row in topology["rows"]]
    assert sensitivity["grid"]["lambdas"] == [0.0, 1.0, 2.0]
    assert sensitivity["grid"]["horizons"] == [2, 3]
    assert sensitivity["grid"]["seeds"] == [0, 1]
    joins = Counter((row["topology"], row["lambda"]) for row in sensitivity["rows"])
    assert all(joins[(row["topology"], row["lambda"])] == 4 for row in causal["rows"])
    _write(root, "output/data/sensitivity_sweep.json", sensitivity)
    _write(root, "output/data/causal_ablation_matrix.json", causal)
    payload = build_ablation_sensitivity_report(root)
    assert payload["all_ablation_rows_joined"] is True
    assert validate_supplemental_payloads(root, {"ablation_sensitivity_report": payload})["ablation_sensitivity_report"] == []
    # Missing canonical support remains red; no aliases or topology narrowing.
    sensitivity["rows"] = [row for row in sensitivity["rows"] if row["topology"] != "loop5"]
    sensitivity["row_count"] = len(sensitivity["rows"])
    _write(root, "output/data/sensitivity_sweep.json", sensitivity)
    unbacked = build_ablation_sensitivity_report(root)
    assert unbacked["all_ablation_rows_joined"] is False
    assert any(row["topology"] == "loop5" and not row["source_backed"] for row in unbacked["rows"])
    _assert_rejected(root, "ablation_sensitivity_report", unbacked, "unsupported ablation effects")


def test_release_rejects_same_count_forged_ids_with_current_report_hash(supplemental_root: Path) -> None:
    root = supplemental_root
    payload = _payload(root, "release_attestation")
    row = next(row for row in payload["rows"] if row["id"] == "validation_report")
    assert row["report_sha256"] == hashlib.sha256((root / row["source"]).read_bytes()).hexdigest()
    row["attested_validation_check_ids"][0] = "outputs.forged_same_length_id"
    _refresh_attestation(payload)
    assert row["validation_check_count"] == len(row["attested_validation_check_ids"])
    assert not release_attestation_consistent_and_current(root, payload)
    _assert_rejected(root, "release_attestation", payload, "validation check IDs or count")


@pytest.mark.parametrize("removed_id", ["validation_report", "release_bundle", "artifact_license", "blocked_scope", "semantic_certificate"])
def test_release_requires_every_source_row(supplemental_root: Path, removed_id: str) -> None:
    root = supplemental_root
    payload = _payload(root, "release_attestation")
    payload["rows"] = [row for row in payload["rows"] if row["id"] != removed_id]
    _refresh_attestation(payload)
    assert not release_attestation_consistent_and_current(root, payload)
    _assert_rejected(root, "release_attestation", payload, "omits or duplicates required attestation rows")


def test_release_rejects_duplicate_rows_even_with_unchanged_count(supplemental_root: Path) -> None:
    root = supplemental_root
    payload = _payload(root, "release_attestation")
    payload["rows"][-1] = deepcopy(payload["rows"][-2])
    _refresh_attestation(payload)
    _assert_rejected(root, "release_attestation", payload, "omits or duplicates required attestation rows")


def test_release_rejects_coordinated_check_count_forgery(supplemental_root: Path) -> None:
    root = supplemental_root
    payload = _payload(root, "release_attestation")
    row = next(row for row in payload["rows"] if row["id"] == "validation_report")
    row["attested_validation_check_ids"].append("outputs.forged_extra_id")
    row["validation_check_count"] += 1
    payload["attested_validation_check_count"] += 1
    _refresh_attestation(payload)
    _assert_rejected(root, "release_attestation", payload, "validation check IDs or count")


def test_release_preserves_consistent_red_without_certifying_green(supplemental_root: Path) -> None:
    root = supplemental_root
    _validation_report(root, failed=("finite_fixture_gate",))
    payload = build_release_attestation(root)
    assert payload["all_attested"] is False
    assert validate_supplemental_payloads(root, {"release_attestation": payload})["release_attestation"] == []
    assert release_attestation_consistent_and_current(root, payload)
    forged = deepcopy(payload)
    forged["rows"][0]["passed"] = True
    _refresh_attestation(forged)
    _assert_rejected(root, "release_attestation", forged, "claims a failed gate passed")


def test_release_preserves_first_report_deferral_but_not_greenness(supplemental_root: Path) -> None:
    root = supplemental_root
    (root / "output/reports/validation_report.json").unlink()
    payload = build_release_attestation(root)
    assert payload["rows"][0]["deferred_until_validation"] is True
    assert payload["all_attested"] is False
    assert payload["all_attested_or_deferred"] is True
    assert validate_supplemental_payloads(root, {"release_attestation": payload})["release_attestation"] == []
    assert release_attestation_consistent_and_current(root, payload)


@pytest.mark.parametrize("field,value", [("failed_checks", []), ("all_passed", True), ("outputs", {})])
def test_release_hash_does_not_authenticate_forged_report_summaries(
    supplemental_root: Path, field: str, value: object,
) -> None:
    root = supplemental_root
    _validation_report(root, failed=("finite_fixture_gate",))
    report = _load(root, "output/reports/validation_report.json")
    report[field] = value
    _write(root, "output/reports/validation_report.json", report)
    payload = build_release_attestation(root)
    assert payload["rows"][0]["passed"] is False
    assert not release_attestation_consistent_and_current(root, payload)
    _assert_rejected(root, "release_attestation", payload, "invalid check maps or summaries")


def test_release_hash_currency_is_preserved(supplemental_root: Path) -> None:
    root = supplemental_root
    payload = _payload(root, "release_attestation")
    _validation_report(root, failed=("release_attestation_schema",))
    _assert_rejected(root, "release_attestation", payload, "current source artifacts or report hash")


def test_release_carveout_is_fixed_point_only_not_observation(supplemental_root: Path) -> None:
    root = supplemental_root
    _validation_report(root, failed=("release_attestation_schema",))
    payload = build_release_attestation(root)
    assert payload["rows"][0]["passed"] is True
    assert release_attestation_consistent_and_current(root, payload)
    _write(root, "output/data/sheaf_gluing_certificate.json", {
        "ok": True,
        "restrictions": {"release_attestation_complete": False, "counterexample_failures_observed": False},
    })
    payload = build_release_attestation(root)
    semantic = next(row for row in payload["rows"] if row["id"] == "semantic_certificate")
    assert semantic["passed"] is False
    assert semantic["ignored_self_restrictions"] == []
    assert payload["all_attested"] is False
    assert release_attestation_consistent_and_current(root, payload)


@pytest.mark.parametrize("key", list(SUPPLEMENTAL_ARTIFACTS))
def test_malformed_supplemental_rows_return_artifact_issues(supplemental_root: Path, key: str) -> None:
    root = supplemental_root
    payload = _payload(root, key)
    payload["rows"] = ["not an object"]
    _assert_rejected(root, key, payload, "invalid payload or source artifacts")


def test_ablation_accepts_existing_policy_uncertainty_shape(supplemental_root: Path) -> None:
    root = supplemental_root
    path = "output/data/uncertainty_summary.json"
    uncertainty = _load(root, path)
    uncertainty["rows"].append({
        "id": "policy_0", "source": "output/data/pymdp_policy_posterior_grid.json",
        "distribution": [0.5, 0.5], "distribution_sum": 1.0,
        "posterior": [0.5, 0.5], "posterior_sum": 1.0, "entropy": 0.6931471805599453,
        "bin": "mid_entropy", "normalized": True, "fallback_reason": "",
        "posterior_concentration": 0.5,
    })
    uncertainty["row_count"] = len(uncertainty["rows"])
    _write(root, path, uncertainty)
    payload = build_ablation_sensitivity_report(root)
    assert payload["all_ablation_rows_joined"] is True
    assert all(row["uncertainty_row_count"] == uncertainty["row_count"] for row in payload["rows"])
    assert validate_supplemental_payloads(root, {"ablation_sensitivity_report": payload})["ablation_sensitivity_report"] == []


def test_ablation_rejects_nonfinite_policy_uncertainty(supplemental_root: Path) -> None:
    root = supplemental_root
    path = "output/data/uncertainty_summary.json"
    uncertainty = _load(root, path)
    row = uncertainty["rows"][0]
    row.pop("belief_entropy")
    row["entropy"] = float("nan")
    _write(root, path, uncertainty)
    _assert_rejected(
        root, "ablation_sensitivity_report", _payload(root, "ablation_sensitivity_report"), "finite numbers",
    )
