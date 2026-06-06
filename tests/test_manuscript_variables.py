from pathlib import Path
import subprocess
import sys

import pytest

from manuscript import variables as manuscript_variables
from manuscript.variables import generate_variables

# test_generate_manuscript_variables_reaches_semantic_fixed_point iterates the full
# variable/semantic fixed point (~42s locally); widen the per-test ceiling so slower CI
# runners don't trip the CI-wide --timeout=120.
pytestmark = pytest.mark.timeout(300)


def test_generate_variables_with_outputs() -> None:
    root = Path(__file__).resolve().parents[1]
    vars_ = generate_variables(root, require_analysis_outputs=False)
    assert vars_["project_name"] == root.name
    assert vars_["lambda_grid_points"] >= 2
    assert vars_["bernoulli_state_count"] == 2
    assert vars_["gnn_spec_version"] == "GNN v1.1"
    assert vars_["pipeline_track_count"] == 30
    assert vars_["sheaf_track_count"] == 33
    assert vars_["lean_graph_world_topology_witness_count"] >= 3
    assert vars_["lean_graph_world_all_topologies_witnessed"] is True
    assert vars_["scholarship_source_count"] >= 8
    assert vars_["scholarship_sources_connected"] is True
    assert vars_["opd_taxonomy_method_count"] >= 8
    assert vars_["hardcoded_variables_all_auto_injected"] is True
    assert vars_["hardcoded_variable_issue_count"] == 0
    assert float(vars_["divergence_reverse_kl"]) >= 0.0
    assert float(vars_["exposure_bias_terminal_gap"]) > 0.0
    assert vars_["classroom_teacher_cue_validity"] >= vars_["classroom_student_cue_validity"]
    assert float(vars_["classroom_mean_reverse_kl_formatted"]) >= 0.0
    assert vars_["classroom_step_count"] >= 1
    assert vars_["pymdp_profile"] == "full_tmaze_sophisticated_inference"
    assert vars_["pymdp_planner"] == "sophisticated_inference"
    assert vars_["si_tmaze_profile"] == "full_tmaze_sophisticated_inference"
    assert vars_["si_tmaze_planner"] == "sophisticated_inference"
    assert vars_["si_tmaze_q_pi_row_count"] >= 1
    assert vars_["si_tmaze_action_probability_row_count"] >= 1
    assert vars_["si_tmaze_observation_modality_count"] == 3
    assert vars_["si_tree_available"] == 1
    assert vars_["pymdp_config_hash"]
    assert "pymdp_mode" not in vars_


def test_invariant_counts_include_simulation_when_merged() -> None:
    root = Path(__file__).resolve().parents[1]
    inv_path = root / "output" / "reports" / "invariants.json"
    if not inv_path.is_file():
        from analysis import run_analysis

        run_analysis(root)
    if not inv_path.is_file():
        pytest.skip("invariants report missing")

    import json

    payload = json.loads(inv_path.read_text(encoding="utf-8"))
    simulation = payload.get("simulation") or {}
    if not simulation:
        pytest.skip("simulation invariants not merged; run simulate_si_tmaze")

    vars_ = generate_variables(root, require_analysis_outputs=False)
    expected_total = len(payload.get("invariants") or {}) + len(simulation)
    expected_passed = sum(1 for value in (payload.get("invariants") or {}).values() if value) + sum(
        1 for value in simulation.values() if value
    )
    assert vars_["invariants_total"] == expected_total
    assert vars_["invariants_passed"] == expected_passed


