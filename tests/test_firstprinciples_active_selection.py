"""Tests for the active-selection module (EFE closes the active half of OPD<->AI).

These exercise the toy-exact identity ``gap_closed = epistemic``, the EFE-driven
selection of the cue policy, exact gap closure, and the three negative controls
(pragmatic-only, uniform, cue-blinding) that make the result non-vacuous.
"""

from __future__ import annotations

import numpy as np
import pytest

from analytical.free_energy import shannon_entropy
from firstprinciples import active_selection as asel


def test_gap_closed_equals_epistemic_identity() -> None:
    # H(r) - E_o[H(r|o)] == I(o;r) == epistemic_value, to machine precision.
    prior_entropy = float(shannon_entropy(np.array([0.5, 0.5])))
    for policy in asel.canonical_policies():
        score = asel.score_policy(policy)
        assert (prior_entropy - score.residual_gap) == pytest.approx(score.epistemic_value, abs=1e-12)
        assert score.closeable_gap == pytest.approx(score.epistemic_value, abs=1e-15)


def test_efe_selects_cue_and_closes_gap_exactly() -> None:
    scores = [asel.score_policy(p) for p in asel.canonical_policies()]
    pick = asel.rank_by_efe(scores)[0]
    assert pick.name == "cue"
    # A perfectly diagnostic cue resolves r; the residual distillation gap is zero.
    assert pick.residual_gap == pytest.approx(0.0, abs=1e-12)
    assert pick.epistemic_value == pytest.approx(float(shannon_entropy(np.array([0.5, 0.5]))), abs=1e-12)


def test_pragmatic_only_control_picks_an_arm_and_leaves_gap_open() -> None:
    # Ablating the epistemic term: a reward-greedy selector commits to an arm and
    # cannot close the distillation gap. This is the load-bearing negative control.
    scores = [asel.score_policy(p) for p in asel.canonical_policies()]
    pick = asel.rank_by_pragmatic_only(scores)[0]
    assert pick.name != "cue"
    assert pick.name.startswith("commit")
    assert pick.residual_gap > 0.5  # ~H(r); the channel is blind to r


def test_uniform_selector_keeps_positive_expected_residual() -> None:
    scores = [asel.score_policy(p) for p in asel.canonical_policies()]
    mean_residual = float(np.mean([s.residual_gap for s in scores]))
    assert mean_residual > 1e-3


def test_blinding_the_cue_reopens_the_gap_nonvacuity() -> None:
    sharp = asel.score_policy(next(p for p in asel.canonical_policies() if p.name == "cue"))
    blinded = asel.score_policy(asel._symmetric_cue(0.5))
    assert blinded.epistemic_value == pytest.approx(0.0, abs=1e-12)
    assert blinded.residual_gap > sharp.residual_gap + 1e-3


def test_validity_sweep_is_monotone_and_obeys_identity() -> None:
    prior_entropy = float(shannon_entropy(np.array([0.5, 0.5])))
    sweep = asel.validity_sweep()
    assert sweep[0]["cue_validity"] == 0.5
    assert sweep[-1]["cue_validity"] == 1.0
    assert sweep[0]["residual_gap"] == pytest.approx(prior_entropy, abs=1e-12)
    assert sweep[-1]["residual_gap"] == pytest.approx(0.0, abs=1e-12)
    for i in range(len(sweep) - 1):
        assert sweep[i]["epistemic_value"] <= sweep[i + 1]["epistemic_value"] + 1e-12
        assert sweep[i]["residual_gap"] >= sweep[i + 1]["residual_gap"] - 1e-12
    for row in sweep:
        assert (prior_entropy - row["residual_gap"]) == pytest.approx(row["epistemic_value"], abs=1e-12)


def test_efe_uses_shared_energy_functional() -> None:
    # The reported EFE must equal the energy module's own decomposition (one
    # definition shared with the passive half -- the two halves cannot drift).
    from firstprinciples import energy

    policy = next(p for p in asel.canonical_policies() if p.name == "cue")
    model = asel.policy_model(policy)
    report = energy.efe_report(model.prior, model)
    score = asel.score_policy(policy)
    assert score.efe == pytest.approx(float(report["efe_epistemic_pragmatic"]), abs=1e-15)


def test_unnormalised_likelihood_raises() -> None:
    bad = asel.RolloutPolicy("bad", likelihood=((0.7, 0.7), (0.2, 0.8)), preferences=(0.5, 0.5))
    with pytest.raises(ValueError):
        asel.policy_model(bad)


