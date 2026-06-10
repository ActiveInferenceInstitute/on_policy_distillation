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

    registry = yaml.safe_load((project_root / "manuscript" / "sheaf" / "tracks.yaml").read_text())["tracks"]
    manifest = yaml.safe_load((project_root / "manuscript" / "sheaf" / "manifest.yaml").read_text())
    public_tracks = {
        str(row["id"])
        for row in yaml.safe_load((project_root / "tracks.yaml").read_text())["tracks"]
        if isinstance(row, dict) and row.get("id")
    }
    claims = yaml.safe_load((project_root / "data" / "claim_ledger.yaml").read_text()).get("claims") or []
    configured = yaml.safe_load((project_root / "manuscript" / "config.yaml").read_text())["analysis"]["scripts"]

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
    assert validate_sheaf_track_artifacts(project_root) == []

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

    assert semantic["ok"] is True
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
    assert release_notes["all_notes_source_backed"] is True
    assert scholarship["all_sources_connected"] is True
    assert proof_dependency["all_theorems_have_dependencies"] is True
    assert transition_table["all_reachable_states_covered"] is True
    assert ablation_sensitivity["all_effects_source_backed"] is True
    assert release_attestation["all_attested"] is True
    assert section_status["all_bound_fragments_present"] is True
    assert section_status["all_sections_have_status"] is True
    assert section_status["cell_count"] == section_status["section_count"] * section_status["track_count"]
    assert render_log["all_events_ok"] is True
    assert render_log["event_count"] >= 6


def test_canonical_sheaf_negative_controls(project_root: Path) -> None:
    from roadmap_tracks import load_sheaf_track_payloads, validate_sheaf_track_payloads

    baseline = load_sheaf_track_payloads(project_root)

    def _issues_after(key: str, mutate) -> list[str]:
        payloads = deepcopy(baseline)
        mutate(payloads[key])
        return validate_sheaf_track_payloads(project_root, payloads)

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

    _assert_issue("counterexample", _break_counterexample, "fixtures passing")

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

    _assert_issue("adversarial_audit", _break_adversarial, "known-bad rows passing")

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
        data["rows"][0]["passed"] = False
        data["all_notes_source_backed"] = False

    _assert_issue("release_notes", _break_release_notes, "unsupported notes")

    def _break_proof_dependency(data: dict) -> None:
        data["rows"][0]["linked"] = False
        data["all_theorems_have_dependencies"] = True

    _assert_issue("proof_dependency_graph", _break_proof_dependency, "unlinked theorem dependencies")

    def _break_transition_table(data: dict) -> None:
        data["covered_models"] = data["covered_models"][:-1]
        data["all_reachable_states_covered"] = True

    _assert_issue("state_transition_table", _break_transition_table, "omits a reachable finite model")

    def _break_ablation_sensitivity(data: dict) -> None:
        data["rows"][0]["source_backed"] = False
        data["all_effects_source_backed"] = True

    _assert_issue("ablation_sensitivity_report", _break_ablation_sensitivity, "unsupported ablation effects")

    def _break_release_attestation(data: dict) -> None:
        data["rows"][1]["passed"] = False
        data["all_attested"] = True

    _assert_issue("release_attestation", _break_release_attestation, "failed gate passed")

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
    config_path = project_root / "manuscript" / "config.yaml"
    manifest_path = project_root / "manuscript" / "sheaf" / "manifest.yaml"
    registry_path = project_root / "manuscript" / "sheaf" / "tracks.yaml"
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
