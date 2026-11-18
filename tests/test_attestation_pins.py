"""Pins for the consistency-vs-greenness split and the attestation carve-out.

Advisor-mandated (run-2): (1) a consistent-but-red attestation is accepted by
the inner validators and rejected only by the greenness gate — proving the
split is load-bearing; (2) the self-row carve-out is exactly one row wide;
(3) oracle negative controls fail for the asserted reason, not incidentally.
No mocks: real builders over real temp trees.
"""

from __future__ import annotations

import hashlib
from copy import deepcopy
import json
from pathlib import Path

from roadmap_tracks.formal_interop import build_model_checking_witnesses
from roadmap_tracks.sheaf_tracks import build_interop_roundtrip_report
from roadmap_tracks.supplemental import (
    build_release_attestation,
    release_attestation_consistent_and_current,
    validate_supplemental_payloads,
)


def _attestation_issues(root: Path, attestation: dict) -> list[str]:
    return validate_supplemental_payloads(root, {"release_attestation": attestation})["release_attestation"]


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _report(tmp_path: Path, failed: list[str]) -> bytes:
    outputs = {"si_summary_schema": True, "release_attestation_schema": True}
    manuscript = {"canonical_sheaf_tracks": True}
    for key in failed:
        (manuscript if key in manuscript else outputs)[key] = False
    payload = {
        "schema": "template_active_inference.validation_report.v1",
        "outputs": outputs,
        "manuscript": manuscript,
        "failed_checks": sorted(set(failed)),
        "all_passed": not failed,
    }
    path = tmp_path / "output" / "reports" / "validation_report.json"
    _write(path, payload)
    return path.read_bytes()


def _companions(root: Path) -> None:
    _write(root / "output/reports/release_bundle_manifest.json", {
        "all_required_sources_present": True, "all_copied_outputs_match_or_deferred": True,
        "bundle_hash": hashlib.sha256(b"finite attestation companion fixture").hexdigest(),
    })
    _write(root / "output/reports/artifact_license_audit.json", {"all_license_safe": True})
    _write(root / "output/reports/blocked_scope_manifest.json", {"all_blocked": True})
    _write(root / "output/data/sheaf_gluing_certificate.json", {
        "ok": True, "restrictions": {"finite_fixture_scope": True},
    })


def test_consistent_but_red_attestation_passes_inner_accepts_outer_rejects(tmp_path: Path) -> None:
    """Pin 1: inner = consistency, outer = greenness; both layers load-bearing."""
    from gates.output_checks import validate_outputs_selected_strict

    _companions(tmp_path)
    _report(tmp_path, failed=["si_summary_schema"])
    consistent_red = build_release_attestation(tmp_path)
    assert {row["id"] for row in consistent_red["rows"]} == {
        "validation_report", "release_bundle", "artifact_license", "blocked_scope", "semantic_certificate",
    }

    # Inner validator: honestly-red is NOT a lie — no issue.
    assert not _attestation_issues(tmp_path, consistent_red)
    # Inner restriction: consistent and hash-current — True even though red.
    assert release_attestation_consistent_and_current(tmp_path, consistent_red) is True
    assert validate_outputs_selected_strict(
        tmp_path, {"release_attestation_schema"}, payloads={"release_attestation": consistent_red}
    ) == {"release_attestation_schema": False}

    # A LYING attestation (flag disagrees with rows) fails the inner layer too.
    lying = deepcopy(consistent_red)
    lying["all_attested"] = True
    assert _attestation_issues(tmp_path, lying)
    assert release_attestation_consistent_and_current(tmp_path, lying) is False


def test_carveout_is_exactly_one_row_wide(tmp_path: Path) -> None:
    """Pin 2: the self-row carve-out cannot mask any non-self failure."""

    # Green companions, report failing ONLY the attestation self-check.
    _report(tmp_path, failed=["release_attestation_schema"])
    _companions(tmp_path)
    attestation = build_release_attestation(tmp_path)
    by_id = {row["id"]: row for row in attestation["rows"]}
    assert by_id["validation_report"]["passed"] is True  # carve-out admits ONLY the self-row

    # The carve-out admits ONLY the declared fixed-point check set — every
    # member of which is itself a first-class validate check, so an admitted
    # failure still fails the overall gate. Anything OUTSIDE the set is never
    # admitted:
    from roadmap_tracks.supplemental import VALIDATION_FIXED_POINT_CHECKS

    _report(tmp_path, failed=["release_attestation_schema", "si_summary_schema"])
    attestation = build_release_attestation(tmp_path)
    by_id = {row["id"]: row for row in attestation["rows"]}
    assert by_id["validation_report"]["passed"] is False
    assert attestation["all_attested"] is False
    # And the admitted set stays an explicit, reviewable constant — a silent
    # wildcard, empty set, or accidental broadening would gut this pin.
    expected_fixed_point_checks = {
        "artifact_provenance_schema",
        "canonical_sheaf_track_schemas",
        "resolved_manuscript_hydrated",
        "canonical_sheaf_tracks",
        "claim_ledger_valid",
        "experiment_plan_metrics",
        "integration_audit_artifacts",
        "integration_audit_track_schemas",
        "manuscript_staleness_report_schema",
        "release_attestation_schema",
        "release_notes_evidence_schema",
        "semantic_sheaf_gluing",
    }
    assert VALIDATION_FIXED_POINT_CHECKS == expected_fixed_point_checks
    assert "si_summary_schema" not in VALIDATION_FIXED_POINT_CHECKS

    # A failing NON-self row (license) is never masked.
    _report(tmp_path, failed=[])
    _write(tmp_path / "output" / "reports" / "artifact_license_audit.json", {"all_license_safe": False})
    attestation = build_release_attestation(tmp_path)
    assert attestation["all_attested"] is False


def test_oracle_negative_controls_fail_for_the_asserted_reason(tmp_path: Path) -> None:
    """Pin 3: empty-dir failures fire inside the oracle, not incidentally upstream."""
    interop = build_interop_roundtrip_report(tmp_path)
    assert interop["all_lossless"] is False
    companion_rows = [row for row in interop["rows"] if row["id"].startswith("companion_present:")]
    assert companion_rows, "presence rows must exist even on an empty tree"
    assert all(row["lossless"] is False for row in companion_rows)  # the fail-closed check itself fired

    witnesses = build_model_checking_witnesses(tmp_path)
    assert witnesses["all_passed"] is False
    tmaze_rows = [row for row in witnesses["rows"] if row["model"].startswith("si_tmaze")]
    assert tmaze_rows and all(row["passed"] is False for row in tmaze_rows)
    assert all(row["counterexamples"] for row in tmaze_rows)  # reason recorded, not incidental


def test_semantic_writer_refreshes_attestation_after_certificate_changes(tmp_path: Path) -> None:
    from manuscript.sheaf.semantic import write_semantic_gluing_outputs

    _companions(tmp_path)
    _report(tmp_path, failed=[])
    assert build_release_attestation(tmp_path)["all_attested"] is True

    outputs = write_semantic_gluing_outputs(tmp_path, refresh_hydration=False)
    certificate = json.loads(outputs["certificate"].read_bytes())
    attestation = json.loads((tmp_path / "output/reports/release_attestation.json").read_bytes())
    assert attestation == build_release_attestation(tmp_path)
    assert certificate["restrictions"]["release_attestation_complete"] is True
    assert attestation["all_attested"] is False
