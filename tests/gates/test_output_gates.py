"""Output gate validation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gates.artifact_manifest import REQUIRED_OUTPUT_CHECK_KEYS
from gates.validation import validate_outputs
from gates.output_checks import validate_outputs_selected_strict

from gate_support import _BOOTSTRAPPED_ROOTS, ensure_gate_artifacts


def ensure_gate_artifacts_for(project_root: Path, *relative_paths: str) -> None:
    """Build the full gate surface only when a negative-control prerequisite is absent."""
    root = project_root.resolve()
    if relative_paths and all((root / rel).is_file() for rel in relative_paths):
        return
    _BOOTSTRAPPED_ROOTS.discard(root)
    ensure_gate_artifacts(root)


def test_validate_outputs_after_analysis() -> None:
    root = Path(__file__).resolve().parents[2]
    from analysis import run_analysis

    run_analysis(root)
    checks = validate_outputs(root, only={"output/data/parameter_sweep.csv"})
    assert checks.get("output/data/parameter_sweep.csv")


# Regenerates heavy sheaf/roadmap gate artifacts; ~57-59s locally and can exceed the
# CI-wide --timeout=120 on slower runners. The per-test marker overrides the CLI value.
@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
def test_validate_outputs_required_artifacts(project_root: Path) -> None:
    ensure_gate_artifacts(project_root)
    checks = validate_outputs(project_root)
    selected_keys = {"si_summary_schema", "figure_source_map_schema", "firstprinciples_statistics_schema"}
    selected = validate_outputs_selected_strict(project_root, selected_keys)
    assert selected == {key: checks[key] for key in selected_keys}
    for key in REQUIRED_OUTPUT_CHECK_KEYS:
        assert checks.get(key), f"missing validate_outputs key: {key}"
    assert checks.get("si_invariants_all_pass") is True
    assert checks.get("invariants_all_pass") is True


def test_validate_outputs_selected_strict_rejects_unknown_key(project_root: Path) -> None:
    with pytest.raises(KeyError, match="unsupported lazy output check keys"):
        validate_outputs_selected_strict(project_root, {"not_a_real_output_check"})


def test_validate_outputs_public_only_rejects_unknown_key(project_root: Path) -> None:
    """A misspelled selected gate must not certify an empty check set."""
    with pytest.raises(KeyError, match="unsupported output check keys"):
        validate_outputs(project_root, only={"not_a_real_output_check"})


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_hidden_temp_figure_artifact_fails(project_root: Path) -> None:
    ensure_gate_artifacts_for(project_root, "output/figures/ising_mi_curve.png")
    temp = project_root / "output" / "figures" / ".distillation_divergence_geometry.broken.png"
    try:
        temp.write_bytes(b"")
        checks = validate_outputs_selected_strict(project_root, {"figure_output_integrity"})
        assert checks["figure_output_integrity"] is False
    finally:
        temp.unlink(missing_ok=True)


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_unreadable_visible_figure_fails(project_root: Path) -> None:
    ensure_gate_artifacts_for(project_root, "output/figures/ising_mi_curve.png")
    broken = project_root / "output" / "figures" / "unreadable_regression.png"
    try:
        broken.write_bytes(b"not a png")
        checks = validate_outputs_selected_strict(project_root, {"figure_output_integrity"})
        assert checks["figure_output_integrity"] is False
    finally:
        broken.unlink(missing_ok=True)


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_unregistered_visible_figure_fails(project_root: Path) -> None:
    ensure_gate_artifacts_for(project_root, "output/reports/figure_hash_manifest.json")
    extra = project_root / "output" / "figures" / "unregistered_but_readable.png"
    try:
        from PIL import Image

        Image.new("RGB", (24, 24), "white").save(extra)
        integrity = validate_outputs_selected_strict(project_root, {"figure_output_integrity"})
        manifest = validate_outputs_selected_strict(project_root, {"figure_hash_manifest_schema"})
        assert integrity["figure_output_integrity"] is False
        assert manifest["figure_hash_manifest_schema"] is False
    finally:
        extra.unlink(missing_ok=True)


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_si_invariants_fail(project_root: Path, tmp_path: Path) -> None:
    path = project_root / "output" / "reports" / "si_invariants.json"
    if not path.is_file():
        pytest.skip("SI invariants report missing; run analysis first")
    backup = tmp_path / "si_invariants.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["all_pass"] = False
    payload["invariants"] = {name: False for name in payload.get("invariants", {})}
    try:
        path.write_text(json.dumps(payload), encoding="utf-8")
        checks = validate_outputs(project_root, only={"si_invariants_all_pass"})
        assert checks["si_invariants_all_pass"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_analytical_invariants_fail(project_root: Path, tmp_path: Path) -> None:
    path = project_root / "output" / "reports" / "invariants.json"
    if not path.is_file():
        pytest.skip("invariants report missing; run analysis first")
    backup = tmp_path / "invariants.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["all_pass"] = False
    analytical = payload.get("invariants") or {}
    payload["invariants"] = {name: False for name in analytical}
    try:
        path.write_text(json.dumps(payload), encoding="utf-8")
        checks = validate_outputs(project_root, only={"invariants_all_pass"})
        assert checks["invariants_all_pass"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


def test_write_invariants_report_preserves_simulation_merge(project_root: Path) -> None:
    from orchestration.analysis import write_invariants_report

    inv_path = project_root / "output" / "reports" / "invariants.json"
    si_summary = project_root / "output" / "data" / "si_tmaze_summary.json"
    if not inv_path.is_file() or not si_summary.is_file():
        from analysis import run_analysis
        from simulation.si_runner import pymdp_available, run_and_persist

        run_analysis(project_root)
        if not pymdp_available():
            pytest.skip("pymdp not installed")
        run_and_persist(project_root)

    before = json.loads(inv_path.read_text(encoding="utf-8"))
    assert before.get("simulation"), "expected merged simulation invariants before rewrite"

    write_invariants_report(project_root)
    after = json.loads(inv_path.read_text(encoding="utf-8"))
    assert after.get("simulation")
    assert after.get("all_pass") is True


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_missing_si_invariants_report(project_root: Path, tmp_path: Path) -> None:
    summary = project_root / "output" / "data" / "si_tmaze_summary.json"
    si_inv = project_root / "output" / "reports" / "si_invariants.json"
    if not summary.is_file():
        pytest.skip("SI summary missing; run analysis first")
    backup = tmp_path / "si_invariants.json.bak"
    had_si_inv = si_inv.is_file()
    if had_si_inv:
        backup.write_text(si_inv.read_text(encoding="utf-8"), encoding="utf-8")
        si_inv.unlink()
    try:
        checks = validate_outputs(project_root, only={"si_invariants_all_pass"})
        assert checks["si_invariants_all_pass"] is False
    finally:
        if had_si_inv:
            si_inv.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_missing_si_value_rows_fail(project_root: Path, tmp_path: Path) -> None:
    summary = project_root / "output" / "data" / "si_tmaze_summary.json"
    ensure_gate_artifacts_for(project_root, "output/data/si_tmaze_summary.json")
    backup = tmp_path / "si_tmaze_summary.json.bak"
    backup.write_text(summary.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["q_pi_by_step"] = []
    payload["action_probabilities"] = []
    payload["tree_available"] = False
    payload["mode"] = "sophisticated_inference"
    try:
        summary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"si_summary_schema"})
        assert checks["si_summary_schema"] is False
    finally:
        summary.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_missing_sheaf_matrix(project_root: Path, tmp_path: Path) -> None:
    matrix = project_root / "output" / "data" / "sheaf_coverage_matrix.json"
    backup = tmp_path / "sheaf_coverage_matrix.json.bak"
    if matrix.is_file():
        backup.write_bytes(matrix.read_bytes())
        matrix.unlink()
    try:
        checks = validate_outputs(project_root, only={"output/data/sheaf_coverage_matrix.json"})
        assert checks.get("output/data/sheaf_coverage_matrix.json") is False
    finally:
        if backup.is_file():
            matrix.write_bytes(backup.read_bytes())


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_missing_sweep(project_root: Path, tmp_path: Path) -> None:
    sweep = project_root / "output" / "data" / "parameter_sweep.csv"
    backup = tmp_path / "parameter_sweep.csv.bak"
    if sweep.is_file():
        backup.write_bytes(sweep.read_bytes())
        sweep.unlink()
    try:
        checks = validate_outputs(project_root, only={"output/data/parameter_sweep.csv"})
        assert checks.get("output/data/parameter_sweep.csv") is False
    finally:
        if backup.is_file():
            sweep.write_bytes(backup.read_bytes())


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_figure_source_map_requires_provenance(project_root: Path, tmp_path: Path) -> None:
    ensure_gate_artifacts_for(project_root, "output/data/figure_source_map.json")
    path = project_root / "output" / "data" / "figure_source_map.json"
    backup = tmp_path / "figure_source_map.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["rows"][0].pop("generator", None)
    payload["rows"][0]["source_fields"] = []
    payload["all_figures_mapped"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"figure_source_map_schema"})
        assert checks["figure_source_map_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_figure_source_map_requires_caption_claim_contract(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(project_root, "output/data/figure_source_map.json")
    path = project_root / "output" / "data" / "figure_source_map.json"
    backup = tmp_path / "figure_source_map.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    row = next(row for row in payload["rows"] if row["figure_id"] == "policy_posterior_grid")
    row["caption_claims"][0]["source_fields"] = ["$.not_a_real_field"]
    row["caption_claims_source_bound"] = True
    row["caption_claims_ok"] = True
    row["mapped"] = True
    payload["all_caption_claims_ok"] = True
    payload["all_figures_mapped"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"figure_source_map_schema"})
        assert checks["figure_source_map_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_caption_term_only_in_token_name(
    project_root: Path,
    tmp_path: Path,
) -> None:
    # A `caption_term` that only matches a `{{token}}` name (which renders to a
    # number after hydration) and never appears in the authored prose must be
    # rejected by row-level rederivation, even when every stored boolean is forged
    # green. This is the historical failure mode: a plausible artifact accepted by
    # a verifier that checked the raw template instead of the rendered caption.
    ensure_gate_artifacts_for(project_root, "output/data/figure_source_map.json")
    path = project_root / "output" / "data" / "figure_source_map.json"
    backup = tmp_path / "figure_source_map.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    row = next(row for row in payload["rows"] if row["figure_id"] == "ising_mi_curve")
    assert "{{sweep_max_residual" in row["caption"]  # token present only in the raw template
    row["caption_claims"][0]["caption_terms"] = ["sweep_max_residual"]
    row["caption_claim_terms_present"] = True
    row["caption_claims_ok"] = True
    row["mapped"] = True
    payload["all_caption_claims_ok"] = True
    payload["all_figures_mapped"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"figure_source_map_schema"})
        assert checks["figure_source_map_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_caption_claim_field_does_not_resolve(
    project_root: Path,
    tmp_path: Path,
) -> None:
    # A claim source_field that is merely *declared* but resolves to no value in the
    # artifact must be rejected by row-level rederivation, even with every stored
    # boolean forged green. Closes the gap where the contract only checked that a
    # field string was listed on the row, not that it binds to artifact content.
    ensure_gate_artifacts_for(project_root, "output/data/figure_source_map.json")
    path = project_root / "output" / "data" / "figure_source_map.json"
    backup = tmp_path / "figure_source_map.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    row = next(row for row in payload["rows"] if row["figure_id"] == "ising_mi_curve")
    row["caption_claims"][0]["source_fields"] = ["$.totally_made_up_field"]
    row["source_fields"] = ["$.totally_made_up_field"]
    row["source_field_count"] = 1
    row["caption_claim_fields_resolved"] = True
    row["caption_claims_source_bound"] = True
    row["caption_claims_ok"] = True
    row["mapped"] = True
    payload["all_caption_claims_ok"] = True
    payload["all_figures_mapped"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"figure_source_map_schema"})
        assert checks["figure_source_map_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_figure_source_map_caption_is_registry_authoritative(
    project_root: Path,
    tmp_path: Path,
) -> None:
    # The figure_source_map gate must treat the registry (figures.yaml) as the source
    # of truth for caption prose: a forged JSON that rewrites the stored caption to
    # satisfy the term check (while keeping every boolean green) must be rejected
    # because the stored caption no longer equals the registry caption.
    ensure_gate_artifacts_for(project_root, "output/data/figure_source_map.json")
    path = project_root / "output" / "data" / "figure_source_map.json"
    backup = tmp_path / "figure_source_map.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    row = next(row for row in payload["rows"] if row["figure_id"] == "policy_posterior_grid")
    row["caption"] = row["caption"] + " Every deterministic row is shown here."
    row["caption_claim_terms_present"] = True
    row["caption_claims_ok"] = True
    row["mapped"] = True
    payload["all_caption_claims_ok"] = True
    payload["all_figures_mapped"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"figure_source_map_schema"})
        assert checks["figure_source_map_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_visualization_audit_rederives_claim_count(
    project_root: Path,
    tmp_path: Path,
) -> None:
    # The visualization audit gate now re-derives caption-claim structure from the
    # registry, so a forged-green audit whose stored claim count disagrees with the
    # registry is rejected on stored booleans alone (defense-in-depth #2).
    ensure_gate_artifacts_for(project_root, "output/reports/visualization_quality_audit.json")
    path = project_root / "output" / "reports" / "visualization_quality_audit.json"
    backup = tmp_path / "visualization_quality_audit.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    row = next(row for row in payload["rows"] if row["figure_id"] == "semantic_gluing_graph")
    row["caption_claim_count"] = 99  # disagrees with the registry's claim count
    row["caption_claims_ok"] = True
    row["ok"] = True
    payload["all_caption_claims_ok"] = True
    payload["all_rows_ok"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"visualization_quality_audit_schema"})
        assert checks["visualization_quality_audit_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


def test_jsonpath_present_rejects_empty_containers() -> None:
    # Defect-2 control: a key that exists but holds an empty container/None must not
    # count as "present" — a zeroed/stale artifact (e.g. {"rows": []}) cannot resolve a
    # caption claim the figure generator itself would refuse to draw. 0/False are kept.
    from roadmap_tracks.integration_audit_artifacts import _jsonpath_present

    assert _jsonpath_present({"rows": [1]}, "$.rows") is True
    assert _jsonpath_present({"rows": []}, "$.rows") is False
    assert _jsonpath_present({"curves": {}}, "$.curves") is False
    assert _jsonpath_present({"x": None}, "$.x") is False
    assert _jsonpath_present({"x": ""}, "$.x") is False
    assert _jsonpath_present({"x": 0}, "$.x") is True
    assert _jsonpath_present({"x": False}, "$.x") is True


def test_asserts_complete_rows_catches_synonyms_and_cross_clause_overclaims() -> None:
    # Defect-4/5 control: completeness overclaims must be caught across the row-unit
    # synonym family and across clause boundaries, while same-clause disclosure and
    # verb collisions ("each edge records a link") must NOT be flagged.
    from roadmap_tracks.integration_audit_artifacts import (
        _asserts_complete_rows,
        _caption_claim_display_transform_ok,
        _normalize_claim_text,
    )

    def flagged(text: str) -> bool:
        return _asserts_complete_rows(_normalize_claim_text(text))

    # synonyms (Defect 4), incl. adjective-filler forms that an early fix let evade
    for overclaim in (
        "all entries are displayed; no entry is omitted",
        "displays every record",
        "all 51 entries are shown",
        "each line of the ledger appears here",
        "the complete set of claims is shown",
        "every single record is rendered",
        "every individual entry is displayed",
        "the complete collection of claims is displayed",
        "the entire list of items is drawn",
        "all rows are visible",
    ):
        assert flagged(overclaim) is True, overclaim
    # cross-clause negation no longer suppresses a real overclaim (Defect 5)
    for overclaim in (
        "figures show no captions, yet all 51 rows are displayed in full",
        "aside from styling, all rows are shown",
    ):
        assert flagged(overclaim) is True, overclaim
    # honest same-clause disclosure / non-matching prose stays legal
    for honest in (
        "not all rows are shown",
        "rather than all rows, a subset is shown",
        "only a subset of rows is shown",
        "the full row-level contract remains in the appendix",
        # determiner-object verb usage: the synonym is a verb, not the unit noun
        "each edge records a declared provenance link",
        "the model claims a result for every observation",
    ):
        assert flagged(honest) is False, honest

    # Gate level: a compacted figure whose caption uses a synonym AS A VERB passes, while
    # a genuine completeness overclaim (incl. cross-sentence) is rejected. The compacted
    # transform requires a disclosure token, which all three inputs carry.
    compacted = {
        "id": "probe",
        "claim_type": "local_deterministic",
        "caption_terms": ["finite toy"],
        "sources": [],
        "source_fields": [],
        "scope": "finite toy",
        "display_transform": "compacted_subset",
    }
    assert _caption_claim_display_transform_ok(
        "Compacted finite toy subset; each edge records a declared provenance link.", [compacted]
    )
    assert not _caption_claim_display_transform_ok(
        "Compacted finite toy subset; every single record is rendered.", [compacted]
    )
    assert not _caption_claim_display_transform_ok(
        "Print-condensed finite toy overview. All entries. Displayed for completeness.", [compacted]
    )


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_visualization_quality_audit_rejects_blank_image(
    project_root: Path,
    tmp_path: Path,
) -> None:
    # Defect-1 control: the audit gate re-opens each PNG, so a genuine-green audit JSON
    # over a blanked image is rejected — image facts cannot pass on stored values alone,
    # including in the selected-only path where no sibling integrity gate re-runs.
    from PIL import Image

    ensure_gate_artifacts_for(project_root, "output/reports/visualization_quality_audit.json")
    path = project_root / "output" / "reports" / "visualization_quality_audit.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    victim = project_root / payload["rows"][0]["output"]
    image_backup = tmp_path / "victim.png"
    image_backup.write_bytes(victim.read_bytes())
    try:
        Image.new("RGB", (1200, 800), "white").save(victim)  # readable but blank
        checks = validate_outputs(project_root, only={"visualization_quality_audit_schema"})
        assert checks["visualization_quality_audit_schema"] is False
    finally:
        victim.write_bytes(image_backup.read_bytes())


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_tmaze_schematic_requires_config_sources(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(project_root, "output/data/figure_source_map.json")
    path = project_root / "output" / "data" / "figure_source_map.json"
    backup = tmp_path / "figure_source_map.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    row = next(row for row in payload["rows"] if row["figure_id"] == "tmaze_schematic")
    row["sources"] = [source for source in row["sources"] if source != "output/data/si_tmaze_summary.json"]
    row["source_path_status"].pop("output/data/si_tmaze_summary.json", None)
    row["source_fields"] = [field for field in row["source_fields"] if "planning_horizon" not in field]
    row["source_field_count"] = len(row["source_fields"])
    row["mapped"] = True
    payload["all_figures_mapped"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"figure_source_map_schema"})
        assert checks["figure_source_map_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_figure_hash_manifest_requires_hashes(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(project_root, "output/reports/figure_hash_manifest.json")
    path = project_root / "output" / "reports" / "figure_hash_manifest.json"
    backup = tmp_path / "figure_hash_manifest.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    payload["rows"][0]["sha256"] = ""
    payload["rows"][0]["size_bytes"] = 1
    payload["all_hashes_present"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"figure_hash_manifest_schema"})
        assert checks["figure_hash_manifest_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_visualization_quality_audit_rejects_overclaiming_row(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(project_root, "output/reports/visualization_quality_audit.json")
    path = project_root / "output" / "reports" / "visualization_quality_audit.json"
    backup = tmp_path / "visualization_quality_audit.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    row = next(row for row in payload["rows"] if row["figure_id"] == "sequential_shift_sensitivity")
    row["caption_overclaim_free"] = False
    row["scope_guard_present"] = False
    row["ok"] = False
    payload["all_caption_overclaims_free"] = True
    payload["all_scope_guards_present"] = True
    payload["all_rows_ok"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"visualization_quality_audit_schema"})
        assert checks["visualization_quality_audit_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_visualization_quality_audit_rejects_caption_claim_row(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(project_root, "output/reports/visualization_quality_audit.json")
    path = project_root / "output" / "reports" / "visualization_quality_audit.json"
    backup = tmp_path / "visualization_quality_audit.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    row = next(row for row in payload["rows"] if row["figure_id"] == "semantic_gluing_graph")
    row["caption_claims_source_bound"] = False
    row["caption_claims_ok"] = False
    row["ok"] = False
    payload["all_caption_claims_ok"] = True
    payload["all_rows_ok"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"visualization_quality_audit_schema"})
        assert checks["visualization_quality_audit_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_visualization_quality_audit_rejects_low_contrast_summary(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(project_root, "output/reports/visualization_quality_audit.json")
    path = project_root / "output" / "reports" / "visualization_quality_audit.json"
    backup = tmp_path / "visualization_quality_audit.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    contrast_row = payload["palette_contrast_report"]["primary_on_paper"]
    contrast_row["ratio"] = 1.0
    contrast_row["passes_aa"] = False
    payload["palette_contrast_ok"] = True
    payload["all_rows_ok"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"visualization_quality_audit_schema"})
        assert checks["visualization_quality_audit_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_visualization_quality_audit_rejects_cover_wording_row(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(project_root, "output/reports/visualization_quality_audit.json")
    path = project_root / "output" / "reports" / "visualization_quality_audit.json"
    backup = tmp_path / "visualization_quality_audit.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    row = next(row for row in payload["rows"] if row["figure_id"] == "graphical_abstract")
    row["claim_wording_ok"] = False
    row["cover_quantitative_free"] = False
    row["accessibility_ok"] = False
    row["ok"] = False
    payload["all_claim_wording_ok"] = True
    payload["all_cover_quantitative_free"] = True
    payload["all_accessibility_metadata_ok"] = True
    payload["all_rows_ok"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"visualization_quality_audit_schema"})
        assert checks["visualization_quality_audit_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_firstprinciples_benchmark_and_statistics_contracts(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(
        project_root,
        "output/data/firstprinciples/empirical_benchmark.json",
        "output/data/firstprinciples/opd_taxonomy.json",
        "output/data/firstprinciples/statistics_demo.json",
        "output/data/firstprinciples/benchmark_table.md",
    )
    empirical_path = project_root / "output" / "data" / "firstprinciples" / "empirical_benchmark.json"
    taxonomy_path = project_root / "output" / "data" / "firstprinciples" / "opd_taxonomy.json"
    statistics_path = project_root / "output" / "data" / "firstprinciples" / "statistics_demo.json"
    table_path = project_root / "output" / "data" / "firstprinciples" / "benchmark_table.md"
    empirical_backup = tmp_path / "empirical_benchmark.json.bak"
    taxonomy_backup = tmp_path / "opd_taxonomy.json.bak"
    statistics_backup = tmp_path / "statistics_demo.json.bak"
    table_backup = tmp_path / "benchmark_table.md.bak"
    empirical_backup.write_text(empirical_path.read_text(encoding="utf-8"), encoding="utf-8")
    taxonomy_backup.write_text(taxonomy_path.read_text(encoding="utf-8"), encoding="utf-8")
    statistics_backup.write_text(statistics_path.read_text(encoding="utf-8"), encoding="utf-8")
    table_backup.write_text(table_path.read_text(encoding="utf-8"), encoding="utf-8")

    try:
        empirical = json.loads(empirical_backup.read_text(encoding="utf-8"))
        empirical["direct_bibkey"] = "thinkingmachines2025opd"
        empirical["source_locator"] = "Qwen3 Technical Report"
        empirical["source_url"] = ""
        empirical["rows"][2]["aime24"] = 70.0
        empirical["thinking_machines_replication"]["aime24_accuracy"] = 0.0
        empirical_path.write_text(json.dumps(empirical, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"firstprinciples_empirical_benchmark_schema"})
        assert checks["firstprinciples_empirical_benchmark_schema"] is False

        empirical_path.write_text(empirical_backup.read_text(encoding="utf-8"), encoding="utf-8")
        taxonomy = json.loads(taxonomy_backup.read_text(encoding="utf-8"))
        taxonomy["methods"] = [
            row for row in taxonomy["methods"] if row["bibkey"] != "chen2026freshness_opd"
        ]
        taxonomy["method_count"] = len(taxonomy["methods"])
        taxonomy["signal_sources"] = [
            source for source in taxonomy["signal_sources"] if source != "freshness_aware_async_buffer"
        ]
        taxonomy_path.write_text(json.dumps(taxonomy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"firstprinciples_taxonomy_schema"})
        assert checks["firstprinciples_taxonomy_schema"] is False

        taxonomy_path.write_text(taxonomy_backup.read_text(encoding="utf-8"), encoding="utf-8")
        statistics = json.loads(statistics_backup.read_text(encoding="utf-8"))
        statistics["sample_size"] = 0
        statistics["paired_permutation"]["n_perm"] = 0
        statistics["effect_size_reference"] = ""
        statistics_path.write_text(json.dumps(statistics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"firstprinciples_statistics_schema"})
        assert checks["firstprinciples_statistics_schema"] is False

        statistics_path.write_text(statistics_backup.read_text(encoding="utf-8"), encoding="utf-8")
        statistics = json.loads(statistics_backup.read_text(encoding="utf-8"))
        statistics["paired_difference"][0] = statistics["paired_difference"][0] + 0.125
        statistics_path.write_text(json.dumps(statistics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"firstprinciples_statistics_schema"})
        assert checks["firstprinciples_statistics_schema"] is False

        statistics_path.write_text(statistics_backup.read_text(encoding="utf-8"), encoding="utf-8")
        statistics = json.loads(statistics_backup.read_text(encoding="utf-8"))
        statistics["teacher_entropy"][0] = statistics["teacher_entropy"][0] + 0.125
        statistics_path.write_text(json.dumps(statistics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"firstprinciples_statistics_schema"})
        assert checks["firstprinciples_statistics_schema"] is False

        statistics_path.write_text(statistics_backup.read_text(encoding="utf-8"), encoding="utf-8")
        table_path.write_text("| metric | value |\n| --- | --- |\n| stale | missing sources |\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"firstprinciples_benchmark_table_present"})
        assert checks["firstprinciples_benchmark_table_present"] is False
    finally:
        empirical_path.write_text(empirical_backup.read_text(encoding="utf-8"), encoding="utf-8")
        taxonomy_path.write_text(taxonomy_backup.read_text(encoding="utf-8"), encoding="utf-8")
        statistics_path.write_text(statistics_backup.read_text(encoding="utf-8"), encoding="utf-8")
        table_path.write_text(table_backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_firstprinciples_classroom_schema(project_root: Path, tmp_path: Path) -> None:
    path = project_root / "output" / "data" / "firstprinciples" / "classroom.json"
    if not path.is_file():
        pytest.skip("classroom artifact missing; run generate_firstprinciples first")
    backup = tmp_path / "classroom.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        payload = json.loads(backup.read_text(encoding="utf-8"))
        payload["privileged_advantage"] = False
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"firstprinciples_classroom_schema"})
        assert checks["firstprinciples_classroom_schema"] is False

        payload = json.loads(backup.read_text(encoding="utf-8"))
        payload["per_step"][0]["student"][0] = 0.0
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs(project_root, only={"firstprinciples_classroom_schema"})
        assert checks["firstprinciples_classroom_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_firstprinciples_sequential_shift_schema(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(project_root, "output/data/firstprinciples/sequential_shift.json")
    path = project_root / "output" / "data" / "firstprinciples" / "sequential_shift.json"
    backup = tmp_path / "sequential_shift.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        path.unlink()
        checks = validate_outputs_selected_strict(project_root, {"firstprinciples_sequential_shift_schema"})
        assert checks["firstprinciples_sequential_shift_schema"] is False

        payload = json.loads(backup.read_text(encoding="utf-8"))
        payload["train_visitation"] = [0.5, 0.5, 0.5, 0.5]
        payload["ok"] = True
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs_selected_strict(project_root, {"firstprinciples_sequential_shift_schema"})
        assert checks["firstprinciples_sequential_shift_schema"] is False

        payload = json.loads(backup.read_text(encoding="utf-8"))
        payload["test_loss_after"] = payload["test_loss_before"]
        payload["on_policy_correction_reduces_test_loss"] = False
        payload["ok"] = True
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs_selected_strict(project_root, {"firstprinciples_sequential_shift_schema"})
        assert checks["firstprinciples_sequential_shift_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_firstprinciples_sequential_shift_sensitivity_schema(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(project_root, "output/data/firstprinciples/sequential_shift_sensitivity.json")
    path = project_root / "output" / "data" / "firstprinciples" / "sequential_shift_sensitivity.json"
    backup = tmp_path / "sequential_shift_sensitivity.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        path.unlink()
        checks = validate_outputs_selected_strict(
            project_root,
            {"firstprinciples_sequential_shift_sensitivity_schema"},
        )
        assert checks["firstprinciples_sequential_shift_sensitivity_schema"] is False

        payload = json.loads(backup.read_text(encoding="utf-8"))
        payload["rows"][1]["test_loss"] = payload["rows"][0]["test_loss"] + 1.0
        payload["rows"][1]["student_induced_test_loss"] = payload["rows"][1]["test_loss"]
        payload["ok"] = True
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs_selected_strict(
            project_root,
            {"firstprinciples_sequential_shift_sensitivity_schema"},
        )
        assert checks["firstprinciples_sequential_shift_sensitivity_schema"] is False

        payload = json.loads(backup.read_text(encoding="utf-8"))
        payload["rows"][0]["student_test_visitation"] = [0.5, 0.5, 0.5, 0.5]
        payload["ok"] = True
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs_selected_strict(
            project_root,
            {"firstprinciples_sequential_shift_sensitivity_schema"},
        )
        assert checks["firstprinciples_sequential_shift_sensitivity_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_figure_source_map_requires_sequential_shift_source(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(project_root, "output/data/figure_source_map.json")
    path = project_root / "output" / "data" / "figure_source_map.json"
    backup = tmp_path / "figure_source_map.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    row = next(row for row in payload["rows"] if row["figure_id"] == "sequential_shift_recovery")
    row["sources"] = []
    row["source_path_status"] = {}
    row["source_fields"] = []
    row["source_field_count"] = 0
    row["validation_gates"] = []
    row["validation_gate_count"] = 0
    row["mapped"] = True
    payload["all_figures_mapped"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs_selected_strict(project_root, {"figure_source_map_schema"})
        assert checks["figure_source_map_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


@pytest.mark.timeout(300)
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_negative_figure_source_map_requires_sequential_sensitivity_source(
    project_root: Path,
    tmp_path: Path,
) -> None:
    ensure_gate_artifacts_for(project_root, "output/data/figure_source_map.json")
    path = project_root / "output" / "data" / "figure_source_map.json"
    backup = tmp_path / "figure_source_map.json.bak"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    payload = json.loads(backup.read_text(encoding="utf-8"))
    row = next(row for row in payload["rows"] if row["figure_id"] == "sequential_shift_sensitivity")
    row["sources"] = ["output/data/firstprinciples/sequential_shift.json"]
    row["source_path_status"] = {"output/data/firstprinciples/sequential_shift.json": True}
    row["source_fields"] = ["$.test_loss_before", "$.test_loss_after"]
    row["source_field_count"] = len(row["source_fields"])
    row["validation_gates"] = ["validate_outputs.firstprinciples_sequential_shift_schema"]
    row["validation_gate_count"] = len(row["validation_gates"])
    row["mapped"] = True
    payload["all_figures_mapped"] = True
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checks = validate_outputs_selected_strict(project_root, {"figure_source_map_schema"})
        assert checks["figure_source_map_schema"] is False
    finally:
        path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
