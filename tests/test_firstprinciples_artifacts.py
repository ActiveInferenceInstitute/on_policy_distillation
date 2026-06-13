"""Tests for the deterministic first-principles artifact emitters."""

from __future__ import annotations

import json
from pathlib import Path

from firstprinciples import artifacts


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_write_all_emits_validated_artifacts(tmp_path: Path) -> None:
    paths = artifacts.write_all(tmp_path)
    expected = {
        "correspondence_map.json",
        "opd_taxonomy.json",
        "divergence_demo.json",
        "reward_tilting_demo.json",
        "exposure_bias_demo.json",
        "sdpg_demo.json",
        "sequential_shift.json",
        "sequential_shift_sensitivity.json",
        "correspondence_table.md",
        "taxonomy_table.md",
    }
    assert expected <= set(paths)
    for name, path in paths.items():
        assert path.is_file()
        if name.endswith(".json"):
            payload = _load(path)
            assert payload["schema"].startswith("firstprinciples.")


def test_correspondence_and_taxonomy_payloads(tmp_path: Path) -> None:
    paths = artifacts.write_all(tmp_path)
    corr = _load(paths["correspondence_map.json"])
    assert corr["ok"] is True and corr["row_count"] >= 10
    tax = _load(paths["opd_taxonomy.json"])
    assert tax["method_count"] >= 8
    by_key = {row["bibkey"]: row for row in tax["methods"]}
    assert by_key["chen2026freshness_opd"]["acronym"] == "f-OPD"
    assert by_key["chen2026freshness_opd"]["signal_source"] == "freshness_aware_async_buffer"
    assert by_key["chen2026freshness_opd"]["divergence"] == "freshness_weighted_reverse_kl"
    assert by_key["chen2026freshness_opd"]["on_policy"] is True
    assert by_key["chen2026freshness_opd"]["privileged_info"] is False
    assert "freshness_aware_async_buffer" in tax["signal_sources"]


def test_divergence_demo_mode_seeking() -> None:
    demo = artifacts.divergence_demo()
    # Teacher is peaked; reverse KL (mode-seeking) is finite and smaller than
    # the symmetric JSD scaling would suggest; all values are finite.
    assert demo["reverse_kl"] >= 0.0
    assert demo["forward_kl"] >= 0.0
    assert demo["clipped_reverse_kl"] <= demo["reverse_kl"] + 1e-9
    assert demo["mode_concentration"]["mode_seeking"] in (True, False)


def test_reward_tilting_demo_optimal() -> None:
    demo = artifacts.reward_tilting_demo()
    assert demo["optimality"]["optimal"] is True


def test_exposure_bias_demo_collapses_off_policy() -> None:
    demo = artifacts.exposure_bias_demo()
    assert demo["gap"]["off_policy_collapses"] is True


def test_sdpg_demo_all_modes_present() -> None:
    demo = artifacts.sdpg_demo()
    assert set(demo["modes"]) == {"fkl", "rkl", "ufkl", "urkl"}
    assert demo["signal_density"]["denser_than_scalar"] is True


def test_markdown_tables_written(tmp_path: Path) -> None:
    paths = artifacts.write_markdown_tables(tmp_path)
    assert "| Method |" in paths["taxonomy_table.md"].read_text(encoding="utf-8")
    assert "Active inference" in paths["correspondence_table.md"].read_text(encoding="utf-8")
