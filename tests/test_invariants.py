from invariants import all_invariants_pass, run_invariants


def test_core_invariants_pass() -> None:
    results = run_invariants()
    assert results
    assert all_invariants_pass(results), results


def test_ising_mi_monotone_invariant_with_negative_control() -> None:
    import numpy as np
    from analytical.hyperparameters import lambda_grid, load_hyperparameters
    from analytical.invariants import inv_ising_mi_monotone, ising_mutual_information

    # The MI-sweep "more coupling means more transferable information" claim is now a
    # checked invariant, not prose.
    assert inv_ising_mi_monotone()
    mi = np.array([ising_mutual_information(lam) for lam in lambda_grid(load_hyperparameters())])
    assert mi.size >= 2
    assert np.all(np.diff(mi) > 0.0)  # strictly increasing on the [0, lambda_max] grid
    # Negative control: a single transposed pair (a dip) must fail the predicate the
    # invariant uses, proving the check is falsifiable.
    dipped = mi.copy()
    dipped[1], dipped[2] = dipped[2], dipped[1]
    assert not bool(np.all(np.diff(dipped) >= 0.0))
