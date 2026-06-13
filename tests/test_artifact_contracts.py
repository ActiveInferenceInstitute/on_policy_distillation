"""Tests for the neutral generated-artifact contract."""

from __future__ import annotations

from pathlib import Path

import yaml

from artifact_contracts import (
    ARTIFACT_CONSUMERS,
    ARTIFACT_GATES,
    ARTIFACT_PRODUCERS,
    DEFAULT_ANALYSIS_SCRIPTS,
    REQUIRED_OUTPUT_CHECK_KEYS,
    REQUIRED_OUTPUTS,
)
from gates.artifact_manifest import (
    REQUIRED_OUTPUT_CHECK_KEYS as LEGACY_REQUIRED_OUTPUT_CHECK_KEYS,
    REQUIRED_OUTPUTS as LEGACY_REQUIRED_OUTPUTS,
)
from manuscript.sheaf.semantic import (
    ARTIFACT_CONSUMERS as LEGACY_ARTIFACT_CONSUMERS,
    ARTIFACT_GATES as LEGACY_ARTIFACT_GATES,
    ARTIFACT_PRODUCERS as LEGACY_ARTIFACT_PRODUCERS,
)
from orchestration.pipeline_manifest import DEFAULT_ANALYSIS_SCRIPTS as LEGACY_ANALYSIS_SCRIPTS


def test_required_output_contract_has_no_duplicates() -> None:
    assert len(REQUIRED_OUTPUTS) == len(set(REQUIRED_OUTPUTS))
    assert len(REQUIRED_OUTPUT_CHECK_KEYS) == len(set(REQUIRED_OUTPUT_CHECK_KEYS))
    assert set(REQUIRED_OUTPUT_CHECK_KEYS) <= set(REQUIRED_OUTPUTS)


def test_configured_analysis_order_matches_contract(project_root: Path) -> None:
    config = yaml.safe_load((project_root / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
    assert config["analysis"]["scripts"] == [step.script for step in DEFAULT_ANALYSIS_SCRIPTS]


def test_required_outputs_have_configured_producers(project_root: Path) -> None:
    config = yaml.safe_load((project_root / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
    configured = set(config["analysis"]["scripts"])
    missing_producers = sorted(set(REQUIRED_OUTPUTS) - set(ARTIFACT_PRODUCERS))
    unknown_producers = sorted(set(ARTIFACT_PRODUCERS.values()) - configured)

    assert missing_producers == []
    assert unknown_producers == []


def test_firstprinciples_benchmark_statistics_artifacts_are_load_bearing() -> None:
    expected = {
        "output/data/firstprinciples/empirical_benchmark.json",
        "output/data/firstprinciples/statistics_demo.json",
        "output/data/firstprinciples/benchmark_table.md",
    }

    assert expected <= set(REQUIRED_OUTPUTS)
    assert expected <= set(REQUIRED_OUTPUT_CHECK_KEYS)
    assert {ARTIFACT_PRODUCERS[path] for path in expected} == {"generate_firstprinciples.py"}
    assert all(ARTIFACT_CONSUMERS[path] for path in expected)
    assert all("validate_outputs" in ARTIFACT_GATES[path] for path in expected)


def test_firstprinciples_sequential_sensitivity_artifacts_are_load_bearing() -> None:
    expected = {
        "output/data/firstprinciples/sequential_shift_sensitivity.json",
        "output/figures/sequential_shift_sensitivity.png",
    }

    assert expected <= set(REQUIRED_OUTPUTS)
    assert "output/data/firstprinciples/sequential_shift_sensitivity.json" in set(REQUIRED_OUTPUT_CHECK_KEYS)
    assert ARTIFACT_PRODUCERS["output/data/firstprinciples/sequential_shift_sensitivity.json"] == (
        "generate_firstprinciples.py"
    )
    assert ARTIFACT_PRODUCERS["output/figures/sequential_shift_sensitivity.png"] == "generate_figures.py"
    assert all(ARTIFACT_CONSUMERS[path] for path in expected)
    assert all("validate_outputs" in ARTIFACT_GATES[path] for path in expected)


def test_legacy_exports_match_neutral_contract() -> None:
    assert LEGACY_REQUIRED_OUTPUTS is REQUIRED_OUTPUTS
    assert LEGACY_REQUIRED_OUTPUT_CHECK_KEYS is REQUIRED_OUTPUT_CHECK_KEYS
    assert LEGACY_ANALYSIS_SCRIPTS is DEFAULT_ANALYSIS_SCRIPTS
    assert LEGACY_ARTIFACT_PRODUCERS is ARTIFACT_PRODUCERS
    assert LEGACY_ARTIFACT_CONSUMERS is ARTIFACT_CONSUMERS
    assert LEGACY_ARTIFACT_GATES is ARTIFACT_GATES


def test_semantic_module_does_not_redeclare_contract_maps(project_root: Path) -> None:
    source = (project_root / "src" / "manuscript" / "sheaf" / "semantic.py").read_text(encoding="utf-8")
    assert "ARTIFACT_CONSUMERS: dict" not in source
    assert "ARTIFACT_GATES: dict" not in source


def test_sheaf_tracks_reexports_canonical_track_contracts() -> None:
    from roadmap_tracks import sheaf_track_contracts as contracts
    from roadmap_tracks import sheaf_tracks

    assert sheaf_tracks.CANONICAL_TRACKS is contracts.CANONICAL_TRACKS
    assert sheaf_tracks.CANONICAL_ARTIFACTS is contracts.CANONICAL_ARTIFACTS
    assert sheaf_tracks.REQUIRED_EDGE_TYPES is contracts.REQUIRED_EDGE_TYPES
    assert sheaf_tracks.VERSIONED_TRACK_RE is contracts.VERSIONED_TRACK_RE
