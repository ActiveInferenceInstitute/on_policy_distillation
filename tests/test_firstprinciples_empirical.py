"""Tests for the curated empirical-benchmark module (literature-reported)."""

from __future__ import annotations

import pytest

from firstprinciples import empirical


def test_benchmark_rows_present_and_attributed() -> None:
    methods = {row.method for row in empirical.BENCHMARKS}
    assert methods == {"off_policy_distillation", "reinforcement_learning", "on_policy_distillation"}
    for row in empirical.BENCHMARKS:
        assert row.bibkey == "thinkingmachines2025opd"  # every figure is source-attributed


def test_compute_reduction_and_gain() -> None:
    # On-policy distillation: higher AIME'24 than RL at a fraction of the GPU-hours.
    assert empirical.compute_reduction() == pytest.approx(17920.0 / 1800.0)
    gain = empirical.accuracy_gain()
    assert gain["aime24_over_rl"] > 0.0
    assert gain["aime24_over_off_policy"] > 0.0


def test_payload_honest_flags() -> None:
    payload = empirical.build_payload()
    assert payload["schema"] == empirical.SCHEMA
    assert payload["source"] == "literature_reported"  # not measured here
    assert payload["opd_beats_rl_on_accuracy"] is True
    assert payload["opd_cheaper_than_rl"] is True
    assert payload["compute_reduction_factor"] > 1.0
    assert payload["ok"] is True


def test_markdown_table() -> None:
    table = empirical.markdown_table()
    assert "AIME'24" in table
    assert "on policy distillation" in table
    with pytest.raises(KeyError):
        empirical._row("does_not_exist")