def test_validate_payload_accepts_honest_certificate() -> None:
    assert asel.validate_payload(asel.build_payload()) == []


def test_validate_payload_catches_lying_residual_row() -> None:
    # Mutate the cue residual but leave `ok` true: the re-derivation must catch
    # both the broken identity and the stored-flag disagreement.
    import copy

    payload = copy.deepcopy(asel.build_payload())
    cue = next(p for p in payload["policies"] if p["name"] == "cue")
    cue["residual_gap"] = 0.5  # was ~0; a lie
    issues = asel.validate_payload(payload)
    assert issues  # non-empty => caught
    assert any("identity" in i for i in issues)
    assert any("stored ok disagrees" in i for i in issues)


def test_validate_payload_catches_tampered_efe_selection() -> None:
    # Make commit_left the EFE-minimiser by lying about its EFE; the row-level
    # re-derivation (argmin over efe) must no longer select cue.
    import copy

    payload = copy.deepcopy(asel.build_payload())
    for p in payload["policies"]:
        if p["name"] == "commit_left":
            p["efe"] = -1.0
    assert asel.validate_payload(payload)  # caught


def test_validate_payload_rejects_malformed() -> None:
    assert asel.validate_payload({}) != []
    assert asel.validate_payload({"schema": asel.SCHEMA, "policies": []}) != []


def test_policy_posterior_uniform_at_zero_and_concentrates() -> None:
    efe = [0.0, 0.5, 0.5, 0.693]  # unique argmin at index 0
    q0 = asel.policy_posterior(efe, 0.0)
    assert all(abs(qi - 0.25) < 1e-12 for qi in q0)
    q_hi = asel.policy_posterior(efe, 1e6)
    assert abs(q_hi[0] - 1.0) < 1e-9
    assert asel.policy_posterior(efe, 5.0)[0] > asel.policy_posterior(efe, 1.0)[0]
    with pytest.raises(ValueError):
        asel.policy_posterior(efe, -1.0)


def test_precision_sweep_monotone_onto_cue() -> None:
    scores = [asel.score_policy(p) for p in asel.canonical_policies()]
    sweep = asel.precision_sweep(scores)
    q = [r["q_cue"] for r in sweep]
    assert sweep[0]["gamma"] == 0.0 and abs(q[0] - 0.25) < 1e-12
    assert all(q[i] <= q[i + 1] + 1e-12 for i in range(len(q) - 1))
    assert q[-1] > 0.999


def test_validate_payload_catches_lying_precision_row() -> None:
    # Tamper q_cue in the stored sweep but leave ok true: re-derivation must catch it.
    import copy

    payload = copy.deepcopy(asel.build_payload())
    payload["precision_sweep"][-1]["q_cue"] = 0.123  # was ~1.0
    issues = asel.validate_payload(payload)
    assert any("precision_sweep q_cue disagrees" in i for i in issues)


def test_validate_rederives_blinded_concentration() -> None:
    # Forge a low blinded-cue efe (via a high stored blinded epistemic) so the
    # blinded menu would concentrate on it; the re-derivation must catch it.
    import copy

    payload = copy.deepcopy(asel.build_payload())
    payload["blinded_cue_epistemic_value"] = 5.0  # -> blinded_cue_efe = H - 5 (menu argmin)
    issues = asel.validate_payload(payload)
    assert any("blinded-cue posterior concentrates" in i for i in issues)


def test_build_payload_certificate_ok() -> None:
    payload = asel.build_payload()
    assert payload["schema"] == asel.SCHEMA
    assert payload["ok"] is True
    assert payload["efe_selected_policy"] == "cue"
    assert payload["pragmatic_only_selected_policy"] != "cue"
    assert payload["gap_closed_equals_epistemic_identity"] is True
    assert payload["validity_sweep_monotone"] is True
    assert payload["validity_sweep_strict"] is True
    assert payload["blinding_reopens_gap"] is True
    assert payload["max_identity_residual"] < 1e-12
    assert payload["efe_selected_residual_gap"] < 1e-9
    assert payload["posterior_uniform_at_zero"] is True
    assert payload["posterior_monotone_in_gamma"] is True
    assert payload["posterior_limit_concentrates_on_cue"] is True
    assert payload["blinded_posterior_does_not_concentrate"] is True
    # full policy menu present
    assert {p["name"] for p in payload["policies"]} == {"cue", "commit_left", "commit_right", "stay"}
