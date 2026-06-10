"""Simulation-track invariants for pymdp T-maze artifacts."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from simulation.numerics import STEP_POSTERIOR_ATOL

InvariantFn = Callable[[Path], bool]


def _load_summary(root: Path) -> dict[str, Any]:
    path = root / "output" / "data" / "si_tmaze_summary.json"
    if not path.exists():
        return {}
    summary: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return summary


def _load_trace(root: Path) -> list[dict[str, Any]]:
    path = root / "output" / "data" / "si_tmaze_trace.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("steps") or [])


def _load_matrices(root: Path) -> dict[str, Any]:
    path = root / "output" / "data" / "si_tmaze_model_matrices.json"
    if not path.exists():
        return {}
    matrices: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return matrices


def inv_belief_entropy_finite(root: Path) -> bool:
    """Check mean_belief_entropy in si_tmaze_summary.json is finite and non-negative."""
    summary = _load_summary(root)
    entropy = float(summary.get("mean_belief_entropy", -1.0))
    return np.isfinite(entropy) and entropy >= 0.0


def inv_actions_length_matches_steps(root: Path) -> bool:
    """Check the summary's action list length equals rollout_timestep_count equals steps + 1."""
    summary = _load_summary(root)
    steps = int(summary.get("steps", 0))
    actions = summary.get("actions") or []
    rollout_count = int(summary.get("rollout_timestep_count", steps + 1))
    return steps >= 1 and len(actions) == rollout_count == steps + 1


def inv_observations_in_obs_space(root: Path) -> bool:
    """Check observations cover exactly the location/outcome/cue modalities and each index is within its modality bound (5/3/3)."""
    summary = _load_summary(root)
    observations = summary.get("observations_by_modality") or {}
    if set(observations) != {"location", "outcome", "cue"}:
        return False
    bounds = {"location": 5, "outcome": 3, "cue": 3}
    return all(all(0 <= int(obs) < bounds[modality] for obs in values) for modality, values in observations.items())


def inv_policy_len_matches_config(root: Path) -> bool:
    """Check the summary's policy_len matches the policy_len recorded in its config block."""
    summary = _load_summary(root)
    config = summary.get("config") or {}
    expected = int(config.get("policy_len", 1))
    return int(summary.get("policy_len", expected)) == expected


def inv_goal_reached(root: Path) -> bool:
    """Check the summary reports goal_reached, falling back to any reward outcome observation (index 1)."""
    summary = _load_summary(root)
    if "goal_reached" in summary:
        return bool(summary["goal_reached"])
    outcomes = (summary.get("observations_by_modality") or {}).get("outcome") or []
    return any(int(obs) == 1 for obs in outcomes)


def inv_trace_step_count_matches_summary(root: Path) -> bool:
    """Check the si_tmaze_trace.json step count equals the summary's rollout_timestep_count."""
    summary = _load_summary(root)
    trace = _load_trace(root)
    return len(trace) == int(summary.get("rollout_timestep_count", 0))


def inv_si_tree_available(root: Path) -> bool:
    """Check the planner is sophisticated_inference and the summary reports tree_available."""
    summary = _load_summary(root)
    return summary.get("planner") == "sophisticated_inference" and summary.get("tree_available") is True


def inv_q_pi_rows_normalized(root: Path) -> bool:
    """Check every trace step flags q_pi_normalized and its q_pi sums to 1 within STEP_POSTERIOR_ATOL."""
    trace = _load_trace(root)
    return bool(trace) and all(
        step.get("q_pi_normalized") is True and abs(float(sum(step.get("q_pi") or [])) - 1.0) <= STEP_POSTERIOR_ATOL
        for step in trace
    )


def inv_model_matrices_full_tmaze(root: Path) -> bool:
    """Check si_tmaze_model_matrices.json has the v1 schema, full T-maze A/B shapes, and all normalization checks passing."""
    matrices = _load_matrices(root)
    return (
        matrices.get("schema") == "template_active_inference.si_tmaze_model_matrices.v1"
        and matrices.get("A_shapes") == [[5, 5], [3, 5, 2], [3, 5, 2]]
        and matrices.get("B_shapes") == [[5, 5, 5], [2, 2, 1]]
        and all(check.get("normalized") is True for check in matrices.get("normalization_checks") or [])
    )


SIMULATION_INVARIANTS: dict[str, InvariantFn] = {
    "belief_entropy_finite": inv_belief_entropy_finite,
    "actions_length_matches_steps": inv_actions_length_matches_steps,
    "observations_in_obs_space": inv_observations_in_obs_space,
    "policy_len_matches_config": inv_policy_len_matches_config,
    "goal_reached": inv_goal_reached,
    "trace_step_count_matches_summary": inv_trace_step_count_matches_summary,
    "si_tree_available": inv_si_tree_available,
    "q_pi_rows_normalized": inv_q_pi_rows_normalized,
    "model_matrices_full_tmaze": inv_model_matrices_full_tmaze,
}


def run_simulation_invariants(project_root: Path) -> dict[str, bool]:
    """Run all SIMULATION_INVARIANTS against the project root and return name -> pass mapping."""
    root = project_root.resolve()
    return {name: fn(root) for name, fn in SIMULATION_INVARIANTS.items()}


def build_merged_invariants_payload(
    project_root: Path,
    *,
    analytical_results: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Single SSOT for merged analytical + simulation invariant reports."""
    from analytical.invariants import run_invariants

    root = project_root.resolve()
    inv_results = analytical_results if analytical_results is not None else run_invariants()
    payload: dict[str, Any] = {
        "invariants": inv_results,
        "all_pass": all(inv_results.values()),
    }
    inv_path = root / "output" / "reports" / "invariants.json"
    existing: dict[str, Any] = {}
    if inv_path.is_file():
        existing = json.loads(inv_path.read_text(encoding="utf-8"))
    si_summary = root / "output" / "data" / "si_tmaze_summary.json"
    if si_summary.is_file():
        simulation = run_simulation_invariants(root)
        payload["simulation"] = simulation
        payload["all_pass"] = all(inv_results.values()) and all(simulation.values())
    elif existing.get("simulation"):
        simulation = existing["simulation"]
        payload["simulation"] = simulation
        payload["all_pass"] = bool(payload["all_pass"]) and all(simulation.values())
    return payload


def write_simulation_invariants(project_root: Path) -> Path:
    """Run the simulation invariants and write results plus all_pass to output/reports/si_invariants.json.

    Returns the written path.
    """
    root = project_root.resolve()
    results = run_simulation_invariants(root)
    out = root / "output" / "reports" / "si_invariants.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"invariants": results, "all_pass": all(results.values())}
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def merge_simulation_into_invariants_report(project_root: Path) -> Path:
    """Rebuild output/reports/invariants.json with simulation results merged via build_merged_invariants_payload.

    Reuses analytical results already stored in the report when present; returns the report path.
    """
    root = project_root.resolve()
    inv_path = root / "output" / "reports" / "invariants.json"
    analytical: dict[str, bool] | None = None
    if inv_path.exists():
        data = json.loads(inv_path.read_text(encoding="utf-8"))
        raw = data.get("invariants") or {}
        if raw:
            analytical = {str(k): bool(v) for k, v in raw.items()}
    payload = build_merged_invariants_payload(root, analytical_results=analytical)
    inv_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return inv_path
