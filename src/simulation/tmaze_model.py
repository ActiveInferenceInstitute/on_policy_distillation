"""pymdp-backed full T-maze generative process/model adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .pymdp_config import PymdpConfig, default_pymdp_config

ACTION_LABELS: dict[int, str] = {
    0: "move_to_center",
    1: "move_to_left_arm",
    2: "move_to_right_arm",
    3: "move_to_cue",
    4: "move_to_middle",
}
LOCATION_LABELS: dict[int, str] = {
    0: "center",
    1: "left_arm",
    2: "right_arm",
    3: "cue_location",
    4: "middle",
}
OUTCOME_LABELS: dict[int, str] = {
    0: "no_outcome",
    1: "reward",
    2: "punishment",
}
CUE_LABELS: dict[int, str] = {
    0: "no_cue",
    1: "cue_left",
    2: "cue_right",
}
REWARD_LOCATION_LABELS: dict[int, str] = {
    0: "reward_left",
    1: "reward_right",
}


@dataclass(frozen=True)
class TMazeSpec:
    profile: str = "full_tmaze_sophisticated_inference"
    environment_class: str = "TMaze"
    num_location_states: int = 5
    num_reward_location_states: int = 2
    num_location_actions: int = 5
    num_modalities: int = 3
    policy_len: int = 1
    planning_horizon: int = 4
    seed: int = 0


def spec_from_config(config: PymdpConfig) -> TMazeSpec:
    return TMazeSpec(
        profile=config.profile,
        policy_len=config.policy_len,
        planning_horizon=config.planning_horizon,
        seed=config.random_seed,
    )


def build_tmaze_environment(config: PymdpConfig | None = None) -> Any:
    """Construct pymdp's full ``TMaze`` environment from the project config."""
    from pymdp.envs import TMaze

    cfg = config or default_pymdp_config()
    env = TMaze(
        reward_condition=cfg.environment.reward_condition,
        cue_validity=cfg.environment.cue_validity,
        reward_probability=cfg.environment.reward_probability,
        punishment_probability=cfg.environment.punishment_probability,
        dependent_outcomes=cfg.environment.dependent_outcomes,
        categorical_obs=cfg.environment.categorical_obs,
    )
    return env


def _as_list_dependencies(dependencies: Any) -> list[list[int]]:
    return [[int(value) for value in factor] for factor in dependencies]


def _normalization_checks(name: str, factors: list[Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for index, factor in enumerate(factors):
        arr = np.asarray(factor, dtype=np.float64)
        if name in {"A", "B"}:
            sums = arr.sum(axis=0)
        else:
            sums = np.array([arr.sum()])
        checks.append(
            {
                "matrix": f"{name}[{index}]",
                "shape": list(arr.shape),
                "axis0_sum_min": float(np.min(sums)),
                "axis0_sum_max": float(np.max(sums)),
                "normalized": bool(np.allclose(sums, 1.0, atol=1e-8)),
            }
        )
    return checks


def build_preference_vectors(env: Any, config: PymdpConfig | None = None) -> list[Any]:
    """Build C vectors following pymdp's full-TMaze SI validation notebook."""
    import jax.numpy as jnp

    del config
    c = [jnp.zeros(a.shape[0], dtype=jnp.float32) for a in env.A]
    c[1] = c[1].at[1].set(2.0)
    c[1] = c[1].at[2].set(-6.0)
    c[2] = c[2].at[1].set(-0.5)
    c[2] = c[2].at[2].set(-0.5)
    return c


def build_initial_state_priors(env: Any) -> list[Any]:
    """Build D priors: center-start location and uniform reward-location belief."""
    import jax.numpy as jnp

    d_loc = jnp.zeros(env.B[0].shape[0], dtype=jnp.float32)
    d_loc = d_loc.at[0].set(1.0)
    d_reward = jnp.ones(env.B[1].shape[0], dtype=jnp.float32)
    d_reward = d_reward / jnp.sum(d_reward, axis=0, keepdims=True)
    return [d_loc, d_reward]


def build_tmaze_generative_model(spec: TMazeSpec | PymdpConfig | None = None) -> dict[str, Any]:
    """Return pymdp full ``TMaze`` A/B/C/D plus labels and normalization evidence."""
    if isinstance(spec, PymdpConfig):
        cfg = spec
        tmaze_spec = spec_from_config(cfg)
    elif isinstance(spec, TMazeSpec):
        cfg = default_pymdp_config()
        tmaze_spec = spec
    else:
        cfg = default_pymdp_config()
        tmaze_spec = spec_from_config(cfg)

    env = build_tmaze_environment(cfg)
    c = build_preference_vectors(env, cfg)
    d = build_initial_state_priors(env)
    a_dependencies = _as_list_dependencies(env.A_dependencies)
    b_dependencies = _as_list_dependencies(env.B_dependencies)

    return {
        "profile": tmaze_spec.profile,
        "environment_class": tmaze_spec.environment_class,
        "env": env,
        "A": list(env.A),
        "B": list(env.B),
        "C": c,
        "D": d,
        "A_dependencies": env.A_dependencies,
        "B_dependencies": env.B_dependencies,
        "policy_len": tmaze_spec.policy_len,
        "planning_horizon": tmaze_spec.planning_horizon,
        "seed": tmaze_spec.seed,
        "labels": {
            "actions": ACTION_LABELS,
            "location_observations": LOCATION_LABELS,
            "outcome_observations": OUTCOME_LABELS,
            "cue_observations": CUE_LABELS,
            "location_states": LOCATION_LABELS,
            "reward_location_states": REWARD_LOCATION_LABELS,
            "modalities": ["location", "outcome", "cue"],
            "state_factors": ["location", "reward_location"],
            "control_factors": ["location", "reward_location_fixed"],
        },
        "dependencies": {
            "A": a_dependencies,
            "B": b_dependencies,
        },
        "normalization_checks": (
            _normalization_checks("A", list(env.A))
            + _normalization_checks("B", list(env.B))
            + _normalization_checks("D", d)
        ),
        "transition_semantics": {
            "location": "adjacent T-maze transitions; invalid actions leave location in place",
            "reward_location": "reward location remains fixed through the trial",
        },
        "environment": {
            "reward_condition": cfg.environment.reward_condition,
            "cue_validity": cfg.environment.cue_validity,
            "reward_probability": cfg.environment.reward_probability,
            "punishment_probability": cfg.environment.punishment_probability,
            "dependent_outcomes": cfg.environment.dependent_outcomes,
            "categorical_obs": cfg.environment.categorical_obs,
        },
        "preferences": {
            "outcome": {OUTCOME_LABELS[index]: float(value) for index, value in enumerate(np.asarray(c[1]))},
            "cue": {CUE_LABELS[index]: float(value) for index, value in enumerate(np.asarray(c[2]))},
        },
    }
