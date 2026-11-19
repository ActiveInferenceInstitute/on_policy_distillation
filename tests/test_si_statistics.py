"""Tests for simulation and analysis statistics."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis import summarize_sweep, write_analysis_statistics
from simulation.statistics import summarize_si_trace


def test_summarize_si_trace_from_fixture() -> None:
    trace = {
        "steps": [
            {"step": 0, "belief_entropy": 0.5, "action": 0, "obs": 0},
            {"step": 1, "belief_entropy": 0.2, "action": 0, "obs": 1},
        ]
    }
    summary = {
        "steps": 2,
        "actions": [0, 0],
        "action_names": ["move_to_cue", "move_to_center"],
        "action_probabilities": [
            {"move_to_cue": 0.75, "move_to_center": 0.25},
            {"move_to_cue": 0.05, "move_to_center": 0.95},
        ],
        "q_pi_entropy_by_step": [0.8, 0.1],
        "observations": [0, 1],
        "observations_by_modality": {"cue": [0, 1], "outcome": [0, 0]},
        "config": {"tmaze": {"num_obs": 2}},
    }
    stats = summarize_si_trace(trace, summary)
    assert stats["steps"] == 2
    assert stats["action_diversity"] == 1
    assert stats["goal_reached"] is True
    assert stats["entropy_min"] == pytest.approx(0.2)
    assert stats["entropy_max"] == pytest.approx(0.5)
    assert stats["policy_entropy_min"] == pytest.approx(0.1)
    assert stats["policy_entropy_mean"] == pytest.approx(0.45)
    assert stats["initial_selected_action_name"] == "move_to_cue"
    assert stats["initial_cue_probability"] == pytest.approx(0.75)
    assert stats["cue_observed_step"] == 1
    assert stats["reward_observed_step"] is None
    assert stats["cue_before_reward"] is False
    assert stats["policy_entropy_drop_after_cue"] == pytest.approx(0.7)


@pytest.mark.parametrize("cue_id", [1, 2], ids=["cue_left", "cue_right"])
@pytest.mark.parametrize(
    ("outcomes", "expected_reward_step"),
    [([0, 0, 2], None), ([0, 0, 2, 1], 3)],
    ids=["punishment_only", "punishment_then_reward"],
)
def test_reward_timing_ignores_punishment(cue_id: int, outcomes: list[int], expected_reward_step: int | None) -> None:
    summary = {
        "observations_by_modality": {
            "cue": [0, cue_id] + [0] * (len(outcomes) - 2),
            "outcome": outcomes,
        }
    }

    stats = summarize_si_trace({"steps": []}, summary)

    assert stats["cue_observed_step"] == 1
    assert stats["reward_observed_step"] == expected_reward_step
    assert stats["cue_before_reward"] is (expected_reward_step is not None)


@pytest.mark.parametrize("cue_id", [1, 2], ids=["cue_left", "cue_right"])
def test_reward_before_cue_is_not_cue_before_reward(cue_id: int) -> None:
    summary = {"observations_by_modality": {"cue": [0, 0, cue_id], "outcome": [0, 1, 0]}}

    stats = summarize_si_trace({"steps": []}, summary)

    assert stats["cue_observed_step"] == 2
    assert stats["reward_observed_step"] == 1
    assert stats["cue_before_reward"] is False


def test_summarize_sweep(tmp_path: Path) -> None:
    csv_path = tmp_path / "parameter_sweep.csv"
    csv_path.write_text(
        "lambda,closed_form_mi,empirical_mi\n0.0,0.0,0.01\n1.0,0.5,0.48\n",
        encoding="utf-8",
    )
    stats = summarize_sweep(csv_path)
    assert stats["grid_points"] == 2
    assert stats["max_residual"] == pytest.approx(0.02)
    assert stats["rmse_mi"] > 0.0


@pytest.mark.render_slow
@pytest.mark.artifact_slow
@pytest.mark.mutates_artifacts
def test_write_analysis_statistics(project_root: Path, tmp_path: Path) -> None:
    from analysis import run_analysis
    from simulation.si_runner import pymdp_available, run_and_persist

    run_analysis(project_root)
    if pymdp_available():
        run_and_persist(project_root)
    out = write_analysis_statistics(project_root)
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "sweep" in payload
    assert "si_tmaze" in payload
    assert payload["pymdp_profile"] == "full_tmaze_sophisticated_inference"
    assert payload["pymdp_planner"] == "sophisticated_inference"
    assert payload["pymdp_config_hash"]
    assert payload["si_tmaze_q_pi_row_count"] >= 1
    assert payload["si_tmaze_action_probability_row_count"] >= 1
    assert payload["si_tmaze_observation_modality_count"] == 3
    assert payload["si_tmaze_tree_available"] is True
    assert payload["si_tmaze"]["initial_cue_probability"] >= 0.0
    assert payload["si_tmaze"]["policy_entropy_mean"] >= 0.0
    assert "cue_before_reward" in payload["si_tmaze"]
    assert "policy_entropy_drop_after_cue" in payload["si_tmaze"]
    assert "pymdp_mode" not in payload
