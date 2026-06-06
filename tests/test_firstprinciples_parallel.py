"""Tests for the two-framework (active-inference + jax ML) parallel demonstration."""

from __future__ import annotations

import numpy as np
import pytest

from firstprinciples import parallel


def test_ml_distillation_converges_to_teacher() -> None:
    teacher = np.array([0.7, 0.2, 0.1])
    result = parallel.ml_distill_to_teacher(teacher, steps=800, lr=0.5)
    assert result.reverse_kl_last < result.reverse_kl_first
    assert result.converged is True
    assert np.max(np.abs(np.asarray(result.student) - teacher)) < 1e-3


def test_parallel_payload_frameworks_agree() -> None:
    payload = parallel.build_payload()
    assert payload["schema"] == parallel.SCHEMA
    # The jax-distilled ML student reproduces the active-inference posterior...
    assert payload["frameworks_agree"] is True
    assert payload["max_abs_difference"] < 1e-3
    # ...and reaches the variational free-energy minimum -ln p(o).
    assert payload["free_energy_matches_minimum"] is True
    assert payload["ok"] is True


def test_ml_distillation_two_state() -> None:
    teacher = np.array([0.85, 0.15])
    result = parallel.ml_distill_to_teacher(teacher)
    assert result.converged is True
    assert abs(result.student[0] - 0.85) < 1e-3
