"""Tests for pymdp.yaml configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from simulation.pymdp_config import (
    apply_pymdp_overrides,
    config_hash,
    load_pymdp_config,
)


def test_load_default_pymdp_config(project_root: Path) -> None:
    cfg = load_pymdp_config(project_root)
    assert cfg.profile == "full_tmaze_sophisticated_inference"
    assert cfg.planner == "sophisticated_inference"
    assert cfg.planning_horizon == 5
    assert cfg.timesteps == 6
    assert cfg.policy_len == 1
    assert cfg.environment.reward_condition == 0
    assert cfg.environment.cue_validity == pytest.approx(0.95)
    assert cfg.environment.reward_probability == pytest.approx(1.0)
    assert cfg.environment.dependent_outcomes is True
    assert cfg.si_search.horizon == 5
    assert cfg.si_search.max_nodes == 5000
    assert cfg.si_search.max_branching == 45
    assert cfg.si_search.observation_prune_threshold == pytest.approx(1e-4)
    assert cfg.validation_comparison.enabled is True
    assert cfg.validation_comparison.planners == ("sophisticated_inference", "vanilla")


def test_apply_overrides(project_root: Path) -> None:
    cfg = load_pymdp_config(project_root)
    updated = apply_pymdp_overrides(cfg, steps=6, horizon=3, seed=42, comparison_enabled=False)
    assert updated.timesteps == 6
    assert updated.planning_horizon == 3
    assert updated.si_search.horizon == 3
    assert updated.random_seed == 42
    assert updated.planner == "sophisticated_inference"
    assert updated.validation_comparison.enabled is False


def test_config_hash_stable(project_root: Path) -> None:
    cfg = load_pymdp_config(project_root)
    assert config_hash(cfg) == config_hash(load_pymdp_config(project_root))
    changed = apply_pymdp_overrides(cfg, horizon=cfg.planning_horizon + 1)
    assert config_hash(cfg) != config_hash(changed)


def test_custom_yaml(tmp_path: Path) -> None:
    custom = tmp_path / "custom_pymdp.yaml"
    custom.write_text(
        "\n".join(
            [
                "profile: full_tmaze_sophisticated_inference",
                "planner: sophisticated_inference",
                "planning_horizon: 4",
                "timesteps: 3",
                "random_seed: 7",
                "environment:",
                "  cue_validity: 0.95",
                "si_search:",
                "  horizon: 4",
                "validation_comparison:",
                "  enabled: false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    cfg = load_pymdp_config(tmp_path, config_path=custom)
    assert cfg.planning_horizon == 4
    assert cfg.timesteps == 3
    assert cfg.random_seed == 7
    assert cfg.planner == "sophisticated_inference"
    assert cfg.validation_comparison.enabled is False


def test_pymdp_config_rejects_invalid_planner(tmp_path: Path) -> None:
    bad = tmp_path / "pymdp.yaml"
    bad.write_text("planner: vanilla\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported canonical pymdp planner"):
        load_pymdp_config(tmp_path, config_path=bad)


def test_pymdp_config_rejects_legacy_state_inference_mode(tmp_path: Path) -> None:
    bad = tmp_path / "pymdp.yaml"
    bad.write_text("mode: state_inference\n", encoding="utf-8")
    with pytest.raises(ValueError, match="legacy pymdp mode"):
        load_pymdp_config(tmp_path, config_path=bad)
