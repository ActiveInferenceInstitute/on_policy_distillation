"""Real SI persistence, effective-config and root-custody regressions."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from orchestration.artifact_lock import artifact_lease
from simulation.invariants import run_simulation_invariants
from simulation.pymdp_config import (
    PymdpConfig,
    apply_pymdp_overrides,
    config_hash,
    config_snapshot,
    default_pymdp_config,
    load_pymdp_config,
)
from simulation.si_artifacts import (
    run_and_persist,
    write_policy_comparison,
    write_policy_posterior_grid,
    write_si_artifacts,
)
from simulation.si_loop import SIRunResult, pymdp_available
from simulation.statistics import summarize_si_trace
from simulation.tmaze_model import ACTION_LABELS, CUE_LABELS, LOCATION_LABELS, OUTCOME_LABELS


def _payload_hash(payload: dict[str, Any], *, length: int | None = None) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return digest if length is None else digest[:length]


def _finite_result(
    config: PymdpConfig,
    entropies: tuple[float, ...] = (1.2, 0.8, 0.2),
    outcomes: tuple[int, ...] = (0, 0, 1),
) -> SIRunResult:
    """Finite persistence fixture, not a claim that an SI rollout was measured."""
    count = len(entropies)
    assert count == len(outcomes) == config.timesteps + 1
    locations = [0, 3, 2, 1][:count]
    actions = [3, 2, 1, 0][:count]
    observations = {"location": locations, "outcome": list(outcomes), "cue": [0, 1, 0, 0][:count]}
    label_maps = {"location": LOCATION_LABELS, "outcome": OUTCOME_LABELS, "cue": CUE_LABELS}
    observation_names = {
        modality: [label_maps[modality][value] for value in values] for modality, values in observations.items()
    }
    q_pi = [[0.2] * 5 for _ in entropies]
    probabilities = [{ACTION_LABELS[action]: 0.2 for action in range(5)} for _ in entropies]
    traces = [
        {
            "step": step,
            "belief_entropy": entropy,
            "observations_by_modality": {modality: values[step] for modality, values in observations.items()},
            "q_pi": q_pi[step],
            "q_pi_sum": 1.0,
            "q_pi_entropy": math.log(5),
            "q_pi_normalized": True,
            "selected_action": actions[step],
            "selected_action_name": ACTION_LABELS[actions[step]],
            "action_probabilities": probabilities[step],
            "config_hash": config_hash(config),
        }
        for step, entropy in enumerate(entropies)
    ]
    reward_observed = 1 in outcomes
    return SIRunResult(
        steps=config.timesteps,
        policy_len=config.policy_len,
        planning_horizon=config.planning_horizon,
        num_policies=5,
        mean_belief_entropy=sum(entropies) / count,
        actions=actions,
        action_names=[ACTION_LABELS[action] for action in actions],
        action_vectors=[[action, 0] for action in actions],
        observations=locations,
        observations_by_modality=observations,
        observation_names_by_modality=observation_names,
        q_pi_by_step=q_pi,
        q_pi_entropy_by_step=[math.log(5)] * count,
        action_probabilities=probabilities,
        planner=config.planner,
        profile=config.profile,
        config_hash=config_hash(config),
        goal_reached=reward_observed,
        reward_observed=reward_observed,
        action_diversity=len(set(actions)),
        tree_available=False,
        tree_stats={"available": False},
        trace_steps=traces,
    )


@pytest.mark.requires_pymdp
@pytest.mark.parametrize("trace_argument", ["omitted", "none", "explicit"])
@pytest.mark.parametrize(
    ("entropies", "outcomes", "non_increasing", "reward_step"),
    [
        ((1.2, 0.8, 0.2), (0, 0, 1), True, 2),
        ((0.2, 0.8, 1.2), (0, 0, 1), False, 2),
        ((1.2, 0.8, 0.2), (0, 0, 2), True, None),
        ((1.2, 0.8, 0.4, 0.2), (0, 0, 2, 1), True, 3),
    ],
    ids=["decreasing", "increasing", "punishment_only", "punishment_then_reward"],
)
def test_write_si_artifacts_resolves_trace_once(
    tmp_path: Path,
    trace_argument: str,
    entropies: tuple[float, ...],
    outcomes: tuple[int, ...],
    non_increasing: bool,
    reward_step: int | None,
) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    config = apply_pymdp_overrides(default_pymdp_config(), steps=len(entropies) - 1, logging_enabled=False)
    result = _finite_result(config, entropies, outcomes)
    kwargs: dict[str, Any] = {}
    if trace_argument != "omitted":
        kwargs["trace_steps"] = None if trace_argument == "none" else result.trace_steps
    with artifact_lease(tmp_path):
        paths = write_si_artifacts(tmp_path, result, config=config, **kwargs)
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    trace = json.loads(paths["trace"].read_text(encoding="utf-8"))
    assert trace["steps"] == result.trace_steps
    assert summary["belief_entropy_start"] == entropies[0]
    assert summary["belief_entropy_end"] == entropies[-1]
    assert summary["belief_entropy_non_increasing"] is non_increasing
    assert summary["config_hash"] == trace["config_hash"] == config_hash(config)
    stats = summarize_si_trace(trace, summary)
    assert stats["entropy_mean"] == pytest.approx(result.mean_belief_entropy)
    assert stats["reward_observed_step"] == reward_step
    assert stats["cue_before_reward"] is (reward_step is not None)
    assert all(math.isfinite(stats[key]) for key in ("entropy_min", "entropy_max", "entropy_mean"))
    invariants = run_simulation_invariants(tmp_path)
    assert invariants["trace_step_count_matches_summary"] is True
    assert invariants["q_pi_rows_normalized"] is True
    assert invariants["model_matrices_full_tmaze"] is True
    assert invariants["si_tree_available"] is False
    report = json.loads((tmp_path / "output/reports/si_invariants.json").read_text(encoding="utf-8"))
    assert report["all_pass"] is False


@pytest.mark.requires_pymdp
def test_write_si_artifacts_preserves_explicit_empty_trace(tmp_path: Path) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    config = apply_pymdp_overrides(default_pymdp_config(), steps=2, logging_enabled=False)
    result = _finite_result(config)
    paths = write_si_artifacts(tmp_path, result, config=config, trace_steps=[])
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    trace = json.loads(paths["trace"].read_text(encoding="utf-8"))
    assert result.trace_steps
    assert trace["steps"] == []
    assert summary["belief_entropy_start"] is None
    assert summary["belief_entropy_end"] is None
    assert summary["belief_entropy_non_increasing"] is False
    invariants = run_simulation_invariants(tmp_path)
    assert invariants["trace_step_count_matches_summary"] is False
    assert invariants["q_pi_rows_normalized"] is False
    assert json.loads((tmp_path / "output/reports/si_invariants.json").read_text(encoding="utf-8"))["all_pass"] is False


def _alternate_config(root: Path, *, logging_enabled: bool) -> PymdpConfig:
    default = default_pymdp_config()
    (root / "pymdp.yaml").write_text(yaml.safe_dump(config_snapshot(default)), encoding="utf-8")
    alternate = replace(
        default,
        planning_horizon=3,
        timesteps=3,
        random_seed=11,
        environment=replace(default.environment, cue_validity=0.8),
        agent=replace(default.agent, vanilla_policy_len=3),
        si_search=replace(default.si_search, horizon=3),
        logging=replace(default.logging, enabled=True, path="output/custom_logs/canonical.jsonl"),
        validation_comparison=replace(default.validation_comparison, seeds=(7,)),
    )
    path = root / "alternate.yaml"
    path.write_text(yaml.safe_dump(config_snapshot(alternate)), encoding="utf-8")
    return apply_pymdp_overrides(
        load_pymdp_config(root, config_path=path), steps=2, horizon=2, seed=19, logging_enabled=logging_enabled
    )


def _assert_comparison_grid(config: PymdpConfig, comparison: dict[str, Any], grid: dict[str, Any]) -> None:
    assert comparison["config"] == grid["config"] == config_snapshot(config)
    assert comparison["config_hash"] == grid["config_hash"] == config_hash(config)
    assert grid["source_payload_sha256"] == _payload_hash(comparison)
    assert grid["row_count"] == sum(len(run["policy_posterior_steps"]) for run in comparison["runs"])
    assert grid["all_available_posteriors_normalized"] is True
    for index, run in enumerate(comparison["runs"]):
        run_config = run["config"]
        assert run["config_hash"] == _payload_hash(run_config, length=16)
        assert run_config["random_seed"] == run["seed"]
        assert run_config["planning_horizon"] == run_config["si_search"]["horizon"] == run["horizon"] == 2
        assert run_config["timesteps"] == run["steps"] == 2
        assert run_config["environment"] == config_snapshot(config)["environment"]
        assert run_config["logging"]["enabled"] is config.logging.enabled
        assert run["policy_len"] == (1 if run["planner"] == "sophisticated_inference" else 2)
        expected = apply_pymdp_overrides(config, seed=run["seed"])
        expected = replace(expected, logging=replace(expected.logging, path=run_config["logging"]["path"]))
        assert run_config == config_snapshot(expected)
        assert run["config_hash"] == config_hash(expected)
        projected = [row for row in grid["rows"] if row["run_index"] == index]
        assert len(projected) == len(run["policy_posterior_steps"]) == 3
        for step, row in zip(run["policy_posterior_steps"], projected, strict=True):
            assert (row["seed"], row["horizon"], row["steps"], row["config_hash"]) == (
                run["seed"],
                run["horizon"],
                run["steps"],
                run["config_hash"],
            )
            for key in ("step", "q_pi", "q_pi_entropy", "action_probabilities", "posterior_source", "fallback_reason"):
                assert row[key] == step[key]
            assert row["q_pi_sum"] == pytest.approx(sum(step["q_pi"]))
            assert row["normalized"] is True


@pytest.mark.requires_pymdp
@pytest.mark.render_slow
@pytest.mark.parametrize(
    ("logging_enabled", "explicit_seeds"), [(False, None), (True, (13,))], ids=["configured_seeds", "explicit_seeds"]
)
def test_comparison_and_grid_preserve_effective_config(
    tmp_path: Path, logging_enabled: bool, explicit_seeds: tuple[int, ...] | None
) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    config = _alternate_config(tmp_path, logging_enabled=logging_enabled)
    with artifact_lease(tmp_path):
        canonical = run_and_persist(tmp_path, config=config)
        before = {name: path.read_bytes() for name, path in canonical["paths"].items()}
        path = write_policy_comparison(tmp_path, config=config, seeds=explicit_seeds)
    comparison = json.loads(path.read_text(encoding="utf-8"))
    grid_path = tmp_path / "output/data/pymdp_policy_posterior_grid.json"
    grid = json.loads(grid_path.read_text(encoding="utf-8"))
    _assert_comparison_grid(config, comparison, grid)
    assert grid["source"] == "provided_comparison_payload"
    assert comparison["summary"]["seeds"] == list(explicit_seeds or (7,))
    assert comparison["summary"]["planners"] == ["sophisticated_inference", "vanilla"]
    assert comparison["summary"]["complete_grid"] is True
    assert comparison["summary"]["run_count"] == 2
    assert comparison["summary"]["vanilla_role"] == "comparison_only"
    assert config.random_seed == 19
    assert config.validation_comparison.seeds == (7,)
    assert canonical["result"].config_hash == config_hash(config)
    for name, artifact in canonical["paths"].items():
        assert artifact.read_bytes() == before[name]
        payload = json.loads(before[name])
        assert payload["config_hash"] == config_hash(config)
        if "config" in payload:
            assert payload["config"] == config_snapshot(config)
    for run in comparison["runs"]:
        log_path = tmp_path / run["config"]["logging"]["path"]
        assert log_path.parent == tmp_path / "output/custom_logs"
        assert log_path.is_file() is logging_enabled
        if logging_enabled:
            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            assert records[0]["seed"] == run["seed"]
            assert records[0]["config_hash"] == run["config_hash"]
            assert records[0]["planner"] == run["planner"]
            steps = [record for record in records if record["event"] == "si_tmaze_step"]
            assert [record["q_pi"] for record in steps] == [step["q_pi"] for step in run["policy_posterior_steps"]]
    assert (tmp_path / config.logging.path).is_file() is logging_enabled

    # The supplied real payload, not a subsequently damaged saved comparison, is authoritative.
    damaged = {**comparison, "runs": []}
    path.write_text(json.dumps(damaged), encoding="utf-8")
    supplied = json.loads(write_policy_posterior_grid(tmp_path, comparison=comparison).read_text(encoding="utf-8"))
    assert supplied == grid
    saved = json.loads(write_policy_posterior_grid(tmp_path).read_text(encoding="utf-8"))
    assert saved["source"] == "output/data/si_policy_comparison.json"
    assert saved["source_payload_sha256"] == _payload_hash(damaged)
    assert saved["rows"] == []
    assert saved["all_available_posteriors_normalized"] is False
    path.unlink()
    missing = json.loads(write_policy_posterior_grid(tmp_path).read_text(encoding="utf-8"))
    assert missing["source"] is None
    assert missing["config"] is None
    assert missing["config_hash"] is None
    assert missing["rows"] == []
    assert missing["all_available_posteriors_normalized"] is False
    assert not path.exists()


@pytest.mark.requires_pymdp
@pytest.mark.render_slow
def test_comparison_without_config_loads_root_config(tmp_path: Path) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    config = _alternate_config(tmp_path, logging_enabled=False)
    (tmp_path / "pymdp.yaml").write_text(yaml.safe_dump(config_snapshot(config)), encoding="utf-8")
    path = write_policy_comparison(tmp_path)
    comparison = json.loads(path.read_text(encoding="utf-8"))
    grid = json.loads(write_policy_posterior_grid(tmp_path).read_text(encoding="utf-8"))
    _assert_comparison_grid(config, comparison, grid)
    assert comparison["summary"]["seeds"] == [7]
    assert grid["source"] == "output/data/si_policy_comparison.json"


@pytest.mark.parametrize(
    "entrypoint",
    [
        "write_model_matrices",
        "write_si_artifacts",
        "run_and_persist",
        "write_policy_comparison",
        "write_policy_posterior_grid",
        "run_si_tmaze",
        "run_validation_comparison_tmaze",
    ],
)
def test_public_si_producers_refuse_competing_custody(project_root: Path, tmp_path: Path, entrypoint: str) -> None:
    child = """
