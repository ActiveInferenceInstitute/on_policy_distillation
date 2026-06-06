"""Tests for the statistics module and the pymdp privilege sweep."""

from __future__ import annotations

from pathlib import Path

import pytest

from firstprinciples import privilege, statistics as stats
from firstprinciples.privilege import PrivilegeSweepConfig
from firstprinciples.classroom import pymdp_available

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# statistics
# --------------------------------------------------------------------------- #
def test_summarize_and_validation() -> None:
    s = stats.summarize([1.0, 2.0, 3.0])
    assert s.n == 3 and s.mean == pytest.approx(2.0) and s.minimum == 1.0 and s.maximum == 3.0
    assert stats.summarize([5.0]).std == 0.0
    with pytest.raises(ValueError):
        stats.summarize([])


def test_bootstrap_ci_deterministic_and_brackets_mean() -> None:
    data = [0.10, 0.12, 0.09, 0.15, 0.11, 0.13]
    a = stats.bootstrap_ci(data, n_boot=500, seed=0)
    b = stats.bootstrap_ci(data, n_boot=500, seed=0)
    assert a == b  # deterministic
    assert a["ci_low"] <= a["point"] <= a["ci_high"]
    with pytest.raises(ValueError):
        stats.bootstrap_ci(data, alpha=1.5)


def test_cohens_d_sign_and_validation() -> None:
    d = stats.cohens_d([0.34, 0.36, 0.31, 0.38], [0.21, 0.25, 0.19, 0.27])
    assert d > 0.0  # student entropy higher than teacher
    assert stats.cohens_d([1.0, 1.0, 1.0], [1.0, 1.0, 1.0]) == 0.0
    with pytest.raises(ValueError):
        stats.cohens_d([1.0], [2.0, 3.0])


def test_paired_tests_detect_consistent_difference() -> None:
    student = [0.34, 0.36, 0.31, 0.38, 0.33, 0.30]
    teacher = [0.21, 0.25, 0.19, 0.27, 0.23, 0.20]
    perm = stats.paired_permutation_test(student, teacher, n_perm=2000, seed=0)
    assert perm["mean_difference"] > 0.0
    assert perm["p_value"] < 0.1
    sign = stats.paired_sign_test(student, teacher)
    assert sign["positive"] == 6.0 and sign["negative"] == 0.0
    assert sign["p_value"] < 0.05
    with pytest.raises(ValueError):
        stats.paired_permutation_test([1.0, 2.0], [1.0])


def test_paired_sign_test_all_zero() -> None:
    out = stats.paired_sign_test([1.0, 2.0], [1.0, 2.0])
    assert out["p_value"] == 1.0


def test_statistics_payload_ok() -> None:
    payload = stats.build_payload()
    assert payload["schema"] == stats.SCHEMA
    assert payload["ok"] is True
    assert payload["cohens_d_student_minus_teacher"] > 0.0


# --------------------------------------------------------------------------- #
# privilege sweep
# --------------------------------------------------------------------------- #
def test_rank_correlation_monotone() -> None:
    assert privilege.rank_correlation([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0]) == pytest.approx(1.0)
    assert privilege.rank_correlation([1.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0]) == pytest.approx(-1.0)
    assert privilege.rank_correlation([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]) == 0.0
    with pytest.raises(ValueError):
        privilege.rank_correlation([1.0], [1.0])


def test_privilege_config_validation() -> None:
    with pytest.raises(ValueError):
        PrivilegeSweepConfig(teacher_cue_validities=())
    with pytest.raises(ValueError):
        PrivilegeSweepConfig(teacher_cue_validities=(1.5,))


@pytest.mark.requires_pymdp
@pytest.mark.timeout(400)
@pytest.mark.skipif(not pymdp_available(), reason="inferactively-pymdp not installed")
def test_privilege_sweep_runs(tmp_path: Path) -> None:
    cfg = PrivilegeSweepConfig(teacher_cue_validities=(0.5, 0.98), student_cue_validity=0.5, steps=2, seed=0)
    out = privilege.run_privilege_sweep(PROJECT_ROOT, cfg)
    assert out["schema"] == privilege.SCHEMA
    assert len(out["levels"]) == 2
    # the high-privilege teacher should be at least as certain as the low-privilege one
    entropies = [lvl["teacher_belief_entropy"] for lvl in out["levels"]]
    assert entropies[-1] <= entropies[0] + 1e-6
