"""Canonical pymdp full-TMaze sophisticated-inference rollout."""

from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import numpy as np

from simulation.logging_utils import RunLogger
from simulation.numerics import STEP_POSTERIOR_ATOL
from simulation.pymdp_config import (
    ComparisonPlanner,
    PymdpConfig,
    apply_pymdp_overrides,
    config_hash,
    load_pymdp_config,
)
from simulation.pymdp_runtime import KNOWN_TREE_MAX_NODES_WARNING, construct_agent_with_diagnostics
from simulation.tmaze_model import ACTION_LABELS, CUE_LABELS, LOCATION_LABELS, OUTCOME_LABELS
from simulation.tmaze_model import build_tmaze_generative_model


def pymdp_available() -> bool:
    try:
        import pymdp  # noqa: F401

        return True
    except ImportError:  # pragma: no cover
        return False


@dataclass(frozen=True)
class SIRunResult:
    steps: int
    policy_len: int
    planning_horizon: int
    num_policies: int
    mean_belief_entropy: float
    actions: list[int]
    action_names: list[str]
    action_vectors: list[list[int]]
    observations: list[int]
    observations_by_modality: dict[str, list[int]]
    observation_names_by_modality: dict[str, list[str]]
    q_pi_by_step: list[list[float]]
    q_pi_entropy_by_step: list[float]
    action_probabilities: list[dict[str, float]]
    planner: str
    profile: str
    config_hash: str
    goal_reached: bool
    reward_observed: bool
    action_diversity: int
    tree_available: bool
    tree_stats: dict[str, Any]
    trace_steps: list[dict[str, Any]] = field(default_factory=list)
    runtime_diagnostics: dict[str, Any] = field(default_factory=dict)

    @property
    def mode(self) -> str:
        return self.planner


def _prob_entropy(values: np.ndarray) -> float:
    probs = np.asarray(values, dtype=np.float64).reshape(-1)
    probs = np.clip(probs, 0.0, None)
    total = float(probs.sum())
    if total <= 0.0:
        return 0.0
    probs = probs / total
    nz = probs[probs > 0.0]
    return float(-np.sum(nz * np.log(nz)))


def _sequence_from_rollout(array: Any) -> list[int]:
    arr = np.asarray(array)
    return [int(value) for value in arr[0, :, 0].tolist()]


def _observations_by_modality(info: dict[str, Any]) -> dict[str, list[int]]:
    observations = info["observation"]
    return {
        "location": _sequence_from_rollout(observations[0]),
        "outcome": _sequence_from_rollout(observations[1]),
        "cue": _sequence_from_rollout(observations[2]),
    }


def _named_observations(observations: dict[str, list[int]]) -> dict[str, list[str]]:
    label_maps = {
        "location": LOCATION_LABELS,
        "outcome": OUTCOME_LABELS,
        "cue": CUE_LABELS,
    }
    return {
        modality: [label_maps[modality].get(int(value), f"{modality}_{value}") for value in values]
        for modality, values in observations.items()
    }


def _belief_entropy_by_step(info: dict[str, Any]) -> list[float]:
    qs = info.get("qs") or []
    if not qs:
        return []
    timesteps = int(np.asarray(qs[0]).shape[1])
    entropies: list[float] = []
    for t in range(timesteps):
        total = 0.0
        for factor in qs:
            total += _prob_entropy(np.asarray(factor)[0, t, :])
        entropies.append(total)
    return entropies


def _q_pi_rows(info: dict[str, Any]) -> tuple[list[list[float]], list[float]]:
    qpi = np.asarray(info["qpi"], dtype=np.float64)[0]
    rows: list[list[float]] = []
    entropies: list[float] = []
    for row in qpi:
        clipped = np.clip(row, 0.0, None)
        total = float(clipped.sum())
        normed = clipped / total if total > 0.0 else clipped
        rows.append([float(value) for value in normed.tolist()])
        entropies.append(_prob_entropy(normed))
    return rows, entropies


