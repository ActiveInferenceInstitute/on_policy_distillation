"""Tests for the energy-based VFE/EFE module (decomposition identities)."""

from __future__ import annotations

import numpy as np
import pytest

from firstprinciples import energy
from firstprinciples.energy import GenerativeModel


def _model() -> GenerativeModel:
    return GenerativeModel(
        prior=np.array([0.5, 0.5]),
        likelihood=np.array([[0.85, 0.15], [0.15, 0.85]]),
        preferences=np.array([0.9, 0.1]),
    )


def test_model_validation() -> None:
    with pytest.raises(ValueError):
        GenerativeModel(prior=np.array([0.5, 0.5]), likelihood=np.array([[0.5, 0.5]]), preferences=np.array([0.5, 0.5]))
    with pytest.raises(ValueError):
        GenerativeModel(prior=np.array([1.0]), likelihood=np.array([[0.6, 0.4]]), preferences=np.array([0.5]))
    with pytest.raises(ValueError):
        GenerativeModel(prior=np.array([0.5, 0.5]), likelihood=np.array([[0.7, 0.4], [0.5, 0.5]]), preferences=np.array([0.5, 0.5]))


def test_vfe_three_decompositions_agree() -> None:
    model = _model()
    for o in (0, 1):
        for q in (np.array([0.5, 0.5]), np.array([0.7, 0.3]), np.array([0.99, 0.01])):
            report = energy.vfe_report(q, model, o)
            assert report["decompositions_agree"] is True


def test_posterior_minimises_vfe_to_neg_log_evidence() -> None:
    model = _model()
    o = 0
    post = energy.posterior(model, o)
    f_post, _, _ = energy.vfe_complexity_accuracy(post, model, o)
    log_ev = float(np.log(energy.evidence(model, o)))
    assert f_post == pytest.approx(-log_ev, abs=1e-9)
    # any other q has higher (or equal) free energy
    f_prior, _, _ = energy.vfe_complexity_accuracy(model.prior, model, o)
    assert f_prior >= f_post - 1e-12


def test_efe_two_decompositions_agree() -> None:
    model = _model()
    for q in (np.array([0.5, 0.5]), np.array([0.8, 0.2])):
        report = energy.efe_report(q, model)
        assert report["decompositions_agree"] is True
        assert report["risk"] >= 0.0
        assert report["ambiguity"] >= 0.0
        assert report["epistemic_value"] >= -1e-12


def test_predicted_observations_normalised() -> None:
    model = _model()
    q_o = energy.predicted_observations(np.array([0.6, 0.4]), model)
    assert q_o.sum() == pytest.approx(1.0)


def test_energy_payload_ok() -> None:
    payload = energy.build_payload()
    assert payload["schema"] == energy.SCHEMA
    assert payload["ok"] is True
    assert payload["posterior_minimises_vfe"] is True
    assert payload["vfe_at_posterior"]["decompositions_agree"] is True
    assert payload["efe"]["decompositions_agree"] is True


def test_structural_zero_likelihood_agrees_at_infinity() -> None:
    # When q places mass on a state with zero likelihood for o, the true VFE is
    # +inf; all three decompositions must agree (no silent log-flooring).
    import math

    model = GenerativeModel(
        prior=np.array([0.5, 0.5]),
        likelihood=np.array([[1.0, 0.0], [0.3, 0.7]]),
        preferences=np.array([0.5, 0.5]),
    )
    report = energy.vfe_report(np.array([0.5, 0.5]), model, 1)
    assert math.isinf(report["vfe_energy_entropy"])
    assert math.isinf(report["vfe_complexity_accuracy"])
    assert math.isinf(report["vfe_divergence_evidence"])
    assert report["decompositions_agree"] is True


def test_evidence_zero_raises() -> None:
    # a state-certain prior with zero likelihood for the observation -> zero evidence
    model = GenerativeModel(
        prior=np.array([1.0, 0.0]),
        likelihood=np.array([[1.0, 0.0], [0.0, 1.0]]),
        preferences=np.array([0.5, 0.5]),
    )
    with pytest.raises(ValueError):
        energy.posterior(model, 1)
