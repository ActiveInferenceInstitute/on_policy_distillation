"""YAML-backed configuration for the canonical pymdp full-TMaze SI rollout."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

import yaml

Planner = Literal["sophisticated_inference"]
ComparisonPlanner = Literal["sophisticated_inference", "vanilla"]

CANONICAL_PROFILE = "full_tmaze_sophisticated_inference"
CANONICAL_PLANNER: Planner = "sophisticated_inference"


@dataclass(frozen=True)
class EnvironmentConfig:
    """T-maze environment settings: reward condition, cue validity, and outcome probabilities."""

    reward_condition: int | None = 0
    cue_validity: float = 0.95
    reward_probability: float = 1.0
    punishment_probability: float = 1.0
    dependent_outcomes: bool = True
    categorical_obs: bool = False


@dataclass(frozen=True)
class AgentConfig:
    """pymdp agent settings: policy lengths, gamma, inference algorithm, action selection, and learning flags."""

    si_policy_len: int = 1
    vanilla_policy_len: int = 4
    gamma: float = 3.0
    inference_algo: str = "fpi"
    action_selection: str = "deterministic"
    sampling_mode: str = "full"
    learn_A: bool = False
    learn_B: bool = False


@dataclass(frozen=True)
class SISearchConfig:
    """Sophisticated-inference tree-search settings: horizon, node/branching caps, and pruning thresholds."""

    horizon: int = 4
    max_nodes: int = 5000
    max_branching: int = 45
    policy_prune_threshold: float = 0.0
    observation_prune_threshold: float = 1e-4
    entropy_stop_threshold: float = 0.0
    neg_efe_stop_threshold: float = 1e10
    kl_threshold: float = -1.0
    prune_penalty: float = 512.0
    gamma: float = 3.0
    topk_obsspace: int = 10000


@dataclass(frozen=True)
class LoggingConfig:
    """Run-logging settings: enabled flag and JSONL output path."""

    enabled: bool = True
    path: str = "output/logs/pymdp_runs.jsonl"


@dataclass(frozen=True)
class ValidationComparisonConfig:
    """Planner-comparison settings for validation runs: enabled flag, planners, and seeds."""

    enabled: bool = True
    planners: tuple[ComparisonPlanner, ...] = ("sophisticated_inference", "vanilla")
    seeds: tuple[int, ...] = (0,)


@dataclass(frozen=True)
class PymdpConfig:
    """Top-level config for the canonical full-TMaze sophisticated-inference rollout."""

    profile: str = CANONICAL_PROFILE
    planner: Planner = CANONICAL_PLANNER
    planning_horizon: int = 4
    timesteps: int = 5
    random_seed: int = 0
    environment: EnvironmentConfig = EnvironmentConfig()
    agent: AgentConfig = AgentConfig()
    si_search: SISearchConfig = SISearchConfig()
    logging: LoggingConfig = LoggingConfig()
    validation_comparison: ValidationComparisonConfig = ValidationComparisonConfig()

    @property
    def policy_len(self) -> int:
        return self.agent.si_policy_len

    @property
    def horizon(self) -> int:
        return self.planning_horizon

    @property
    def steps(self) -> int:
        return self.timesteps

    @property
    def mode(self) -> Planner:
        """Compatibility alias for older manuscript statistics consumers."""
        return self.planner


def _coerce_planner(value: Any) -> Planner:
    planner = str(value or CANONICAL_PLANNER)
    if planner != CANONICAL_PLANNER:
        raise ValueError(f"unsupported canonical pymdp planner: {planner!r}")
    return CANONICAL_PLANNER


def _coerce_comparison_planner(value: Any) -> ComparisonPlanner:
    planner = str(value)
    if planner not in {"sophisticated_inference", "vanilla"}:
        raise ValueError(f"unsupported pymdp comparison planner: {planner!r}")
    return planner  # type: ignore[return-value]


def _coerce_reward_condition(value: Any) -> int | None:
    if value is None or str(value).lower() == "null":
        return None
    condition = int(value)
    if condition not in {0, 1}:
        raise ValueError("reward_condition must be 0, 1, or null")
    return condition


def _parse_raw(raw: dict[str, Any]) -> PymdpConfig:
    if "mode" in raw:
        raise ValueError("legacy pymdp mode is unsupported; canonical runs always use sophisticated_inference")

    environment_raw = raw.get("environment") or {}
    agent_raw = raw.get("agent") or {}
    search_raw = raw.get("si_search") or {}
    logging_raw = raw.get("logging") or {}
    comparison_raw = raw.get("validation_comparison") or {}
    planning_horizon = int(raw.get("planning_horizon", raw.get("horizon", 4)))
    timesteps = int(raw.get("timesteps", raw.get("steps", 5)))
    profile = str(raw.get("profile", CANONICAL_PROFILE))
    if profile != CANONICAL_PROFILE:
        raise ValueError(f"unsupported pymdp profile: {profile!r}")
    planner = _coerce_planner(raw.get("planner", CANONICAL_PLANNER))
    search_horizon = int(search_raw.get("horizon", planning_horizon))

    return PymdpConfig(
        profile=profile,
        planner=planner,
        planning_horizon=planning_horizon,
        timesteps=timesteps,
        random_seed=int(raw.get("random_seed", 0)),
        environment=EnvironmentConfig(
            reward_condition=_coerce_reward_condition(environment_raw.get("reward_condition", 0)),
            cue_validity=float(environment_raw.get("cue_validity", 0.95)),
            reward_probability=float(environment_raw.get("reward_probability", 1.0)),
            punishment_probability=float(environment_raw.get("punishment_probability", 1.0)),
            dependent_outcomes=bool(environment_raw.get("dependent_outcomes", True)),
            categorical_obs=bool(environment_raw.get("categorical_obs", False)),
        ),
        agent=AgentConfig(
            si_policy_len=int(agent_raw.get("si_policy_len", 1)),
            vanilla_policy_len=int(agent_raw.get("vanilla_policy_len", planning_horizon)),
            gamma=float(agent_raw.get("gamma", 3.0)),
            inference_algo=str(agent_raw.get("inference_algo", "fpi")),
            action_selection=str(agent_raw.get("action_selection", "deterministic")),
            sampling_mode=str(agent_raw.get("sampling_mode", "full")),
            learn_A=bool(agent_raw.get("learn_A", False)),
            learn_B=bool(agent_raw.get("learn_B", False)),
        ),
        si_search=SISearchConfig(
            horizon=search_horizon,
            max_nodes=int(search_raw.get("max_nodes", 5000)),
            max_branching=int(search_raw.get("max_branching", 45)),
            policy_prune_threshold=float(search_raw.get("policy_prune_threshold", 0.0)),
            observation_prune_threshold=float(search_raw.get("observation_prune_threshold", 1e-4)),
            entropy_stop_threshold=float(search_raw.get("entropy_stop_threshold", 0.0)),
            neg_efe_stop_threshold=float(search_raw.get("neg_efe_stop_threshold", 1e10)),
            kl_threshold=float(search_raw.get("kl_threshold", -1.0)),
            prune_penalty=float(search_raw.get("prune_penalty", 512.0)),
            gamma=float(search_raw.get("gamma", agent_raw.get("gamma", 3.0))),
            topk_obsspace=int(search_raw.get("topk_obsspace", 10000)),
        ),
        logging=LoggingConfig(
            enabled=bool(logging_raw.get("enabled", True)),
            path=str(logging_raw.get("path", "output/logs/pymdp_runs.jsonl")),
        ),
        validation_comparison=ValidationComparisonConfig(
            enabled=bool(comparison_raw.get("enabled", True)),
            planners=tuple(
                _coerce_comparison_planner(value)
                for value in comparison_raw.get("planners", ("sophisticated_inference", "vanilla"))
            ),
            seeds=tuple(int(value) for value in comparison_raw.get("seeds", (int(raw.get("random_seed", 0)),))),
        ),
    )


def default_pymdp_config() -> PymdpConfig:
    """Return a PymdpConfig with all default values."""
    return PymdpConfig()


def pymdp_config_path(project_root: Path) -> Path:
    """Return the canonical pymdp.yaml path under the project root."""
    return project_root.resolve() / "pymdp.yaml"


def load_pymdp_config(
    project_root: Path,
    *,
    config_path: Path | None = None,
) -> PymdpConfig:
    """Load PymdpConfig from pymdp.yaml (or config_path), returning defaults when the file is absent.

    Raises ValueError for legacy `mode` keys, non-canonical profiles/planners, or invalid reward conditions.
    """
    path = config_path or pymdp_config_path(project_root)
    if not path.is_file():
        return default_pymdp_config()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _parse_raw(raw)


def apply_pymdp_overrides(
    config: PymdpConfig,
    *,
    steps: int | None = None,
    horizon: int | None = None,
    seed: int | None = None,
    logging_enabled: bool | None = None,
    comparison_enabled: bool | None = None,
) -> PymdpConfig:
    """Return a copy of the config with any provided steps/horizon/seed/logging/comparison overrides applied.

    A horizon override also updates the SI search horizon, and vanilla_policy_len when it tracked the old horizon.
    """
    updated = config
    if horizon is not None:
        updated = replace(updated, planning_horizon=horizon, si_search=replace(updated.si_search, horizon=horizon))
        if updated.agent.vanilla_policy_len == config.planning_horizon:
            updated = replace(updated, agent=replace(updated.agent, vanilla_policy_len=horizon))
    if steps is not None:
        updated = replace(updated, timesteps=steps)
    if seed is not None:
        updated = replace(updated, random_seed=seed)
    if logging_enabled is not None:
        updated = replace(updated, logging=replace(updated.logging, enabled=logging_enabled))
    if comparison_enabled is not None:
        updated = replace(
            updated,
            validation_comparison=replace(updated.validation_comparison, enabled=comparison_enabled),
        )
    return updated


def config_snapshot(config: PymdpConfig) -> dict[str, Any]:
    """Return a JSON-serializable dict of every config field, used for logging and hashing."""
    return {
        "profile": config.profile,
        "planner": config.planner,
        "planning_horizon": config.planning_horizon,
        "timesteps": config.timesteps,
        "random_seed": config.random_seed,
        "policy_len": config.policy_len,
        "environment": {
            "reward_condition": config.environment.reward_condition,
            "cue_validity": config.environment.cue_validity,
            "reward_probability": config.environment.reward_probability,
            "punishment_probability": config.environment.punishment_probability,
            "dependent_outcomes": config.environment.dependent_outcomes,
            "categorical_obs": config.environment.categorical_obs,
        },
        "agent": {
            "si_policy_len": config.agent.si_policy_len,
            "vanilla_policy_len": config.agent.vanilla_policy_len,
            "gamma": config.agent.gamma,
            "inference_algo": config.agent.inference_algo,
            "action_selection": config.agent.action_selection,
            "sampling_mode": config.agent.sampling_mode,
            "learn_A": config.agent.learn_A,
            "learn_B": config.agent.learn_B,
        },
        "si_search": {
            "horizon": config.si_search.horizon,
            "max_nodes": config.si_search.max_nodes,
            "max_branching": config.si_search.max_branching,
            "policy_prune_threshold": config.si_search.policy_prune_threshold,
            "observation_prune_threshold": config.si_search.observation_prune_threshold,
            "entropy_stop_threshold": config.si_search.entropy_stop_threshold,
            "neg_efe_stop_threshold": config.si_search.neg_efe_stop_threshold,
            "kl_threshold": config.si_search.kl_threshold,
            "prune_penalty": config.si_search.prune_penalty,
            "gamma": config.si_search.gamma,
            "topk_obsspace": config.si_search.topk_obsspace,
        },
        "logging": {
            "enabled": config.logging.enabled,
            "path": config.logging.path,
        },
        "validation_comparison": {
            "enabled": config.validation_comparison.enabled,
            "planners": list(config.validation_comparison.planners),
            "seeds": list(config.validation_comparison.seeds),
        },
    }


def config_hash(config: PymdpConfig) -> str:
    """Return the first 16 hex chars of the SHA-256 over the sorted JSON config snapshot."""
    payload = json.dumps(config_snapshot(config), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
