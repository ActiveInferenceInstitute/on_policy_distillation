import numpy as np

from analytical.free_energy import (
    free_energy,
    kl_divergence,
    marginal_free_energy,
    shannon_entropy,
    total_correlation,
    total_correlation_via_kl,
)
from analytical.hyperparameters import lambda_grid, load_hyperparameters


def test_shannon_entropy_uniform_binary() -> None:
    p = np.array([0.5, 0.5])
    assert np.isclose(shannon_entropy(p), np.log(2.0))


def test_total_correlation_independent_is_zero() -> None:
    q = np.array([[0.25, 0.25], [0.25, 0.25]])
    assert abs(total_correlation(q)) < 1e-9
    assert abs(total_correlation_via_kl(q)) < 1e-9


def test_kl_divergence_identical_is_zero() -> None:
    p = np.array([0.3, 0.7])
    assert abs(kl_divergence(p, p)) < 1e-12


def test_lambda_grid_length() -> None:
    hp = load_hyperparameters()
    grid = lambda_grid(hp)
    assert len(grid) == hp.lambda_grid_points


def test_free_energy_zero_prior_support_is_infinite() -> None:
    # q places mass where the prior is zero => E_q[log p] = -inf, so the free
    # energy must be +inf (consistent with kl_divergence), not a silently
    # floored large finite value.
    q = np.array([0.5, 0.5])
    prior = np.array([1.0, 0.0])
    g = np.zeros(2)
    assert free_energy(q, prior, g, gamma=1.0) == float("inf")
    assert kl_divergence(q, prior) == float("inf")


def test_free_energy_full_support_is_finite() -> None:
    q = np.array([0.5, 0.5])
    prior = np.array([0.8, 0.2])
    g = np.zeros(2)
    fe = free_energy(q, prior, g, gamma=1.0)
    assert np.isfinite(fe)
    # F = -E_q[log p] - H(q); the entropy cancels none of the prior term here.
    assert np.isclose(fe, -(0.5 * np.log(0.8) + 0.5 * np.log(0.2)) - np.log(2.0))


def test_marginal_free_energy_zero_prior_support_is_infinite() -> None:
    # Single-stream q (ndim=1): the marginal equals q, so placing mass where the
    # marginal prior is zero yields +inf (matching kl_divergence).
    q = np.array([0.5, 0.5])
    mf_prior = [np.array([1.0, 0.0])]
    per_stream_g = [np.zeros(2)]
    assert marginal_free_energy(q, mf_prior, per_stream_g, gamma=1.0, k=0) == float("inf")