def test_invariant_counts_fall_back_to_si_invariants(project_root: Path, tmp_path: Path) -> None:
    import json

    inv_path = project_root / "output" / "reports" / "invariants.json"
    si_inv_path = project_root / "output" / "reports" / "si_invariants.json"
    if not inv_path.is_file() or not si_inv_path.is_file():
        pytest.skip("invariant reports missing; run analysis first")

    inv_backup = tmp_path / "invariants.json.bak"
    inv_backup.write_text(inv_path.read_text(encoding="utf-8"), encoding="utf-8")
    si_backup = tmp_path / "si_invariants.json.bak"
    si_backup.write_text(si_inv_path.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        analytical_only = {
            "invariants": json.loads(inv_backup.read_text(encoding="utf-8")).get("invariants") or {},
            "all_pass": True,
        }
        inv_path.write_text(json.dumps(analytical_only), encoding="utf-8")
        si_data = json.loads(si_backup.read_text(encoding="utf-8"))
        si_invariants = si_data.get("invariants") or {}
        vars_ = generate_variables(project_root, require_analysis_outputs=False)
        expected_total = len(analytical_only["invariants"]) + len(si_invariants)
        expected_passed = sum(1 for value in analytical_only["invariants"].values() if value) + sum(
            1 for value in si_invariants.values() if value
        )
        assert vars_["invariants_total"] == expected_total
        assert vars_["invariants_passed"] == expected_passed
    finally:
        inv_path.write_text(inv_backup.read_text(encoding="utf-8"), encoding="utf-8")


def test_ising_mi_saturation_from_sweep() -> None:
    root = Path(__file__).resolve().parents[1]
    import csv

    sweep_path = root / "output" / "data" / "parameter_sweep.csv"
    if not sweep_path.is_file():
        from analysis import run_analysis

        run_analysis(root)
    rows = list(csv.DictReader(sweep_path.open(newline="", encoding="utf-8")))
    expected = max(float(row["closed_form_mi"]) for row in rows)
    vars_ = generate_variables(root, require_analysis_outputs=False)
    assert abs(float(vars_["ising_mi_saturation"]) - expected) < 1e-12


def test_variable_helpers_handle_missing_optional_inputs(tmp_path: Path) -> None:
    assert manuscript_variables._ising_mi_saturation_from_sweep([]) == 0.0
    assert manuscript_variables._load_json(tmp_path / "missing.json") == {}
    assert manuscript_variables._pipeline_track_count(tmp_path) == 0
    assert manuscript_variables._gnn_spec_version(tmp_path) == ""


def test_gnn_spec_version_skips_blank_lines_after_header(tmp_path: Path) -> None:
    gnn_dir = tmp_path / "gnn"
    gnn_dir.mkdir()
    (gnn_dir / "bernoulli_toy.gnn.md").write_text(
        "# Model\n\n## GNNVersionAndFlags\n\nGNN v9.9\n",
        encoding="utf-8",
    )
    assert manuscript_variables._gnn_spec_version(tmp_path) == "GNN v9.9"


def test_generate_variables_requires_analysis_outputs(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing analysis artifact"):
        generate_variables(tmp_path, require_analysis_outputs=True)


def test_generate_manuscript_variables_reaches_semantic_fixed_point(project_root: Path) -> None:
    """The hydration entry point must leave semantic/sheaf validators converged."""
    from manuscript.sheaf.semantic import validate_semantic_gluing
    from roadmap_tracks import validate_sheaf_track_artifacts

    result = subprocess.run(
        [sys.executable, "scripts/z_generate_manuscript_variables.py"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert validate_semantic_gluing(project_root) == []
    assert validate_sheaf_track_artifacts(project_root) == []


def test_hardcoded_variable_audit_flags_literal_generated_value(project_root: Path) -> None:
    """A generated value typed into source prose must fail the auto-injection audit."""
    from manuscript.hydrate import format_variables
    from roadmap_tracks.integration_audit import build_hardcoded_variable_audit

    vars_ = generate_variables(project_root, require_analysis_outputs=False)
    formatted = format_variables(vars_)
    literal = formatted.get("pymdp_config_hash")
    if not literal:
        pytest.skip("pymdp config hash unavailable")

    path = project_root / "manuscript" / "sections" / "imrad" / "intro_motivation" / "prose.md"
    original = path.read_text(encoding="utf-8")
    try:
        clean = build_hardcoded_variable_audit(project_root)
        assert clean["all_values_auto_injected"] is True
        path.write_text(original + f"\nHard-coded generated hash {literal}.\n", encoding="utf-8")
        drifted = build_hardcoded_variable_audit(project_root)
        assert drifted["all_values_auto_injected"] is False
        assert any(issue["token"] == "pymdp_config_hash" for issue in drifted["issues"])
    finally:
        path.write_text(original, encoding="utf-8")