def _first_action_probabilities(agent: Any, info: dict[str, Any]) -> list[dict[str, float]]:
    qpi = info["qpi"]
    unique_actions = np.asarray(agent.unique_multiactions)[:, 0].astype(int).tolist()
    probabilities: list[dict[str, float]] = []
    for t in range(np.asarray(qpi).shape[1]):
        marginal = np.asarray(agent.multiaction_probabilities(qpi[:, t, :])[0], dtype=np.float64)
        probabilities.append(
            {
                ACTION_LABELS.get(action, f"action_{action}"): float(probability)
                for action, probability in zip(unique_actions, marginal.tolist(), strict=True)
                if action >= 0
            }
        )
    return probabilities


def _tree_stats(tree: Any, *, known_tree_warning_count: int) -> dict[str, Any]:
    if tree is None:
        return {"available": False, "type": None, "known_tree_warning_count": known_tree_warning_count}
    stats = {
        "available": True,
        "type": type(tree).__name__,
        "known_tree_warning_count": known_tree_warning_count,
    }
    for attr in ("node_count", "num_nodes", "depth", "max_depth"):
        if hasattr(tree, attr):
            value = getattr(tree, attr)
            if isinstance(value, (int, float, str, bool)):
                stats[attr] = value
    return stats


def _build_si_policy_search(config: PymdpConfig) -> Any:
    from pymdp.planning.si import si_policy_search

    search = config.si_search
    return si_policy_search(
        horizon=search.horizon,
        max_nodes=search.max_nodes,
        max_branching=search.max_branching,
        policy_prune_threshold=search.policy_prune_threshold,
        observation_prune_threshold=search.observation_prune_threshold,
        entropy_stop_threshold=search.entropy_stop_threshold,
        neg_efe_stop_threshold=search.neg_efe_stop_threshold,
        kl_threshold=search.kl_threshold,
        prune_penalty=search.prune_penalty,
        gamma=search.gamma,
        topk_obsspace=search.topk_obsspace,
    )


