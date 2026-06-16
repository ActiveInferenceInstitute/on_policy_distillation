"""Registry-backed invariants for the analytical track."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from .bernoulli_toy import (
    BERNOULLI_VERIFICATION_TOLERANCE,
    empirical_mutual_information,
    ising_joint_posterior,
    ising_mutual_information,
)
from .decomposition import decomposition_identity_holds
from .hyperparameters import lambda_grid, load_hyperparameters

InvariantFn = Callable[[], bool]


def inv_ising_mi_at_zero() -> bool:
    """Check the closed-form Ising mutual information is zero at lambda = 0 within tolerance."""
    return abs(ising_mutual_information(0.0)) <= BERNOULLI_VERIFICATION_TOLERANCE


def inv_ising_mi_saturates() -> bool:
    """Check the Ising mutual information saturates to ln 2 at large lambda (100.0)."""
    high = ising_mutual_information(100.0)
    return bool(np.isclose(high, np.log(2.0), atol=1e-3))


def inv_empirical_matches_closed_form() -> bool:
    """Check empirical and closed-form mutual information agree within tolerance across the lambda grid."""
    hp = load_hyperparameters()
    for lam in lambda_grid(hp):
        closed = ising_mutual_information(lam)
        empirical = empirical_mutual_information(lam)
        if abs(closed - empirical) > hp.bernoulli_verification_tolerance:
            return False
    return True


def inv_ising_mi_monotone() -> bool:
    """Check closed-form Ising mutual information is monotone non-decreasing across the
    lambda grid. This is the load-bearing 'more coupling means more transferable
    information' property of the MI-sweep result; without it that claim is unchecked."""
    hp = load_hyperparameters()
    mi = np.array([ising_mutual_information(lam) for lam in lambda_grid(hp)], dtype=np.float64)
    return bool(mi.size >= 2 and np.all(np.diff(mi) >= -BERNOULLI_VERIFICATION_TOLERANCE))


def inv_decomposition_identity() -> bool:
    """Check the free-energy decomposition identity holds for the Ising joint posterior at lambda = 1.5."""
    lam = 1.5
    q = ising_joint_posterior(lam)
    from .bernoulli_toy import ising_coupling, symmetric_mean_field_prior

    mf = symmetric_mean_field_prior()
    g0 = [np.zeros(2, dtype=np.float64), np.zeros(2, dtype=np.float64)]
    return decomposition_identity_holds(
        q,
        mf,
        g0,
        ising_coupling(),
        np.zeros((2, 2), dtype=np.float64),
        gamma=1.0,
        lam=lam,
    )


def inv_joint_is_pmf() -> bool:
    """Check the Ising joint posterior at lambda = 2.0 is a valid probability mass function."""
    from .joint_dist import is_pmf

    q = ising_joint_posterior(2.0)
    return is_pmf(q)


def inv_mean_field_at_lambda_zero() -> bool:
    """Check the Ising joint posterior factorizes (is mean-field) at lambda = 0."""
    from .joint_dist import is_mean_field

    q = ising_joint_posterior(0.0)
    return is_mean_field(q)


CORE_INVARIANTS: dict[str, InvariantFn] = {
    "ising_mi_at_zero": inv_ising_mi_at_zero,
    "ising_mi_saturates": inv_ising_mi_saturates,
    "ising_mi_monotone": inv_ising_mi_monotone,
    "empirical_matches_closed_form": inv_empirical_matches_closed_form,
    "decomposition_identity": inv_decomposition_identity,
    "joint_is_pmf": inv_joint_is_pmf,
    "mean_field_at_lambda_zero": inv_mean_field_at_lambda_zero,
}


def run_invariants() -> dict[str, bool]:
    """Run all CORE_INVARIANTS and return name -> pass mapping."""
    return {name: fn() for name, fn in CORE_INVARIANTS.items()}


def all_invariants_pass(results: dict[str, bool] | None = None) -> bool:
    """Return True when every invariant passes, running them when no results dict is given."""
    inv = results if results is not None else run_invariants()
    return all(inv.values())
