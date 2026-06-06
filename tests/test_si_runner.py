import json
import subprocess
import sys

import pytest

from simulation.logging_utils import RunLogger
from simulation.pymdp_config import apply_pymdp_overrides, load_pymdp_config
from simulation.si_runner import pymdp_available, run_and_persist, run_si_tmaze, write_si_artifacts
from simulation.tmaze_model import build_tmaze_generative_model


def test_tmaze_model_shapes() -> None:
    model = build_tmaze_generative_model()
    assert [tuple(factor.shape) for factor in model["A"]] == [(5, 5), (3, 5, 2), (3, 5, 2)]
    assert [tuple(factor.shape) for factor in model["B"]] == [(5, 5, 5), (2, 2, 1)]
    assert model["profile"] == "full_tmaze_sophisticated_inference"
    assert model["environment_class"] == "TMaze"
    assert model["labels"]["actions"][3] == "move_to_cue"
    assert model["dependencies"]["A"] == [[0], [0, 1], [0, 1]]
    assert model["dependencies"]["B"] == [[0], [1]]
    assert all(check["normalized"] for check in model["normalization_checks"])
    assert int(model["policy_len"]) == 1


def test_tmaze_model_uses_config_likelihood(project_root) -> None:
    cfg = apply_pymdp_overrides(load_pymdp_config(project_root), horizon=4)
    model = build_tmaze_generative_model(cfg)
    cue_tensor = model["A"][2]
    assert float(cue_tensor[1, 3, 0]) == pytest.approx(cfg.environment.cue_validity)
    assert float(cue_tensor[2, 3, 1]) == pytest.approx(cfg.environment.cue_validity)


@pytest.mark.requires_pymdp
def test_si_tmaze_rollout(project_root, tmp_path) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    cfg = apply_pymdp_overrides(load_pymdp_config(project_root), seed=123)
    logger = RunLogger(tmp_path / "log.jsonl")
    logger.fresh()
    result = run_si_tmaze(project_root, config=cfg, logger=logger)
    assert result.profile == "full_tmaze_sophisticated_inference"
    assert result.planner == "sophisticated_inference"
    assert result.steps == 5
    assert len(result.actions) == 6
    assert len(result.observations_by_modality) == 3
    assert all(len(values) == 6 for values in result.observations_by_modality.values())
    assert result.policy_len == 1
    assert result.planning_horizon == 4
    assert result.num_policies == 5
    assert result.config_hash
    assert result.goal_reached
    assert result.tree_available is True
    assert result.tree_stats["available"] is True
    assert result.action_probabilities[0]["move_to_cue"] == max(result.action_probabilities[0].values())
    assert result.action_probabilities[0]["move_to_cue"] > 0.5
    assert all(abs(sum(row) - 1.0) < 1e-6 for row in result.q_pi_by_step)
    assert logger.records()[0]["event"] == "si_tmaze_run_header"
    step_record = logger.step_records()[0]
    assert step_record["planner"] == "sophisticated_inference"
    assert step_record["config_hash"] == result.config_hash
    assert "q_pi" in step_record
    assert "action_probabilities" in step_record
    assert set(step_record["observations_by_modality"]) == {"location", "outcome", "cue"}


@pytest.mark.requires_pymdp
def test_write_si_artifacts_schema(project_root, tmp_path) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    cfg = load_pymdp_config(project_root)
    logger = RunLogger(tmp_path / "log.jsonl", enabled=False)
    result = run_si_tmaze(project_root, config=cfg, steps=2, logger=logger)
    paths = write_si_artifacts(project_root, result, config=cfg)
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    trace = json.loads(paths["trace"].read_text(encoding="utf-8"))
    matrices = json.loads(paths["model_matrices"].read_text(encoding="utf-8"))
    report = json.loads(paths["run_report"].read_text(encoding="utf-8"))
    assert summary["profile"] == "full_tmaze_sophisticated_inference"
    assert summary["planner"] == "sophisticated_inference"
    assert "mode" not in summary
    assert summary["validation_comparison"]["vanilla_role"] == "comparison_only"
    assert summary["tree_available"] is True
    assert summary["expected_known_warnings"]["tree_max_nodes"] >= 1
    assert len(trace["steps"]) == len(summary["actions"])
    assert trace["steps"][0]["action_probabilities"]["move_to_cue"] == max(
        trace["steps"][0]["action_probabilities"].values()
    )
    assert matrices["A_shapes"] == [[5, 5], [3, 5, 2], [3, 5, 2]]
    assert matrices["B_shapes"] == [[5, 5, 5], [2, 2, 1]]
    assert matrices["environment"]["cue_validity"] == pytest.approx(0.95)
    assert report["log_record_count"] >= 0


@pytest.mark.requires_pymdp
def test_canonical_run_rejects_legacy_mode_override(project_root) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    with pytest.raises(TypeError):
        apply_pymdp_overrides(load_pymdp_config(project_root), mode="policy_inference")  # type: ignore[call-arg]


def test_simulate_cli_help(project_root) -> None:
    script = project_root / "scripts" / "simulate_si_tmaze.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "--seed" in proc.stdout
    assert "--comparison" in proc.stdout
    assert "--mode" not in proc.stdout


@pytest.mark.requires_pymdp
def test_run_and_persist(project_root) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    payload = run_and_persist(project_root)
    assert payload["paths"]["summary"].exists()
