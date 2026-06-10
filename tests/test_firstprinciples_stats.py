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
    teacher = [0.21, 0.25, 0.19, 0.27, 0.23, 0.20]
    student = [0.34, 0.36, 0.31, 0.38, 0.33, 0.30]
    payload = stats.build_payload(teacher, student)
    assert payload["schema"] == stats.SCHEMA
    assert payload["ok"] is True
    assert payload["sample_size"] == 6
    assert payload["paired_permutation"]["n"] == 6
    assert payload["paired_permutation"]["n_perm"] == 5000
    assert payload["effect_size_reference"] == "cohen1988power"
    assert payload["claim_scope"].startswith("toy-classroom")
    assert payload["cohens_d_student_minus_teacher"] > 0.0
    assert payload["teacher_entropy"] == teacher  # echoes its measured inputs


def test_statistics_payload_ok_is_not_a_significance_claim() -> None:
    teacher = [0.69, 0.10, 0.10, 0.10]
    student = [0.69, 0.69, 0.00, 0.00]
    payload = stats.build_payload(teacher, student)
    assert payload["ok"] is True
    assert payload["advantage_bootstrap_ci"]["ci_low"] < 0.0
    assert payload["paired_permutation"]["n"] == payload["sample_size"]
    assert payload["claim_scope"].startswith("toy-classroom")


def test_statistics_payload_requires_real_series() -> None:
    """No synthetic fallback: the artifact cannot exist without classroom data."""
    import inspect

    with pytest.raises(TypeError):
        stats.build_payload()  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        stats.build_payload([0.2, 0.3], [0.3])
    with pytest.raises(ValueError):
        stats.build_payload([0.2], [0.3])
    with pytest.raises(ValueError):
        stats.build_payload([0.2, float("nan")], [0.3, 0.4])
    # The module must not carry hard-coded entropy datasets anywhere.
    source = inspect.getsource(stats)
    assert "0.21, 0.25" not in source


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
@pytest.mark.render_slow
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


def test_privilege_sweep_payload_contract() -> None:
    """Contract + negative controls for the dose-response payload (no pymdp needed)."""
    import json
    from pathlib import Path

    artifact = Path(__file__).resolve().parents[1] / "output" / "data" / "firstprinciples" / "privilege_sweep.json"
    if not artifact.is_file():
        pytest.skip("privilege_sweep.json not generated yet (run generate_firstprinciples.py)")
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["schema"] == "firstprinciples.privilege_sweep.v1"
    levels = payload["levels"]
    assert len(levels) >= 2
    validities = [row["teacher_cue_validity"] for row in levels]
    assert validities == sorted(validities)
    # Re-derive the headline claims from the rows — never trust the flags alone.
    gaps = [row["entropy_gap"] for row in levels]
    for row in levels:
        assert abs(row["entropy_gap"] - (row["student_belief_entropy"] - row["teacher_belief_entropy"])) <= 1e-12
    baseline_rows = [g for v, g in zip(validities, gaps, strict=True) if v == payload["student_cue_validity"]]
    assert baseline_rows and abs(baseline_rows[0]) <= 1e-9  # identical agents ⇒ exactly zero
    assert payload["h4_baseline_gap_zero"] is True
    # Monotone non-decreasing claim must match the data the flag summarizes.
    non_decreasing = all(b >= a - 1e-12 for a, b in zip(gaps, gaps[1:], strict=False))
    assert payload["h3_gap_grows_with_privilege"] == (payload["gap_rank_correlation"] >= 0.0)
    assert non_decreasing  # current deterministic sweep is a clean step

    # Negative control: a doctored non-monotone gap series must flip the flags
    # when re-derived through the builder's own correlation.
    from firstprinciples.privilege import rank_correlation

    doctored = list(gaps)
    doctored[0], doctored[-1] = doctored[-1], doctored[0]
    assert rank_correlation(validities, doctored) < 0.0  # the oracle bites
