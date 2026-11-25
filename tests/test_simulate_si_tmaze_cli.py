"""Execute the real SI CLI only in copied temporary source/config roots."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from orchestration.artifact_lock import ARTIFACT_LEASE_ENV, artifact_lease
from simulation.pymdp_config import (
    apply_pymdp_overrides,
    config_hash,
    config_snapshot,
    default_pymdp_config,
    load_pymdp_config,
)
from simulation.si_loop import pymdp_available


@pytest.fixture
def cli_root(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "si_cli"
    (root / "scripts").mkdir(parents=True)
    shutil.copyfile(project_root / "scripts/simulate_si_tmaze.py", root / "scripts/simulate_si_tmaze.py")
    shutil.copytree(project_root / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
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
        logging=replace(default.logging, path="output/custom_logs/cli.jsonl"),
        validation_comparison=replace(default.validation_comparison, seeds=(7,)),
    )
    (root / "configs").mkdir()
    (root / "configs/custom.yaml").write_text(yaml.safe_dump(config_snapshot(alternate)), encoding="utf-8")
    return root


def _child_env(root: Path, inherited_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if inherited_env is None else inherited_env)
    if inherited_env is None:
        # This fixture is a different physical root from the outer pytest lease.
        env.pop(ARTIFACT_LEASE_ENV, None)
    env["PYTHONPATH"] = str(root / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["MPLBACKEND"] = "Agg"
    return env


def _lease_probe(root: Path) -> subprocess.CompletedProcess[str]:
    code = """
import sys
from orchestration.artifact_lock import ArtifactLeaseBusy, artifact_lease
try:
    with artifact_lease(sys.argv[1]):
        pass
except ArtifactLeaseBusy:
    raise SystemExit(2)
