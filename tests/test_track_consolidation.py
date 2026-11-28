"""Canonical sheaf-track consolidation tests and negative controls."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from gate_support import ensure_gate_artifacts

VERSIONED_TRACK_RE = re.compile(r"(?:^|_)v[2-9]$")
# test_canonical_track_contract_negative_controls regenerates the full sheaf-track
# artifact set 5x (4 negative controls + restore); ~85s locally but ubuntu CI runners
# have been observed ~3.5x slower, breaching a 300s ceiling. 600s gives margin for the
# slowest leg without masking a real hang (the test is correct, just heavy).
pytestmark = pytest.mark.timeout(600)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def test_live_track_surface_uses_canonical_ids(project_root: Path) -> None:
    from gates.artifact_manifest import REQUIRED_OUTPUTS
    from roadmap_tracks.sheaf_tracks import CANONICAL_TRACKS, LEGACY_ARTIFACTS

    registry = yaml.safe_load((project_root / "docs" / "manuscript" / "sheaf" / "tracks.yaml").read_text())["tracks"]
    manifest = yaml.safe_load((project_root / "docs" / "manuscript" / "sheaf" / "manifest.yaml").read_text())
    public_tracks = {
        str(row["id"])
        for row in yaml.safe_load((project_root / "tracks.yaml").read_text())["tracks"]
        if isinstance(row, dict) and row.get("id")
    }
    claims = yaml.safe_load((project_root / "data" / "claim_ledger.yaml").read_text()).get("claims") or []
    configured = yaml.safe_load((project_root / "docs" / "manuscript" / "config.yaml").read_text())["analysis"]["scripts"]

    bound_tracks = {
        str(track_id) for section in manifest["sections"] for track_id in ((section.get("tracks") or {}).keys())
    }
    claim_ids = {str(claim.get("id")) for claim in claims}

    assert set(CANONICAL_TRACKS).issubset(registry)
    assert set(CANONICAL_TRACKS).issubset(public_tracks)
    assert set(CANONICAL_TRACKS).issubset(bound_tracks)
    assert not any(VERSIONED_TRACK_RE.search(track_id) for track_id in registry)
    assert not any(VERSIONED_TRACK_RE.search(track_id) for track_id in public_tracks)
    assert not any(VERSIONED_TRACK_RE.search(track_id) for track_id in bound_tracks)
    assert not any(VERSIONED_TRACK_RE.search(claim_id) for claim_id in claim_ids)
    assert "generate_sheaf_tracks.py" in configured
    assert "generate_v2_sheaf_tracks.py" not in configured
    assert "generate_v3_sheaf_tracks.py" not in configured
    assert not (set(LEGACY_ARTIFACTS) & set(REQUIRED_OUTPUTS))


@pytest.mark.artifact_slow
def test_canonical_sheaf_artifacts_are_present_and_valid(project_root: Path) -> None:
    from roadmap_tracks import validate_sheaf_track_artifacts

    ensure_gate_artifacts(project_root)
    paths = {
        "semantic": project_root / "output" / "data" / "sheaf_gluing_certificate.json",
        "dependency": project_root / "output" / "data" / "validation_dependency_graph.json",
        "evidence_fields": project_root / "output" / "data" / "evidence_field_index.json",
        "release_bundle": project_root / "output" / "reports" / "release_bundle_manifest.json",
        "theorem_traceability": project_root / "output" / "data" / "theorem_traceability_matrix.json",
        "artifact_diffoscope": project_root / "output" / "reports" / "artifact_diffoscope.json",
        "scholarship": project_root / "output" / "data" / "scholarship_source_matrix.json",
        "proof_extraction": project_root / "output" / "data" / "proof_extraction_index.json",
        "state_space_catalog": project_root / "output" / "data" / "state_space_catalog.json",
        "causal_ablation": project_root / "output" / "data" / "causal_ablation_matrix.json",
        "artifact_license": project_root / "output" / "reports" / "artifact_license_audit.json",
        "release_notes": project_root / "output" / "reports" / "release_notes_evidence.json",
        "proof_dependency_graph": project_root / "output" / "data" / "proof_dependency_graph.json",
        "state_transition_table": project_root / "output" / "data" / "state_transition_table.json",
        "ablation_sensitivity_report": project_root / "output" / "reports" / "ablation_sensitivity_report.json",
        "release_attestation": project_root / "output" / "reports" / "release_attestation.json",
        "section_status": project_root / "output" / "data" / "sheaf_section_status_matrix.json",
        "render_log": project_root / "output" / "reports" / "sheaf_render_log.json",
    }

    assert _relative_posix(paths["semantic"], project_root) == "output/data/sheaf_gluing_certificate.json"
    assert _relative_posix(paths["dependency"], project_root) == "output/data/validation_dependency_graph.json"
    assert _relative_posix(paths["evidence_fields"], project_root) == "output/data/evidence_field_index.json"
    assert _relative_posix(paths["release_bundle"], project_root) == "output/reports/release_bundle_manifest.json"
    assert _relative_posix(paths["theorem_traceability"], project_root) == (
        "output/data/theorem_traceability_matrix.json"
    )
    assert _relative_posix(paths["artifact_diffoscope"], project_root) == ("output/reports/artifact_diffoscope.json")
    assert _relative_posix(paths["scholarship"], project_root) == "output/data/scholarship_source_matrix.json"
    assert _relative_posix(paths["proof_extraction"], project_root) == "output/data/proof_extraction_index.json"
    assert _relative_posix(paths["state_space_catalog"], project_root) == "output/data/state_space_catalog.json"
    assert _relative_posix(paths["causal_ablation"], project_root) == "output/data/causal_ablation_matrix.json"
    assert _relative_posix(paths["artifact_license"], project_root) == "output/reports/artifact_license_audit.json"
    assert _relative_posix(paths["release_notes"], project_root) == "output/reports/release_notes_evidence.json"
    assert _relative_posix(paths["proof_dependency_graph"], project_root) == ("output/data/proof_dependency_graph.json")
    assert _relative_posix(paths["state_transition_table"], project_root) == ("output/data/state_transition_table.json")
    assert _relative_posix(paths["ablation_sensitivity_report"], project_root) == (
        "output/reports/ablation_sensitivity_report.json"
    )
    assert _relative_posix(paths["release_attestation"], project_root) == "output/reports/release_attestation.json"
    assert _relative_posix(paths["section_status"], project_root) == "output/data/sheaf_section_status_matrix.json"
    assert _relative_posix(paths["render_log"], project_root) == "output/reports/sheaf_render_log.json"
    assert validate_sheaf_track_artifacts(project_root, require_observations=False) == []

    semantic = _load(project_root / "output" / "data" / "sheaf_gluing_certificate.json")
    evidence = _load(project_root / "output" / "data" / "evidence_field_index.json")
    release = _load(project_root / "output" / "reports" / "release_bundle_manifest.json")
    theorem = _load(project_root / "output" / "data" / "theorem_traceability_matrix.json")
    gate_index = _load(project_root / "output" / "data" / "validation_gate_index.json")
    diffoscope = _load(project_root / "output" / "reports" / "artifact_diffoscope.json")
    proof = _load(project_root / "output" / "data" / "proof_extraction_index.json")
    catalog = _load(project_root / "output" / "data" / "state_space_catalog.json")
    ablation = _load(project_root / "output" / "data" / "causal_ablation_matrix.json")
    license_audit = _load(project_root / "output" / "reports" / "artifact_license_audit.json")
    release_notes = _load(project_root / "output" / "reports" / "release_notes_evidence.json")
    scholarship = _load(project_root / "output" / "data" / "scholarship_source_matrix.json")
    proof_dependency = _load(project_root / "output" / "data" / "proof_dependency_graph.json")
    transition_table = _load(project_root / "output" / "data" / "state_transition_table.json")
    ablation_sensitivity = _load(project_root / "output" / "reports" / "ablation_sensitivity_report.json")
    release_attestation = _load(project_root / "output" / "reports" / "release_attestation.json")
    section_status = _load(project_root / "output" / "data" / "sheaf_section_status_matrix.json")
    render_log = _load(project_root / "output" / "reports" / "sheaf_render_log.json")

    from manuscript.sheaf.semantic import validate_semantic_gluing
    from roadmap_tracks.negative_controls import counterexample_payload
    from roadmap_tracks.supplemental import build_release_attestation

    controls = counterexample_payload(project_root)
    assert validate_semantic_gluing(project_root, require_observations=False) == []
    if controls["observed_count"] == 0:
        assert semantic["ok"] is False
        assert any("requires successful current per-case observations" in issue
                   for issue in validate_sheaf_track_artifacts(project_root))
    assert semantic["restrictions"]["no_versioned_live_tracks"] is True
    assert evidence["all_fields_mapped"] is True
    assert release["all_required_sources_present"] is True
    assert theorem["all_theorems_linked"] is True
    assert gate_index["all_indexed"] is True
    assert diffoscope["all_equal"] is True
    assert proof["all_extracted"] is True
    assert proof["theorem_count"] == proof["inventory_theorem_count"]
    assert proof["all_inventory_theorems_extracted"] is True
    assert proof["missing_inventory_theorems"] == []
    assert proof["extra_extracted_theorems"] == []
    assert catalog["all_finite"] is True
    assert ablation["complete_grid"] is True
    assert license_audit["all_license_safe"] is True
    assert release_notes["all_notes_source_backed"] is all(
        row["source"] and row["passed"] for row in release_notes["rows"]
    )
    assert scholarship["all_sources_connected"] is True
    assert proof_dependency["all_theorems_have_dependencies"] is True
    assert proof_dependency["all_edge_keys_unique"] is True
    assert proof_dependency["all_required_edge_types_present"] is True
    assert proof_dependency["all_edge_targets_resolved"] is True
    assert proof_dependency["duplicate_edge_keys"] == []
    assert proof_dependency["orphan_edge_targets"] == []
    assert transition_table["all_reachable_states_covered"] is True
    assert transition_table["all_reachable_states_have_outgoing"] is True
    assert transition_table["all_terminal_states_have_self_transition"] is True
    assert transition_table["missing_outgoing_state_keys"] == []
    assert transition_table["models_without_terminal_self_transition"] == []
    assert transition_table["all_transition_keys_unique"] is True
    assert transition_table["duplicate_transition_keys"] == []
    assert transition_table["transition_key_count"] == transition_table["row_count"]
    assert ablation_sensitivity["all_effects_source_backed"] is True
    assert ablation_sensitivity["all_ablation_rows_joined"] is True
    assert ablation_sensitivity["source_row_count_agreement"] is True
    assert ablation_sensitivity["row_count"] == ablation_sensitivity["ablation_source_row_count"]
    assert release_attestation == build_release_attestation(project_root)
    assert release_attestation["attested_source_count"] == release_attestation["row_count"]
    validation_row = next(row for row in release_attestation["rows"] if row["id"] == "validation_report")
    assert release_attestation["attested_validation_check_count"] == len(validation_row["attested_validation_check_ids"])
    assert section_status["all_bound_fragments_present"] is True
    assert section_status["all_sections_have_status"] is True
    assert section_status["cell_count"] == section_status["section_count"] * section_status["track_count"]
    assert render_log["all_events_ok"] is True
    assert render_log["event_count"] >= 6


def test_canonical_sheaf_negative_controls(project_root: Path) -> None:
    from roadmap_tracks import load_sheaf_track_payloads, validate_sheaf_track_payloads

    ensure_gate_artifacts(project_root)
    baseline = load_sheaf_track_payloads(project_root)
    assert validate_sheaf_track_payloads(project_root, baseline, require_observations=False) == []

    def _issues_after(key: str, mutate) -> list[str]:
        payloads = deepcopy(baseline)
        mutate(payloads[key])
        return validate_sheaf_track_payloads(project_root, payloads, require_observations=False)

    def _assert_issue(key: str, mutate, needle: str) -> None:
        assert any(needle in issue for issue in _issues_after(key, mutate))

    def _break_replay(data: dict) -> None:
        data["rows"][0]["matched"] = False
        data["all_replay_rows_matched"] = False

    _assert_issue("replay_matrix", _break_replay, "replay mismatch")

    def _break_sensitivity(data: dict) -> None:
        data["rows"] = data["rows"][:-1]
        data["row_count"] = len(data["rows"])
        data["complete_grid"] = False

    _assert_issue("sensitivity", _break_sensitivity, "grid is incomplete")

    def _break_uncertainty(data: dict) -> None:
        data["rows"][0]["distribution_sum"] = 1.5
        data["rows"][0]["normalized"] = False
        data["all_normalized"] = False

    _assert_issue("uncertainty", _break_uncertainty, "unnormalized")

    def _break_counterexample(data: dict) -> None:
        data["rows"][0]["fixture_replay_status"] = "passed"
        data["all_expected_failures_observed"] = False

    _assert_issue("counterexample", _break_counterexample, "inconsistent with the registered cases")

    def _break_model(data: dict) -> None:
        data["rows"][0]["counterexamples"] = ["finite miss"]
        data["rows"][0]["passed"] = False
        data["all_passed"] = False

    _assert_issue("model_checking", _break_model, "finite counterexample")

    def _break_interop(data: dict) -> None:
        data["rows"][0]["shape_diff"] = ["policy_shape"]
        data["all_shape_diffs_empty"] = False
        data["all_lossless"] = False

    _assert_issue("interop", _break_interop, "not lossless")

    def _break_adversarial(data: dict) -> None:
        data["rows"][0]["known_bad_passed"] = True
        data["known_bad_rows_passed"] = 1

    _assert_issue("adversarial_audit", _break_adversarial, "inconsistent with the registered cases")

    def _break_dependency(data: dict) -> None:
        data["edge_types"] = ["producer_to_track"]
        data["all_required_edge_types_present"] = False

    _assert_issue("dependency", _break_dependency, "lacks required edge types")

    def _break_scope(data: dict) -> None:
        data["promotion_matrix"][0]["promotion_complete"] = False
        data["all_live_tracks_valid"] = False

    _assert_issue("track_improvement_scope", _break_scope, "promotion rows")

    def _break_blocked(data: dict) -> None:
        data["all_blocked"] = False

    _assert_issue("blocked_scope_manifest", _break_blocked, "empirical scope blocked")

    def _break_evidence(data: dict) -> None:
        data["rows"][0]["mapped"] = False
        data["all_fields_mapped"] = False

    _assert_issue("evidence_fields", _break_evidence, "unmapped evidence fields")

    def _break_release(data: dict) -> None:
        data["rows"][0]["source_present"] = False
        data["all_required_sources_present"] = False

    _assert_issue("release_bundle", _break_release, "missing required deliverables")

    def _break_theorem(data: dict) -> None:
        data["rows"][0]["linked"] = False
        data["all_theorems_linked"] = False

    _assert_issue("theorem_traceability", _break_theorem, "unlinked theorem rows")

    def _break_gate(data: dict) -> None:
        data["rows"][0]["indexed"] = False
        data["all_indexed"] = False

    _assert_issue("gate_ergonomics", _break_gate, "unindexed gates")

    def _break_diffoscope(data: dict) -> None:
        data["rows"][0]["equal"] = False
        data["all_equal"] = False

    _assert_issue("artifact_diffoscope", _break_diffoscope, "artifact drift")

    def _break_scholarship(data: dict) -> None:
        data["rows"][0]["bib_has_locator"] = False
        data["rows"][0]["connected"] = True
        data["all_sources_connected"] = True

    _assert_issue("scholarship", _break_scholarship, "disconnected source rows")

    def _break_proof(data: dict) -> None:
        data["rows"] = [row for row in data["rows"] if row["theorem"] != "tmaze_goal_absorbing"]
        data["theorem_count"] = len(data["rows"])
        data["all_extracted"] = True
        data["all_constructive"] = True
        data["all_inventory_theorems_extracted"] = True
        data["missing_inventory_theorems"] = []

    _assert_issue("proof_extraction", _break_proof, "theorem inventory mismatch")

    def _break_catalog(data: dict) -> None:
        data["rows"][0]["finite"] = False
        data["all_finite"] = False

    _assert_issue("state_space_catalog", _break_catalog, "missing finite spaces")

    def _break_ablation(data: dict) -> None:
        data["rows"] = data["rows"][:-1]
        data["row_count"] = len(data["rows"])
        data["complete_grid"] = False

    _assert_issue("causal_ablation", _break_ablation, "incomplete deterministic rows")

    def _break_license(data: dict) -> None:
        data["rows"][0]["license_safe"] = False
        data["all_license_safe"] = False

    _assert_issue("artifact_license", _break_license, "unsafe artifacts")

    def _break_release_notes(data: dict) -> None:
        assert data["all_notes_source_backed"] is False
        data["all_notes_source_backed"] = True

    assert _issues_after("release_notes", _break_release_notes)

    def _break_proof_dependency(data: dict) -> None:
        data["rows"][0]["linked"] = False
        data["all_theorems_have_dependencies"] = True

    _assert_issue("proof_dependency_graph", _break_proof_dependency, "unlinked theorem dependencies")

    def _duplicate_proof_edge(data: dict) -> None:
        data["edges"][1]["edge_key"] = data["edges"][0]["edge_key"]
        data["duplicate_edge_keys"] = []
        data["all_edge_keys_unique"] = True

    _assert_issue("proof_dependency_graph", _duplicate_proof_edge, "duplicate dependency edges")

    def _orphan_proof_edge(data: dict) -> None:
        data["edges"][0]["target"] = "missing:model:witness"
        data["edges"][0]["edge_key"] = f"{data['edges'][0]['source']}::missing:model:witness::{data['edges'][0]['kind']}"
        data["orphan_edge_targets"] = []
        data["all_edge_targets_resolved"] = True

    _assert_issue("proof_dependency_graph", _orphan_proof_edge, "orphan theorem dependency targets")

    def _break_transition_table(data: dict) -> None:
        data["covered_models"] = data["covered_models"][:-1]
        data["all_reachable_states_covered"] = True

    _assert_issue("state_transition_table", _break_transition_table, "omits a reachable finite model")

    def _duplicate_transition_key(data: dict) -> None:
        data["rows"][1]["transition_key"] = data["rows"][0]["transition_key"]
        data["duplicate_transition_keys"] = []
        data["all_transition_keys_unique"] = True

    _assert_issue("state_transition_table", _duplicate_transition_key, "duplicate transition keys")

    def _break_transition_outgoing_coverage(data: dict) -> None:
        data["rows"][0]["next_state_key"] = "si_tmaze::uncovered"
        data["missing_outgoing_state_keys"] = []
        data["all_reachable_states_have_outgoing"] = True

    _assert_issue("state_transition_table", _break_transition_outgoing_coverage, "omits outgoing transitions")

    def _break_terminal_self_transition(data: dict) -> None:
        for row in data["rows"]:
            row["terminal_self_transition"] = False
        data["models_without_terminal_self_transition"] = []
        data["all_terminal_states_have_self_transition"] = True

    _assert_issue("state_transition_table", _break_terminal_self_transition, "omits terminal self-transition")

    def _break_ablation_sensitivity(data: dict) -> None:
        data["rows"][0]["source_backed"] = False
        data["all_effects_source_backed"] = True

    _assert_issue("ablation_sensitivity_report", _break_ablation_sensitivity, "unsupported ablation effects")

    def _break_ablation_join(data: dict) -> None:
        data["rows"][0]["source_join_key"] = ""
        data["all_ablation_rows_joined"] = True
        data["source_row_count_agreement"] = True

    _assert_issue("ablation_sensitivity_report", _break_ablation_join, "stale source joins")

    def _break_release_attestation(data: dict) -> None:
        data["rows"][1]["passed"] = False
        data["all_attested"] = True

    _assert_issue("release_attestation", _break_release_attestation, "failed gate passed")

    def _break_release_attestation_count(data: dict) -> None:
        data["attested_source_count"] += 1

    _assert_issue("release_attestation", _break_release_attestation_count, "attested source count")

    def _break_section_status(data: dict) -> None:
        data["missing_required_count"] = 1
        data["all_bound_fragments_present"] = False

    _assert_issue("section_status", _break_section_status, "missing bound fragments")

    def _break_render_log(data: dict) -> None:
        data["events"][0]["status"] = "failed"
        data["all_events_ok"] = False

    _assert_issue("render_log", _break_render_log, "failed render events")

    def _break_semantic(data: dict) -> None:
        data["restrictions"]["replay_matrix_all_matched"] = False

    _assert_issue("semantic", _break_semantic, "stale relative to canonical restrictions")


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_canonical_track_contract_negative_controls(project_root: Path) -> None:
    from roadmap_tracks.sheaf_tracks import (
        _canonical_restrictions,
        build_artifact_provenance,
        build_blocked_scope_manifest,
        build_track_improvement_scope,
    )

    ensure_gate_artifacts(project_root)
    config_path = project_root / "docs" / "manuscript" / "config.yaml"
    manifest_path = project_root / "docs" / "manuscript" / "sheaf" / "manifest.yaml"
    registry_path = project_root / "docs" / "manuscript" / "sheaf" / "tracks.yaml"
    ledger_path = project_root / "data" / "claim_ledger.yaml"
    originals = {
        config_path: config_path.read_text(encoding="utf-8"),
        manifest_path: manifest_path.read_text(encoding="utf-8"),
        registry_path: registry_path.read_text(encoding="utf-8"),
        ledger_path: ledger_path.read_text(encoding="utf-8"),
    }
    try:
        config_path.write_text(
            originals[config_path].replace("    - generate_sheaf_tracks.py\n", ""),
            encoding="utf-8",
        )
        provenance = build_artifact_provenance(project_root)
        assert provenance["all_producers_configured"] is False
        config_path.write_text(originals[config_path], encoding="utf-8")

        manifest_payload = yaml.safe_load(originals[manifest_path])
        for section in manifest_payload["sections"]:
            (section.get("tracks") or {}).pop("evidence_fields", None)
        manifest_path.write_text(yaml.safe_dump(manifest_payload, sort_keys=False), encoding="utf-8")
        scope = build_track_improvement_scope(project_root)
        missing_evidence = [row for row in scope["promotion_matrix"] if row["track_id"] == "evidence_fields"]
        assert missing_evidence and missing_evidence[0]["has_manuscript_consumer"] is False
        assert scope["all_live_tracks_valid"] is False
        manifest_path.write_text(originals[manifest_path], encoding="utf-8")

        registry_payload = yaml.safe_load(originals[registry_path])
        registry_payload["tracks"]["empirical_adapter"] = {"order": 999, "renderer": "markdown", "label": "Empirical"}
        registry_path.write_text(yaml.safe_dump(registry_payload, sort_keys=False), encoding="utf-8")
        blocked = build_blocked_scope_manifest(project_root)
        assert blocked["all_blocked"] is False
        assert blocked["rows"][0]["no_live_registry_entry"] is False
        registry_path.write_text(originals[registry_path], encoding="utf-8")

        ledger_payload = yaml.safe_load(originals[ledger_path])
        ledger_payload["claims"] = [
            claim for claim in ledger_payload["claims"] if claim.get("path") != "output/data/evidence_field_index.json"
        ]
        ledger_path.write_text(yaml.safe_dump(ledger_payload, sort_keys=False), encoding="utf-8")
        restrictions = _canonical_restrictions(project_root)
        assert restrictions["all_canonical_artifacts_have_claims"] is False
    finally:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")


def test_canonical_sensitivity_rejects_incomplete_warm_inputs(tmp_path: Path) -> None:
    from roadmap_tracks.sheaf_tracks import build_sensitivity_sweep
    from roadmap_tracks.toy_sweep import build_sensitivity_sweep as build_authoritative

    authoritative = build_authoritative(tmp_path)
    path = tmp_path / "output/data/sensitivity_sweep.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(authoritative), encoding="utf-8")
    canonical = build_sensitivity_sweep(tmp_path)
    expected = {
        (row["lambda"], row["horizon"], row["seed"], row["topology"]): row for row in authoritative["rows"]
    }
    assert set(canonical["grid"]["topologies"]) == set(authoritative["grid"]["topologies"])
    assert len(canonical["grid"]["topologies"]) == 4
    for row in canonical["rows"]:
        source = expected[(row["lambda"], row["horizon"], row["seed"], row["topology"])]
        assert all(row[field] == source[field] for field in ("mi", "goal_reached", "belief_entropy_terminal"))
    for mutation in ("missing_topology", "missing_cell", "missing_value", "empty"):
        changed = deepcopy(authoritative)
        if mutation == "missing_topology":
            topology = changed["grid"]["topologies"][-1]
            changed["rows"] = [row for row in changed["rows"] if row["topology"] != topology]
        elif mutation == "missing_cell":
            changed["rows"].pop()
        elif mutation == "missing_value":
            del changed["rows"][0]["mi"]
        else:
            changed = {}
        path.write_text(json.dumps(changed), encoding="utf-8")
        with pytest.raises(ValueError, match="sensitivity source"):
            build_sensitivity_sweep(tmp_path)


@pytest.mark.parametrize("key", [
    "proof_dependency_graph", "state_transition_table", "ablation_sensitivity_report", "release_attestation",
])
def test_supplemental_consumers_share_source_authentication(
    tmp_path: Path, key: str,
) -> None:
    from gates.output_checks import validate_outputs_selected_strict
    from roadmap_tracks import load_sheaf_track_payloads, validate_sheaf_track_payloads
    from roadmap_tracks.supplemental import SUPPLEMENTAL_ARTIFACTS, validate_supplemental_payloads
    from test_supplemental_source_binding import supplemental_root

    root = supplemental_root.__wrapped__(tmp_path)
    payloads = {name: _load(root / relative) for name, relative in SUPPLEMENTAL_ARTIFACTS.items()}
    check = f"{key}_schema"
    assert validate_supplemental_payloads(root, payloads)[key] == []
    assert validate_outputs_selected_strict(root, {check}, payloads=payloads) == {check: True}
    changed = deepcopy(payloads)
    if key == "proof_dependency_graph":
        kind = changed[key]["required_edge_types"][0]
        changed[key]["edges"] = [edge for edge in changed[key]["edges"] if edge["kind"] != kind]
        changed[key]["required_edge_types"].remove(kind)
    elif key == "state_transition_table":
        model = changed[key]["required_models"][0]
        changed[key]["rows"] = [row for row in changed[key]["rows"] if row["model"] != model]
        changed[key]["required_models"].remove(model)
        changed[key]["covered_models"].remove(model)
    elif key == "ablation_sensitivity_report":
        changed[key]["rows"][0]["source_join_key"] = "unrelated::42"
    else:
        row = next(row for row in changed[key]["rows"] if row["id"] == "validation_report")
        row["attested_validation_check_ids"][0] = "outputs.forged_same_count"
    direct = validate_supplemental_payloads(root, changed)[key]
    assert direct
    assert validate_outputs_selected_strict(root, {check}, payloads=changed) == {check: False}
    all_payloads = load_sheaf_track_payloads(root)
    all_payloads.update(changed)
    issues = validate_sheaf_track_payloads(root, all_payloads, validate_saved_certificate=False,
                                         require_observations=False)
    filename = Path(SUPPLEMENTAL_ARTIFACTS[key]).name
    assert [issue for issue in issues if filename in issue] == direct
    (root / SUPPLEMENTAL_ARTIFACTS[key]).write_text(json.dumps(changed[key]), encoding="utf-8")
    assert validate_supplemental_payloads(root)[key] == direct
    assert validate_outputs_selected_strict(root, {check}) == {check: False}


@pytest.mark.artifact_slow
def test_bootstrap_readiness_accepts_only_authentic_unobserved_state(project_root: Path, tmp_path: Path) -> None:
    import shutil
    from gate_support import _gate_artifacts_ready
    from gates.output_checks import validate_outputs
    from ontology.bindings import resolve_model_ontology_path
    from orchestration.artifact_pipeline import hydrate_manuscript_fixed_point
    from roadmap_tracks.negative_controls import counterexample_payload
    from roadmap_tracks.integration_audit import validate_integration_audit_artifacts
    from test_negative_control_receipts import _copy_authored

    ensure_gate_artifacts(project_root)
    root = _copy_authored(project_root, tmp_path / "source")
    shutil.copytree(project_root / "output", root / "output",
                    ignore=shutil.ignore_patterns("negative_control_receipts", ".artifact.lock"))
    hydrate_manuscript_fixed_point(root, require_analysis_outputs=False)
    assert counterexample_payload(root)["observed_count"] == 0
    assert _gate_artifacts_ready(root, include_manuscript=True) is True
    strict = validate_outputs(root, only={"counterexample_matrix_schema", "adversarial_audit_schema"})
    assert strict == {"counterexample_matrix_schema": False, "adversarial_audit_schema": False}
    assert validate_integration_audit_artifacts(root, require_release_evidence=False) == []
    assert validate_integration_audit_artifacts(root)
    from gates.output_checks import validate_outputs_selected_strict

    integration_key = "integration_audit_track_schemas"
    assert validate_outputs_selected_strict(root, {integration_key}, require_observations=False) == {integration_key: True}
    assert validate_outputs_selected_strict(root, {integration_key}) == {integration_key: False}

    promotion_key = "track_improvement_scope_schema"
    assert validate_outputs_selected_strict(root, {promotion_key}, require_observations=False) == {promotion_key: True}
    assert validate_outputs_selected_strict(root, {promotion_key}) == {promotion_key: False}
    promotion_path = root / "output/data/track_improvement_scope.json"
    promotion_bytes = promotion_path.read_bytes()
    promotion = json.loads(promotion_bytes)
    row = next(row for row in promotion["promotion_matrix"] if row["negative_control_observed"] is False)
    row["negative_control_observed"] = True
    promotion_path.write_text(json.dumps(promotion), encoding="utf-8")
    try:
        assert validate_outputs_selected_strict(root, {promotion_key}, require_observations=False) == {promotion_key: False}
    finally:
        promotion_path.write_bytes(promotion_bytes)
    audit_path = root / "output/reports/adversarial_audit.json"
    audit_bytes = audit_path.read_bytes()
    altered = json.loads(audit_bytes)
    assert altered["all_expected_failures_documented"] is True and altered["observed_count"] == 0
    altered["rows"][0]["known_bad_passed"] = True
    audit_path.write_text(json.dumps(altered), encoding="utf-8")
    try:
        assert any("adversarial_audit.json is inconsistent" in issue
                   for issue in validate_integration_audit_artifacts(root, require_release_evidence=False))
    finally:
        audit_path.write_bytes(audit_bytes)
    abstract = root / "docs/manuscript/00_abstract.md"
    abstract_bytes = abstract.read_bytes()
    abstract.write_text("This finite toy is illustrative; we measured production LLMs.\n", encoding="utf-8")
    try:
        assert any("scope_boundary_audit.json" in issue
                   for issue in validate_integration_audit_artifacts(root, require_release_evidence=False))
    finally:
        abstract.write_bytes(abstract_bytes)
    ontology = resolve_model_ontology_path(root, "si_tmaze")
    ontology.write_text(ontology.read_text().replace("q_pi: PolicyPosterior", "q_pi: HiddenState"), encoding="utf-8")
    assert _gate_artifacts_ready(root, include_manuscript=True) is False


def _finite_comparison_input(root: Path, project_root: Path) -> dict:
    """A genuine finite posterior input, independent of canonical run defaults."""
    import math
    import shutil
    from dataclasses import replace
    from simulation.pymdp_config import apply_pymdp_overrides, config_hash, config_snapshot, load_pymdp_config

    shutil.copy2(project_root / "pymdp.yaml", root / "pymdp.yaml")
    base = apply_pymdp_overrides(load_pymdp_config(root), horizon=2, steps=1, seed=91)
    seeds = (7, 11)
    planners = ("sophisticated_inference", "vanilla")
    runs = []
    for seed in seeds:
        for planner in planners:
            configured = apply_pymdp_overrides(base, seed=seed)
            log_path = Path(base.logging.path).parent / f"pymdp_compare_{planner}_2_{seed}.jsonl"
            configured = replace(configured, logging=replace(configured.logging, path=str(log_path)))
            values = [0.75, 0.25]
            steps = [{
                "step": step, "posterior_available": True, "posterior_source": planner,
                "q_pi": values, "q_pi_sum": sum(values), "q_pi_normalized": abs(sum(values) - 1.0) <= 1e-9,
                "q_pi_entropy": -sum(value * math.log(value) for value in values),
                "action_probabilities": {"0": values[0], "1": values[1]}, "fallback_reason": None,
            } for step in range(base.timesteps + 1)]
            runs.append({
                "planner": planner, "seed": seed, "role": "validation_comparison",
                "config": config_snapshot(configured), "config_hash": config_hash(configured),
                "horizon": base.planning_horizon, "steps": base.timesteps,
                "policy_len": (base.agent.si_policy_len if planner == "sophisticated_inference"
                               else base.agent.vanilla_policy_len),
                "goal_reached": [0, 1][-1] == 1,
                "policy_posterior_steps": steps,
                "policy_posterior_all_normalized": all(step["q_pi_normalized"] for step in steps),
            })
    return {
        "schema": "template_active_inference.si_policy_comparison.v2",
        "scope": "comparison_only", "canonical_planner": "sophisticated_inference",
        "config": config_snapshot(base), "config_hash": config_hash(base), "runs": runs,
        "summary": {
            "run_count": len(runs), "planners": sorted(planners), "seeds": list(seeds), "horizons": [2],
            "expected_run_count": len(seeds) * len(planners), "complete_grid": True,
            "vanilla_role": "comparison_only", "all_efe_rows_explained": True,
            "all_available_posteriors_normalized": all(run["policy_posterior_all_normalized"] for run in runs),
        },
    }


@pytest.mark.parametrize("mutation", ["missing_run", "missing_grid_row", "run_hash", "run_config", "grid_hash", "source_hash"])
def test_selected_policy_gates_bind_effective_input_not_root_defaults(
    project_root: Path, tmp_path: Path, mutation: str,
) -> None:
    from gates.output_checks import validate_outputs_selected_strict
    from simulation.si_artifacts import write_policy_posterior_grid

    comparison = _finite_comparison_input(tmp_path, project_root)
    comparison_path = tmp_path / "output/data/si_policy_comparison.json"
    comparison_path.parent.mkdir(parents=True)
    comparison_path.write_text(json.dumps(comparison), encoding="utf-8")
    grid_path = write_policy_posterior_grid(tmp_path, comparison=comparison)
    keys = {"si_policy_comparison_schema", "pymdp_policy_posterior_grid_schema"}
    assert validate_outputs_selected_strict(tmp_path, keys) == {key: True for key in keys}
    if mutation in {"missing_run", "run_hash", "run_config"}:
        changed = deepcopy(comparison)
        if mutation == "missing_run":
            changed["runs"].pop()
        elif mutation == "run_hash":
            changed["runs"][0]["config_hash"] = "0" * 16
        else:
            import hashlib

            run = changed["runs"][0]
            run["config"]["environment"]["cue_validity"] = 0.625
            run["config_hash"] = hashlib.sha256(
                json.dumps(run["config"], sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()[:16]
        comparison_path.write_text(json.dumps(changed), encoding="utf-8")
        checks = validate_outputs_selected_strict(tmp_path, keys)
        assert checks == {key: False for key in keys}
    else:
        grid = _load(grid_path)
        if mutation == "missing_grid_row":
            grid["rows"].pop()
            grid["row_count"] = len(grid["rows"])
        elif mutation == "grid_hash":
            grid["config_hash"] = "0" * 16
        else:
            grid["source_payload_sha256"] = "0" * 64
        grid_path.write_text(json.dumps(grid), encoding="utf-8")
        assert validate_outputs_selected_strict(tmp_path, keys) == {
            "si_policy_comparison_schema": True, "pymdp_policy_posterior_grid_schema": False,
        }
