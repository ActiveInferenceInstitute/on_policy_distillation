"""Statistics derived from pymdp simulation artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _entropy_stats(trace_steps: list[dict[str, Any]]) -> dict[str, float]:
    entropies = [float(step.get("belief_entropy", 0.0)) for step in trace_steps]
    if not entropies:
        return {"entropy_min": 0.0, "entropy_max": 0.0, "entropy_mean": 0.0}
    return {
        "entropy_min": min(entropies),
        "entropy_max": max(entropies),
        "entropy_mean": sum(entropies) / len(entropies),
    }


def _series_stats(values: list[Any], prefix: str) -> dict[str, float]:
    series = [float(value) for value in values if value is not None]
    if not series:
        return {f"{prefix}_min": 0.0, f"{prefix}_max": 0.0, f"{prefix}_mean": 0.0}
    return {
        f"{prefix}_min": min(series),
        f"{prefix}_max": max(series),
        f"{prefix}_mean": sum(series) / len(series),
    }


def _first_positive_step(values: list[Any]) -> int | None:
    for idx, value in enumerate(values):
        if int(value) > 0:
            return idx
    return None


def summarize_si_trace(trace: Mapping[str, Any], summary: Mapping[str, Any]) -> dict[str, Any]:
    steps = list(trace.get("steps") or [])
    actions = list(summary.get("actions") or [])
    observations = list(summary.get("observations") or [])
    policy_entropy = list(summary.get("q_pi_entropy_by_step") or [])
    action_probabilities = list(summary.get("action_probabilities") or [])
    action_names = list(summary.get("action_names") or [])
    observations_by_modality = summary.get("observations_by_modality") or {}
    cue_observed_step = _first_positive_step(list(observations_by_modality.get("cue") or []))
    reward_observed_step = _first_positive_step(list(observations_by_modality.get("outcome") or []))
    initial_action_probabilities = action_probabilities[0] if action_probabilities else {}
    goal_state = int((summary.get("config") or {}).get("tmaze", {}).get("num_obs", 2)) - 1
    goal_reached = bool(observations and int(observations[-1]) == goal_state)
    if "goal_reached" in summary:
        goal_reached = bool(summary["goal_reached"])
    stats = {
        "steps": int(summary.get("steps", len(steps))),
        "action_diversity": len(set(actions)),
        "goal_reached": goal_reached,
        "initial_selected_action_name": str(action_names[0]) if action_names else "",
        "initial_cue_probability": float(initial_action_probabilities.get("move_to_cue", 0.0) or 0.0),
        "cue_observed_step": cue_observed_step,
        "reward_observed_step": reward_observed_step,
        "cue_before_reward": cue_observed_step is not None
        and reward_observed_step is not None
        and cue_observed_step < reward_observed_step,
        **_entropy_stats(steps),
        **_series_stats(policy_entropy, "policy_entropy"),
    }
    if policy_entropy and cue_observed_step is not None:
        initial_entropy = float(policy_entropy[0])
        post_cue_entropy = min(float(value) for value in policy_entropy[cue_observed_step:] if value is not None)
        stats["policy_entropy_drop_after_cue"] = initial_entropy - post_cue_entropy
    else:
        stats["policy_entropy_drop_after_cue"] = 0.0
    return stats


def load_si_artifacts(project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    root = project_root.resolve()
    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    trace_path = root / "output" / "data" / "si_tmaze_trace.json"
    summary: dict[str, Any] = {}
    trace: dict[str, Any] = {"steps": []}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if trace_path.exists():
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
    return summary, trace
