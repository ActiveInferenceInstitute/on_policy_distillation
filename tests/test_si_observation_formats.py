"""Local observation-format contracts, not end-to-end categorical SI acceptance."""

from __future__ import annotations

import importlib.metadata
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from simulation.pymdp_config import default_pymdp_config
from simulation.pymdp_runtime import construct_agent_with_diagnostics
from simulation.si_loop import _action_vectors_from_rollout, _named_observations, _observations_by_modality


@pytest.mark.parametrize("environment_axis", [False, True], ids=["compact", "tmaze_axis"])
@pytest.mark.parametrize("soft_categorical", [False, True], ids=["one_hot", "categorical"])
def test_observation_ids_and_categorical_vectors_decode_identically(
    environment_axis: bool, soft_categorical: bool
) -> None:
    expected = {"location": [0, 3, 1], "outcome": [0, 2, 1], "cue": [0, 2, 1]}
    discrete = []
    categorical = []
    for values, num_obs in zip(expected.values(), (5, 3, 3), strict=True):
        indices = np.asarray(values, dtype=np.int64)[None, :]
        probabilities = np.eye(num_obs, dtype=np.float64)[indices]
        if soft_categorical:
            probabilities = 0.8 * probabilities + 0.2 / num_obs
        if environment_axis:
            indices = indices[:, :, None]
            probabilities = probabilities[:, :, None, :]
        discrete.append(indices)
        categorical.append(probabilities)

    decoded_ids = _observations_by_modality({"observation": discrete}, categorical_obs=False)
    decoded_vectors = _observations_by_modality({"observation": categorical}, categorical_obs=True)

    assert decoded_ids == decoded_vectors == expected
    names = _named_observations(decoded_vectors)
    assert names["location"] == ["center", "cue_location", "left_arm"]
    assert names["outcome"] == ["no_outcome", "punishment", "reward"]
    assert names["cue"] == ["no_cue", "cue_right", "cue_left"]


def test_action_vectors_are_not_categorical_observations() -> None:
    expected = [[0, 0], [3, 0], [1, 0]]
    actions = np.asarray([expected], dtype=np.int64)

    vectors = _action_vectors_from_rollout(actions)

    assert vectors == expected
    assert [vector[0] for vector in vectors] == [0, 3, 1]
    assert [vector[1] for vector in vectors] == [0, 0, 0]


@pytest.mark.requires_pymdp
@pytest.mark.parametrize("outcome_id", [1, 2], ids=["reward", "punishment"])
def test_constructed_pinned_agent_infers_each_observation_format(tmp_path: Path, outcome_id: int) -> None:
    import jax.numpy as jnp
    import pymdp.agent as pymdp_agent

    distribution = importlib.metadata.distribution("inferactively-pymdp")
    assert distribution.version == "1.0.4"
    assert Path(pymdp_agent.__file__).resolve() == Path(distribution.locate_file("pymdp/agent.py")).resolve()

    base = default_pymdp_config()
    posteriors = []
    for categorical_obs in (False, True):
        config = replace(base, environment=replace(base.environment, categorical_obs=categorical_obs))
        # A real finite inference problem with distinct reward/punishment likelihoods.
        model = {
            "A": [jnp.array([[0.1, 0.1], [0.8, 0.1], [0.1, 0.8]], dtype=jnp.float32)],
            "B": [jnp.eye(2, dtype=jnp.float32)[..., None]],
            "C": [jnp.zeros(3, dtype=jnp.float32)],
            "D": [jnp.array([0.5, 0.5], dtype=jnp.float32)],
            "A_dependencies": [[0]],
            "B_dependencies": [[0]],
        }
        agent, diagnostic = construct_agent_with_diagnostics(
            tmp_path,
            config=config,
            model=model,
            policy_len=1,
            context=f"observation_boundary:{categorical_obs}:{outcome_id}",
        )
        assert isinstance(agent, pymdp_agent.Agent)
        assert agent.categorical_obs is categorical_obs
        assert diagnostic["versions"]["inferactively_pymdp"] == "1.0.4"

        indices = jnp.array([[outcome_id]], dtype=jnp.int32)
        observations = [jnp.eye(3, dtype=jnp.float32)[indices] if categorical_obs else indices]
        posterior = np.asarray(agent.infer_states(observations, agent.D)[0]).reshape(-1)
        expected = np.array([8.0 / 9.0, 1.0 / 9.0])
        if outcome_id == 2:
            expected = expected[::-1]
        assert np.isfinite(posterior).all()
        np.testing.assert_allclose(posterior, expected, rtol=1e-6, atol=1e-6)
        posteriors.append(posterior)

    np.testing.assert_allclose(posteriors[0], posteriors[1], rtol=1e-6, atol=1e-6)