"""
    return subprocess.run(
        [sys.executable, "-B", "-c", code, str(root)],
        cwd=root,
        env=_child_env(root),
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.requires_pymdp
@pytest.mark.render_slow
@pytest.mark.parametrize("log_disabled", [False, True], ids=["logging_enabled", "logging_disabled"])
def test_cli_effective_config_and_comparison_seeds(cli_root: Path, log_disabled: bool) -> None:
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    custom = cli_root / "configs/custom.yaml"
    expected = apply_pymdp_overrides(
        load_pymdp_config(cli_root, config_path=custom),
        steps=2,
        horizon=2,
        seed=19,
        logging_enabled=False if log_disabled else None,
        comparison_enabled=True,
    )
    argv = [
        sys.executable,
        "-B",
        "scripts/simulate_si_tmaze.py",
        "--config",
        str(custom),
        "--steps",
        "2",
        "--horizon",
        "2",
        "--seed",
        "19",
        "--comparison",
    ]
    if log_disabled:
        argv.append("--log-disabled")
    with artifact_lease(cli_root) as lease:
        handoff = lease.handoff()
        process = subprocess.run(
            argv,
            cwd=cli_root,
            env=_child_env(cli_root, handoff.env),
            pass_fds=handoff.pass_fds,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert process.returncode == 0, process.stdout + process.stderr
        # The real child must not release its parent's shared open-file description.
        probe = _lease_probe(cli_root)
        assert probe.returncode == 2, probe.stdout + probe.stderr
    probe = _lease_probe(cli_root)
    assert probe.returncode == 0, probe.stdout + probe.stderr

    data = cli_root / "output/data"
    summary = json.loads((data / "si_tmaze_summary.json").read_text(encoding="utf-8"))
    trace = json.loads((data / "si_tmaze_trace.json").read_text(encoding="utf-8"))
    matrices = json.loads((data / "si_tmaze_model_matrices.json").read_text(encoding="utf-8"))
    report = json.loads((cli_root / "output/reports/si_tmaze_run_report.json").read_text(encoding="utf-8"))
    comparison = json.loads((data / "si_policy_comparison.json").read_text(encoding="utf-8"))
    grid = json.loads((data / "pymdp_policy_posterior_grid.json").read_text(encoding="utf-8"))
    for artifact in (summary, matrices, report, comparison, grid):
        assert artifact["config"] == config_snapshot(expected)
        assert artifact["config_hash"] == config_hash(expected)
    assert trace["config_hash"] == config_hash(expected)
    assert summary["planner"] == "sophisticated_inference"
    assert summary["steps"] == report["steps"] == 2
    assert summary["planning_horizon"] == report["planning_horizon"] == 2
    assert report["seed"] == 19
    assert matrices["environment"]["cue_validity"] == pytest.approx(0.8)
    assert len(trace["steps"]) == 3
    assert comparison["summary"]["seeds"] == [7]
    assert comparison["summary"]["run_count"] == 2
    assert comparison["summary"]["vanilla_role"] == "comparison_only"
    assert {run["planner"] for run in comparison["runs"]} == {"sophisticated_inference", "vanilla"}
    assert grid["source"] == "provided_comparison_payload"
    comparison_bytes = json.dumps(comparison, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert grid["source_payload_sha256"] == hashlib.sha256(comparison_bytes).hexdigest()
    assert grid["row_count"] == 6
    for index, run in enumerate(comparison["runs"]):
        assert run["seed"] == run["config"]["random_seed"] == 7
        run_config = apply_pymdp_overrides(expected, seed=7)
        run_config = replace(run_config, logging=replace(run_config.logging, path=run["config"]["logging"]["path"]))
        assert run["config"] == config_snapshot(run_config)
        assert run["config_hash"] == config_hash(run_config)
        assert run["horizon"] == run["steps"] == 2
        assert run["policy_len"] == (1 if run["planner"] == "sophisticated_inference" else 2)
        projected = [row for row in grid["rows"] if row["run_index"] == index]
        assert len(projected) == len(run["policy_posterior_steps"]) == 3
        for step, row in zip(run["policy_posterior_steps"], projected, strict=True):
            assert row["config_hash"] == run["config_hash"]
            assert row["seed"] == 7
            assert row["horizon"] == row["steps"] == 2
            for key in ("step", "q_pi", "q_pi_entropy", "action_probabilities", "posterior_source", "fallback_reason"):
                assert row[key] == step[key]
            assert row["normalized"] is True
        log_path = cli_root / run_config.logging.path
        assert log_path.is_file() is (not log_disabled)
        if not log_disabled:
            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            assert records[0]["seed"] == 7
            assert records[0]["config_hash"] == run["config_hash"]
            logged_steps = [record for record in records if record["event"] == "si_tmaze_step"]
            assert [record["q_pi"] for record in logged_steps] == [
                step["q_pi"] for step in run["policy_posterior_steps"]
            ]
    canonical_log = cli_root / expected.logging.path
    assert canonical_log.is_file() is (not log_disabled)
    if log_disabled:
        assert report["log_record_count"] == 0
        assert not list((cli_root / "output").rglob("*.jsonl"))
    else:
        records = [json.loads(line) for line in canonical_log.read_text(encoding="utf-8").splitlines()]
        assert records[0]["seed"] == 19
        assert records[0]["config_hash"] == config_hash(expected)
        assert len(records) == report["log_record_count"] == 4
    assert "policy_comparison:" in process.stdout
    assert "policy_posterior_grid:" in process.stdout


@pytest.mark.parametrize("env_only", [False, True], ids=["competing_writer", "metadata_without_fd"])
def test_cli_refuses_custody_without_real_handoff(cli_root: Path, env_only: bool) -> None:
    with artifact_lease(cli_root) as parent:
        env = _child_env(cli_root, parent.handoff().env) if env_only else _child_env(cli_root)
        process = subprocess.run(
            [sys.executable, "-B", "scripts/simulate_si_tmaze.py", "--steps", "2"],
            cwd=cli_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert process.returncode == 1, process.stdout + process.stderr
        assert "without artifact custody" in process.stderr
        assert {path.name for path in (cli_root / "output").iterdir()} == {".artifact.lock"}
        assert _lease_probe(cli_root).returncode == 2


def test_cli_rejects_wrong_root_handoff(cli_root: Path, tmp_path: Path) -> None:
    other = tmp_path / "other_root"
    other.mkdir()
    with artifact_lease(other) as parent:
        handoff = parent.handoff()
        process = subprocess.run(
            [sys.executable, "-B", "scripts/simulate_si_tmaze.py"],
            cwd=cli_root,
            env=_child_env(cli_root, handoff.env),
            pass_fds=handoff.pass_fds,
            capture_output=True,
            text=True,
            timeout=30,
        )
    assert process.returncode == 1, process.stdout + process.stderr
    assert "different physical root" in process.stderr
    assert not (cli_root / "output").exists()


@pytest.mark.parametrize("metadata", ["not-json", '{"version":1}'])
def test_cli_rejects_malformed_handoff(cli_root: Path, metadata: str) -> None:
    env = _child_env(cli_root)
    env[ARTIFACT_LEASE_ENV] = metadata
    process = subprocess.run(
        [sys.executable, "-B", "scripts/simulate_si_tmaze.py"],
        cwd=cli_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert process.returncode == 1, process.stdout + process.stderr
    assert "invalid artifact lease handle" in process.stderr
    assert not (cli_root / "output").exists()