import sys
from pathlib import Path
from orchestration.artifact_lock import ArtifactLeaseBusy
from simulation import si_artifacts, si_loop
from simulation.pymdp_config import apply_pymdp_overrides, default_pymdp_config
from test_si_artifacts import _finite_result
root = Path(sys.argv[1])
name = sys.argv[2]
config = apply_pymdp_overrides(default_pymdp_config(), steps=2)
function = getattr(si_artifacts, name, None) or getattr(si_loop, name)
kwargs = {} if name == 'write_policy_posterior_grid' else {'config': config}
args = [root, _finite_result(config)] if name == 'write_si_artifacts' else [root]
if name == 'run_validation_comparison_tmaze':
    kwargs['planner'] = 'vanilla'
try:
    function(*args, **kwargs)
except ArtifactLeaseBusy:
    raise SystemExit(2)
"""
    with artifact_lease(tmp_path) as lease:
        # Metadata without pass_fds must not authorize any programmatic writer.
        env = lease.handoff().env
        env["PYTHONPATH"] = os.pathsep.join((str(project_root / "src"), str(project_root / "tests")))
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.run(
            [sys.executable, "-B", "-c", child, str(tmp_path), entrypoint],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert process.returncode == 2, process.stdout + process.stderr
        assert {path.name for path in (tmp_path / "output").iterdir()} == {".artifact.lock"}