def _run_pymdp_rollout(
    project_root: Path,
    *,
    config: PymdpConfig,
    planner: Literal["sophisticated_inference", "vanilla"],
    logger: RunLogger | None = None,
) -> SIRunResult:
    if not pymdp_available():  # pragma: no cover
        raise RuntimeError("inferactively-pymdp is not installed")

    import jax
    import jax.random as jr
    from pymdp.envs import rollout

    root = project_root.resolve()
    model = build_tmaze_generative_model(config)
    policy_len = config.agent.si_policy_len if planner == "sophisticated_inference" else config.agent.vanilla_policy_len
    agent, runtime_diagnostics = construct_agent_with_diagnostics(
        root,
        config=config,
        model=model,
        policy_len=policy_len,
        context=f"si_tmaze:{planner}:h{config.planning_horizon}:s{config.random_seed}",
    )

    policy_search = _build_si_policy_search(config) if planner == "sophisticated_inference" else None
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    jax.clear_caches()
    with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
        if policy_search is None:
            _, info = rollout(
                agent, model["env"], num_timesteps=config.timesteps, rng_key=jr.PRNGKey(config.random_seed)
            )
        else:
            _, info = rollout(
                agent,
                model["env"],
                num_timesteps=config.timesteps,
                rng_key=jr.PRNGKey(config.random_seed),
                policy_search=policy_search,
            )

    runtime_output = "\n".join(part for part in (stdout_buffer.getvalue(), stderr_buffer.getvalue()) if part.strip())
    known_tree_warning_count = runtime_output.count(KNOWN_TREE_MAX_NODES_WARNING)
    runtime_diagnostics["known_tree_warning_count"] = known_tree_warning_count
    if runtime_output:
        runtime_diagnostics["rollout_output_excerpt"] = runtime_output.splitlines()[:8]

    actions = _sequence_from_rollout(info["action"])
    action_names = [ACTION_LABELS.get(action, f"action_{action}") for action in actions]
    action_vectors = np.asarray(info["action"], dtype=np.int64)[0].tolist()
    observations_by_modality = _observations_by_modality(info)
    observation_names = _named_observations(observations_by_modality)
    q_pi_by_step, q_pi_entropy_by_step = _q_pi_rows(info)
    action_probabilities = _first_action_probabilities(agent, info)
    belief_entropies = _belief_entropy_by_step(info)
    tree_stats = _tree_stats(info.get("tree"), known_tree_warning_count=known_tree_warning_count)
    reward_observed = any(value == 1 for value in observations_by_modality["outcome"])

    log = logger or RunLogger.from_project_root(
        root,
        relative_path=config.logging.path,
        enabled=config.logging.enabled,
    )
    log.emit_run_header(
        config_hash=config_hash(config),
        planner=planner,
        profile=config.profile,
        seed=config.random_seed,
        policy_len=policy_len,
        planning_horizon=config.planning_horizon,
    )

    trace_steps: list[dict[str, Any]] = []
    for t, action in enumerate(actions):
        record = {
            "step": t,
            "action": action,
            "action_name": action_names[t],
            "action_vector": action_vectors[t],
            "selected_action": action,
            "selected_action_name": action_names[t],
            "observations_by_modality": {modality: values[t] for modality, values in observations_by_modality.items()},
            "observation_names_by_modality": {modality: values[t] for modality, values in observation_names.items()},
            "belief_entropy": belief_entropies[t] if t < len(belief_entropies) else None,
            "q_pi": q_pi_by_step[t],
            "q_pi_sum": float(sum(q_pi_by_step[t])),
            "q_pi_entropy": q_pi_entropy_by_step[t],
            "q_pi_normalized": abs(float(sum(q_pi_by_step[t])) - 1.0) <= STEP_POSTERIOR_ATOL,
            "action_probabilities": action_probabilities[t],
            "planner": planner,
            "profile": config.profile,
            "tree_available": tree_stats["available"],
            "tree_stats": tree_stats if planner == "sophisticated_inference" else {"available": False},
            "config_hash": config_hash(config),
        }
        trace_steps.append(record)
        with log.timed(
            event="si_tmaze_step",
            step=t,
            obs=observations_by_modality["location"][t],
            action=action,
        ) as ctx:
            ctx.update(record)

    return SIRunResult(
        steps=config.timesteps,
        policy_len=policy_len,
        planning_horizon=config.planning_horizon,
        num_policies=int(agent.policies.num_policies),
        mean_belief_entropy=float(np.mean(belief_entropies)) if belief_entropies else 0.0,
        actions=actions,
        action_names=action_names,
        action_vectors=action_vectors,
        observations=observations_by_modality["location"],
        observations_by_modality=observations_by_modality,
        observation_names_by_modality=observation_names,
        q_pi_by_step=q_pi_by_step,
        q_pi_entropy_by_step=q_pi_entropy_by_step,
        action_probabilities=action_probabilities,
        planner=planner,
        profile=config.profile,
        config_hash=config_hash(config),
        goal_reached=reward_observed,
        reward_observed=reward_observed,
        action_diversity=len(set(actions)),
        tree_available=bool(tree_stats["available"]),
        tree_stats=tree_stats,
        trace_steps=trace_steps,
        runtime_diagnostics=runtime_diagnostics,
    )


def run_si_tmaze(
    project_root: Path,
    *,
    config: PymdpConfig | None = None,
    steps: int | None = None,
    logger: RunLogger | None = None,
) -> SIRunResult:
    """Run the canonical full-TMaze sophisticated-inference profile."""
    cfg = config or load_pymdp_config(project_root)
    if steps is not None:
        cfg = apply_pymdp_overrides(cfg, steps=steps)
    return _run_pymdp_rollout(project_root, config=cfg, planner="sophisticated_inference", logger=logger)


def run_validation_comparison_tmaze(
    project_root: Path,
    *,
    config: PymdpConfig,
    planner: ComparisonPlanner,
    logger: RunLogger | None = None,
) -> SIRunResult:
    """Run SI or vanilla pymdp planning for comparison artifacts only."""
    return _run_pymdp_rollout(project_root, config=config, planner=planner, logger=logger)
