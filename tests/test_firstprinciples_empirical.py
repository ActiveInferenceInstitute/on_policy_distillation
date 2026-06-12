"""Tests for the curated empirical-benchmark module (literature-reported)."""

from __future__ import annotations

import pytest

from firstprinciples import empirical


def test_benchmark_rows_present_and_attributed() -> None:
    methods = {row.method for row in empirical.BENCHMARKS}
    assert methods == {"off_policy_distillation", "reinforcement_learning", "on_policy_distillation"}
    for row in empirical.BENCHMARKS:
        assert row.bibkey == "qwen2025technical_report"  # direct table source
        assert row.relayed_by == "thinkingmachines2025opd"  # contextual relay/replication post
        assert row.source_locator == "Qwen3 Technical Report, Table 21"
        assert "Qwen3-8B" in row.source_heading
        assert row.source_note


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
    assert payload["direct_bibkey"] == "qwen2025technical_report"
    assert payload["source_locator"] == "Qwen3 Technical Report, Table 21"
    assert payload["source_heading"] == "Comparison of reinforcement learning and on-policy distillation on Qwen3-8B"
    assert payload["relayed_by_bibkey"] == "thinkingmachines2025opd"
    assert payload["thinking_machines_replication"]["aime24_accuracy"] == pytest.approx(70.0)
    assert payload["thinking_machines_replication"]["efficiency_range_min"] == pytest.approx(9.0)
    assert payload["thinking_machines_replication"]["efficiency_range_max"] == pytest.approx(30.0)
    assert payload["opd_beats_rl_on_accuracy"] is True
    assert payload["opd_cheaper_than_rl"] is True
    assert payload["compute_reduction_factor"] > 1.0
    assert payload["ok"] is True


def test_markdown_table() -> None:
    table = empirical.markdown_table()
    assert "AIME'24" in table
    assert "on policy distillation" in table
    assert "qwen2025technical_report" in table
    assert "thinkingmachines2025opd" in table
    with pytest.raises(KeyError):
        empirical._row("does_not_exist")
