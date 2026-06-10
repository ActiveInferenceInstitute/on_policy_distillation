"""Tests for simulation invariants and logging schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from simulation.invariants import run_simulation_invariants, write_simulation_invariants
from simulation.logging_utils import RunLogger, validate_record
from simulation.si_runner import pymdp_available, run_and_persist

# test_validate_outputs_gate_checks rebuilds the full gate-artifact bundle (~56s locally);
# give this module a wider per-test ceiling so slower CI runners don't trip --timeout=120.
pytestmark = pytest.mark.timeout(300)


def test_validate_record_requires_step_keys() -> None:
    with pytest.raises(ValueError, match="missing keys"):
        validate_record({"event": "si_tmaze_step", "step": 0})


def test_run_logger_header_schema(tmp_path: Path) -> None:
    log = RunLogger(tmp_path / "runs.jsonl")
    log.fresh()
    log.emit_run_header(
        config_hash="abc",
        planner="sophisticated_inference",
        profile="full_tmaze_sophisticated_inference",
        seed=0,
        policy_len=1,
        planning_horizon=4,
    )
    record = log.records()[0]
    assert record["event"] == "si_tmaze_run_header"
    assert record["config_hash"] == "abc"
    assert record["planner"] == "sophisticated_inference"


@pytest.mark.requires_pymdp
@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_simulation_invariants_after_run(project_root: Path) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    run_and_persist(project_root)
    results = run_simulation_invariants(project_root)
    assert all(results.values())
    assert "si_tree_available" in results
    assert "q_pi_rows_normalized" in results
    assert "model_matrices_full_tmaze" in results
    out = write_simulation_invariants(project_root)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["all_pass"] is True


@pytest.mark.requires_pymdp
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_validate_outputs_gate_checks(project_root: Path) -> None:
    from gates.validation import validate_outputs
    from simulation.si_artifacts import write_policy_comparison, write_policy_posterior_grid

    if not pymdp_available():
        pytest.skip("pymdp not installed")
    run_and_persist(project_root)
    write_policy_comparison(project_root)
    write_policy_posterior_grid(project_root)
    checks = validate_outputs(
        project_root,
        only={
            "si_trace_present",
            "si_summary_schema",
            "si_tmaze_model_matrices_schema",
            "pymdp_policy_posterior_grid_schema",
        },
    )
    assert checks.get("si_trace_present")
    assert checks.get("si_summary_schema")
    assert checks.get("si_tmaze_model_matrices_schema")
    assert checks.get("pymdp_policy_posterior_grid_schema")
