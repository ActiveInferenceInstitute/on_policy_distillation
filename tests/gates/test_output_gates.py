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
