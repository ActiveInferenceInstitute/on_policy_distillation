"""Regression checks for review-disposition ledgers."""

from __future__ import annotations

from pathlib import Path


def test_deep_review_ledger_records_qwen_table_pin_as_landed(project_root: Path) -> None:
    text = (project_root / "docs" / "reviews" / "deep-review-2026-06.md").read_text(encoding="utf-8")
    assert "Qwen3 Technical Report, Table 21" in text
    assert "Comparison of reinforcement learning and on-policy distillation on Qwen3-8B" in text
    assert "| External OPD-vs-RL table: pin exact Qwen table/figure | **LANDED** |" in text
    assert "table/figure pin **DEFERRED**" not in text
    assert "Requires re-opening the primary Qwen3 report" not in text
